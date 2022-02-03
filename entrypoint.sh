#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "PostgreSQL started"
fi

# Install any new dependencies
poetry install --no-interaction --no-ansi

# Run migrations 
python manage.py migrate

# Create superuser (developer:developer)
python manage.py loaddata devsuperuser.json

# collectstatic 
python manage.py collectstatic --no-input --clear

exec "$@"