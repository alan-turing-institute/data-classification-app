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


### Run unit tests
Note: the `staticfiles` folder must exist before running the tests.


```
cd haven
pytest

```
### More information and Troubleshooting

See the [Local Development Notes][local-development-notes]
