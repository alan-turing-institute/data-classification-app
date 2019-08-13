# Data Safe Haven web management application

These instructions are for running a local test instance of the management web application on your machine, using Docker and Docker Compose.
This is closer to how the application runs in production. 
It could also be used for local development, although there are several enhancements required to make that smooth (bind-mount source files, gunicorn/npm auto-reload etc.).

## Local Development Setup

### Install system requirements

* Docker (tested with 19.03)
* docker-compose (tested with 1.22)

### Set up environment variables

Create a file named `.env` with the following entries:

```python
# A randomly generated string
SECRET_KEY='my-secret-key'

# Address you wish the app to be available on
APP_BIND_ADDRESS=127.0.0.1:8000

# This should match APP_BIND_ADDRESS
ALLOWED_HOSTS=127.0.0.1

# Credentials used in creating Postgres database 
POSTGRES_USER=haven
POSTGRES_PASSWORD=my-password

# Database connection should match above credentials
DATABASE_URL=postgres://haven:my-password@db:5432/haven

# Config file you want to use
DJANGO_SETTINGS_MODULE=config.settings.local
```

Note that if you also have a `haven/.env` file (for local development without Docker), most values can be set in either `.env` or `haven/.env`.
The exceptions are any specifically needed by docker-compose, e.g. `APP_BIND_ADDRESS` or by Postgres, e.g. `POSTGRES_USER`.
If values are set in both files, `.env` takes precedence.

## Run server

```bash
docker-compose build
docker-compose up
```

### Create initial admin user account

```bash
docker-compose exec app haven/manage.py createsuperuser
```

## Accessing the test server

The local server can be accessed at the address you specify in `.env`, e.g. `http://127.0.0.1:8000/`.