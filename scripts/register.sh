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

# Construct domain
BASE_DOMAIN="${APP_NAME}.azurewebsites.net"

# ALLOWED_HOSTS must not contain the protocol
ALLOWED_HOSTS="${BASE_DOMAIN}"

# The safe haven URL
BASE_URL="https://${BASE_DOMAIN}/"






#ToDo: verify if other redirect URIs are required
OAUTH2_REDIRECT_URI="${BASE_URL}auth/complete/azuread-tenant-oauth2/"

APP_URI="${BASE_URL}"

KEYVAULT_NAME="${APP_NAME}"



initialise () {
    # We need to explicitly set the subscription in order to change the default tenant. Azure will create the keyvault
    # in the default tenant regardless of the --subscription setting
    az account set --subscription "${SUBSCRIPTION}"

    if [[ $(az group exists --name ${RESOURCE_GROUP} --subscription "${SUBSCRIPTION}") != "true" ]]; then
        echo "Creating resource group"
        az group create --name ${RESOURCE_GROUP} --location ${LOCATION} --subscription "${SUBSCRIPTION}"

        echo "Creating key vault"
        az keyvault create --name "${KEYVAULT_NAME}" --resource-group "${RESOURCE_GROUP}" --location "${LOCATION}" --subscription "${SUBSCRIPTION}"
    fi
}

generate_key () {
    openssl rand 32 -base64
}

create_registration () {

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
    az ad app permission admin-consent --id "${client_id}"

    local django_secret_key=$(generate_key)

    # The key vault may be in a different tenant to the registration, so we need to change it back here.
    # Using --subscription in az keyvault commands without changing the default tenant/subscription can result in a permissions error
    az account set --subscription "${SUBSCRIPTION}"

    az keyvault secret set --name "AZUREAD-OAUTH2-KEY" --vault-name "${KEYVAULT_NAME}" --value "${client_id}"
    az keyvault secret set --name "AZUREAD-OAUTH2-SECRET" --vault-name "${KEYVAULT_NAME}" --value "${client_secret}"
    az keyvault secret set --name "AZUREAD-OAUTH2-TENANT-ID" --vault-name "${KEYVAULT_NAME}" --value "${tenant_id}"
}


initialise
create_registration
