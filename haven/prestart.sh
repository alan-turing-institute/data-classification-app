#! /usr/bin/env sh

# Debugging: start SSH server
#mkdir -p /var/run/sshd
#/usr/sbin/sshd

# Collect static files
mkdir -p /app/staticfiles
python3 /app/manage.py collectstatic --noinput --clear

echo Running DSH migrations...
python3 /app/manage.py migrate

