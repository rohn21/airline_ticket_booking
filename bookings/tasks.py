# bookings/tasks.py
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_booking_created_email(self, booking_id):
    logger.info("send_booking_created_email booking_id=%s", booking_id)
    return {"booking_id": booking_id, "status": "created_email_queued"}


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_booking_confirmed_email(self, booking_id):
    logger.info("send_booking_confirmed_email booking_id=%s", booking_id)
    return {"booking_id": booking_id, "status": "confirmed_email_queued"}


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def generate_ticket_artifact(self, booking_id):
    logger.info("generate_ticket_artifact booking_id=%s", booking_id)
    return {"booking_id": booking_id, "status": "ticket_generation_done"}


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def create_booking_audit_log(self, booking_id, event_name, meta=None):
    logger.info(
        "create_booking_audit_log booking_id=%s event_name=%s meta=%s",
        booking_id,
        event_name,
        meta or {},
    )
    return {"booking_id": booking_id, "event_name": event_name}