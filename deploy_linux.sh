#! /usr/bin/env sh

# Data Safe Haven web management application - deployment script for Azure App Service for Linux
#
# This script will be executed on the Azure container whenever the web app is deployed or redeployed.
# This includes redeployments (whether automated or manually triggered) that follow changes to code or settings. or a force redeploy from the Azure portal.
# This script must therefore be safe and robust to execute on an active production environment.

# The Azure App Service for Linux container will first update the codebase, install dependencies from requirements.txt and then execute this script.
# The path to this script is specified in the Startup Command specified in configuration settings for App Service for Linux.

# This script must have a .sh extension for the Azure container to recognise as a shell script.

echo Running SH deployment script

cd /home/site/repository

echo Collecting static files...
mkdir -p /home/site/repository/staticfiles
python3 haven/manage.py collectstatic --noinput --clear

echo Running DSH migrations...
python3 haven/manage.py migrate

echo Running web server...
gunicorn --bind=0.0.0.0 --timeout 600 --chdir haven config.wsgi --error-logfile '-' --log-level 'debug'
