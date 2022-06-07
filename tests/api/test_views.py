import json
from datetime import timedelta
from urllib.parse import parse_qs, urlparse

import pytest
from django.urls import reverse
from django.utils import timezone
from oauth2_provider.models import Application

from haven.api.models import ApplicationProfile
from haven.api.utils import WORK_PACKAGE_TIER_EXPIRY_SECONDS_MAP
from haven.core import recipes
from haven.projects.roles import ProjectRole


@pytest.mark.django_db
class TestOAuthFlow:
    def test_oauth_flow(
        self,
        as_system_manager,
        pkce_verifier,
        pkce_code_challenge,
        oauth_application_registration_data,
    ):
        """This tests that a client can use the OAuth2 views to gain an access token"""
        original_application_count = Application.objects.count()
        original_application_profile_count = ApplicationProfile.objects.count()

        # Register a new client (e.g. data-access-controller)
        response = as_system_manager.post(
            reverse("oauth2_provider:register"),
            data=oauth_application_registration_data,
        )
        assert response.status_code == 302

        assert Application.objects.count() == original_application_count + 1
        assert ApplicationProfile.objects.count() == original_application_profile_count + 1

        application = Application.objects.last()
        application_profile = ApplicationProfile.objects.last()

        # Assert `ApplicationProfile` object created with the correct information
        assert application_profile.application == application
        assert (
            application_profile.maximum_tier == oauth_application_registration_data["maximum_tier"]
        )

        # Assert redirected to application detail view
        assert response.url == reverse("oauth2_provider:detail", kwargs={"pk": application.id})

        authorize_data = {
            "redirect_uri": oauth_application_registration_data["redirect_uris"],
            "scope": "read write",
            "nonce": "",
            "client_id": oauth_application_registration_data["client_id"],
            "state": "",
            "response_type": "code",
            "code_challenge": pkce_code_challenge,
            "code_challenge_method": "S256",
            "claims": "",
            "allow": "Authorize",
        }
        # Authorize access, this is equivalent to a user clicking the "Authorize" button in the
        # browser
        response = as_system_manager.post(reverse("oauth2_provider:authorize"), data=authorize_data)

        assert response.status_code == 302

        # Get `code` from redirect url
        parsed_query_params = parse_qs(urlparse(response.url).query)
        assert "code" in parsed_query_params
        auth_code = parsed_query_params["code"][0]

        # Request access token with authentication code from previous request
        response = as_system_manager.post(
            reverse("oauth2_provider:token"),
            data={
                "redirect_uri": oauth_application_registration_data["redirect_uris"],
                "client_id": oauth_application_registration_data["client_id"],
                "client_secret": oauth_application_registration_data["client_secret"],
                "code": auth_code,
                "code_verifier": pkce_verifier,
                "grant_type": "authorization_code",
            },
        )

        assert response.status_code == 200

        # Get contents of response
        response_json = json.loads(response.content.decode())

        # Ensure tokens and scope are present
        assert response_json.get("access_token")
        assert response_json.get("refresh_token")
        assert response_json["scope"] == authorize_data["scope"]

    def test_application_profile_update(
        self,
        as_system_manager,
        oauth_application_registration_data,
        oauth_application,
        application_profile,
    ):
        """
        This tests a system manager can update the application profile from the application update
        view
        """
        original_application_profile_count = ApplicationProfile.objects.count()

        maximum_tier = 1
        update_data = {
            **oauth_application_registration_data,
            **{"maximum_tier": maximum_tier},
        }

        # Register a new client (e.g. data-access-controller)
        response = as_system_manager.post(
            reverse("oauth2_provider:update", kwargs={"pk": oauth_application.id}),
            data=update_data,
        )
        assert response.status_code == 302

        # Assert no new application profile objects created
        assert ApplicationProfile.objects.count() == original_application_profile_count

        application_profile.refresh_from_db()
        assert application_profile.maximum_tier == maximum_tier


