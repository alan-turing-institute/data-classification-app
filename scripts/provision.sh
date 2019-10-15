#!/usr/bin/env bash

#
# Script for deploying the Data Safe Haven management application on Azure.
#
# Requires:
#  1. The Azure CLI to be installed:
#      https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest
#
#  2. An environment file (.env) to be configured for your deployment.
#      See .env.example for more information
#
#  3. git installed and configured to push the code
#
# To run this script:
#   provision.sh -e ENV_FILENAME
#
#     where ENV_FILENAME is the path and name of your .env file.
#



set -e

# Document usage for this script
usage() {
    echo "usage: $0 [-h] [-e envfile]"
    echo "  -h            display help"
    echo "  -e path to file containing environment variables"
    exit 1
}

CURRENT_DIR=$(dirname "$0")
ENVFILE="${CURRENT_DIR}/.env"

# Read command line arguments, overriding defaults where necessary
while getopts "h:e:" opt; do
    case $opt in
        h)
            usage
            ;;
        e)
            ENVFILE=$OPTARG
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            ;;
    esac
done


if [ -e $ENVFILE ]
then
    source $ENVFILE
else
    echo "Envfile does not exist: $ENVFILE"
    exit 1
fi



generate_key () {
    openssl rand 32 -base64
}

# Fetch a secret from the Azure keyvault
function get_azure_secret() {
    local SECRET_NAME="$1"
    az keyvault secret show --name "${SECRET_NAME}" --vault-name "${KEYVAULT_NAME}" --query "value" -otsv
}

# Fetch a secret from the Azure keyvault, but generate and store one if it does not exist
function get_or_create_azure_secret() {
    local SECRET_NAME="$1"

    # Get current value from keyvault
    local keyvault_value=$(get_azure_secret  "$1")

    # If there is no current key then generate a new one
    if [ -z "${keyvault_value}" ]
    then
          echo "Creating new key for $1"
          keyvault_value=$(generate_key)
          az keyvault secret set --name "$1" --vault-name "${KEYVAULT_NAME}" --value "${keyvault_value}"
    fi

    echo "${keyvault_value}"
}

# Exit if a deployment already exists
error_if_already_deployed() {
    if [[ $(az group exists --name ${RESOURCE_GROUP} --subscription "${SUBSCRIPTION}") == "true" ]]; then
        echo "This script is for crearing a new deployment, but the resource group already exists"
        exit 1
    fi
}

azure_login() {
    az login
    switch_to_app_tenant
}

# Switch Azure CLI to the tenant used for app creation
switch_to_app_tenant () {
    # We need to explicitly set the subscription in order to change the default tenant.
    # This is because Azure CLI does not already respect the --subscription argument.
    echo "Preparing to switch to $SUBSCRIPTION"
    az account set --subscription "${SUBSCRIPTION}"
}

# Switch Azure CLI to the tenant used for app registration
switch_to_registration_tenant () {
    # The tenant we use to register the app may not have a subscription, in which case we cannot use
    # 'az account set --subscription'. Instead we need to set the tenant by calling 'az login' with
    # the --allow-no-subscriptions flag.
    az login --tenant "${REGISTRATION_TENANT}" --allow-no-subscriptions
}

create_resource_group() {
    echo "Creating resource group"
    az group create --name "${RESOURCE_GROUP}" --location "${LOCATION}"

    # Create a lock to prevent accidental deletion of the resource group and the resources it contains
    az lock create --name LockDataSafeHaven --lock-type CanNotDelete --resource-group "${RESOURCE_GROUP}" --notes "Prevents accidental deletion of Data Safe Haven management webapp and its resources"
}

create_keyvault() {
    echo "Creating keyvault"
    az keyvault create --name "${KEYVAULT_NAME}" --resource-group "${RESOURCE_GROUP}" --location "${LOCATION}"
}

