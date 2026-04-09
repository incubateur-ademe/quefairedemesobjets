#!/bin/env bash

python manage.py createcachetable
python manage.py migrate --check
python manage.py migrate

# TEMPORARY, required to have search function after deploy
python manage.py enable_unaccent
python manage.py enable_trigram

python manage.py clearsessions
python manage.py clear_cache --all
python manage.py create_remote_db_server

gunicorn core.wsgi --bind 0.0.0.0:8000 --timeout 120 --workers 3