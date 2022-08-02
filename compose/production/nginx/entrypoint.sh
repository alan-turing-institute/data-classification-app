#!/usr/bin/env sh
set -eu

envsubst '${BASE_DOMAIN}' < /etc/nginx/conf.d/dca.conf.template > /etc/nginx/conf.d/dca.conf
envsubst '${BASE_DOMAIN}' < /etc/nginx/includes/auth.conf.template > /etc/nginx/includes/auth.conf
envsubst '${BASE_DOMAIN}' < /etc/nginx/includes/ssl.conf.template > /etc/nginx/includes/ssl.conf

exec "$@"
