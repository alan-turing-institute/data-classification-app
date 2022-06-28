# Classification webapp for the Turing Data Safe Haven

This is a web application that can be used for data classification. It is designed for use with
the [Turing Safe Haven](https://github.com/alan-turing-institute/data-safe-haven).


## Requirements

The web application is not designed for any specific cloud platform, but currently has only been tested on Azure.
 The web framework is built on Django with Python3. It uses an external database (tested on PostgreSQL),
 OAuth2 for authentication (tested on OAuth2 for Azure Active Directory) and Graph API for group membership.

The webapp has been tested, and instructions are provided for, the following deployment scenarios:
- local development, using a locally-hosted SQL database (eg PostgreSQL)
- web deployment, using an Azure subscription



## Learn more about the Turing Safe Haven

* [Main project README](https://github.com/alan-turing-institute/data-safe-haven/blob/master/README.md)
* [Contributing guidelines](https://github.com/alan-turing-institute/data-safe-haven/blob/master/CONTRIBUTING.md)
* [Code of Conduct](https://github.com/alan-turing-institute/data-safe-haven/blob/master/CODE_OF_CONDUCT.md)

## Deploying test instances for development

* [Setting up local development](docs/development/set-up-local-development.md)
* [Creating a staging server on Azure](docs/development/create-staging-server-on-azure.md)
* [Local development notes](docs/development/local-development-notes.md)


## Deploying a production instance on Azure

* [Web deployment on Azure](docs/create-management-webapp/azure-deploy-management-webapp.md)

## Sample user guide

* [Instructions for data provider representatives](docs/user_guide/user_guide.md)
