#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "PostgreSQL started"
fi

# Install any new dependencies
poetry install --no-interaction --no-ansi

# Run migrations
python manage.py migrate easyaudit  # Needs to run first as other migrations will trigger this
python manage.py migrate

# Create superuser (developer:developer)
python manage.py loaddata devsuperuser.json

exec "$@"
