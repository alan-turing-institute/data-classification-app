import json
from urllib.parse import parse_qs, urlparse

import pytest
from django.urls import reverse
from oauth2_provider.models import Application


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
