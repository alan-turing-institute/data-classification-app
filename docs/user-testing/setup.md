# Preparing for app UX testing sessions
    
This short guide will walk you through how to set up your staging environment of the Turing IG App for user testing sessions.

The first part of the guide shows how to set up the app for the first user session.

The second part of the guide shows how to reset the app to be ready for each subsequent user session.
    
## Initial set up
    
Follow these steps once you have successfully deployed your app, to prepare the app for the first user testing session:

### Getting started

1. Clone the latest version of the ```development``` branch to your local machine 

2. Login to your deployed app with ```authelia``` login credentials

### Adding Test Users

1. Click `Users` in the top navigation bar

2. There should be 2 manager users listed. We're now going to import additional test user profiles. If you already have some (around 10) test user profiles in place, you can skip to 'Adding Projects'

3. Click `Import user list`

4. Select the file `docs/create-users/example_user_form.csv` from your local copy of the development branch

Your users should now be added

### Adding Test Projects

1. From the top navigation bar, click `Projects`. If you already have three test projects loaded, you can skip to step 4

2. Login to your staged enviroment via SSH
    * [This guide](access-staging-server.md) explains how to gain access to the server via SSH
 
3. Load the test project data by running:
     ```
     sudo docker exec -it <YOUR_APP_CONTAINER_NAME> python manage.py loaddata test-data.json
     ```
     > :bulb: **NOTE**:
     You can find the name of your app container by running ```docker ps```. The name of the app is under 'NAMES' (and is NOT ```nginx```, ```db```, ```authelia``` or ```certbot```)
   

4. In the app UI, make sure you're still logged in as ```authelia```

5. For each project, assign ```authelia``` as 'Investigator':
    - Click the project title
    - Click `Add Participant`
    - Select:
        - **Username**: authelia
        - **Role**: Investigator
        - **Work packages**: Check 'Ingress'
    - Click `Add Participant`
    - Return to 'Projects' page, and repeat for all projects

Your app is now ready for user testing

## Resetting after each session

The easiest way to reset your app after each user testing session is through the UI itself.

For the project the user tested:

1. Select the Work Package that has 'Classification Underway'

2. Click `Clear Classifications` -> `Clear Classifications`

3. Return to the project main screen

4. Select the dataset the user created

5. Click `Delete Dataset` -> `Delete Dataset`

6. Click `Edit Participants`

7. Click the trash icon to delete the users the tester assigned. This should be:
    * Project Manager
    * Referee
    * Data Provider Representative
    > **DO NOT** delete ```authelia```
8. Click `Save Participants`

Your app is now ready for the next user testing session! :rocket:
