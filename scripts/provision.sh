#
# Requires the Azure CLI:
#
# https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest
#

RESOURCE_GROUP=datasafehaven
PLAN_NAME=datasafehaven
APP_NAME=datasafehaven
APP_SLOT=dev

SQL_SERVER_NAME=datasafehaven
DB_USERNAME=havenadmin
DB_PASSWORD='<choose-a-database-password>'
DB_PASSWORD=Hgl0NzO27Ra1
DB_NAME="${APP_NAME}_${APP_SLOT}"

SECRET_KEY='<generate-a-random-string-of-characters>'
SECRET_KEY='mtd=_x966l9gg&q%uf!hf4ixdv47#a@adsms=v0%w%x4gm+3&4'
LOCATION='ukwest'
SAFE_HAVEN_DOMAIN="${APP_NAME}-${APP_SLOT}.azurewebsites.net"

# az login

az group create --name $RESOURCE_GROUP --location $LOCATION
az appservice plan create --name $PLAN_NAME --resource-group $RESOURCE_GROUP --sku S1
az webapp create --name $APP_NAME --resource-group $RESOURCE_GROUP --plan $PLAN_NAME

# Set up the database server
az sql server create --admin-user=$DB_USERNAME --admin-password=$DB_PASSWORD --name=$SQL_SERVER_NAME --location=$LOCATION --resource-group=$APP_NAME

az sql server firewall-rule create --server $SQL_SERVER_NAME --resource-group $RESOURCE_GROUP --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0 --name AllowAllWindowsAzureIps

# Create the database
az sql db create --name=$DB_NAME --resource-group=$APP_NAME --server=$SQL_SERVER_NAME

# Create a deployment slot for dev
az webapp deployment slot create --name $APP_NAME --resource-group $RESOURCE_GROUP --slot $APP_SLOT

# Settings for dev server
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --slot  $APP_SLOT --settings SECRET_KEY=$SECRET_KEY
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --slot  $APP_SLOT --settings DATABASE_URL="mssql://$DB_USERNAME:$DB_PASSWORD@$SQL_SERVER_NAME.database.windows.net:1433/$DB_NAME"
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --slot  $APP_SLOT --settings DJANGO_SETTINGS_MODULE='config.settings.dev'
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --slot  $APP_SLOT --settings ALLOWED_HOSTS="$APP_NAME-$APP_SLOT.azurewebsites.net"
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --slot  $APP_SLOT --settings SAFE_HAVEN_DOMAIN="${APP_NAME}-${APP_SLOT}.azurewebsites.net"

# (Adding site extensions can't be done with az: see https://github.com/Azure/azure-cli/issues/7617)
cat <<EOF
To complete the deployment:

1. Set up Python 3.6 site extension
* Browse to Azure Portal -> $APP_NAME / Deployment slots / $SLOT_NAME
* Click Extensions and install Python 3.6 x86

2. Set up GitHub deployment
* Browse to Azure Portal -> $APP_NAME / Deployment slots / $SLOT_NAME
* Click Deployment Center, then connect to GitHub.
* Through the GitHub connection, browse to 'alan-turing-institute' and then the 'data-safe-haven-webapp' repository, selecting whichever branch is appropriate for the slot.
EOF
