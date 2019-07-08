#!/usr/bin/env bash

set -e

docker build -f "./Dockerfile" -t dsh-web "."

docker push datasafehaventestreg.azurecr.io/dsh-web:v1
