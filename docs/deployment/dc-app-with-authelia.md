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
* Create a .env file, including `remote` in the list of `AUTH_TYPES`, and your custom domain in `ALLOWED_HOSTS`. **Avoid quotes around variables**:

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

Edit the following files to replace `data-classification.example.com` with your custom domain:
* `nginx/conf.d/nginx.conf`: where you see `auth.data-classification.example.com`, keep the auth bit.

```
server {
    server_name auth.<your-domain-here>;
    ...
}
```
* `nginx/auth.conf`:  

```html
error_page 401 =302 https://auth.<your-domain-here>/?rd=$target_url;
```
* `authelia/configuration.yml`:

```yaml
default_redirection_url: https://<your-domain-here>
...
totp:
  # should this be the domain?
  issuer: <your-domain-here>
...
access_control:
  rules:
    # Rules applied to everyone
    #- domain: dca.uksouth.cloudapp.azure.com
     # policy: bypass
    - domain: <your-domain-here>

  session:
    domain: <your-domain-here>
```

## Certificates

* Edit `nginx/conf.d/nginx.conf` and comment out the two https server blocks (otherwise `nginx` will complain we don't have ssl certificates)
* Create directories for certbot to store things:

  `mkdir -p data/certbot/{conf,www}`
* Change permissions on www:

  `chmod 777 data/certbot/www`
* Edit init-letsencrypt.sh and change the domains array var on line 8 to:

  ```html
  domains=(<your-domain-here> auth.<your-domain-here>)
```
* Make sure `staging=1` on line 16, then save your changes
* Make init-letsencrypt.sh executable:

  `chmod 775 init-letsencrypt.sh`
* Run the script:

  `sudo ./init-letsencrypt.sh`
* If it works without any complaints, set staging to 0 and run the script again
* Now you can edit nginx/conf.d/nginx.conf and uncomment the https server blocks
* Edit nginx/ssl.conf to match your custom domain so it points to the correct certificate locations:
```
ssl_certificate /etc/letsencrypt/live/auth.data-classification.example.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/auth.data-classification.example.com/privkey.pem;
```
* Rebuild the containers and bring them up again:
  `sudo docker-compose -f docker-compose.prod.yml up -d --build`

## Authelia ldap configuration
TBC

## Authelia OIDC setup
TBC
