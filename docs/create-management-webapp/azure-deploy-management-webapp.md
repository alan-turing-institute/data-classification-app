# Data Safe Haven web management application: deploying a production server

These instructions are for deploying a production instance of the management web application from a GitHub repository.

[1. Set up a production server](#1.-Set-up-a-production-server)

[2. Update a production server](#2.-Update-a-production-server)

[3. Troubleshooting](#3.-Troubleshooting)

## 1. Set up a production server


### Prerequisites

You will need

 * The Azure CLI installed on your machine
 * Azure tenant and subscription access to create and register webapps
 * The subscription names and tenant IDs of the Azure Active Directories where you will install and register the app
 * GitHub credentials with permissions to add a deploy key, if your repository is private 
 * GitHub credentials with permissions to add a deploy hook, if using continuous deployment 
 

### Configure your environment settings

You need to create an environment settings file before deploying the webapp for the first time.
This file is used by the provisioning script to create the webapp deployment and configure the application settings. It can also be used to modify the deployment in future. 
It is recommended (but not required) that you keep a copy of the file as it will make it easier to modify an existing deployment.

Copy the template file `deployment/.env.example` to a custom file for your deployment, e.g. `deployment/.env.production`. Set the required parameters in `deployment/.env.production` for your environment and deployment.
You use this environment file by adding a parameter to the `provision.sh` script as described below. The script will set environment variables
in the Azure Django app. These variables can be modified later using the Azure CLI or the Azure Portal.


### Run the provisioning script

Install the [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest)

Use `az login` to log in on the command line.

Check that the values in your `.env.production` file are correct.

Then run `deployment/provision.sh -e deployment/.production.env` to create the webapp and relevant resources.
The path after `-e` describes the location of your custom environment file (if you omit `-e` and the following filename, it will look for `deployment/.env`).

You will need to enter your GitHub credentials if required for configuring continuous deployment or deployment from a private repository.  

Note: the provisioning script is idempotent. If run on an existing installation, it will update the installation to match the new settings.

### Set up IP restrictions for the SCM App repository

* Browse to Azure Portal -> App Services / (YOUR APP NAME) / Networking / Configure Access Restrictions
* Select the (YOUR APP NAME).scm.azurewebsites.net tab
* Unselect "Same restrictions..."
* Add a rule for each IP range to enable
  * If you plan to deploy using Cloud Shell ensure the IP ranges are added during the time of deployment
  * For continuous deployment, include IP ranges for GitHub hooks: https://api.github.com/meta

### Add a UPN claim to allow guest users to log in
* Log into the Azure portal and switch to the AD tenant
* Select "App Registrations" and select your app
* Under Manage, select "Token Configuration"
* Click "Add optional claim"
* Select "ID", "upn" and click "Add"
* Edit the claim by clicking the pencil icon at the right
* Switch "Externally authenticated" to Yes
* Click "Save"

### Enforce MFA for users logging into the web app

* Log into the Azure portal and switch to the AD tenant
* Switch to Azure Active Directory -> Security -> Conditional Access
* Click "New Policy"
* Set the options as follows:
  - Name: "Require MFA for classification webapp"
  - Users: All users
  - Cloud apps or actions:
     - Select what this policy applies to: Cloud Apps
     - Include: Select apps
     - Select: name of webapp App Registration (e.g. Data Safe Haven Development)
  - Access controls: Grant access -> Require multi-factor authentication
  - Enable policy: On
* Click "Save"
* Save

### Setup custom domain
If you are using a custom domain for your webapp (i.e. your site `https://www.some.domain.com` is not the default Azure site `https://AZURE_APP_NAME.azurewebsites.net`),
use the following steps to configure your custom domain on the Azure portal:
* If the parent domain `some.domain.com` does not already have an Azure DNS zone, then you need to create one and copy the NS records to the parent domain. __NB. You don't need to do this if your SHM domain is `some.domain.com` and your website is `www.some.domain.com` as you will have created the DNS Zone `some.domain.com` during the SHM deployment.__ 
    * On the Azure portal, create an Azure DNS Zone for your custom domain. Note the required NS records listed for this zone.
    * Add the Azure NS records listed in the previous step to your domain provider.
* On the Azure portal, In the Azure DNS zone, add a new Record set. The Value parameter should be set to the azurewebsites domain for your webapp
  - Name: www
  - Type: CNAME
  - Value: AZURE_APP_NAME.azurewebsites.net
  - TTL: 1 hour
  - Alias: No
* In the App Service, add a new Custom Domain for your custom domain. Note that validation may not work until the DNS records have propagated.
* In the App Service TLS/SSL settings, under Private Key Certificates, click Create App Service Managed Certificate to create a certificate for your custom domain
* In the App Service Custom domains, add an SSL binding (choose SNI SSL) for your custom domain






## 2. Update a production server

The procedure for modifying a server depends on the type of change you want to make. These are described below:


### Update the software version of the Safe Haven webapp

This is done by updating the codebase on the App Service SCM using continuous deployment or manual synchronisation: 


#### a. When continuous deployment is enabled

When continuous deployment is configured through GitHub, pushing new code to the configured branch will automatically update the webapp.


#### b. When continuous deployment is disabled

If your configuration file did not enable continuous deployment, you need to manually trigger a code update.
There are several ways to do this:
 * On the Azure portal, go to the App Service, select Deployment Center and click the *Sync* button 
 * or, run `deployment/update_code.sh -e deployment/.production.env`.
As above, the path after `-e` describes the location of your custom environment file and must match the file you used for provisioning.


### Modify the application settings  

Application settings such as the website title can be changed in two ways:
 * Modify your environment settings file and re-run the provisioning script as described above
 * Change settings directly through the Azure portal (`App Service`>`Settings`>`Configuration`>`Application Settings`) 

Note that re-running the provision script will overwrite any changes you made on the portal. 

### Modify server resources

Server resources such as resource group names can be changed in two ways:
 * Modify your environment settings file and re-run the provisioning script as described above
 * Change settings directly through the Azure portal 

Note that re-running the provision script will overwrite any changes you made on the portal. 

## 3. Troubleshooting

* If deployment fails immediately with a subscription error, you may be logged into a different tenant or subscription.
   Go to the Azure portal and switch to the tenant where you want your app to be created and re-run the provisioning script.

* If continuous deployment and manual deployment both fail, and your repository is private, check that a deploy key has been correctly added to the GitHub repository and test it works.

* If continuous deployment does not happen automatically when the codebase changes, but manual deployment works, check that a deploy hook has been correctly added to the GitHub repository. Also check that your IP restrictions to the SCM do not block access to GitHub. 

* If redeployment becomes stuck following a repository modification to the `deploy_linux.sh` file, you may need to perform the following workaround (see issue #272)
  * On the Azure portal, go to the deployed App Service
  * Under `Configuration`/`General Settings`/`Stack Settings`, change `Startup Command` from `/home/site/repository/deploy_linux.sh` to blank.
  * Under `Deployment Centre` click `Sync`
  * Wait for deployment to complete/fail 
  * Under `Configuration`/`General Settings`/`Stack Settings`, change `Startup Command` from blank to `/home/site/repository/deploy_linux.sh`.
  * Under `Deployment Centre` click `Sync`

* If you are redeploying the webapp and setting a custom webapp domain, the `Create App Service Managed Certificate` action may succeed but no private key certificate appears on the portal.
  This may indicate a certificate was left behind when the webapp was deleted and you may need to manually delete this. 
  To delete a redundant certificate, on the Azure portal, go to the resource group, select Settings > Resources, check `Show hidden types`, select the redundant certificate and delete.