@pytest.mark.django_db
class TestDatasetListAPIView:
    def test_get_dataset_list(
        self,
        project_participant,
        as_project_participant_api,
        classified_work_package,
        make_accessible_work_package,
    ):
        """
        Test that an API user can request dataset list api to see which datasets they have access
        to. The user must be a participant of a project, the datasets must be associated with this
        project and a classified work package, which this user is also associated with.
        """
        num_accessible_datasets = 3
        accessible_work_packages = [
            make_accessible_work_package(project_participant)
            for _ in range(num_accessible_datasets)
        ]

        # Create more work packages that are not associated with api user, and associated datasets
        # should not show up in dataset list view
        unaccessible_work_packages = [classified_work_package(0) for _ in range(3)]

        response = as_project_participant_api.get(reverse("api:dataset_list"))

        assert response.status_code == 200

        results = json.loads(response.content.decode())["results"]

        assert len(results) == num_accessible_datasets

        uuid_results = [dataset["uuid"] for dataset in results]

        # Assert datasets in `accessible_work_packages` are in results
        for work_package in accessible_work_packages:
            for dataset in work_package.datasets.all():
                assert str(dataset.uuid) in uuid_results

                matching_dataset = list(
                    filter(lambda x: x.get("uuid", None) == str(dataset.uuid), results)
                )[0]

                # Assert that the related accessible work packages are returned as a part of
                # serialization
                expected_work_packages = set(
                    str(uuid) for uuid in dataset.work_packages.all().values_list("uuid", flat=True)
                )
                assert expected_work_packages == set(matching_dataset["work_packages"])
                # Assert that the related projects are returned as a part of serialization
                expected_projects = set(
                    str(uuid) for uuid in dataset.projects.all().values_list("uuid", flat=True)
                )
                assert expected_projects == set(matching_dataset["projects"])

                assert (
                    matching_dataset["default_representative_email"]
                    == dataset.default_representative.email
                )

        # Assert datasets in `unaccessible_work_packages` are not in results
        for work_package in unaccessible_work_packages:
            for dataset in work_package.datasets.all():
                assert str(dataset.uuid) not in uuid_results

    def test_get_dataset_list_empty(
        self,
        as_project_participant_api,
        classified_work_package,
    ):
        """
        Test that dataset list view returns an empty array when there are no accessible datasets
        """
        # Create work packages that are not associated with api user, and associated datasets
        # should not show up in dataset list view
        [classified_work_package(0) for _ in range(3)]

        response = as_project_participant_api.get(reverse("api:dataset_list"))

        assert response.status_code == 200

        results = json.loads(response.content.decode())["results"]
        assert results == []

    def test_get_dataset_list_missing_token(self, DRFClient):
        """
        Test that dataset list API returns an error response when access token is not present in
        headers
        """
        # By default DRFClient has no access token applied
        response = DRFClient.get(reverse("api:dataset_list"))
        assert response.status_code == 401

    def test_get_project_dataset_list(
        self,
        project_participant,
        as_project_participant_api,
        classified_work_package,
        make_accessible_work_package,
    ):
        """
        Test that an API user can request project dataset list api to see which datasets they have
        access to for a specific project.
        The user must be a participant of a project, the datasets must be associated with this
        project and a classified work package, which this user is also associated with.
        """
        accessible_work_package = make_accessible_work_package(project_participant)

        # Create more work packages that are not associated with api user, and associated datasets
        # should not show up in dataset list view
        unaccessible_work_packages = [classified_work_package(0) for _ in range(3)]

        # Filter dataset list view by one project
        response = as_project_participant_api.get(
            reverse(
                "api:project_dataset_list",
                kwargs={"projects__uuid": accessible_work_package.project.uuid},
            )
        )

        assert response.status_code == 200

        results = json.loads(response.content.decode())["results"]

        assert len(results) == 1

        uuid_results = [dataset["uuid"] for dataset in results]

        for dataset in accessible_work_package.datasets.all():
            assert str(dataset.uuid) in uuid_results

        # Assert datasets in `unaccessible_work_packages` are not in results
        for work_package in unaccessible_work_packages:
            for dataset in work_package.datasets.all():
                assert str(dataset.uuid) not in uuid_results

    def test_get_work_package_dataset_list(
        self,
        project_participant,
        as_project_participant_api,
        classified_work_package,
        make_accessible_work_package,
    ):
        """
        Test that an API user can request work package dataset list api to see which
        datasets they have to for a specific work package.
        The user must be a participant of a project, the datasets must be associated with this
        project and a classified work package, which this user is also associated with.
        """
        accessible_work_package = make_accessible_work_package(project_participant)

        # Create more work packages that are not associated with api user, and associated datasets
        # should not show up in dataset list view
        unaccessible_work_packages = [classified_work_package(0) for _ in range(3)]

        # Filter dataset list view by one work package
        response = as_project_participant_api.get(
            reverse(
                "api:work_package_dataset_list",
                kwargs={"work_packages__uuid": accessible_work_package.uuid},
            )
        )

        assert response.status_code == 200

        results = json.loads(response.content.decode())["results"]

        assert len(results) == 1

        uuid_results = [dataset["uuid"] for dataset in results]

        for dataset in accessible_work_package.datasets.all():
            assert str(dataset.uuid) in uuid_results

        # Assert datasets in `unaccessible_work_packages` are not in results
        for work_package in unaccessible_work_packages:
            for dataset in work_package.datasets.all():
                assert str(dataset.uuid) not in uuid_results

    def test_get_project_work_package_dataset_list(
        self,
        project_participant,
        as_project_participant_api,
        classified_work_package,
        make_accessible_work_package,
    ):
        """
        Test that an API user can request project work package dataset list api to see which
        datasets they have to for a specific project and work package.
        The user must be a participant of a project, the datasets must be associated with this
        project and a classified work package, which this user is also associated with.
        """
        accessible_work_package = make_accessible_work_package(project_participant)

        # Create more work packages that are not associated with api user, and associated datasets
        # should not show up in dataset list view
        unaccessible_work_packages = [classified_work_package(0) for _ in range(3)]

        # Filter dataset list view by one project and work package
        response = as_project_participant_api.get(
            reverse(
                "api:project_work_package_dataset_list",
                kwargs={
                    "projects__uuid": accessible_work_package.project.uuid,
                    "work_packages__uuid": accessible_work_package.uuid,
                },
            )
        )

        assert response.status_code == 200

        results = json.loads(response.content.decode())["results"]

        assert len(results) == 1

        uuid_results = [dataset["uuid"] for dataset in results]

        for dataset in accessible_work_package.datasets.all():
            assert str(dataset.uuid) in uuid_results

        # Assert datasets in `unaccessible_work_packages` are not in results
        for work_package in unaccessible_work_packages:
            for dataset in work_package.datasets.all():
                assert str(dataset.uuid) not in uuid_results

    def test_system_manager_dataset_list(
        self,
        system_manager,
        as_system_manager_api,
        classified_work_package,
        make_accessible_work_package,
    ):
        """
        Test a system manager can request dataset list api to see all datasets, regardless of
        whether they are participants of the project/work package.
        """
        work_packages = [make_accessible_work_package(system_manager) for _ in range(3)]

        # Create more work packages that are not associated with api user, the associated datasets
        # should still be returned for system managers
        other_work_packages = [classified_work_package(0) for _ in range(3)]

        response = as_system_manager_api.get(reverse("api:dataset_list"))

        assert response.status_code == 200

        results = json.loads(response.content.decode())["results"]

        assert len(results) == len(work_packages) + len(other_work_packages)

        uuid_results = [dataset["uuid"] for dataset in results]

        # Assert all datasets in` are in results
        for work_package in work_packages + other_work_packages:
            for dataset in work_package.datasets.all():
                assert str(dataset.uuid) in uuid_results

                matching_dataset = list(
                    filter(lambda x: x.get("uuid", None) == str(dataset.uuid), results)
                )[0]

                # Assert that the related accessible work packages are returned as a part of
                # serialization
                expected_work_packages = set(
                    str(uuid) for uuid in dataset.work_packages.all().values_list("uuid", flat=True)
                )
                assert expected_work_packages == set(matching_dataset["work_packages"])
                # Assert that the related projects are returned as a part of serialization
                expected_projects = set(
                    str(uuid) for uuid in dataset.projects.all().values_list("uuid", flat=True)
                )
                assert expected_projects == set(matching_dataset["projects"])

                assert (
                    matching_dataset["default_representative_email"]
                    == dataset.default_representative.email
                )

    def test_programme_manager_dataset_list(
        self,
        programme_manager,
        as_programme_manager_api,
        classified_work_package,
        make_accessible_work_package,
    ):
        """
        Test a programme manager can request dataset list api to see all datasets, regardless of
        whether they are participants of the project/work package.
        """
        work_packages = [make_accessible_work_package(programme_manager) for _ in range(3)]

        # Create more work packages that are not associated with api user, the associated datasets
        # should still be returned for programme managers
        other_work_packages = [classified_work_package(0) for _ in range(3)]

        response = as_programme_manager_api.get(reverse("api:dataset_list"))

        assert response.status_code == 200

        results = json.loads(response.content.decode())["results"]

        assert len(results) == len(work_packages) + len(other_work_packages)

        uuid_results = [dataset["uuid"] for dataset in results]

        # Assert all datasets in` are in results
        for work_package in work_packages + other_work_packages:
            for dataset in work_package.datasets.all():
                assert str(dataset.uuid) in uuid_results

                matching_dataset = list(
                    filter(lambda x: x.get("uuid", None) == str(dataset.uuid), results)
                )[0]

                # Assert that the related accessible work packages are returned as a part of
                # serialization
                expected_work_packages = set(
                    str(uuid) for uuid in dataset.work_packages.all().values_list("uuid", flat=True)
                )
                assert expected_work_packages == set(matching_dataset["work_packages"])
                # Assert that the related projects are returned as a part of serialization
                expected_projects = set(
                    str(uuid) for uuid in dataset.projects.all().values_list("uuid", flat=True)
                )
                assert expected_projects == set(matching_dataset["projects"])

                assert (
                    matching_dataset["default_representative_email"]
                    == dataset.default_representative.email
                )

    def test_limited_by_maximum_tier(
        self,
        project_participant,
        as_project_participant_api,
        make_accessible_work_package,
        application_profile,
    ):
        """
        Test that an API user is limited to datasets by the `maximum_tier` of the application
        profile
        """
        application_profile.maximum_tier = 2
        application_profile.save()

        num_accessible_datasets = 3
        accessible_work_packages = [
            make_accessible_work_package(project_participant, tier=0)
            for _ in range(num_accessible_datasets)
        ]

        # The datasets associated with these work packages are unaccessible because the tier is
        # higher than the maximum tier allowed by the application profile
        unaccessible_work_packages = [
            make_accessible_work_package(project_participant, tier=4) for _ in range(3)
        ]

        response = as_project_participant_api.get(reverse("api:dataset_list"))

        assert response.status_code == 200

        results = json.loads(response.content.decode())["results"]

        assert len(results) == num_accessible_datasets

        uuid_results = [dataset["uuid"] for dataset in results]

        # Assert datasets in `accessible_work_packages` are in results
        for work_package in accessible_work_packages:
            for dataset in work_package.datasets.all():
                assert str(dataset.uuid) in uuid_results

                matching_dataset = list(
                    filter(lambda x: x.get("uuid", None) == str(dataset.uuid), results)
                )[0]

                # Assert that the related accessible work packages are returned as a part of
                # serialization
                expected_work_packages = set(
                    str(uuid) for uuid in dataset.work_packages.all().values_list("uuid", flat=True)
                )
                assert expected_work_packages == set(matching_dataset["work_packages"])
                # Assert that the related projects are returned as a part of serialization
                expected_projects = set(
                    str(uuid) for uuid in dataset.projects.all().values_list("uuid", flat=True)
                )
                assert expected_projects == set(matching_dataset["projects"])

                assert (
                    matching_dataset["default_representative_email"]
                    == dataset.default_representative.email
                )

        # Assert datasets in `unaccessible_work_packages` are not in results
        for work_package in unaccessible_work_packages:
            for dataset in work_package.datasets.all():
                assert str(dataset.uuid) not in uuid_results

    def test_one_dataset_two_classified_work_packages(
        self,
        project_participant,
        as_project_participant_api,
        make_accessible_work_package,
        application_profile,
        investigator,
    ):
        """
        Test that if a dataset is associated with two work packages, one with a tier above and one
        with a tier below than the maximum tier, and the requesting user is a participant of both
        work packages, that the user can still see the dataset
        """
        application_profile.maximum_tier = 2
        application_profile.save()

        accessible_work_package = make_accessible_work_package(project_participant, tier=0)
        unaccessible_work_package = make_accessible_work_package(project_participant, tier=4)

        unaccessible_work_package.project = accessible_work_package.project
        unaccessible_work_package.save()

        unaccessible_work_package.add_dataset(
            accessible_work_package.datasets.last(), investigator.user
        )

        response = as_project_participant_api.get(reverse("api:dataset_list"))

        assert response.status_code == 200

        results = json.loads(response.content.decode())["results"]

        assert len(results) == 1

        uuid_results = [dataset["uuid"] for dataset in results]

        dataset = accessible_work_package.datasets.last()

        # Assert dataset can still be seen in results even though it has two work packages, one
        # above and one below the maximum tier
        assert str(dataset.uuid) in uuid_results

        matching_dataset = list(
            filter(lambda x: x.get("uuid", None) == str(dataset.uuid), results)
        )[0]

        # Assert only work package with tier below the maximum tier is returned in serialized
        # work packages
        assert set([str(accessible_work_package.uuid)]) == set(matching_dataset["work_packages"])
        # Assert that the related projects are returned as a part of serialization
        expected_projects = set(
            str(uuid) for uuid in dataset.projects.all().values_list("uuid", flat=True)
        )
        assert expected_projects == set(matching_dataset["projects"])

        assert (
            matching_dataset["default_representative_email"] == dataset.default_representative.email
        )