create_app() {
    echo "Creating the webapp"

    # App service plan
    az appservice plan create --name "${PLAN_NAME}" --resource-group "${RESOURCE_GROUP}" --sku S1 --is-linux

    # Webapp
    az webapp create --name "${APP_NAME}" --resource-group "${RESOURCE_GROUP}" --plan "${PLAN_NAME}" --runtime "PYTHON|3.7"  --deployment-local-git

    # Configure webapp logging
    az webapp log config --name "${APP_NAME}" --resource-group "${RESOURCE_GROUP}" --application-logging true --web-server-logging filesystem --docker-container-logging filesystem --detailed-error-messages true --level warning

    # Force the proxy to redirect non-https traffic to https
    az webapp update --name "${APP_NAME}" --resource-group "${RESOURCE_GROUP}" --https-only true

    # Configure startup file
    az webapp config set --name "${APP_NAME}" --resource-group "${RESOURCE_GROUP}" --startup-file "/home/site/repository/deploy_linux.sh"

    local deployment_url=$(az webapp deployment source config-local-git --name "${APP_NAME}" --resource-group "${RESOURCE_GROUP}" --query "url" -otsv)
     az keyvault secret set --name "DEPLOYMENT-URL" --vault-name "${KEYVAULT_NAME}" --value "${deployment_url}"

    # Create Django secret key
    local django_secret_key=$(get_or_create_azure_secret  "SECRET-KEY")
}

create_mssql_db() {
    echo "Creating the DB server"
    local db_username=${DB_USERNAME}
    local db_password=${DB_PASSWORD}
    local database_url="mssql://${db_username}:${db_password}@$DB_SERVER_NAME.database.windows.net:1433/$DB_NAME"

    # Create the db server
    az sql server create --admin-user="${db_username}" --admin-password="${db_password}" --name="${DB_SERVER_NAME}" --location="${LOCATION}" --resource-group="${RESOURCE_GROUP}"

    # Configure the firewall
    az sql server firewall-rule create --server "${DB_SERVER_NAME}" --resource-group "${RESOURCE_GROUP}" --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0 --name AllowAllWindowsAzureIps

    # Create the database
    az sql db create --name="${DB_NAME}" --resource-group="${RESOURCE_GROUP}" --server="${DB_SERVER_NAME}"

    # Store DB credentials in keyvault
    az keyvault secret set --name "DB-USERNAME" --vault-name "${KEYVAULT_NAME}" --value "${db_username}"
    az keyvault secret set --name "DB-PASSWORD" --vault-name "${KEYVAULT_NAME}" --value "${db_password}"
    az keyvault secret set --name "DB-URL" --vault-name "${KEYVAULT_NAME}" --value "${database_url}"
}

create_postgresql_db() {
    echo "Creating the DB server"

    local db_username=${DB_USERNAME}
    local db_password=${DB_PASSWORD}
    local database_url="postgresql://${db_username}@$DB_SERVER_NAME:${db_password}@$DB_SERVER_NAME.postgres.database.azure.com:5432/$DB_NAME"

    # Create the postgresql server
    az postgres server create --admin-user="${db_username}" --admin-password="${db_password}" --name="${DB_SERVER_NAME}" --location="${LOCATION}" --resource-group="${RESOURCE_GROUP}" --sku-name B_Gen5_1 --ssl-enforcement Enabled

    # Configure the firewall
    az postgres server firewall-rule create --server "${DB_SERVER_NAME}" --resource-group "${RESOURCE_GROUP}" --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0 --name AllowAllWindowsAzureIps

    # Create the database
    az postgres db create --name="${DB_NAME}" --resource-group="${RESOURCE_GROUP}" --server="${DB_SERVER_NAME}"

    # Store DB credentials in keyvault
    az keyvault secret set --name "DB-USERNAME" --vault-name "${KEYVAULT_NAME}" --value "${db_username}"
    az keyvault secret set --name "DB-PASSWORD" --vault-name "${KEYVAULT_NAME}" --value "${db_password}"
    az keyvault secret set --name "DB-URL" --vault-name "${KEYVAULT_NAME}" --value "${database_url}"
}

