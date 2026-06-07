from .base import *
from decouple import config

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST"),
        "PORT": config("DB_PORT"),
    }
}

# Security hardening
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Redis URLs (use environment variables in production)
REDIS_BROKER_URL = config('REDIS_BROKER_URL', default='redis://localhost:6379/0')
REDIS_RESULT_URL = config('REDIS_RESULT_URL', default='redis://localhost:6379/1')
REDIS_CACHE_URL = config('REDIS_CACHE_URL', default='redis://localhost:6379/2')

# Celery - Production optimized
CELERY_BROKER_URL = REDIS_BROKER_URL
CELERY_RESULT_BACKEND = REDIS_RESULT_URL
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Kolkata'

# Worker optimization - Production critical
CELERY_WORKER_CONCURRENCY = int(config('CELERY_WORKER_CONCURRENCY', default='4'))
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # Critical: prevents memory overload
CELERY_TASK_ACKS_LATE = True  # Ensures tasks aren't lost on worker crash
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_WORKER_MAX_MEMORY_PER_CHILD = 50000  # 50MB per worker

# Redis broker transport - Production essential
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'visibility_timeout': 3600,  # 1 hour - match your longest task
    'master_name': 'mymaster',  # For Redis Sentinel (future)
    'fanout_patterns': True,
    'fanout_prefix': True,
}

# Task routing - Scale by task type
CELERY_TASK_ROUTES = {
    'bookings.tasks.expire_unpaid_bookings': {'queue': 'critical'},
    'notifications.tasks.*': {'queue': 'low'},
    'payments.tasks.*': {'queue': 'high'},
}

# Beat scheduler (periodic tasks)
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_BEAT_MAX_LOOP_INTERVAL = 5  # Check every 5s for precision

# Security & Reliability
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_SEND_SENT_EVENT = True
CELERY_WORKER_SEND_TASK_EVENTS = True
CELERY_WORKER_TASK_ERROR_WHITELIST = []

# Django Redis Cache - Optimized
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_CACHE_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {
                "max_connections": 20,
                "retry_on_timeout": True,
            },
            "PARSER_CLASS": "redis.connection.HiredisParser",
            "IGNORE_EXCEPTIONS": True,
        },
        "KEY_PREFIX": "django_cache",
        "TIMEOUT": 300,
        "DEFAULT_TIMEOUT": 300,
    }
}

# Add to INSTALLED_APPS
# INSTALLED_APPS += [
#     'django_celery_results',
# ]