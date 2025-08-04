source /opt/PycharmProjects/PythonProjects/django_projects/env/bin/activate
export $(cat .env | xargs)
python manage.py makemigrations
python manage.py migrate