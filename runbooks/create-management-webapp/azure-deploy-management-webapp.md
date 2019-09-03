# Data Safe Haven web management application: set up production server

These instructions for for deploying a production instance of the management web application using local git deployment.


## Prerequisites

You will need

 * The Azure CLI installed on your machine
 * Azure tenant and subscription access to create and register webapps
 * The subscription names and tenant IDs of the Azure Active Directories where you will install and register the app


### Configure your environment settings

Copy the template file `scripts/.env.example` to a custom file for your deplyment, eg. `scripts/.env.production`. Set the required parameters in `scripts/.env.production` for your environment and deployment.
You use this environment file by adding a parameter to the `provision.sh` script as described below. The script will set environment variables
in the Azure Django app. These variables can be modified later using the Azure CLI or the Azure Portal.


### Run the provisioning script

Install the [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest)

Use `az login` to log in on the command line.

Check that the values in your `.env.production` file are correct.

Then run `scripts/provision.sh -e scripts/.production.env` to create the webapp and relevant resources.
The path after `-e` describes the location of your custom environment file (if you omit `-e` and the following filename, it will look for `scripts/.env`).


* If deployment fails immediately with a subscription error, you may be logged into a different tenant or subscription.
   Go to the Azure portal and switch to the tenant where you want your app to be created and re-run the provisioning script.



### Set up IP restrictions for the SCM App repository

* Browse to Azure Portal -> App Services / (YOUR APP NAME) / Networking / Configure Access Restrictions
* Select the (YOUR APP NAME).scm.azurewebsites.net tab
* Unselect "Same restrictions..."
* Add a rule for each IP range to enable
  * If you plan to deploy using Cloud Shell ensure the IP ranges are added during the time of deployment
  * For continuous deployment, include IP ranges for GitHub hooks: https://api.github.com/meta

### Update code when continuous deployment is disabled

If your configuration file did not enable continuous deployment, you need to manually trigger a code update.
There are two ways to do this:
 * On the Azure portal, go to the App Service, select Deployment Center and click the *Sync* button 
 * or, run `scripts/update_code.sh -e scripts/.production.env`.
As above, the path after `-e` describes the location of your custom environment file and must match the file you used for provisioning.

### Add a VNet integration to the App Service

* Browse to Azure Portal -> App Services / ${APP_NAME} / Networking / VNet Integration / Click here to configure
* Click Add VNet (preview)
* From the Virtual Network drop-down, select ${VNET_NAME}
* Under Subnet, choose Select Existing and select ${SUBNET_NAME} from the drop-down
* Click OK
