#!/bin/sh
set -e

chown -R celery:celery /var/lib/celery
if [ "$1" = '/opt/django-venv/bin/gunicorn' ]; then
    /opt/django-venv/bin/python /opt/app/lernanta/manage.py collectstatic --noinput
    cp -r /opt/django-venv/django/contrib/admin/media/ /opt/app/lernanta/static_serv/admin/
    dockerize -wait tcp://mysql:3306
    #/opt/django-venv/bin/python /opt/app/manage.py migrate --noinput
    exec "$@"
fi

exec "$@"