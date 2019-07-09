#! /usr/bin/env sh

# Collect static files
mkdir -p /app/staticfiles
python3 /app/manage.py collectstatic --noinput --clear

echo Running DSH migrations...
python3 /app/manage.py migrate

