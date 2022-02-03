#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "PostgreSQL started"
fi

# Install dependencies
poetry install --no-interaction --no-ansi

# Run migrations 
python manage.py migrate
# collectstatic 
python manage.py collectstatic --no-input --clear

exec "$@"