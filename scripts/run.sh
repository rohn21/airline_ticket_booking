#!/bin/bash
ENV=${1:-dev}
source /opt/PycharmProjects/PythonProjects/django_projects/env/bin/activate

if [ "$ENV" == "prod" ]; then
    export DJANGO_SETTINGS_MODULE=config.settings.prod
else
    export DJANGO_SETTINGS_MODULE=config.settings.dev
fi

python manage.py runserver
