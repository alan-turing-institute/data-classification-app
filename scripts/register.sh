#
# Requires the Azure CLI:
#
# https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest
#

set -e

# Document usage for this script
usage() {
    echo "usage: $0 [-h] [-e envfile]"
    echo "  -h            display help"
    echo "  -e path to file containing environment variables"
    exit 1
}


# See Format of env file:
# .env.example

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


# Construct domain and URL for the Sfae Haven Management Webapp
BASE_DOMAIN="${APP_NAME}.azurewebsites.net"
BASE_URL="https://${BASE_DOMAIN}/"

# This must be set to the URL to where the app's OAuth2 pipeline redirects after authentication
OAUTH2_REDIRECT_URI="${BASE_URL}auth/complete/azuread-tenant-oauth2/"

# ALLOWED_HOSTS must not contain the protocol
ALLOWED_HOSTS="${BASE_DOMAIN}"


DJANGO_SETTINGS_MODULE='config.settings.dev'



APP_URI="${BASE_URL}"
PLAN_NAME="${APP_NAME}"
KEYVAULT_NAME="${APP_NAME}"
SQL_SERVER_NAME="${APP_NAME}"
CONTAINER_REGISTRY_NAME=$(echo "${APP_NAME}" | sed 's/[^a-zA-Z0-9]//g')
DOCKER_TAG_PREFIX="dsh-web"
DOCKER_TAG="${DOCKER_TAG_PREFIX}:v1"
DOCKER_IMAGE_NAME="${CONTAINER_REGISTRY_NAME}.azurecr.io/${DOCKER_TAG}"
DOCKER_IMAGE_URL="https://${DOCKER_IMAGE_NAME}"

DB_NAME=datasafehavendb
DB_USERNAME=havenadmin


generate_key () {
    openssl rand 32 -base64
}

function get_azure_secret() {
    local SECRET_NAME="$1"
    az keyvault secret show --name "${SECRET_NAME}" --vault-name "${KEYVAULT_NAME}" --query "value" -otsv
}

create_app() {
    echo "Creating App Service Plan"
    az appservice plan create --name "${PLAN_NAME}" --resource-group "${RESOURCE_GROUP}" --sku S1 --is-linux

    echo "Creating App Service"
    az webapp create --name "${APP_NAME}" --resource-group "${RESOURCE_GROUP}" --plan "${PLAN_NAME}" --deployment-container-image-name "${DOCKER_IMAGE_NAME}"

    local registry_username=$(get_azure_secret  "REGISTRY-USERNAME")
    local registry_password=$(get_azure_secret  "REGISTRY-PASSWORD")

    az webapp config container set --name "${APP_NAME}" --resource-group "${RESOURCE_GROUP}" --docker-custom-image-name "${DOCKER_IMAGE_NAME}" --docker-registry-server-url "${DOCKER_IMAGE_URL}" --docker-registry-server-user "${registry_username}" --docker-registry-server-password "${registry_password}"

    # Create a secret key for Django and store in keyvault
    local django_secret_key=$(generate_key)
    az keyvault secret set --name "SECRET-KEY" --vault-name "${KEYVAULT_NAME}" --value "${django_secret_key}"
}

create_resource_group() {
    echo "Creating resource group"
    az group create --name "${RESOURCE_GROUP}" --location "${LOCATION}" --subscription "${SUBSCRIPTION}"
}

create_keyvault() {
    echo "Creating key vault"
    az keyvault create --name "${KEYVAULT_NAME}" --resource-group "${RESOURCE_GROUP}" --location "${LOCATION}" --subscription "${SUBSCRIPTION}"
}

create_db() {
    echo "Creating the DB server"
    local db_username=${DB_USERNAME}
    local db_password=$(generate_key)
    az sql server create --admin-user="${DB_USERNAME}" --admin-password="${db_password}" --name="${SQL_SERVER_NAME}" --location="${LOCATION}" --resource-group="$RESOURCE_GROUP"
    az sql server firewall-rule create --server "${SQL_SERVER_NAME}" --resource-group "${RESOURCE_GROUP}" --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0 --name AllowAllWindowsAzureIps

    echo "Creating the database"
    az sql db create --name="${DB_NAME}" --resource-group="${RESOURCE_GROUP}" --server="${SQL_SERVER_NAME}"

    # Store DB credentials in keyvault
    local database_url="mssql://$DB_USERNAME:$DB_PASSWORD@$SQL_SERVER_NAME.database.windows.net:1433/$DB_NAME"
    az keyvault secret set --name "DB-USERNAME" --vault-name "${KEYVAULT_NAME}" --value "${db_username}"
    az keyvault secret set --name "DB-PASSWORD" --vault-name "${KEYVAULT_NAME}" --value "${db_password}"
    az keyvault secret set --name "DB-URL" --vault-name "${KEYVAULT_NAME}" --value "${database_url}"
}

