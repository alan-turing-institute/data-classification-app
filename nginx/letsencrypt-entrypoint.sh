#!/usr/bin/env sh
set -eu

envsubst '${BASE_DOMAIN}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

exec "$@"