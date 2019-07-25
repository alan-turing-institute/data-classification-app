#! /usr/bin/env sh

echo STARTUP SCRIPT

# Debugging: start SSH server
#mkdir -p /var/run/sshd
#/usr/sbin/sshd

# Collect static files
mkdir -p /home/site/repository/staticfiles

cd /home/site/repository
pip3 install -r requirements.txt
python3 haven/manage.py collectstatic --noinput --clear

echo Running DSH migrations...
python3 haven/manage.py migrate

gunicorn --bind=0.0.0.0 --timeout 600 --chdir haven config.wsgi