@pytest.mark.django_db
class TestDatasetDetailAPIView:
    def test_get_dataset_detail(
        self,
        project_participant,
        as_project_participant_api,
        make_accessible_work_package,
    ):
        """
        Test that an API user can request dataset detail api to see dataset information if they
        have access to it.
        The user must be a participant of a project, the dataset must be associated with this
        project and a classified work package, which this user is also associated with.
        """
        work_package = make_accessible_work_package(project_participant)

        dataset = work_package.datasets.last()

        response = as_project_participant_api.get(
            reverse("api:dataset_detail", kwargs={"uuid": dataset.uuid})
        )

        assert response.status_code == 200

        result = json.loads(response.content.decode())
        assert result["uuid"] == str(dataset.uuid)

        # Assert that the related accessible work packages are returned as a part of serialization
        expected_work_packages = set(
            str(uuid) for uuid in dataset.work_packages.all().values_list("uuid", flat=True)
        )
        assert expected_work_packages == set(result["work_packages"])
        # Assert that the related projects are returned as a part of serialization
        expected_projects = set(
            str(uuid) for uuid in dataset.projects.all().values_list("uuid", flat=True)
        )
        assert expected_projects == set(result["projects"])

        assert result["default_representative_email"] == dataset.default_representative.email

    def test_get_dataset_detail_not_accessible(
        self,
        as_project_participant_api,
        classified_work_package,
    ):
        """
        Test that dataset detail view returns an error response when there are no accessible
        datasets
        """
        # Create work package that is not associated with api user, and associated dataset
        # should not show up in dataset detail view
        work_package = classified_work_package(0)

        response = as_project_participant_api.get(
            reverse("api:dataset_detail", kwargs={"uuid": work_package.datasets.last().uuid})
        )

        assert response.status_code == 404

    def test_get_dataset_detail_missing_token(self, DRFClient, classified_work_package):
        """
        Test dataset detail API returns an error response when access token is not present in
        headers
        """
        work_package = classified_work_package(0)

        # By default DRFClient has no access token applied
        response = DRFClient.get(
            reverse("api:dataset_detail", kwargs={"uuid": work_package.datasets.last().uuid})
        )
        assert response.status_code == 401

    def test_get_project_dataset_detail(
        self,
        project_participant,
        as_project_participant_api,
        make_accessible_work_package,
    ):
        """
        Test that an API user can request project dataset detail api to see dataset information if
        they have access to it for a specific project.
        The user must be a participant of a project, the dataset must be associated with this
        project and a classified work package, which this user is also associated with.
        """
        work_package = make_accessible_work_package(project_participant)

        dataset = work_package.datasets.last()

        response = as_project_participant_api.get(
            reverse(
                "api:project_dataset_detail",
                kwargs={
                    "projects__uuid": work_package.project.uuid,
                    "uuid": work_package.datasets.last().uuid,
                },
            )
        )

        assert response.status_code == 200

        result = json.loads(response.content.decode())
        assert result["uuid"] == str(dataset.uuid)

    def test_get_work_package_dataset_detail(
        self,
        project_participant,
        as_project_participant_api,
        make_accessible_work_package,
    ):
        """
        Test that an API user can request work package dataset detail api to see dataset information
        if they have access to it for a specific work package.
        The user must be a participant of a project, the dataset must be associated with this
        project and a classified work package, which this user is also associated with.
        """
        work_package = make_accessible_work_package(project_participant)

        dataset = work_package.datasets.last()

        response = as_project_participant_api.get(
            reverse(
                "api:work_package_dataset_detail",
                kwargs={
                    "work_packages__uuid": work_package.uuid,
                    "uuid": work_package.datasets.last().uuid,
                },
            )
        )

        assert response.status_code == 200

        result = json.loads(response.content.decode())
        assert result["uuid"] == str(dataset.uuid)

    def test_get_project_work_package_dataset_detail(
        self,
        project_participant,
        as_project_participant_api,
        make_accessible_work_package,
    ):
        """
        Test that an API user can request project work package dataset detail api to see dataset
        information if they have access to it for a specific project and work package.
        The user must be a participant of a project, the dataset must be associated with this
        project and a classified work package, which this user is also associated with.
        """
        work_package = make_accessible_work_package(project_participant)

        dataset = work_package.datasets.last()

        response = as_project_participant_api.get(
            reverse(
                "api:project_work_package_dataset_detail",
                kwargs={
                    "projects__uuid": work_package.project.uuid,
                    "work_packages__uuid": work_package.uuid,
                    "uuid": work_package.datasets.last().uuid,
                },
            )
        )

        assert response.status_code == 200

        result = json.loads(response.content.decode())
        assert result["uuid"] == str(dataset.uuid)

    def test_limited_by_maximum_tier(
        self,
        project_participant,
        as_project_participant_api,
        make_accessible_work_package,
        application_profile,
    ):
        """
        Test that if dataset is associated with a work package that has a tier above the maximum
        tier of the work package that the dataset detail API does not return this dataset
        """
        application_profile.maximum_tier = 2
        application_profile.save()

        # Dataset associated with this work package will not be returned over the API because the
        # tier is above the maximum tier of the application profile
        work_package = make_accessible_work_package(project_participant, tier=4)

        dataset = work_package.datasets.last()

        response = as_project_participant_api.get(
            reverse("api:dataset_detail", kwargs={"uuid": dataset.uuid})
        )

        assert response.status_code == 404


