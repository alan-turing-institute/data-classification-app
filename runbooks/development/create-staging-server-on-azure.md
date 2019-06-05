# Data Safe Haven web management application

These instructions for for deploying a staging/test instance of the management web application in a testing environment.
Django web application for the data safe haven.


## Prerequisites

To deploy a development instance at the ATI, you will need access to the Alan Turing Institute active directory (where the resource groups and apps will be created) and the Data Study Group Development active directory (where the app is registered with Azure and test users can be created).


## Deployment to Azure

Azure deployment requires you to configure an `.env` file, run a deployment script, and perform certain actions on the Azure Portal.

To deploy a development instance at the ATI, you will need access to the Alan Turing Institute active directory (where the resource groups and apps will be created) and the Data Study Group Development active directory (where the app is registered with Azure and test users can be created).

### Register an app using the Azure Active Directory

This step may not be required if your app was previously registered, because the registration will remain even if the webapp and resource group are deleted.

This step is performed first because we need the registration parameters to configure our `.env` file for OAuth2 authentication below.
However, you could perform this step later as long as you update the variables on the Azure deployment afterwards

The step is described in a separate runbook under "create-management-webapp".
This step will produce a keyvault which you will need for the steps below.


### Configure your environment settings

Copy the template file `scripts/.env.example` to `scripts/.env`. Set all the parameters in `scripts/.env` for your environment and deployment.
You may use a custom filename/location by adding a parameter to the `provision.sh` script as described below. The script will set variables
in the Azure app. These variables can be modified later using the Azure CLI or the Azure Portal.

The AD/OAuth2 parameters are set from the values in the keyvault as follows:
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