create_container_registry() {
    echo "Creating the container registry"
    az acr create --resource-group "${RESOURCE_GROUP}" --name "${CONTAINER_REGISTRY_NAME}" --sku Basic --location "${LOCATION}" --admin-enabled true

    local registry_username=$(az acr credential show --name "${CONTAINER_REGISTRY_NAME}" --query "username" -otsv)
    local registry_password=$(az acr credential show --name "datasafehaventestreg" --query "passwords[?name=='password'].value" -otsv)
    az keyvault secret set --name "REGISTRY-USERNAME" --vault-name "${KEYVAULT_NAME}" --value "${registry_username}"
    az keyvault secret set --name "REGISTRY-PASSWORD" --vault-name "${KEYVAULT_NAME}" --value "${registry_password}"
}

initialise () {
    # We need to explicitly set the subscription in order to change the default tenant. Azure will create the keyvault
    # in the default tenant regardless of the --subscription setting
    az account set --subscription "${SUBSCRIPTION}"

    if [[ $(az group exists --name ${RESOURCE_GROUP} --subscription "${SUBSCRIPTION}") != "true" ]]; then

        create_resource_group
        create_keyvault
        create_container_registry
        create_db
        create_app
    else
        echo "Resource group already exists - has this app already been created?"
    fi
}

create_registration () {
    echo "Creating app registration"

    # Tenant where the app registration will be created
    local tenant_id="${REGISTRATION_TENANT}"

    # The tenant we use to register the app may not have a subscription, in which case we need to set it explicitly with
    # the --allow-no-subscriptions flag
    az login --tenant "${tenant_id}" --allow-no-subscriptions

    local client_secret=$(generate_key)

    # Create app registration
    local app_permissions='[{"resourceAppId": "00000003-0000-0000-c000-000000000000","resourceAccess": [{"id": "e1fe6dd8-ba31-4d61-89e7-88639da4683d","type": "Scope"},{"id": "06da0dbc-49e2-44d2-8312-53f166ab848a","type": "Scope"}]}]'
    az ad app create --display-name "${DISPLAY_NAME}" --homepage "${BASE_URL}" --reply-urls "${OAUTH2_REDIRECT_URI}" --password "${client_secret}" --credential-description "Client secret" --end-date "2299-12-31" --identifier-uris "${APP_URI}" --required-resource-accesses "${app_permissions}"

    # Get the Application ID (Client ID) which is set when the app is created
    local client_id=$(az ad app list --identifier-uri "${APP_URI}" --query "[].appId" -o tsv)

    # Consent to permissions
    echo "Permissions consent"
    az ad app permission admin-consent --id "${client_id}"

    # The key vault may be in a different tenant to the registration, so we need to change it back here.
    # Using --subscription in az keyvault commands without changing the default tenant/subscription can result in a permissions error
    az account set --subscription "${SUBSCRIPTION}"

    # Store authentication credentials in keyvault
    az keyvault secret set --name "AZUREAD-OAUTH2-KEY" --vault-name "${KEYVAULT_NAME}" --value "${client_id}"
    az keyvault secret set --name "AZUREAD-OAUTH2-SECRET" --vault-name "${KEYVAULT_NAME}" --value "${client_secret}"
    az keyvault secret set --name "AZUREAD-OAUTH2-TENANT-ID" --vault-name "${KEYVAULT_NAME}" --value "${tenant_id}"
}

deploy_settings () {
    local secret_key=$(get_azure_secret  "SECRET-KEY")
    local azuread_oauth2_key=$(get_azure_secret  "AZUREAD-OAUTH2-KEY")
    local azuread_oauth2_secret=$(get_azure_secret  "AZUREAD-OAUTH2-SECRET")
    local azuread_oauth2_tenant_id=$(get_azure_secret  "AZUREAD-OAUTH2-TENANT-ID")
    local db_username=$(get_azure_secret  "DB-USERNAME")
    local db_password=$(get_azure_secret  "DB-PASSWORD")
    local database_url=$(get_azure_secret  "DB-URL")

    az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings SECRET_KEY="${secret_key}"
    az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings DATABASE_URL="${database_url}"
    az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE}"
    az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings ALLOWED_HOSTS="${ALLOWED_HOSTS}"
    az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings SAFE_HAVEN_DOMAIN="${SAFE_HAVEN_DOMAIN}"
    az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings AZUREAD_OAUTH2_KEY="${azuread_oauth2_key}"
    az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings AZUREAD_OAUTH2_SECRET="${azuread_oauth2_secret}"
    az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings AZUREAD_OAUTH2_TENANT_ID="${azuread_oauth2_tenant_id}"
    az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings USE_LDAP="${USE_LDAP}"
    az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings LDAP_SERVER="${LDAP_SERVER}"
    az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings LDAP_USER="${LDAP_USER}"
    az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings LDAP_PASSWORD="${LDAP_PASSWORD}"

    az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings EMAIL_HOST="${EMAIL_HOST}"
    az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings EMAIL_HOST_USER="${EMAIL_HOST_USER}"
    az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings EMAIL_HOST_PASSWORD="${EMAIL_HOST_PASSWORD}"

    az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings BASE_URL="${BASE_URL}"

}


#initialise
create_registration
deploy_settings