create_registration () {
    echo "Creating app registration"

    # OAuth2 - must be set to the URL to where the app's OAuth2 pipeline redirects after authentication
    local oauth2_redirect_uri="${BASE_URL}auth/complete/azuread-tenant-oauth2/"

    # Microsoft Graph permissions
    local app_permissions='[{"resourceAppId": "00000003-0000-0000-c000-000000000000","resourceAccess": [{"id": "e1fe6dd8-ba31-4d61-89e7-88639da4683d","type": "Scope"},{"id": "06da0dbc-49e2-44d2-8312-53f166ab848a","type": "Scope"}]}]'

    # Tenant where the app registration will be created
    local tenant_id="${REGISTRATION_TENANT}"

    # Azure URI for this app registration
    local app_uri="${BASE_URL}"

    # A client secret used in the OAuth2 call
    local client_secret=$(get_or_create_azure_secret  "SECRET-KEY")

    # The tenant we use to register the app may not be the tenant used to create the app
    switch_to_registration_tenant

    # Create app registration
    echo "... registering app"
    az ad app create --display-name "${DISPLAY_NAME}" --homepage "${BASE_URL}" --reply-urls "${oauth2_redirect_uri}" --password "${client_secret}" --credential-description "Client secret" --end-date "2299-12-31" --identifier-uris "${app_uri}" --required-resource-accesses "${app_permissions}"

    # Get the Application ID (Client ID) which is set when the app is created
    local client_id=$(az ad app list --identifier-uri "${app_uri}" --query "[].appId" -o tsv)

    # Consent to permissions
    echo "... setting app permissions"
    az ad app permission admin-consent --id "${client_id}"

    # The key vault may be in a different tenant to the registration, so we need to change it back here.
    # If we don't do this, the keyvault commands may return permission errors, even with the --subscription parameter.
    switch_to_app_tenant

    # Store authentication credentials in keyvault
    echo "... storing credentials in the keyvault"
    az keyvault secret set --name "AZUREAD-OAUTH2-KEY" --vault-name "${KEYVAULT_NAME}" --value "${client_id}"
    az keyvault secret set --name "AZUREAD-OAUTH2-SECRET" --vault-name "${KEYVAULT_NAME}" --value "${client_secret}"
    az keyvault secret set --name "AZUREAD-OAUTH2-TENANT-ID" --vault-name "${KEYVAULT_NAME}" --value "${tenant_id}"
}

