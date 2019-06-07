# Creating an Azure AD registration for the Data Safe Haven web management application

These instructions are for a System Manager to create an App Registration which allows the Data Safe Haven management web application to be deployed and run using Azure.

This process will generate keys which should be stored in an Azure key vault. These keys will be required during deployment. The deployment process itself is covered in a separate runbook and can be performed by a different user, provided they have access to the key vault and appropriate Azure permissions.

This registration process only needs to be performed once per management application. Updating or redeployment of an existing application does not require a new registration.

## Prerequisites

You will need

 * The new domain name of the management webapp (eg `YourSafeHaven`). This must be globally unique in Azure and will define the website address (eg `YourSafeHaven.azurewebsites.net`).
 * The user-facing display name of the management webapp (eg `Your Safe Haven management application`).
 * Permissions to create an App Registration on the appropriate Azure Active Directory.
 * An Azure Key vault or equivalent secure location to store the keys so they can be accessed by the user performing the deployment.

## Steps to register the Data Safe Haven management webapp

### Go to Azure
 * Log into the Azure Portal
 * Switch to the appropriate organisational directory where the app registration should be created (to change directory in Azure, click on your user icon at the top right and select "Switch Directory")
### Create the App registration
 * Open "Azure Active Directory" from the Azure menu on the left
 * Open "App Registrations"
 * Click "All Applications" and verify that a registration does not already exist for your webapp
 * Click "New registration"
 * Under "Name", enter the user-facing display name
 * Under "Redirect URI" add the authentication endpoint as follows (replace YourSafeHaven with the domain name defined above, and ensure you include the trailing slash) `https://YourSafeHaven.azurewebsites.net/auth/complete/azuread-tenant-oauth2/`
 * Click "Register"
 * Select "Branding"
 * Set the home page URL with the following, replacing YourSafeHaven with your domain defined above, e.g.`https://YourSafeHaven.azurewebsites.net`
 * Click "Save".
### Add permissions
 * Open "API permissions"
 * Click "Add a permission"
 * Select "Microsoft Graph" from the Commonly used Microsoft APIs
 * Select "Delegated permissions"
 * For each of the following, search for the permission name and tick the checkbox to the left of the permission:
   * `profile` (View users' basic profile)
   * `email` (View users' email address)
   * `Directory.Read.All` (Read directory data)
   * `User.Read` (Sign in and read user profile)
   * `Directory.AccessAsUser.All` (Access directory as the signed in user)
 * Click "Add permissions". The above permissions should now appear in the list.
 * Click "Grant admin consent for (your organisational directory name)"
 * Click "Yes" to confirm. 
### Create a key
 * Open "Certificates and secrets"
 * Click "New client secret"
 * Enter "Description" as `App key`
 * Select "Expires: never" 
 * Click "Add"
 * Copy the key value by clicking the copy icon nex to the value (you MUST do this now as you will not be able to read it later).
 * Paste the key value as a new secret in your Azure key vault, giving it the name (replacing YourSafeHaven with your domain name defined above) `YourSafeHaven-app-key`
## Copy application and tenant IDs
 * In "App registrations", open your new registration and select "Overview"
 * Copy the "Application (client) ID" and add as a new secret in your Azure key vault, giving it the name (replacing YourSafeHaven with your domain name defined above) `YourSafeHaven-application-id`
 * Copy the "Directory (tenant) ID" and add as a new secret in your Azure key vault, giving it the name (replacing YourSafeHaven with your domain name defined above) `YourSafeHaven-tenant-id`

## Deploy the Safe Haven management webapp
There is a separate runbook for this. Ensure the Key vault used above is accessible to the user who will deploy the app.
