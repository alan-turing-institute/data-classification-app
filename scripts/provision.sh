#!/usr/bin/env bash

#
# Script for deploying or updating the Data Safe Haven management application on Azure.
#
# Requires:
#  1. The Azure CLI to be installed:
#      https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest
#
#  2. An environment file (.env) to be configured for your deployment.
#      See .env.example for more information
#
#  3. Azure login with sufficient permissions to deploy resources and create an App Registration on the appropriate tenant
#
#  4. If deploying from a private GitHub repository, a GitHub login with sufficient permissions to add a deploy key
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
    echo "$(head /dev/urandom | LC_ALL=C tr -dc A-Za-z0-9 | head -c32)"
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
          keyvault_value=$(generate_key)
          az keyvault secret set --name "$1" --vault-name "${KEYVAULT_NAME}" --value "${keyvault_value}" --output none
    fi

    echo "${keyvault_value}"
}

azure_login() {
    if [ -z "${SKIP_AZURE_LOGIN}" ]; then
        az login
        switch_to_app_tenant
    fi
}

# Switch Azure CLI to the tenant used for app creation
switch_to_app_tenant () {
    # We need to explicitly set the subscription in order to change the default tenant.
    # This is because Azure CLI does not always respect the --subscription argument.

    if [ -z "${SKIP_AZURE_LOGIN}" ]; then
        echo "Preparing to switch to $SUBSCRIPTION"
        az account set --subscription "${SUBSCRIPTION}"
    fi
}

# Switch Azure CLI to the tenant used for app registration
switch_to_registration_tenant () {
    # The tenant we use to register the app may not have a subscription, in which case we cannot use
    # 'az account set --subscription'. Instead we need to set the tenant by calling 'az login' with
    # the --allow-no-subscriptions flag.
    if [ -z "${SKIP_AZURE_LOGIN}" ]; then
        az login --tenant "${REGISTRATION_TENANT}" --allow-no-subscriptions
    fi
}

# Return response from a get call
function curl_with_retry() {
    local url="$1"
    local description="$2"

    local retry=0
    until [ "$retry" -gt 20 ]; do
      local result
      result=$(curl --fail --silent "${url}")
      status="$?"

      if [ $status -eq 0 ]; then
        echo "${result}"
        return
      fi

      echo "Retry ${retry}" 1>&2
      ((retry++))
      sleep 30;
    done
    echo "Failed to execute curl for ${description}" 1>&2
    exit 1
}

create_or_update_resource_group() {
    echo "Creating or updating the resource group ${RESOURCE_GROUP}"
    az group create --name "${RESOURCE_GROUP}" --location "${LOCATION}"

    # Create a lock to prevent accidental deletion of the resource group and the resources it contains
    az lock create --name LockDataSafeHaven --lock-type CanNotDelete --resource-group "${RESOURCE_GROUP}" --notes "Prevents accidental deletion of Data Safe Haven management webapp and its resources"
}

create_or_update_keyvault() {
    echo "Creating or updating the keyvault ${KEYVAULT_NAME}"
    az keyvault create --name "${KEYVAULT_NAME}" --resource-group "${RESOURCE_GROUP}" --location "${LOCATION}"
}

create_or_update_app() {
    echo "Creating or updating the app service ${APP_NAME}"

    # App service plan
    az appservice plan create --name "${PLAN_NAME}" --resource-group "${RESOURCE_GROUP}" --sku S1 --is-linux

    # Webapp
    az webapp create --name "${APP_NAME}" --resource-group "${RESOURCE_GROUP}" --plan "${PLAN_NAME}" --runtime "PYTHON|3.7"

    # Configure webapp logging
    az webapp log config --name "${APP_NAME}" --resource-group "${RESOURCE_GROUP}" --application-logging true --web-server-logging filesystem --docker-container-logging filesystem --detailed-error-messages true --level warning

    # Force the proxy to redirect non-https traffic to https
    az webapp update --name "${APP_NAME}" --resource-group "${RESOURCE_GROUP}" --https-only true

    # Configure startup file
    az webapp config set --name "${APP_NAME}" --resource-group "${RESOURCE_GROUP}" --startup-file "/home/site/repository/deploy_linux.sh"

    # Get deployment URL
    local scm_uri=$(az webapp deployment list-publishing-credentials --name "${APP_NAME}" --resource-group "${RESOURCE_GROUP}" --query "scmUri" -otsv)
    local deployment_url="${scm_uri}:443/${APP_NAME}.git/"
    az keyvault secret set --name "DEPLOYMENT-URL" --vault-name "${KEYVAULT_NAME}" --value "${deployment_url}"

    # Create Django secret key
    local django_secret_key=$(get_or_create_azure_secret  "SECRET-KEY")
}

