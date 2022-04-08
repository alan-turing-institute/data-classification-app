# Development notes


Django requires some housekeeping tasks. The provisioning scripts will run these automatically on deployment,
but for local development you may need to run these manually.

## How to contribute?

Great news that you are up for contributing :tada: In order to contribute to this repo, we are following a [`git flow`](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow) to manage the team's contributions asyncronously.

### Issue creation
As soon as you have identified a contribution, please make a "task issue" using our pre-defined [template](https://github.com/alan-turing-institute/data-classification-app/blob/development/.github/ISSUE_TEMPLATE/task-issue-template.md).

### Branching
After filling in and submitting your issue, please create a branch for you to `commit` your changes to.

> :rotating_light: NOTE, please perform:
`git pull origin/development` beforehand to make sure you have all the "dev" progress on your local branch! :rotating_light:

### Naming your Branch
We have adopted a naming strategy to make it easier to connect your developer contributions to a known issue for the team. The naming convention is as follows:

```
{issue_number}/{short-description-of-changes}
```
This allows us to match each branch with changes to an issue.

### Making a Pull Request
Within the repository there is a [`pull_request_template`](https://github.com/alan-turing-institute/data-classification-app/blob/development/.github/pull_request_template.md) which is required to be filled out in order for a member of the development team to review your PR.

> :rotating_light: The NOTE: there is a **"Fixes"** within the template which allows a developer to enter an `#{issue_number}` which will further indicate to the dev team what issue your changes will address!  :rotating_light:



## Update static files - if you have modified CSS etc.

```bash
mkdir -p staticfiles
python manage.py collectstatic
```

For staging/production deployments, the provisioning scripts will run this during deployment.


## Updating requirements
Python dependencies are managed via [`poetry`](https://python-poetry.org/docs/basic-usage/) and our version of python is managed by [`pyenv`](https://github.com/pyenv/pyenv). See how to configure both using this [demo](https://blog.jayway.com/2019/12/28/pyenv-poetry-saviours-in-the-python-chaos/py)

To add a new python package to the requirements:

* in the root project directory run `poetry add <package-name>`
* Run `poetry update` to rebuild the `poetry.lock` file


## Updating the compiled JS files

If you modify the JS/CSS you may need to update the compiled files using `gulp`.
You will need to install `gulp` and `gulp-cli` which require `node`. It is strongly recommended that you do not install node directly but use a node versioning tool such as `nvm`. The `gulpfile` is at `static/gulpfile.js`.



### Apply migrations

If a code update has modified the database models, you will need to run the migration on your local database.

```bash
python manage.py migrate
```
### Renaming migrations
We are implementing a dev workflow to rename migrations to more intuitive names, describing the update to the model structure a migration executes.
Please follow these steps to ensure safe renaming:
1. After running `python manage.py migrate` you will see an automated migration file in the app's `/migrations/`directory. Rename the file.
2. Repoint any dependencies to the new file with the new filename.
3. If the renamed migration was already applied, apply it again using --fake

**HINT:** If it's a brand new migration, 2 and 3 won't apply, and it's perfectly fine to rename them.

If you modify the database model in your code, you will need to generate the required Django migration files and commit them into the repository.
For staging/production deployments, the provisioning scripts will run migrations automatically during deployment.


## Troubleshooting

If errors are encountered in the browser after deploy, the following settings can be added to web.config to display useful errors in the browser:
```
<configuration>
    <system.webServer>
        <httpErrors errorMode="Detailed" />
    </system.webServer>
    <system.web>
        <customErrors mode="Off"/>
        <compilation debug="true"/>
    </system.web>
</configuration>
```
