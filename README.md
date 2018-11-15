# Data Safe Haven
Django web application for the data safe haven.
This project can be set up in two configurations

- local development, using a locally-hosted PostgreSQL server
- web deployment, using an Azure server

---

## Local Development Setup

### Install system requirements

* Python 3.6+
* Postgres 10+ (with dev headers)

### Install requirements into virtualenv

```bash
pip install -r requirements/local.txt
```

### Set up PostgreSQL

The `--createdb` flag should be set for the database user when running tests (so test databases can be set up and torn down). This should not be done on a production system.

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
haven/manage.py runserver
```

### Test server
The server can be accessed at `http://127.0.0.1:8000/`. The credentials are those

### Run unit tests
These look for a folder called `staticfiles` which should be created before running the tests.


```
mkdir -p haven/staticfiles
cd haven

# Create staticfiles directory to suppress warnings from whitenoise
mkdir -p staticfiles

pytest
```

## Contributing

Python dependencies are managed via [`pip-tools`](https://pypi.org/project/pip-tools/). To add a new python package to the requirements:

* Add the package name and version to the relevant `.in` file in `requirements/` (usually `requirements/base.in`)
* Run `make -C requirements/` to rebuild the requirements txt files

---

## Deployment to Azure

Install the [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest)

Use `az login` to log in on the command line.

Check that the values at the top of `scripts/provision.sh` are correct.

Then run `scripts/provision.sh` to create the webapp and relevant resources.

Instructions are given at the end of the script to run some manual steps that need to be performed through the Azure portal.
These instructions will also give you the URL at which the site is hosted.

If errors are encountered in the browser after deploy, the following settings can be added to web.config to display useful errors in the browser:
```
<configuration>
    <system.webServer>
        <httpErrors errorMode="Detailed" />
    </system.webServer>
    <system.web>
        <customErrors mode="Off"/>
        <compilation debug="true"/>
    </system.web>
</configuration>
```