# Set or update settings for a deployed webapp
deploy_settings () {

    local secret_key=$(get_azure_secret  "SECRET-KEY")
    local azuread_oauth2_key=$(get_azure_secret  "AZUREAD-OAUTH2-KEY")
    local azuread_oauth2_secret=$(get_azure_secret  "AZUREAD-OAUTH2-SECRET")
    local azuread_oauth2_tenant_id=$(get_azure_secret  "AZUREAD-OAUTH2-TENANT-ID")
    local db_username=$(get_azure_secret  "DB-USERNAME")
    local db_password=$(get_azure_secret  "DB-PASSWORD")
    local database_url=$(get_azure_secret  "DB-URL")

    # Domains that Django can serve for. NB. must not contain the protocol
    local allowed_hosts="${BASE_DOMAIN},127.0.0.1"

    az webapp config appsettings set --name ${APP_NAME} --resource-group ${RESOURCE_GROUP} --settings SECRET_KEY="${secret_key}"
    az webapp config appsettings set --name ${APP_NAME} --resource-group ${RESOURCE_GROUP} --settings DATABASE_URL="${database_url}"
    az webapp config appsettings set --name ${APP_NAME} --resource-group ${RESOURCE_GROUP} --settings DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE}"
    az webapp config appsettings set --name ${APP_NAME} --resource-group ${RESOURCE_GROUP} --settings ALLOWED_HOSTS="${allowed_hosts}"
    az webapp config appsettings set --name ${APP_NAME} --resource-group ${RESOURCE_GROUP} --settings SAFE_HAVEN_DOMAIN="${SAFE_HAVEN_DOMAIN}"
    az webapp config appsettings set --name ${APP_NAME} --resource-group ${RESOURCE_GROUP} --settings AZUREAD_OAUTH2_KEY="${azuread_oauth2_key}"
    az webapp config appsettings set --name ${APP_NAME} --resource-group ${RESOURCE_GROUP} --settings AZUREAD_OAUTH2_SECRET="${azuread_oauth2_secret}"
    az webapp config appsettings set --name ${APP_NAME} --resource-group ${RESOURCE_GROUP} --settings AZUREAD_OAUTH2_TENANT_ID="${azuread_oauth2_tenant_id}"
    az webapp config appsettings set --name ${APP_NAME} --resource-group ${RESOURCE_GROUP} --settings USE_LDAP="${USE_LDAP}"
    az webapp config appsettings set --name ${APP_NAME} --resource-group ${RESOURCE_GROUP} --settings LDAP_SERVER="${LDAP_SERVER}"
    az webapp config appsettings set --name ${APP_NAME} --resource-group ${RESOURCE_GROUP} --settings LDAP_USER="${LDAP_USER}"
    az webapp config appsettings set --name ${APP_NAME} --resource-group ${RESOURCE_GROUP} --settings LDAP_PASSWORD="${LDAP_PASSWORD}"

    az webapp config appsettings set --name ${APP_NAME} --resource-group ${RESOURCE_GROUP} --settings EMAIL_HOST="${EMAIL_HOST}"
    az webapp config appsettings set --name ${APP_NAME} --resource-group ${RESOURCE_GROUP} --settings EMAIL_HOST_USER="${EMAIL_HOST_USER}"
    az webapp config appsettings set --name ${APP_NAME} --resource-group ${RESOURCE_GROUP} --settings EMAIL_HOST_PASSWORD="${EMAIL_HOST_PASSWORD}"

    az webapp config appsettings set --name ${APP_NAME} --resource-group ${RESOURCE_GROUP} --settings BASE_URL="${BASE_URL}"

    # Prevent App Service for Linux from maintaining storage between deployments, which causes problems with the startup command not being found
    az webapp config appsettings set --name ${APP_NAME} --resource-group ${RESOURCE_GROUP} --settings WEBSITES_ENABLE_APP_SERVICE_STORAGE="False"
}

azure_login
error_if_already_deployed
create_resource_group
create_keyvault
create_postgresql_db
create_app
create_registration
deploy_settings

# At time of writing, the following steps must be done on the Azure Portal
cat <<EOF

To complete the deployment:

1. Set up IP restrictions for the App Service
* Browse to Azure Portal -> App Services / ${APP_NAME} / Networking / Configure Access Restrictions
* Under ${APP_NAME}.azurewebsites.net, add a rule under for each IP range to enable
* Under ${APP_NAME}.scm.azurewebsites.net, select "Same restrictions...", or add a rule for each IP range to enable

2. Choose a method to deploy the code

  2A. Continuous deployment using GitHub
    * Browse to Azure Portal -> App Services / $APP_NAME / Deployment Center
    * If there is an existing deployment you will need to disable this using the Disconnect button
    * Select GitHub and click Authorize
    * In the 'Configure' step, select:
      - Organization: 'alan-turing-institute'
      - repository: 'data-safe-haven-webapp'
      - branch: the branch you wish to continuously deploy (eg master, development)

  2B. Local git deployment
    * Browse to Azure Portal -> App Services / $APP_NAME  / Deployment Center
    * Click the FTP/Credentials button
    * Under USER CREDENTIALS set username as DSH_DEPLOYMENT_USER and choose a password
    * To deploy your current head branch, run the script "deploy_code.sh -e $ENVFILE"
    * Enter the deployment password when prompted

EOF
