>**NB:** if you do not have write access to the staging server, follow these [instructions](access-staging-server). 


# Preparing for app UX testing sessions

To-do list, ahead of first testing session: 

1. Log into app as System Manager and add example user data from `docs/create-users/example_user_form.csv` (if not already created)
1. Load test project data from command line: `docker exec -it django python manage.py loaddata ./docs/user-testing/test-data.json`
1. Log into the admin UI with the default account (e.g. `authelia`) - this will also be the account that the tester uses - and assign this account to be an `Investigator` on each of the three test projects

To reset ahead of subsequent sessions: 

1. Log in and manually delete tester's dataset
1. Run command in step two above