@pytest.mark.django_db
class TestDatasetExpiryAPIView:
    # Freeze time to make testing datetimes deterministic
    @pytest.mark.freeze_time("2022-01-01")
    @pytest.mark.parametrize("work_package_tier", [0, 1, 2, 3, 4])
    def test_expires_at(
        self,
        work_package_tier,
        project_participant,
        as_project_participant_api,
        make_accessible_work_package,
    ):
        """
        Test that dataset expiry API returns the correct `expires_at` datetime for work package tier
        """
        work_package = make_accessible_work_package(project_participant)
        work_package.tier = work_package_tier
        work_package.save()

        dataset = work_package.datasets.last()

        response = as_project_participant_api.get(
            reverse("api:dataset_expiry", kwargs={"uuid": str(dataset.uuid)})
        )

        assert response.status_code == 200

        result = json.loads(response.content.decode())

        assert result["uuid"] == str(dataset.uuid)
        assert result["expires_at"] == str(
            timezone.now()
            + timedelta(seconds=WORK_PACKAGE_TIER_EXPIRY_SECONDS_MAP[work_package_tier])
        )

    # Freeze time to make testing datetimes deterministic
    @pytest.mark.freeze_time("2022-01-01")
    def test_expires_at_uses_maximum_tier(
        self,
        project_participant,
        as_project_participant_api,
        make_accessible_work_package,
        programme_manager,
        data_provider_representative,
    ):
        """
        Test that if dataset has multiple classified work packages associated with it that the
        `expires_at` datetime uses the highest work package tier
        """
        work_package = make_accessible_work_package(project_participant)
        work_package.tier = 0
        work_package.save()
        dataset = work_package.datasets.last()

        # Associate dataset with 4 further classified work packages
        for work_package_tier in range(1, 5):
            work_package = make_accessible_work_package(project_participant)
            work_package.tier = work_package_tier
            work_package.save()
            work_package.project.add_dataset(
                dataset, data_provider_representative.user, programme_manager
            )
            work_package.add_dataset(dataset, programme_manager)

        response = as_project_participant_api.get(
            reverse("api:dataset_expiry", kwargs={"uuid": str(dataset.uuid)})
        )

        assert response.status_code == 200

        result = json.loads(response.content.decode())

        assert result["uuid"] == str(dataset.uuid)
        assert result["expires_at"] == str(
            timezone.now()
            # Assert that the highest tier is used, in this case zero
            + timedelta(seconds=WORK_PACKAGE_TIER_EXPIRY_SECONDS_MAP[4])
        )

    def test_limited_by_maximum_tier(
        self,
        project_participant,
        as_project_participant_api,
        make_accessible_work_package,
        application_profile,
    ):
        """
        Test that if dataset is associated with a work package that has a tier above the maximum
        tier of the work package that the dataset expiry API does not return this dataset
        """
        application_profile.maximum_tier = 2
        application_profile.save()

        # Dataset associated with this work package will not be returned over the API because the
        # tier is above the maximum tier of the application profile
        work_package = make_accessible_work_package(project_participant, tier=4)

        dataset = work_package.datasets.last()

        response = as_project_participant_api.get(
            reverse("api:dataset_expiry", kwargs={"uuid": dataset.uuid})
        )

        assert response.status_code == 404


