# Development notes


Django requires some housekeeping tasks. The provisioning scripts will run these automatically on deployment,
but for local development you may need to run these manually.


## Update static files - if you have modified CSS etc.

```bash
mkdir -p haven/staticfiles
haven/manage.py collectstatic
```

For staging/production deployments, the provisioning scripts will run this during deployment.


## Updating requirements

Python dependencies are managed via [`pip-tools`](https://pypi.org/project/pip-tools/).

To add a new python package to the requirements:

* Add the package name and version to the relevant `.in` file in `requirements/` (usually `requirements/base.in`)
* Run `make -C requirements/` to rebuild the requirements txt files


## Updating the compiled JS files

If you modify the JS/CSS you may need to update the compiled files using `gulp`.
You will need to install `gulp` and `gulp-cli` which require `node`. It is strongly recommended that you do not install node directly but use a node versioning tool such as `nvm`. The `gulpfile` is at `haven/static/gulpfile.js`.



### Apply migrations

If a code update has modified the database models, you will need to run the migration on your local database.

```bash
haven/manage.py migrate
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
