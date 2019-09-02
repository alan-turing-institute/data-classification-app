# Creating users on the Data Safe Haven web management application

 * If required, create a System Manager user and assign to the SG SHM System Managers group  
 * Enter the user details of other users in a csv file (see `example_user_form.csv` for the format)
 * Log into the management webapp as the a System Manager user
 * Under `Users` click `Import user list` and select the file you created above.
 * When the users have been imported into the system, click `Export UserCreate.csv`
 * Use the downloaded `UserCreate.csv` file to create the other users on Azure following the appropriate runbook.
