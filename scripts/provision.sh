#
# Requires the Azure CLI:
#
# https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest
#

# Deployment parameters
RESOURCE_GROUP=datasafehaven
PLAN_NAME=datasafehaven
APP_NAME=datasafehaven # please note that this name must be *globally* unique
APP_SLOT=dev
SQL_SERVER_NAME=datasafehaven
DB_USERNAME=havenadmin
LOCATION='ukwest'

# Document usage for this script
usage() {  
    echo "usage: $0 [-h] [-e envfile]"
    echo "  -h            display help"
    echo "  -e path to file containing environment variables"
    exit 1
}


# See Format of env file: 
# .env.example


# Set default key and password
SECRET_KEY='mtd=_x966l9gg&q%uf!hf4ixdv47#a@adsms=v0%w%x4gm+3&4'
DB_PASSWORD=Hgl0NzO27Ra1
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

# Construct DB and slot names
DB_NAME="${APP_NAME}_${APP_SLOT}"
SLOT_NAME="${APP_NAME}-${APP_SLOT}"
SAFE_HAVEN_DOMAIN="${SLOT_NAME}.azurewebsites.net"

# Must have called `az login` by this point

# Create resource group if it does not already exist, then create appservice and webapp inside it
if [ "$(az group exists --name $RESOURCE_GROUP)" != "true" ]; then
    echo "Creating resource group"
    az group create --name $RESOURCE_GROUP --location $LOCATION
fi
echo "Creating webapp..."
az appservice plan create --name $PLAN_NAME --resource-group $RESOURCE_GROUP --sku S1
az webapp create --name $APP_NAME --resource-group $RESOURCE_GROUP --plan $PLAN_NAME

# Set up the database server
echo "Setting up the database server"
az sql server create --admin-user=$DB_USERNAME --admin-password=$DB_PASSWORD --name=$SQL_SERVER_NAME --location=$LOCATION --resource-group=$APP_NAME
az sql server firewall-rule create --server $SQL_SERVER_NAME --resource-group $RESOURCE_GROUP --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0 --name AllowAllWindowsAzureIps

# Create the database
echo "Creating the database"
az sql db create --name=$DB_NAME --resource-group=$APP_NAME --server=$SQL_SERVER_NAME

echo "Setting up the server"
# Create a deployment slot for dev
az webapp deployment slot create --name $APP_NAME --resource-group $RESOURCE_GROUP --slot $APP_SLOT

# Settings for dev server
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --slot $APP_SLOT --settings SECRET_KEY=$SECRET_KEY
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --slot $APP_SLOT --settings DATABASE_URL="mssql://$DB_USERNAME:$DB_PASSWORD@$SQL_SERVER_NAME.database.windows.net:1433/$DB_NAME"
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --slot $APP_SLOT --settings DJANGO_SETTINGS_MODULE='config.settings.dev'
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --slot $APP_SLOT --settings ALLOWED_HOSTS="${SAFE_HAVEN_DOMAIN}"
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --slot $APP_SLOT --settings SAFE_HAVEN_DOMAIN="${SAFE_HAVEN_DOMAIN}"
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --slot $APP_SLOT --settings AZUREAD_OAUTH2_KEY="${AZUREAD_OAUTH2_KEY}"
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --slot $APP_SLOT --settings AZUREAD_OAUTH2_SECRET="${AZUREAD_OAUTH2_SECRET}"
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --slot $APP_SLOT --settings AZUREAD_OAUTH2_TENANT_ID="${AZUREAD_OAUTH2_TENANT_ID}"
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --slot $APP_SLOT --settings USE_LDAP="${USE_LDAP}"
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --slot $APP_SLOT --settings LDAP_SERVER="${LDAP_SERVER}"
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --slot $APP_SLOT --settings LDAP_USER="${LDAP_USER}"
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --slot $APP_SLOT --settings LDAP_PASSWORD="${LDAP_PASSWORD}"

az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --slot $APP_SLOT --settings EMAIL_HOST="${EMAIL_HOST}"
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --slot $APP_SLOT --settings EMAIL_HOST_USER="${EMAIL_HOST_USER}"
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --slot $APP_SLOT --settings EMAIL_HOST_PASSWORD="${EMAIL_HOST_PASSWORD}"

az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --slot $APP_SLOT --settings BASE_URL="${BASE_URL}"

# (Adding site extensions can't be done with az: see https://github.com/Azure/azure-cli/issues/7617)
cat <<EOF
To complete the deployment:

1. Set up Python 3.6 site extension
* Browse to Azure Portal -> App Services / $APP_NAME / Deployment slots / ${SLOT_NAME} / Extensions
* Click Add, then Choose Extension and select Python 3.6.4 x86. Accept the terms and install.

2. Set up GitHub deployment
* Browse to Azure Portal -> App Services / $APP_NAME / Deployment slots / ${SLOT_NAME} / Deployment Center
* Select GitHub and click Authorize
* In the 'Configure' step, select:
  - Organization: 'alan-turing-institute'
  - repository: 'data-safe-haven-webapp'
  - branch: whatever is appropriate for this slot

3. The webapp should now be accessible at: ${SAFE_HAVEN_DOMAIN}
EOF
