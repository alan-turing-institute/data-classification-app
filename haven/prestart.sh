#! /usr/bin/env sh

# Collect static files
RUN mkdir -p /app/staticfiles
RUN python3 /app/manage.py collectstatic --noinput --clear

echo Running DSH migrations...
python3 /app/manage.py migrate

