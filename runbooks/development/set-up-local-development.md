# Data Safe Haven web management application

These instructions are for running a local test instance of the management web application on your machine.


## Local Development Setup

### Install system requirements

* Python 3.7+
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
haven/manage.py migrate easyaudit
haven/manage.py migrate
```

### Create initial admin user account

```bash
haven/manage.py createsuperuser
```

### Update static files

```bash
mkdir -p haven/staticfiles
haven/manage.py collectstatic
```

### Apply migrations

```bash
haven/manage.py migrate
```

### Run server

```bash
haven/manage.py runserver
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


```
cd haven
pytest

```
### More information and Troubleshooting

See the [Local Development Notes][local-development-notes]
