# Data Safe Haven web management application: set up staging server

These instructions are for deploying a staging/test instance of the management web application in a testing environment.


## Prerequisites

You will need

 * The Azure CLI installed on your machine
 * Azure tenant and subscription access to create and register webapps
 * The subscription names and tenant IDs of the Azure Active Directories where you will install and register the app
 * Appropriate GitHub repository permissions for continuous deployment


### Configure your environment settings

You use this environment file by adding a parameter to the `provision.sh` script as described below. The script will set environment variables
in the Azure Django app. These variables can be modified later using the Azure CLI or the Azure Portal.


### Run the provisioning script

Install the [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest)

Use `az login` to log in on the command line.

Check that the values in your `.staging.env` file are correct.

Then run `deployment/provision.sh -e deployment/.staging.env` to create the webapp and relevant resources.
The path after `-e` describes the location of your custom environment file (if you omit `-e` and the following filename, it will look for `deployment/.env`).


* If deployment fails immediately with a subscription error, you may be logged into a different tenant or subscription.
   Go to the Azure portal and switch to the tenant where you want your app to be created and re-run the provisioning script.


### Set up IP restrictions for the App Service

* Browse to Azure Portal -> App Services / (YOUR APP NAME) / Networking / Configure Access Restrictions
* Under (YOUR APP NAME).azurewebsites.net, add a rule under for each IP range to enable
* Under (YOUR APP NAME).scm.azurewebsites.net, select "Same restrictions...", or add a rule for each IP range to enable


### Set up GitHub continuous deployment - note this requires a user with appropriate GitHub permissions

* Browse to Azure Portal -> App Services / (YOUR APP NAME) / Deployment Center
* If there is an existing deployment you will need to disable this using the Disconnect button
* Select GitHub and click Authorize. You may be required to enter GitHub credentials
* In the 'Configure' step, select:
  - Organization: 'alan-turing-institute'
  - repository: 'data-safe-haven-webapp'
  - branch: the branch to deploy (e.g. master, development)
