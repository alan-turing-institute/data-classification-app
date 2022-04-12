# Preparing for app UX testing sessions

To-do list, ahead of first testing session: 

1. Log into app as System Manager and add example user data from `docs/create-users/example_user_form.csv` (if not already created)
1. Load test project data from command line: `docker exec -it django python manage.py loaddata ./docs/user-testing/test-data.json`
1. Select an account that tester will be logged in as, and manually assign account as `Investigator` to each of the three test projects

To reset ahead of subsequent sessions: 

1. Log in and manually delete tester's dataset
1. Run command in step two above