#!/bin/sh
set -e

chown -R celery:celery /var/lib/celery
if [ "$1" = '/opt/django-venv/bin/gunicorn' ]; then
    dockerize -wait tcp://mysql:3306
    #/opt/django-venv/bin/python /opt/app/manage.py migrate --noinput
    #/opt/django-venv/bin/python /opt/app/manage.py collectstatic --noinput
    exec "$@"
fi

exec "$@"
