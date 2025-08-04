# config/celery.py
import os
from celery import Celery
from decouple import config

os.environ.setdefault("DJANGO_SETTINGS_MODULE", config("DJANGO_SETTINGS_MODULE"))

app = Celery('air_booking_system')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