update_deployment_configuration () {
    echo "Creating or updating the deployment configuration"

    # Get deployment URL
    local scm_uri=$(az webapp deployment list-publishing-credentials --name "${APP_NAME}" --resource-group "${RESOURCE_GROUP}" --query "scmUri" -otsv)

    # Fetch deploy hook
    local deploy_hook="${scm_uri}/deploy"
    az keyvault secret set --name "DEPLOY-HOOK" --vault-name "${KEYVAULT_NAME}" --value "${deploy_hook}"

    # Fetch deploy key
    local deploy_key_request="${scm_uri}/api/sshkey?ensurePublicKey=1"
    local key_with_quotes=$(curl_with_retry "${deploy_key_request}" "Requesting deploy key from SCM")
    local deploy_key=$(sed -e 's/^"//' -e 's/"$//' <<<"${key_with_quotes}")
    az keyvault secret set --name "DEPLOY-KEY" --vault-name "${KEYVAULT_NAME}" --value "${deploy_key}"

    if [ -z ${DEPLOYMENT_GITHUB_REPO} ]; then
        echo "No GitHub repository was specified for adding a deploy key. If you are deploying from a private repository you will need to add a deploy key to your repository."
    else
        echo "Adding GitHub deploy key."
        echo "Please enter your GitHub username and password when prompted."
        read -p "Enter your GitHub username: " github_username
        local scm_base_url="${APP_NAME}.scm.azurewebsites.net"
        local deploy_key_args="{\"title\":\"${scm_base_url}\",\"key\":\"${deploy_key}\",\"read_only\":true}"
        curl --user "${github_username}" --request POST --data "${deploy_key_args}" "https://api.github.com/repos/${DEPLOYMENT_GITHUB_REPO}/keys"

        if [ ! -z ${DEPLOYMENT_AUTO_UPDATE} ]; then
            echo "Adding GitHub deploy hook to enable auto-deployment."
            echo "Please enter your GitHub password when prompted."
            local deploy_hook_args="{\"config\":{\"url\": \"${deploy_hook}\"}}"
            curl --user "${github_username}" --request POST --data "${deploy_hook_args}" "https://api.github.com/repos/${DEPLOYMENT_GITHUB_REPO}/hooks"
        fi
    fi

    # Set the source code URL and branch
    az webapp deployment source config --branch "${DEPLOYMENT_BRANCH}" --name "${APP_NAME}" --repo-url "${DEPLOYMENT_SOURCE}" --resource-group "${RESOURCE_GROUP}"
}

create_or_update_postgresql_db() {
    echo "Creating or updating the DB server ${DB_SERVER_NAME}"

    local db_username=${DB_USERNAME}
    local db_password=$(get_or_create_azure_secret  "DB-PASSWORD")

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

create_or_update_registration () {
    echo "Creating or updating the app registration"

    # OAuth2 - must be set to the URL to where the app's OAuth2 pipeline redirects after authentication
    local oauth2_redirect_uri="${BASE_URL}auth/complete/azuread-tenant-oauth2/"

    # Microsoft Graph permissions
    local app_permissions='[{"resourceAppId": "00000003-0000-0000-c000-000000000000","resourceAccess": [{"id": "e1fe6dd8-ba31-4d61-89e7-88639da4683d","type": "Scope"},{"id": "06da0dbc-49e2-44d2-8312-53f166ab848a","type": "Scope"}]}]'

    # Tenant where the app registration will be created
    local tenant_id="${REGISTRATION_TENANT}"

    # Azure URI for this app registration
    local app_uri="${BASE_URL}"

    # A client secret used in the OAuth2 call
    local client_secret=$(get_or_create_azure_secret  "AZUREAD-OAUTH2-SECRET")

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
update_app_settings () {
    echo "Setting or updating the app configuration settings"

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
    az webapp config appsettings set --name ${APP_NAME} --resource-group ${RESOURCE_GROUP} --settings WEBAPP_TITLE="${WEBAPP_TITLE}"
    az webapp config appsettings set --name ${APP_NAME} --resource-group ${RESOURCE_GROUP} --settings SAFE_HAVEN_DOMAIN="${SAFE_HAVEN_DOMAIN}"
    az webapp config appsettings set --name ${APP_NAME} --resource-group ${RESOURCE_GROUP} --settings SECURITY_GROUP_SYSTEM_MANAGERS="${SECURITY_GROUP_SYSTEM_MANAGERS}"
    az webapp config appsettings set --name ${APP_NAME} --resource-group ${RESOURCE_GROUP} --settings SECURITY_GROUP_PROGRAMME_MANAGERS="${SECURITY_GROUP_PROGRAMME_MANAGERS}"
    az webapp config appsettings set --name ${APP_NAME} --resource-group ${RESOURCE_GROUP} --settings SECURITY_GROUP_PROJECT_MANAGERS="${SECURITY_GROUP_PROJECT_MANAGERS}"
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
create_or_update_resource_group
create_or_update_keyvault
create_or_update_postgresql_db
create_or_update_app
create_or_update_registration
update_app_settings
update_deployment_configuration

# At time of writing, the following steps must be done on the Azure Portal
cat <<EOF

To complete the deployment:

Set up IP restrictions for the SCM repository
* Browse to Azure Portal -> App Services / ${APP_NAME} / Networking / Configure Access Restrictions
* Select the ${APP_NAME}.scm.azurewebsites.net tab
* Add a rule for each IP range to enable.
  * If you plan to deploy using Cloud Shell ensure the IP ranges are added during the time of deployment
  * For continuous deployment, include IP ranges for GitHub hooks: https://api.github.com/meta
EOF
