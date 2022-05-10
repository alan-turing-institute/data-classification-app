import json
from urllib.parse import parse_qs, urlparse

import pytest
from django.urls import reverse
from oauth2_provider.models import Application

from haven.projects.roles import ProjectRole


@pytest.mark.django_db
class TestOAuthFlow:
    def test_oauth_flow(self, as_system_manager, pkce_verifier, pkce_code_challenge):
        """This tests that a client can use the OAuth2 views to gain an access token"""
        original_count = Application.objects.count()

        application_data = {
            "name": "Test",
            "client_id": "IcqQdcuqWmXfm28NLhvvCkGpfOcQr5t7ZLxol1Dj",
            "initial-client_id": "IcqQdcuqWmXfm28NLhvvCkGpfOcQr5t7ZLxol1Dj",
            "client_secret": (
                "1Yrycxhi3CG1tAzvWgDenzOweXE6XNrMbckQaYQnzN81I9JUz3PKtqZc9wpn3nZCUQciP"
                "phZTx8DxCz4W97PrQigTrA58gFi4qR52UsRz0P7yDyoSWdXNaFPsWQcXlji"
            ),
            "initial-client_secret": (
                "1Yrycxhi3CG1tAzvWgDenzOweXE6XNrMbckQaYQnzN81I9JUz3PKtqZc9wpn3nZCUQciP"
                "phZTx8DxCz4W97PrQigTrA58gFi4qR52UsRz0P7yDyoSWdXNaFPsWQcXlji"
            ),
            "client_type": "confidential",
            "authorization_grant_type": "authorization-code",
            "redirect_uris": "http://testserver/noexist/callback",
            "algorithm": "",
        }
        # Register a new client (e.g. data-access-controller)
        response = as_system_manager.post(
            reverse("oauth2_provider:register"), data=application_data
        )
        assert response.status_code == 302

        assert Application.objects.count() == original_count + 1

        application = Application.objects.last()
        # Assert redirected to application detail view
        assert response.url == reverse("oauth2_provider:detail", kwargs={"pk": application.id})

        authorize_data = {
            "redirect_uri": application_data["redirect_uris"],
            "scope": "read write",
            "nonce": "",
            "client_id": application_data["client_id"],
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
                "redirect_uri": application_data["redirect_uris"],
                "client_id": application_data["client_id"],
                "client_secret": application_data["client_secret"],
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
        programme_manager,
        project_participant,
        as_project_participant_api,
        classified_work_package,
    ):
        """
        Test that an API user can request dataset list api to see which datasets they have to.
        The user must be a participant of a project, the datasets must be associated with this
        project and a classified work package, which this user is also associated with.
        """
        num_accessible_datasets = 3
        # Create work packages and add api user
        accessible_work_packages = [
            classified_work_package(0) for _ in range(num_accessible_datasets)
        ]
        for work_package in accessible_work_packages:
            work_package.project.add_user(
                user=project_participant,
                role=ProjectRole.RESEARCHER.value,
                created_by=programme_manager,
            )
            work_package.add_user(
                project_participant,
                programme_manager,
            )

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


@pytest.mark.django_db
class TestDatasetDetailAPIView:
    def test_get_dataset_detail(
        self,
        programme_manager,
        project_participant,
        as_project_participant_api,
        classified_work_package,
    ):
        """
        Test that an API user can request dataset detail api to see dataset information if they
        have access to it.
        The user must be a participant of a project, the dataset must be associated with this
        project and a classified work package, which this user is also associated with.
        """
        # Create work package and add api user
        work_package = classified_work_package(0)
        work_package.project.add_user(
            user=project_participant,
            role=ProjectRole.RESEARCHER.value,
            created_by=programme_manager,
        )
        work_package.add_user(
            project_participant,
            programme_manager,
        )

        dataset = work_package.datasets.last()

        response = as_project_participant_api.get(
            reverse("api:dataset_detail", kwargs={"uuid": work_package.datasets.last().uuid})
        )

        assert response.status_code == 200

        result = json.loads(response.content.decode())

        assert result["uuid"] == str(dataset.uuid)

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
