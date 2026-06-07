#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Function to wait for a service to be ready
wait_for_service() {
    local host="$1"
    local port="$2"
    local service_name="$3"

    echo "Waiting for $service_name at $host:$port..."
    while ! nc -z "$host" "$port"; do
      sleep 1
    done
    echo "$service_name is up!"
}

# Wait for Postgres
if [ -n "$DB_HOST" ]; then
    wait_for_service "$DB_HOST" "$DB_PORT" "PostgreSQL"
fi

# Wait for Redis
if [ -n "$REDIS_HOST" ]; then
    wait_for_service "$REDIS_HOST" "$REDIS_PORT" "Redis"
fi

# Default command logic
case "$1" in
    "web")
        echo "Running Migrations..."
        python manage.py migrate --noinput
        echo "Collecting Static Files..."
        python manage.py collectstatic --noinput
        echo "Starting Gunicorn..."
        exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120
        ;;
    "worker")
        echo "Starting Celery Worker..."
        exec celery -A config worker --loglevel=info
        ;;
    "beat")
        echo "Starting Celery Beat..."
        exec celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
        ;;
    *)
        # If any other command is passed (e.g. 'python manage.py ...'), run it
        echo "Running custom command: $@"
        exec "$@"
        ;;
esac
