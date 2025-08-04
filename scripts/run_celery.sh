source /opt/PycharmProjects/PythonProjects/django_projects/env/bin/activate
export $(cat .env | xargs)
celery -A celery worker --loglevel=info