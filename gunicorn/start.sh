#!/bin/bash

source /opt/PycharmProjects/PythonProjects/django_projects/env/bin/activate
export $(cat .env | xargs)

exec gunicorn config.wsgi:application \
  --bind 127.0.0.1:8000 \
  --workers 3 \
  --timeout 120 \
  --log-level info \
  --access-logfile - \
  --error-logfile -
