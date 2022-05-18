# Data Safe Haven web management application

These instructions are for running a local test instance of the management web application on your machine.

## Cloning the github repo
Clone the github repo using the following command in your local terminal:

```
git clone git@github.com:alan-turing-institute/data-classification-app.git
```

After entering the folder containing the main repositories' code (either through `cd`'ing into your folder containing the downloaded repo files, or using your OS' method) follow the quick docker setup below.

## :whale: Quick setup with `docker`

#### Local dev docker set-up:

To build two containers `data_classification_app_db` and `django`.

To build the containers from scratch, from the folllowing commands:

```
docker-compose build --no-cache
docker-compose up -d
docker-compose ps # (to check the running containers)

```

The site should now be up and running at `http://localhost:8000`

### Accessing the Admin interface

Visit `localhost:8000/admin` and sign in with username `developer`, password `developer`. This user should be a superuser with the system manager role applied. Check the admin console to make sure classification guidance and classification questions have been imported. Projects and users can be added manually from the admin interface.

To bring down containers and volumes prior to a clean build:

`docker-compose down -v`

> :rotating_light: The following instructions are not required if you have completed `docker` setup  :rotating_light:

## Local Development Setup (not tested alternative to Docker)

### Install system requirements

* Python 3.8+
* Postgres 10+ (with dev headers)

### Install requirements into virtual environment

```bash
pip install poetry
poetry install
```

### Set up PostgreSQL

The `--createdb` flag should be set for the database user when running tests (so test databases can be set up and torn down). This should not be done on a production system.

```bash
createuser haven --createdb
createdb -O haven haven
```

### Set up environment variables

Create a file named `.env` in the repository root with the following entries (these can also be set as environment variables
when the webserver is run):

```python
# A randomly generated string
SECRET_KEY='my-secret-key'

# Database connection string: depends on local postgres setup
DATABASE_URL='postgres://haven:haven@localhost/haven'
```

### Apply migrations

```bash
python manage.py migrate easyaudit
python manage.py migrate
```

### Create initial admin user account

```bash
python manage.py createsuperuser
```

### Update static files

```bash
mkdir -p staticfiles
python manage.py collectstatic
```

### Apply migrations

```bash
python manage.py migrate
```

### Run server

```bash
python manage.py runserver
```

### Accessing the test server
The local server can be accessed at `http://127.0.0.1:8000/`.

For local development, the application can authenticate against the local database, instead of Azure.
However, there are no log in pages in the application - instead you log in using the Django admin interface at `http://127.0.0.1:8000/admin/login`.

To start with, log in as the superuser you created above.
Go to `http://127.0.0.1:8000/admin/identity/user/`, click on the username, and at the bottom of the page change the `Role` field to `System Manager`, and then `Save`.

You will then be able to use the application at `http://127.0.0.1:8000/` with System Manager privileges.
You can then create projects, create users, and assign the users to projects in the same way as the Azure deployment.
However, if you wish to log in as the user, you must make some additional changes in the admin interface.
For each user you wish to log in as, do the following:

1. Go to `http://127.0.0.1:8000/admin/identity/user/`
1. Click on the appropriate username
1. Click on the link to set the password, and complete the form that appears
1. Check the box that says `Staff status`
1. Click `Save`

You will then need to log out as the superuser (http://127.0.0.1:8000/admin/logout), before logging back in as the new user.
Note that you need to use the full username, e.g. `user1@dsgroupdev.co.uk`.

### Run unit tests
Note: the `staticfiles` folder must exist before running the tests.


```bash
make test
```

### More information and Troubleshooting

See the [Local Development Notes](local-development-notes)
