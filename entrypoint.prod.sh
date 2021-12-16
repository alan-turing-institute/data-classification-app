#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
   
    echo "PostgreSQL started"
fi

exec "$@"