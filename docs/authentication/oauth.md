## OAuth

This data-classification-app (DCA) is an [OAuth2](https://oauth.net/2/) provider, it uses the library [django-oauth-toolkit](https://github.com/jazzband/django-oauth-toolkit). Multiple data-access-controller (DAC) clients should be able to authorize to a single data-classification-app instance.

### Sequence diagram
The following is a typical request sequence diagram of the OAuth flow for the successful authorization of a DAC user. It uses the `authorization_code` grant type, some query parameters have been omitted for brevity:

```mermaid
sequenceDiagram
    participant user as User in browser
    participant app as Data<br/>Access<br/>Controller (DAC)
    participant dca as Data<br/>Classification<br/>App (DCA)
    user->>app: Resource request <br/>e.g. dataset list view
    app->>user: Redirect to DCA
    user->>dca: Call authorize url with query parameters<br/>e.g. /o/authorize/?=client_id=xxx&grant_type=authorization_code
    dca->>user: Asks user for permission<br/>e.g. Do you authorize the DAC app to access your datasets?
    user->>dca: Authorization granted
    dca->>user: Redirect to DAC with authorization code
    user->>app: Call callback url with authorization code<br/> e.g. /o/callback/?authorization_code=xxx
    app->>dca: Call token url with authorization code and client secret<br/> e.g. /o/token/?authorization_code=xxx&client_secret=xxx
    dca->>app: Access token and refresh token
    app->>dca: API resource request with access token <br/>e.g. /api/v1/datasets/?access_token=xxx
    dca->>app: Resource <br/>e.g. dataset list json object
    app->>user: Resource <br/>e.g. dataset list html
```

### Proof Key for Code Exchange
[Proof Key for Code Exchange](https://oauth.net/2/pkce/) (PKCE) has been enabled on the OAuth flow, this is an extension to the original OAuth2 protocol which was initially required for mobile applications but is now recommended for server based application. `code_challenge` and `code_challenge_method` query parameters are required for the authorize url call followed up by the appropriate `code_verifier` query parameter when calling the token url. See [here](https://help.aweber.com/hc/en-us/articles/360036524474-How-do-I-use-Proof-Key-for-Code-Exchange-PKCE-) for an example of how to generate the `code_challenge` and `code_verifier` values with python.

### Flowchart
The following is a flowchart which captures the high level user flow for a DAC application user authorizing with a DCA application. This flow assumes that Single-Sign-On (SSO) has not been implemented and the user is required to login to both systems with separate credentials. It is assumed that all requests are well formed and receive a successful response, in the case of an unsuccessful request the user will be shown an error message and be asked to retry their current step:

```mermaid
flowchart TD
     start([User requests view<br/>with OAuth protected<br/>resource on DAC app]) --> loggedInDAC{Is user<br/>logged into<br/>DAC app?}
     loggedInDAC --- yes1[Yes] --> refreshTokenPresent{Does user<br/>have a non-expired<br/>refresh token saved<br/>to the database?}
     loggedInDAC --- no1[No] --> redirectToLoginDAC[Redirect to DAC<br/>app login view]
     redirectToLoginDAC --> userLogsInDAC[User logs into DAC app]
     userLogsInDAC --> start
     refreshTokenPresent --- yes3[Yes] --> refreshToken[Request refresh token<br/>endpoint to receive new access<br/>and refresh token]
     refreshToken --> saveRefreshToken1[Save new refresh token<br/>to the database]
     saveRefreshToken1 --> callResourceAPI[Use access token to<br/>request resource API]
     callResourceAPI --> serveView([Serve DAC view to user<br/>which includes resource])
     refreshTokenPresent --- no2[No] --> redirectToAuthorize[Redirect user to DCA<br/>authorize url with appropriate<br/>query parameters]
     redirectToAuthorize --> loggedInDCA{Is user<br/>logged into<br/>DCA app?}
     loggedInDCA --> no3[No] --> redirectToLoginDCA[Redirect to DCA<br/>app login view]
     redirectToLoginDCA --> userLogsInDCA[User logs into DCA app]
     userLogsInDCA --> redirectToAuthorize
     loggedInDCA --- yes4[Yes] --> askToAuthorize{User<br/>authorizes<br/>access?}
     askToAuthorize --- Cancelled --> DACHomepage([Redirect to DAC home page<br/>with error message])
     askToAuthorize --- Granted --> callback[Redirect to DAC<br/>callback view with<br/>authorization code]
     callback --> authCodeUsed[Use authorization code<br/>to request new access<br/>and refresh token]
     authCodeUsed --> saveRefreshToken2[Save new refresh token<br/>to the database]
     saveRefreshToken2 --> start
```
