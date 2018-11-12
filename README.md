# Data Safe Haven
Django web application for the data safe haven


## Setup

### Install system requirements

* Python 3.6+
* Postgres 10+ (with dev headers)

### Install requirements into virtualenv

```bash
pip install -r requirements/base.txt
```

or, for local dev setup:

```bash
pip install -r requirements/local.txt
```

### Set up PostgreSQL

The --createdb flag should be set for the database user if running tests (so test databases can be set up and torn down). This should not be done on a production system.

```bash
createuser haven --createdb
createdb -O haven haven
```

### Set up environment variables

Create a file named `haven/.env` with the following entries (these can also be set as environment variables
when the webserver is run):

```python
# A randomly generated string
SECRET_KEY='my-secret-key'

# Database connection string: depends on local postgres setup
DATABASE_URL='postgres://haven:haven@localhost/haven'
```

### Apply migrations

```bash
haven/manage.py migrate
```

### Create initial admin user account

```bash
haven/manage.py createsuperuser
```

### Run server

```bash
python haven/manage.py runserver
```

### Run unit tests

```
cd haven
pytest
```

## Contributing

Python dependencies are managed via [`pip-tools`](https://pypi.org/project/pip-tools/). To add a new python package to the requirements:

* Add the package name and version to the relevant `.in` file in `requirements/` (usually `requirements/base.in`)
* Run `make -C requirements/` to rebuild the requirements txt files



## Deploy to Azure

Install the Azure CLI: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest

```
az login
export APP_NAME='datasafehaven'
az group create --name $APP_NAME --location westeurope
az appservice plan create --name $APP_NAME --resource-group $APP_NAME --sku S1
az webapp create --name $APP_NAME --resource-group $APP_NAME --plan $APP_NAME

az webapp config set --python-version 3.6 --name $APP_NAME --resource-group $APP_NAME # set python version
az webapp config appsettings set --name $APP_NAME --resource-group $APP_NAME --settings APP_CONFIG_NAME=dev


az webapp deployment source config --name $APP_NAME --repo-url https://github.com/alan-turing-institute/data-safe-haven --resource-group $APP_NAME --app-working-dir=webapp --branch=master --cd-app-type=python --git-token  --python-version=3.6


az webapp deployment slot create --name APP_NAME --resource-group $APP_NAME --slot $APP_SLOT

az webapp config appsettings set --name $APP_NAME --resource-group $APP_NAME --slot  $APP_SLOT --settings SECRET_KEY='<random-string-of-characters>'


az webapp config appsettings set --name $APP_NAME --resource-group $APP_NAME --slot  $APP_SLOT --settings DATABASE_URL='mssql://<username>:<password>@tcp:datasafehaven.database.windows.net:1433/haven-dev'
```
az webapp config appsettings set --name $APP_NAME --resource-group $APP_NAME --slot  $APP_SLOT --settings DJANGO_SETTINGS_MODULE='config.settings.dev'