@pytest.mark.django_db
class TestProjectListAPIView:
    def test_get_project_list(
        self,
        programme_manager,
        project_participant,
        as_project_participant_api,
    ):
        """
        Test that an API user can request project list api to see which projects they have to.
        The user must be a participant of a project to access it.
        """
        num_accessible_projects = 3
        # Create projects and add api user
        accessible_projects = [
            recipes.project.make(created_by=programme_manager)
            for _ in range(num_accessible_projects)
        ]
        for project in accessible_projects:
            project.add_user(
                user=project_participant,
                role=ProjectRole.RESEARCHER.value,
                created_by=programme_manager,
            )

        # Create more projects that are not associated with api user, these projects will not show
        # up in project list view
        unaccessible_projects = [
            recipes.project.make(created_by=programme_manager) for _ in range(3)
        ]

        response = as_project_participant_api.get(reverse("api:project_list"))

        assert response.status_code == 200

        results = json.loads(response.content.decode())["results"]

        assert len(results) == num_accessible_projects

        uuid_results = [project["uuid"] for project in results]

        # Assert projects in `accessible_projects` are in results
        for project in accessible_projects:
            assert str(project.uuid) in uuid_results

            matching_project = list(
                filter(lambda x: x.get("uuid", None) == str(project.uuid), results)
            )[0]

            # Assert that the related accessible work packages are returned as a part of
            # serialization
            expected_work_packages = set(
                str(uuid) for uuid in project.work_packages.all().values_list("uuid", flat=True)
            )
            assert expected_work_packages == set(matching_project["work_packages"])
            # Assert that the related accessible datasets are returned as a part of serialization
            expected_datasets = set(
                str(uuid) for uuid in project.datasets.all().values_list("uuid", flat=True)
            )
            assert expected_datasets == set(matching_project["datasets"])

        # Assert projects in `unaccessible_projects` are not in results
        for project in unaccessible_projects:
            assert str(project.uuid) not in uuid_results

    def test_get_project_list_empty(
        self,
        as_project_participant_api,
        programme_manager,
    ):
        """
        Test that project list view returns an empty array when there are no accessible datasets
        """
        # Create projects that are not associated with api user, these projects will not show
        # up in project list view
        [recipes.project.make(created_by=programme_manager) for _ in range(3)]

        response = as_project_participant_api.get(reverse("api:project_list"))

        assert response.status_code == 200

        results = json.loads(response.content.decode())["results"]
        assert results == []

    def test_get_project_list_missing_token(self, DRFClient):
        """
        Test that project list API returns an error response when access token is not present in
        headers
        """
        # By default DRFClient has no access token applied
        response = DRFClient.get(reverse("api:project_list"))
        assert response.status_code == 401

    def test_system_manager_project_list(
        self,
        programme_manager,
        system_manager,
        as_system_manager_api,
    ):
        """
        Test that system manager can request project list api and see all projects, regardless of
        whether they are a participant
        """
        # Create projects and add api user
        projects = [recipes.project.make(created_by=programme_manager) for _ in range(3)]
        for project in projects:
            project.add_user(
                user=system_manager,
                role=ProjectRole.RESEARCHER.value,
                created_by=programme_manager,
            )

        # Create more projects that are not associated with api user, these projects will still show
        # up in project list view for system manager
        other_projects = [recipes.project.make(created_by=programme_manager) for _ in range(3)]

        response = as_system_manager_api.get(reverse("api:project_list"))

        assert response.status_code == 200

        results = json.loads(response.content.decode())["results"]

        assert len(results) == len(projects) + len(other_projects)

        uuid_results = [project["uuid"] for project in results]

        # Assert all projects are in results for system manager
        for project in projects + other_projects:
            assert str(project.uuid) in uuid_results

            matching_project = list(
                filter(lambda x: x.get("uuid", None) == str(project.uuid), results)
            )[0]

            # Assert that the related accessible work packages are returned as a part of
            # serialization
            expected_work_packages = set(
                str(uuid) for uuid in project.work_packages.all().values_list("uuid", flat=True)
            )
            assert expected_work_packages == set(matching_project["work_packages"])
            # Assert that the related accessible datasets are returned as a part of serialization
            expected_datasets = set(
                str(uuid) for uuid in project.datasets.all().values_list("uuid", flat=True)
            )
            assert expected_datasets == set(matching_project["datasets"])

    def test_programme_manager_project_list(
        self,
        programme_manager,
        system_manager,
        as_programme_manager_api,
    ):
        """
        Test that programme manager can request project list api and see all projects, regardless of
        whether they are a participant
        """
        # Create projects and add api user
        projects = [recipes.project.make(created_by=system_manager) for _ in range(3)]
        for project in projects:
            project.add_user(
                user=system_manager,
                role=ProjectRole.RESEARCHER.value,
                created_by=programme_manager,
            )

        # Create more projects that are not associated with api user, these projects will still show
        # up in project list view for programme manager
        other_projects = [recipes.project.make(created_by=system_manager) for _ in range(3)]

        response = as_programme_manager_api.get(reverse("api:project_list"))

        assert response.status_code == 200

        results = json.loads(response.content.decode())["results"]

        assert len(results) == len(projects) + len(other_projects)

        uuid_results = [project["uuid"] for project in results]

        # Assert all projects are in results for programme manager
        for project in projects + other_projects:
            assert str(project.uuid) in uuid_results

            matching_project = list(
                filter(lambda x: x.get("uuid", None) == str(project.uuid), results)
            )[0]

            # Assert that the related accessible work packages are returned as a part of
            # serialization
            expected_work_packages = set(
                str(uuid) for uuid in project.work_packages.all().values_list("uuid", flat=True)
            )
            assert expected_work_packages == set(matching_project["work_packages"])
            # Assert that the related accessible datasets are returned as a part of serialization
            expected_datasets = set(
                str(uuid) for uuid in project.datasets.all().values_list("uuid", flat=True)
            )
            assert expected_datasets == set(matching_project["datasets"])


