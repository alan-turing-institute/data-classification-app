#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "PostgreSQL started"
fi

# Run migrations 
python /app/manage.py flush --no-input 
python /app/manage.py migrate easyaudit
python /app/manage.py migrate
# collectstatic 
python manage.py collectstatic --no-input --clear

exec "$@"