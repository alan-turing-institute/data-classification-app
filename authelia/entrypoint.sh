#!/usr/bin/env sh
set -eu

envsubst '${BASE_DOMAIN}' < /config/configuration.template.yml > /config/configuration.yml

exec "$@"