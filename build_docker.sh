#!/usr/bin/env bash

set -e

CONTAINER_REGISTRY_NAME=datasafehaventestreg
DOCKER_TAG_PREFIX="dsh-web"
DOCKER_TAG="${DOCKER_TAG_PREFIX}:v1"

az acr build --registry ${CONTAINER_REGISTRY_NAME} --image ${DOCKER_TAG} .
