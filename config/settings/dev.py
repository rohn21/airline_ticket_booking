from .base import *
from decouple import config

DEBUG = True

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

CORS_ALLOW_ALL_ORIGINS = True

# Redis - Development (single instance)
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')

# Celery - Development optimized
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = "django-db"
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Kolkata'

# Development worker settings (lighter than production)
CELERY_WORKER_CONCURRENCY = 2  # Lower for dev
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # Prevents overload
CELERY_TASK_ACKS_LATE = True  # Safe for dev
CELERY_TASK_TRACK_STARTED = True  # Good for debugging

# Redis transport (dev-friendly)
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'visibility_timeout': 3600,  # 1 hour
    'retry_on_timeout': True,
}

# Simple task routing for dev
CELERY_TASK_ROUTES = {
    'bookings.tasks.expire_unpaid_bookings': {'queue': 'default'},
}

# Beat scheduler for periodic tasks
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_BEAT_MAX_LOOP_INTERVAL = 30  # Check every 30s

# Django Redis Cache - Dev optimized
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": config('REDIS_CACHE_URL', default='redis://localhost:6379/2'),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {"max_connections": 10},
            "IGNORE_EXCEPTIONS": True,  # Dev convenience
        },
        "KEY_PREFIX": "dev_cache",
        "TIMEOUT": 300,
    }
}

# Logging for debugging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'suppress_metrics': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': lambda record: '/metrics' not in record.getMessage(),
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'filters': ['suppress_metrics'],
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.server': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'bookings.tasks': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'flights.tasks': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
