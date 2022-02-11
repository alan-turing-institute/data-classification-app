# Setup instructions for various OAuth2 backends

## GitHub

Register a new application at [GitHub Developers](https://github.com/settings/applications/new). Use the following homepage and callback URLs, replacing `localhost:8000` with the appropriate domain in production:
- Homepage URL: http://localhost:8000/
- Authorisation Callback URL: http://localhost:8000/auth/complete/github

This will generate a Client Key and Client Secret which should be made available as environment variables `GITHUB_OAUTH2_KEY` and `GITHUB_OAUTH2_SECRET` respectively; e.g. by adding them to .env.prod. **DO NOT COMMIT THEM TO VERSION CONTROL**

Add the following to the settings file to make sure the Client Key and Client Secret are picked up from the environment and made available to Python Social Auth:

```
SOCIAL_AUTH_GITHUB_KEY = env.str("GITHUB_OAUTH2_KEY", default="")
SOCIAL_AUTH_GITHUB_SECRET = env.str("GITHUB_OAUTH2_SECRET", default="")
```

Add the GitHub backend to `AUTHENTICATION_BACKENDS` in settings:
```
AUTHENTICATION_BACKENDS = [
    ...,
    "social_core.backends.github.GithubOAuth2",
]
```

Optionally, provide an alternative display name for the backend in settings:
```
AUTH_BACKEND_DISPLAY_NAMES = {
    ...,
    "github": "GitHub",
}
```

## ORCID Sandbox
[Register a new client application](https://info.orcid.org/register-a-client-application-sandbox-member-api/) for the ORCID sandbox member API.

* Update existing credentials: No
* Credential type: Basic
* Name: Data Classification App (doesn't really matter)
* Homepage URL: http://localhost:8000
* Redirect URIs: http://localhost:8000/auth/complete/orcid

Submit the form and a while later you should receive a client key and client secret by email. Add these to the environment as ORCID_OAUTH2_KEY and ORCID_OAUTH2_SECRET. **DO NOT COMMIT THEM TO VERSION CONTROL**.

Add the following to the settings file to make sure the Client Key and Client Secret are picked up from the environment and made available to Python Social Auth:

```
SOCIAL_AUTH_ORCID_SANDBOX_KEY = env.str("ORCID_OAUTH2_KEY", default="")
SOCIAL_AUTH_ORCID_SANDBOX_SECRET = env.str("ORCID_OAUTH2_SECRET", default="")
```

Add the GitHub backend to `AUTHENTICATION_BACKENDS` in settings:
```
AUTHENTICATION_BACKENDS = [
    ...,
    "social_core.backends.orcid.ORCIDOAuth2Sandbox",,
]
```

Optionally, provide an alternative display name for the backend in settings:
```
AUTH_BACKEND_DISPLAY_NAMES = {
    ...,
    "orcid-sandbox": "ORCID Sandbox",
}
```