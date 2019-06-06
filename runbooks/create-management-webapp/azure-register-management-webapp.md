# Creating an Azure AD registration for the Data Safe Haven web management application

These instructions are for System Managers to create an Azure AD registration for the management application.

This registration step only needs to be performed once; the webapp can be updated using the same app registration.

The actual deployment is described in a separate runbook. System Manager can delegate the actual deployment by storing the required
deployment keys in a secure keyvault.


## Prerequisites

You will need

 * The desired name of the management webapp (`YOUR-WEBAPP-NAME`), which must be globally unique in Azure and will define the website address (e.g. `YOUR-WEBAPP-NAME.azurewebsites.net`).
 * Read/write access to the Azure subscription that will allow you to register the webapp (e.g. Data Safen Have Management subscription)
 * Write access to a keyvault which can be accessed by the users who will deploy the webapp.


### Register an app using the Azure Active Directory

 * Log into the Azure Portal and switch to the directory for registering the application (click on your user icon and Switch Directory)
 * Choose Azure Active Directory/App Registrations
 * Click View All Applications and check that a registration does not already exist for your webapp
 * Click New Application Registration
 * Choose a suitable application name (eg. DSH web management development)
 * Under Redirect URI add the authentication endpoint (you must include the trailing slash) eg. https://YOUR-WEBAPP-NAME.azurewebsites.net/auth/complete/azuread-tenant-oauth2/
 * Click Register
 * Under Required Permissions add the following permissions for Microsoft Graph:
   * Read directory data
   * Sign in and read user profile
   * Access directory as the signed in user
   * View users' email address
   * View users' basic profile
 * Under Certificates and secrets add a new client secret called "App key". Copy the value into the keyvault now, as you won't be able to read it later..
 * Under Overview copy the Application ID into the keyvault.
 * Under Branding set the home page URL eg,. https://YOUR-WEBAPP-NAME.azurewebsites.net/
 * Under Azure Active Directory/Properties, copy the Directory ID (also known as Tenant ID) into the keyvault.

### Your keyvault should have the following values:
 * Application ID: the applicatin ID for the registration created above.
 * App key: the "App key" secret created above.
 * Directory ID: the AD Directory ID (also known as Tenant ID), which can be found under Azure Active Directory/Properties.

Ensure the keyvault is accessible to the user who will deploy the app
