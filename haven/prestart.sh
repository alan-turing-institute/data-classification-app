#! /usr/bin/env sh

echo Running DSH migrations...
python3 /app/manage.py migrate
