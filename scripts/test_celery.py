import os
import sys
import django
from celery.result import AsyncResult

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from bookings.tasks import send_booking_created_email
from flights.tasks import warm_flight_list_cache
from bookings.models import Booking

def test_celery():
    print("--- Starting Celery Smoke Test ---")
    
    # 1. Test Simple Task
    print("Testing flights.tasks.warm_flight_list_cache...")
    res1 = warm_flight_list_cache.delay()
    print(f"Task ID: {res1.id}")
    
    # 2. Test Task with Arguments
    booking = Booking.objects.first()
    if booking:
        print(f"Testing bookings.tasks.send_booking_created_email for Booking ID: {booking.id}...")
        res2 = send_booking_created_email.delay(booking.id)
        print(f"Task ID: {res2.id}")
    else:
        print("No bookings found in DB, skipping booking task test.")

    print("\nCheck your Celery worker logs for execution confirmation.")
    print("Check Django Admin Task Results for status.")
    print("--- Smoke Test Completed ---")

if __name__ == "__main__":
    test_celery()
