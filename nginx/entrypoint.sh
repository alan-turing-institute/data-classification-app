#!/usr/bin/env sh
set -eu

envsubst '${BASE_DOMAIN}' < /etc/nginx/conf.d/dca.conf.template > /etc/nginx/conf.d/dca.conf

exec "$@"