@pytest.mark.django_db
class TestProjectDetailAPIView:
    def test_get_project_detail(
        self,
        programme_manager,
        project_participant,
        as_project_participant_api,
        make_accessible_work_package,
        data_provider_representative,
        investigator,
    ):
        """
        Test that an API user can request project detail api to see project information if they
        have access to it.
        The user must be a participant of a project to access it.
        """
        # Create project and add api user
        project = recipes.project.make(created_by=programme_manager)
        project.add_user(
            user=project_participant,
            role=ProjectRole.RESEARCHER.value,
            created_by=programme_manager,
        )

        # Add accessible work packages and datasets to project
        work_packages = [make_accessible_work_package(project_participant) for i in range(3)]
        for work_package in work_packages:
            work_package.project = project
            work_package.save()
            for dataset in work_package.datasets.all():
                project.add_dataset(dataset, data_provider_representative.user, investigator.user)

        response = as_project_participant_api.get(
            reverse("api:project_detail", kwargs={"uuid": project.uuid})
        )

        assert response.status_code == 200

        result = json.loads(response.content.decode())
        assert result["uuid"] == str(project.uuid)

        # Assert that the related accessible work packages are returned as a part of serialization
        expected_work_packages = set(
            str(uuid) for uuid in project.work_packages.all().values_list("uuid", flat=True)
        )
        assert expected_work_packages == set(result["work_packages"])
        # Assert that the related accessible datasets are returned as a part of serialization
        expected_datasets = set(
            str(uuid) for uuid in project.datasets.all().values_list("uuid", flat=True)
        )
        assert expected_datasets == set(result["datasets"])

    def test_get_project_detail_not_accessible(
        self,
        as_project_participant_api,
        programme_manager,
    ):
        """
        Test that dataset detail view returns an error response when there are no accessible
        datasets
        """
        # Create project that is not associated with api user, this project will not show
        # up in project detail view
        project = recipes.project.make(created_by=programme_manager)

        response = as_project_participant_api.get(
            reverse("api:project_detail", kwargs={"uuid": project.uuid})
        )

        assert response.status_code == 404

    def test_get_project_detail_missing_token(self, DRFClient, programme_manager):
        """
        Test project detail API returns an error response when access token is not present in
        headers
        """
        project = recipes.project.make(created_by=programme_manager)

        # By default DRFClient has no access token applied
        response = DRFClient.get(reverse("api:project_detail", kwargs={"uuid": project.uuid}))
        assert response.status_code == 401


