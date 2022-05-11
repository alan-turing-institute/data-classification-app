import json
from urllib.parse import parse_qs, urlparse

import pytest
from django.urls import reverse
from oauth2_provider.models import Application

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
        original_count = Application.objects.count()

        # Register a new client (e.g. data-access-controller)
        response = as_system_manager.post(
            reverse("oauth2_provider:register"),
            data=oauth_application_registration_data,
        )
        assert response.status_code == 302

        assert Application.objects.count() == original_count + 1

        application = Application.objects.last()
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
        to for a specific project.
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

        # Filter dataset list view by one project
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

        # Filter dataset list view by one project
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


@pytest.mark.django_db
class TestProjectListAPIView:
    def test_get_project_list(
        self,
        programme_manager,
        project_participant,
        as_project_participant_api,
        project,
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

        uuid_results = [dataset["uuid"] for dataset in results]

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


@pytest.mark.django_db
class TestProjectDetailAPIView:
    def test_get_project_detail(
        self,
        programme_manager,
        project_participant,
        as_project_participant_api,
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

        uuid_results = [dataset["uuid"] for dataset in results]

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

        uuid_results = [dataset["uuid"] for dataset in results]

        assert str(accessible_work_package.uuid) in uuid_results

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
