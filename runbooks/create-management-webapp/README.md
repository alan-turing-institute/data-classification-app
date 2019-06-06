# Creating an Azure AD registration for the Data Safe Haven web management application

To create and deploy a production instance:

 * The System Manager should create an app registration and store deployment keys in a secure keyvault on Azure - see [runbook](azure-register-management-webapp)
 * The deployment can then be performed by the System Manager or a delegated developer with access to the keyvault -  - see [runbook](azure-deploy-management-webapp)
