# Steps to setup data classification app with authelia on a virtual machine

## Domains
You'll need to setup a domain for the app, as well as an 'auth' subdomain off it, pointing to the VM; e.g.:
* data-classification.example.com
* auth.data-classification.example.com

## Initial configuration
* Create a directory for the app and clone the repository:
```
mkdir dc-app && cd dc-app
git clone git@github.com:alan-turing-institute/data-classification-app.git .
```
* Create a .env file, including `remote` in the list of `AUTH_TYPES`, and your custom domain in `ALLOWED_HOSTS` and `BASE_DOMAIN`. **Avoid quotes around variables**:

```
DJANGO_SETTINGS_MODULE=haven.settings.local

SECRET_KEY=notasecret # try https://djecrety.ir/ for example
APP_NAME=data-classification-app
WEBAPP_TITLE=Data Classification
BASE_DOMAIN=data-classification.example.com
ALLOWED_HOSTS=data-classification.example.com
DEBUG=false
AUTH_TYPES=remote,local

# Database parameters
DATABASE_URL=pgsql://haven:haven@db:5432/haven

# Email parameters
EMAIL_HOST=smtp.sendgrid.net
EMAIL_HOST_USER=sendgrid-username
EMAIL_HOST_PASSWORD=sendgrid-password
EMAIL_PORT=587
EMAIL_USE_TLS=True
FROM_MAIL=noreply@example.com
```
* Create a configuration file for Authelia from the template:
```
cd authelia
export BASE_DOMAIN=<custom domain>
. setup-config.sh
cd ..
```

## Certificates

* Create directories for certbot to store things:
  
  `mkdir -p data/certbot/{conf,www}`
* Change permissions on www:
  
  `chmod 777 data/certbot/www`

* Make init-letsencrypt.sh executable:
  
  `chmod 775 init-letsencrypt.sh`
* Build the containers:

  `sudo docker-compose -f docker-compose.prod.yml build`
* Run the script:
  
  `./init-letsencrypt.sh`
* If it works without any complaints, set staging to 0 and run the script again

  `LETSENCRYPT_STAGING=0 ./init-letencrypt.sh`

## Authelia ldap configuration
TBC

## Authelia OIDC setup
TBC
