# Remote authentication with Authelia and LDAP
The Data Classification App can be configured to use remote authentication by including `remote` in the `AUTH_TYPES` environment variable at deployment. The `production.yml` docker-compose file will automatically build an Authelia service which can be configured to connect to LDAP or use a local file: `users_database.yml`.

## Deploying with authelia on a virtual machine

### Domains
You'll need to setup a domain for the app, as well as an 'auth' subdomain off it, pointing to the VM; e.g.:
* data-classification.example.com
* auth.data-classification.example.com

### Initial configuration
* Create a directory for the app and clone the repository:
```
mkdir dc-app && cd dc-app
git clone git@github.com:alan-turing-institute/data-classification-app.git .
```
* Create `.django` and `.postgres` env files under `./.envs/.production/`, including `remote` in the list of `AUTH_TYPES`, and your custom domain in `ALLOWED_HOSTS` and `BASE_DOMAIN`. 
* If using LDAP, you can specify the Sytem Manager and Programme Manager LDAP Groups
**Avoid quotes around variables**:

`.envs/.production/.django`
```
DJANGO_SETTINGS_MODULE=haven.settings.production

SECRET_KEY=notasecret # try https://djecrety.ir/ for example
APP_NAME=data-classification-app
WEBAPP_TITLE=Data Classification
BASE_DOMAIN=data-classification.example.com
ALLOWED_HOSTS=data-classification.example.com
DEBUG=false
AUTH_TYPES=remote

# LDAP role groups
SYSTEM_MANAGER_LDAP_GROUP=dca_sys_man
PROGRAMME_MANAGER_LDAP_GROUP=dca_prog_man

# Email parameters
EMAIL_HOST=smtp.sendgrid.net
EMAIL_HOST_USER=sendgrid-username
EMAIL_HOST_PASSWORD=sendgrid-password
EMAIL_PORT=587
EMAIL_USE_TLS=True
FROM_MAIL=noreply@example.com
```

`.envs/.production/.postgres`
```
POSTGRES_DB=haven
POSTGRES_USER=haven
POSTGRES_PASSWORD=haven
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

* Create a configuration file for Authelia from the template:
```
cd compose/production/authelia
export BASE_DOMAIN=<custom domain>
. setup-config.sh
cd ..
```
* Generate a new random alphanumeric strings for jwt_secret and session/secret and substitute these for placeholders in authelia/configuration.yml

### Certificates

* Build the containers before starting:

  `sudo docker-compose -f production.yml build`
* Create directories for certbot to store things:

  `mkdir -p data/certbot/{conf,www}`
* Change permissions on www:

  `chmod 777 data/certbot/www`
* Make init-letsencrypt.sh executable:

  `chmod 775 init-letsencrypt.sh`
* Set the BASE_DOMAIN environment variable (if not already done so):

  `export BASE_DOMAIN=<custom domain>`
* Run the script:
  
  `./init-letsencrypt.sh`
* If it works without any complaints, set staging to 0 and run the script again

  `LETSENCRYPT_STAGING=0 ./init-letsencrypt.sh`

