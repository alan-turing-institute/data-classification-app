#!/usr/bin/env bash

#
# Script for pushing code to a deployment for the Data Safe Haven management application on Azure.
#
# Requires:
#  1. The Azure CLI to be installed:
#      https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest
#
#  2. An environment file (.env) to be configured for your deployment.
#      See .env.example for more information
#
#  3. git installed and configured to push the code
#
#  4. The provisioning script provision.sh to have been run successfully
#
#
# To run this script:
#   deploy_code.sh -e ENV_FILENAME
#
#     where ENV_FILENAME is the path and name of your .env file.
#



set -e

# Document usage for this script
usage() {
    echo "usage: $0 [-h] [-e envfile]"
    echo "  -h            display help"
    echo "  -e path to file containing environment variables"
    exit 1
}

CURRENT_DIR=$(dirname "$0")
ENVFILE="${CURRENT_DIR}/.env"

# Read command line arguments, overriding defaults where necessary
while getopts "h:e:" opt; do
    case $opt in
        h)
            usage
            ;;
        e)
            ENVFILE=$OPTARG
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            ;;
    esac
done


if [ -e $ENVFILE ]
then
    source $ENVFILE
else
    echo "Envfile does not exist: $ENVFILE"
    exit 1
fi



# Fetch a secret from the Azure keyvault
function get_azure_secret() {
    local SECRET_NAME="$1"
    az keyvault secret show --name "${SECRET_NAME}" --vault-name "${KEYVAULT_NAME}" --query "value" -otsv
}

azure_login() {
    az login
    az account set --subscription "${SUBSCRIPTION}"
}

# Set or update the codebase for a deployed webapp
deploy_code () {
    # Set or update the remote
    local deployment_url=$(get_azure_secret "DEPLOYMENT-URL")
    local remote_name="azure_deployment"
    if git remote get-url ${remote_name} > /dev/null 2> /dev/null
    then
        echo "Updating remote definition ${remote_name}: ${deployment_url}"
        git remote set-url "${remote_name}" "${deployment_url}"
    else
        echo "Adding remote definition ${remote_name}: ${deployment_url}"
        git remote add "${remote_name}" "${deployment_url}"
    fi

    # Push current branch to master on the remote container
    echo "Pushing head branch to remote"
    git push "${remote_name}" HEAD:master
}

azure_login
deploy_code
