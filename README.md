# Data Safe Haven web management application
Django web application for the data safe haven.
This project can be set up in two configurations

- local development, using a locally-hosted PostgreSQL server
- web deployment, using an Azure server

---


## Local Development Setup

### Install system requirements

* Python 3.6+
* Postgres 10+ (with dev headers)

### Install requirements into virtualenv

```bash
pip install -r requirements/local.txt
```

### Set up PostgreSQL

The `--createdb` flag should be set for the database user when running tests (so test databases can be set up and torn down). This should not be done on a production system.

```bash
createuser haven --createdb
createdb -O haven haven
```

### Set up environment variables

Create a file named `haven/.env` with the following entries (these can also be set as environment variables
when the webserver is run):

```python
# A randomly generated string
SECRET_KEY='my-secret-key'

# Database connection string: depends on local postgres setup
DATABASE_URL='postgres://haven:haven@localhost/haven'
```

### Apply migrations

```bash
haven/manage.py migrate
```

### Create initial admin user account

```bash
haven/manage.py createsuperuser
```

### Run server

```bash
haven/manage.py runserver
```

### Test server
The server can be accessed at `http://127.0.0.1:8000/`. The credentials are those

### Run unit tests
These look for a folder called `staticfiles` which should be created before running the tests.


```
mkdir -p haven/staticfiles
cd haven

# Create staticfiles directory to suppress warnings from whitenoise
mkdir -p staticfiles

pytest
```

## Contributing

Python dependencies are managed via [`pip-tools`](https://pypi.org/project/pip-tools/). To add a new python package to the requirements:

* Add the package name and version to the relevant `.in` file in `requirements/` (usually `requirements/base.in`)
* Run `make -C requirements/` to rebuild the requirements txt files

---

## Deployment to Azure

Azure deployment requires you to configure an `.env` file, run a deployment script, and perform certain actions on the Azure Portal.

### Register an app using the Azure Active Directory

This step may not be required if your app was previously registered, because the registration will remain even if the webapp and resource group are deleted.

This step is performed first because we need the registration parameters to configure our `.env` file for OAuth2 authentication below.
However, you could perform this step later as long as you update the variables on the Azure deployment afterwards

 * Log into the Azure Portal and switch to the Data Study Group Development folder (click on your user icon and Switch Directory)
 * Choose Azure Active Directory/App Registrations
 * Click View All Applications and check that a registration does not already exist for your webapp
 * Click New Application Registration
 * Choose a suitable application name (eg. DSH web management development)
 * Set the sign-on URL to the deployment URL eg. https://datasafehaven.azurewebsites.net/
 * Go to the Settings for this new registration
 * Under Reply URL add the authentication endpoint (you must include the trailing slash) eg. https://datasafehaven.azurewebsites.net/auth/complete/azuread-tenant-oauth2/
 * Under Required Permissions add the following permissions for Microsoft Graph:
   * Read directory data
   * Sign in and read user profile
   * Access directory as the signed in user
   * View users' email address
   * View users' basic profile
 * Under Keys, add a new Passwords called "App key". Copy the value into a suitable keyvault as you won't be able to read it later. You will need it for the AZUREAD_OAUTH2_SECRET parameter in the `.env` file below.
 * Note the Application ID which will be needed for AZUREAD_OAUTH2_KEY.

### Configure your environment settings

Copy the template file `scripts/.env.example` to `scripts/.env`. Set all the parameters in `scripts/.env` for your environment and deployment.
You may use a custom filename/location by adding a parameter to the `provision.sh` script as described below. The script will set variables
in the Azure app. These variables can be modified later using the Azure CLI or the Azure Portal.

The AD/OAuth2 parameters are set as follows:
 * `AZUREAD_OAUTH2_KEY` is the Application ID for your application registration created above.
 * `AZUREAD_OAUTH2_SECRET` is the App key created above.
 * `AZUREAD_OAUTH2_TENANT_ID` is the Directory ID for the Data Study Group Development AD, which can be found under Azure Active Directory/Properties.


### Run the deployment script

Install the [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest)

Use `az login` to log in on the command line.

Check that the values in your `.env` file are correct.

Then run `scripts/provision.sh` to create the webapp and relevant resources.
Use the `-e` parameter to choose an environment file; otherwise the default is `scripts/.env`

Instructions are given at the end of the script to run some manual steps that need to be performed through the Azure portal.
These instructions will also give you the URL at which the site is hosted.



###

### To complete the deployment on Azure Portal

Note: You may need to switch your AD directory to The Alan Turing Institute if you were previously working on a different directory.
Click your user icon and "Change Directory"

1. Set up Python 3.6 site extension
* Browse to Azure Portal -> App Services / $APP_NAME / Extensions
* Click Add, then Choose Extension and select Python 3.6.4 x86. Accept the terms and install.

2. Set up GitHub deployment - note this requires a user with admin access to the repository
* Browse to Azure Portal -> App Services / $APP_NAME / Deployment Center
* Select GitHub and click Authorize
* In the 'Configure' step, select:
  - Organization: 'alan-turing-institute'
  - repository: 'data-safe-haven-webapp'
  - branch: whatever is appropriate

3. The webapp should now be accessible at your configured domain


### Register the app in Azure


## Troubleshooting

If errors are encountered in the browser after deploy, the following settings can be added to web.config to display useful errors in the browser:
```
<configuration>
    <system.webServer>
        <httpErrors errorMode="Detailed" />
    </system.webServer>
    <system.web>
        <customErrors mode="Off"/>
        <compilation debug="true"/>
    </system.web>
</configuration>
```