@pytest.mark.django_db
class TestWorkPackageListAPIView:
    def test_get_work_package_list(
        self,
        project_participant,
        as_project_participant_api,
        classified_work_package,
        make_accessible_work_package,
    ):
        """
        Test that an API user can request work package list api to see which work packages they have
        to.
        The user must be a participant of a work package, a participant of the work packages project
        and the work package must be classified.
        """
        num_accessible_work_packages = 3
        accessible_work_packages = [
            make_accessible_work_package(project_participant)
            for _ in range(num_accessible_work_packages)
        ]

        # Create more work packages that are not associated with api user, these work packages
        # should not show up in work package list view
        unaccessible_work_packages = [classified_work_package(0) for _ in range(3)]

        response = as_project_participant_api.get(reverse("api:work_package_list"))

        assert response.status_code == 200

        results = json.loads(response.content.decode())["results"]

        assert len(results) == num_accessible_work_packages

        uuid_results = [work_package["uuid"] for work_package in results]

        # Assert work packages in `accessible_work_packages` are in results
        for work_package in accessible_work_packages:
            assert str(work_package.uuid) in uuid_results

            matching_work_package = list(
                filter(lambda x: x.get("uuid", None) == str(work_package.uuid), results)
            )[0]

            # Assert that the related accessible project is returned as a part of serialization
            assert str(work_package.project.uuid) == matching_work_package["project"]
            # Assert that the related accessible datasets are returned as a part of serialization
            expected_datasets = set(
                str(uuid) for uuid in work_package.datasets.all().values_list("uuid", flat=True)
            )
            assert expected_datasets == set(matching_work_package["datasets"])

        # Assert work packages in `unaccessible_work_packages` are not in results
        for work_package in unaccessible_work_packages:
            assert str(work_package.uuid) not in uuid_results

    def test_get_work_package_list_empty(
        self,
        as_project_participant_api,
        classified_work_package,
    ):
        """
        Test that work package list view returns an empty array when there are no accessible
        work packages
        """
        # Create work packages that are not associated with api user, these work packages
        # should not show up in work package list view
        [classified_work_package(0) for _ in range(3)]

        response = as_project_participant_api.get(reverse("api:work_package_list"))

        assert response.status_code == 200

        results = json.loads(response.content.decode())["results"]
        assert results == []

    def test_get_work_package_list_missing_token(self, DRFClient):
        """
        Test that work package list API returns an error response when access token is not present
        in headers
        """
        # By default DRFClient has no access token applied
        response = DRFClient.get(reverse("api:work_package_list"))
        assert response.status_code == 401

    def test_get_project_work_package_list(
        self,
        project_participant,
        as_project_participant_api,
        classified_work_package,
        make_accessible_work_package,
    ):
        """
        Test that an API user can request project work package list api to see which work packages
        they have to filtered by a specific project.
        The user must be a participant of a work package, a participant of the work packages project
        and the work package must be classified.
        """
        accessible_work_package = make_accessible_work_package(project_participant)

        # Create more work packages that are not associated with api user, these work packages
        # should not show up in work package list view
        unaccessible_work_packages = [classified_work_package(0) for _ in range(3)]

        response = as_project_participant_api.get(
            reverse(
                "api:project_work_package_list",
                kwargs={"project__uuid": accessible_work_package.project.uuid},
            )
        )

        assert response.status_code == 200

        results = json.loads(response.content.decode())["results"]

        assert len(results) == 1

        uuid_results = [work_package["uuid"] for work_package in results]

        assert str(accessible_work_package.uuid) in uuid_results

        # Assert work packages in `unaccessible_work_packages` are not in results
        for work_package in unaccessible_work_packages:
            assert str(work_package.uuid) not in uuid_results

    def test_system_manager_package_list(
        self,
        system_manager,
        as_system_manager_api,
        classified_work_package,
        make_accessible_work_package,
    ):
        """
        Test that a system manager can request work package list api to view all work packages,
        regardless of whether the user is a participant of a work package or if the work package is
        classified
        """
        work_packages = [make_accessible_work_package(system_manager) for _ in range(3)]

        # Create more work packages that are not associated with api user, these work packages
        # should still show up in work package list view for system manager
        other_work_packages = [classified_work_package(0) for _ in range(3)]

        response = as_system_manager_api.get(reverse("api:work_package_list"))

        assert response.status_code == 200

        results = json.loads(response.content.decode())["results"]

        assert len(results) == len(work_packages) + len(other_work_packages)

        uuid_results = [work_package["uuid"] for work_package in results]

        # Assert all work packages are in results for system manager
        for work_package in work_packages + other_work_packages:
            assert str(work_package.uuid) in uuid_results

            matching_work_package = list(
                filter(lambda x: x.get("uuid", None) == str(work_package.uuid), results)
            )[0]

            # Assert that the related accessible project is returned as a part of serialization
            assert str(work_package.project.uuid) == matching_work_package["project"]
            # Assert that the related accessible datasets are returned as a part of serialization
            expected_datasets = set(
                str(uuid) for uuid in work_package.datasets.all().values_list("uuid", flat=True)
            )
            assert expected_datasets == set(matching_work_package["datasets"])

    def test_programme_manager_package_list(
        self,
        programme_manager,
        as_programme_manager_api,
        classified_work_package,
        make_accessible_work_package,
    ):
        """
        Test that a programme manager can request work package list api to view all work packages,
        regardless of whether the user is a participant of a work package or if the work package is
        classified
        """
        work_packages = [make_accessible_work_package(programme_manager) for _ in range(3)]

        # Create more work packages that are not associated with api user, these work packages
        # should still show up in work package list view for programme manager
        other_work_packages = [classified_work_package(0) for _ in range(3)]

        response = as_programme_manager_api.get(reverse("api:work_package_list"))

        assert response.status_code == 200

        results = json.loads(response.content.decode())["results"]

        assert len(results) == len(work_packages) + len(other_work_packages)

        uuid_results = [work_package["uuid"] for work_package in results]

        # Assert all work packages are in results for programme manager
        for work_package in work_packages + other_work_packages:
            assert str(work_package.uuid) in uuid_results

            matching_work_package = list(
                filter(lambda x: x.get("uuid", None) == str(work_package.uuid), results)
            )[0]

            # Assert that the related accessible project is returned as a part of serialization
            assert str(work_package.project.uuid) == matching_work_package["project"]
            # Assert that the related accessible datasets are returned as a part of serialization
            expected_datasets = set(
                str(uuid) for uuid in work_package.datasets.all().values_list("uuid", flat=True)
            )
            assert expected_datasets == set(matching_work_package["datasets"])

    def test_limited_by_maximum_tier(
        self,
        project_participant,
        as_project_participant_api,
        make_accessible_work_package,
        application_profile,
    ):
        """
        Test that only work packages that have a tier below the maximum tier of the application
        profile are returned by the work package lis API
        """
        application_profile.maximum_tier = 2
        application_profile.save()

        num_accessible_work_packages = 3
        accessible_work_packages = [
            make_accessible_work_package(project_participant, tier=0)
            for _ in range(num_accessible_work_packages)
        ]

        # These work packages are unaccessible because their tier is above the application profile
        # maximum tier
        unaccessible_work_packages = [
            make_accessible_work_package(project_participant, tier=4)
            for _ in range(num_accessible_work_packages)
        ]

        response = as_project_participant_api.get(reverse("api:work_package_list"))

        assert response.status_code == 200

        results = json.loads(response.content.decode())["results"]

        assert len(results) == num_accessible_work_packages

        uuid_results = [work_package["uuid"] for work_package in results]

        # Assert work packages in `accessible_work_packages` are in results
        for work_package in accessible_work_packages:
            assert str(work_package.uuid) in uuid_results

            matching_work_package = list(
                filter(lambda x: x.get("uuid", None) == str(work_package.uuid), results)
            )[0]

            # Assert that the related accessible project is returned as a part of serialization
            assert str(work_package.project.uuid) == matching_work_package["project"]
            # Assert that the related accessible datasets are returned as a part of serialization
            expected_datasets = set(
                str(uuid) for uuid in work_package.datasets.all().values_list("uuid", flat=True)
            )
            assert expected_datasets == set(matching_work_package["datasets"])

        # Assert work packages in `unaccessible_work_packages` are not in results
        for work_package in unaccessible_work_packages:
            assert str(work_package.uuid) not in uuid_results


