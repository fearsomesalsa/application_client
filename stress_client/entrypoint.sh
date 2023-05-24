#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Postgres еще не запущен..."

    # Проверяем доступность хоста и порта
    while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
      sleep 0.1
    done

fi

#make migration
echo "Apply database migration"
python manage.py migrate --noinput
#collectstatic
echo "Collect static files"
python manage.py collectstatic --no-input --clear 
echo "Postgres запущен"

exec "$@"
