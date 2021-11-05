# Development notes


Django requires some housekeeping tasks. The provisioning scripts will run these automatically on deployment,
but for local development you may need to run these manually.


## Update static files - if you have modified CSS etc.

```bash
mkdir -p staticfiles
manage.py collectstatic
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