@pytest.mark.django_db
class TestWorkPackageDetailAPIView:
    def test_get_work_package_detail(
        self,
        project_participant,
        as_project_participant_api,
        make_accessible_work_package,
    ):
        """
        Test that an API user can request work package detail api to see work package information
        if they have access to it.
        The user must be a participant of a work package, a participant of the work packages project
        and the work package must be classified.
        """
        work_package = make_accessible_work_package(project_participant)

        response = as_project_participant_api.get(
            reverse("api:work_package_detail", kwargs={"uuid": work_package.uuid})
        )

        assert response.status_code == 200

        result = json.loads(response.content.decode())
        assert result["uuid"] == str(work_package.uuid)

        # Assert that the related accessible project is returned as a part of serialization
        assert str(work_package.project.uuid) == result["project"]
        # Assert that the related accessible datasets are returned as a part of serialization
        expected_datasets = set(
            str(uuid) for uuid in work_package.datasets.all().values_list("uuid", flat=True)
        )
        assert expected_datasets == set(result["datasets"])

    def test_get_work_package_detail_not_accessible(
        self,
        as_project_participant_api,
        classified_work_package,
    ):
        """
        Test that work package detail view returns an error response when there are no accessible
        datasets
        """
        # Create work package that is not associated with api user, this work package
        # should not show up in dataset detail view
        work_package = classified_work_package(0)

        response = as_project_participant_api.get(
            reverse("api:work_package_detail", kwargs={"uuid": work_package.uuid})
        )

        assert response.status_code == 404

    def test_get_work_package_detail_missing_token(self, DRFClient, classified_work_package):
        """
        Test work package detail API returns an error response when access token is not present in
        headers
        """
        work_package = classified_work_package(0)

        # By default DRFClient has no access token applied
        response = DRFClient.get(
            reverse("api:work_package_detail", kwargs={"uuid": work_package.uuid})
        )
        assert response.status_code == 401

    def test_get_project_work_package_detail(
        self,
        project_participant,
        as_project_participant_api,
        make_accessible_work_package,
    ):
        """
        Test that an API user can request project work package detail api to see work package
        information if they have access to it, filtered by a specific project.
        The user must be a participant of a work package, a participant of the work packages project
        and the work package must be classified.
        """
        work_package = make_accessible_work_package(project_participant)

        response = as_project_participant_api.get(
            reverse(
                "api:project_work_package_detail",
                kwargs={
                    "project__uuid": work_package.project.uuid,
                    "uuid": work_package.uuid,
                },
            )
        )

        assert response.status_code == 200

        result = json.loads(response.content.decode())
        assert result["uuid"] == str(work_package.uuid)

    def test_limited_by_maximum_tier(
        self,
        project_participant,
        as_project_participant_api,
        make_accessible_work_package,
        application_profile,
    ):
        """
        Test that the work package detail API does not return a work package that has a tier above
        the maximum tier of the application profile
        """
        application_profile.maximum_tier = 2
        application_profile.save()

        # Work package will not be returned because the tier is above the maximum tier of the work
        # package
        work_package = make_accessible_work_package(project_participant, tier=4)

        response = as_project_participant_api.get(
            reverse("api:work_package_detail", kwargs={"uuid": work_package.uuid})
        )

        assert response.status_code == 404


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url_name,url_pk",
    [
        ("list", False),
        ("register", False),
        ("detail", True),
        ("delete", True),
        ("update", True),
    ],
)
class TestOAuthApplicationViews:
    def test_standard_user(
        self, url_name, url_pk, standard_user, as_standard_user, oauth_application
    ):
        """
        Test that standard user, who is not a superuser and does not have the correct role, is
        redirected from application views
        """
        oauth_application.user = standard_user
        oauth_application.save()

        url_kwargs = {}
        if url_pk:
            url_kwargs = {"pk": oauth_application.pk}

        response = as_standard_user.get(reverse(f"oauth2_provider:{url_name}", kwargs=url_kwargs))

        assert response.status_code == 302

    def test_superuser(self, url_name, url_pk, standard_user, as_standard_user, oauth_application):
        """Test that superuser can access application views"""
        standard_user.is_superuser = True
        standard_user.save()

        oauth_application.user = standard_user
        oauth_application.save()

        url_kwargs = {}
        if url_pk:
            url_kwargs = {"pk": oauth_application.pk}

        response = as_standard_user.get(reverse(f"oauth2_provider:{url_name}", kwargs=url_kwargs))

        assert response.status_code == 200

    def test_system_manager(
        self, url_name, url_pk, system_manager, as_system_manager, oauth_application
    ):
        """Test that system manager can access application views"""
        oauth_application.user = system_manager
        oauth_application.save()

        url_kwargs = {}
        if url_pk:
            url_kwargs = {"pk": oauth_application.pk}

        response = as_system_manager.get(reverse(f"oauth2_provider:{url_name}", kwargs=url_kwargs))

        assert response.status_code == 200

    def test_programme_manager(
        self,
        url_name,
        url_pk,
        programme_manager,
        as_programme_manager,
        oauth_application,
    ):
        """Test that system manager can access application views"""
        oauth_application.user = programme_manager
        oauth_application.save()

        url_kwargs = {}
        if url_pk:
            url_kwargs = {"pk": oauth_application.pk}

        response = as_programme_manager.get(
            reverse(f"oauth2_provider:{url_name}", kwargs=url_kwargs)
        )

        assert response.status_code == 200

    def test_unauthenticated(self, url_name, url_pk, client, oauth_application):
        """Test that anonymous user is redirected from application views"""
        url_kwargs = {}
        if url_pk:
            url_kwargs = {"pk": oauth_application.pk}

        response = client.get(reverse(f"oauth2_provider:{url_name}", kwargs=url_kwargs))

        assert response.status_code == 302
