# Setup instructions for various OAuth2 backends

## GitHub

Register a new application at [GitHub Developers](https://github.com/settings/applications/new). Use the following homepage and callback URLs, replacing `localhost:8000` with the appropriate domain in production:
- Homepage URL: http://localhost:8000/
- Authorisation Callback URL: http://localhost:8000/auth/complete/github

This will generate a Client Key and Client Secret which should be made available as environment variables `SOCIAL_AUTH_GITHUB_KEY` and `SOCIAL_AUTH_GITHUB_SECRET` respectively; e.g. by adding them to `.env`. **DO NOT COMMIT THEM TO VERSION CONTROL**

To use GitHub as an authentication provider, the following environment variables must also be set:
```
AUTH_TYPES="social"
SOCIAL_AUTH_PROVIDERS="github"
```


## ORCID Sandbox
**This version of the ORCID API is for development purposes and does not contain live ORCID data.** You can create new ORCID sandbox ids in order to test it.

[Register a new client application](https://info.orcid.org/register-a-client-application-sandbox-member-api/) for the ORCID sandbox member API.

* Update existing credentials: No
* Credential type: Basic
* Name: Data Classification App (doesn't really matter)
* Homepage URL: http://localhost:8000
* Redirect URIs: http://localhost:8000/auth/complete/orcid-sandbox

Submit the form and a while later you should receive a client key and client secret by email. Add these to the environment as `SOCIAL_AUTH_ORCID_SANDBOX_KEY` and `SOCIAL_AUTH_ORCID_SANDBOX_SECRET`. **DO NOT COMMIT THEM TO VERSION CONTROL**.

To use ORCID Sandbox as an authentication provider, the following environment variables must also be set:
```
AUTH_TYPES="social"
SOCIAL_AUTH_PROVIDERS="orcid-sandbox"
```

## Azure AD Tenant
The `.env` file will need to include the following:
```
AUTH_TYPES="social"
SOCIAL_AUTH_PROVIDERS="azure-ad-tenant"

SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_KEY=""
SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET=""
SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_TENANT_ID=""
SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_RESOURCE=""
```