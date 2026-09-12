# bookings/tasks.py
from celery import shared_task
from celery.utils.log import get_task_logger
from bookings.models import Booking

logger = get_task_logger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_booking_created_email(self, booking_id):
    logger.info("send_booking_created_email booking_id=%s", booking_id)
    try:
        booking = Booking.objects.select_related("user", "flight", "flight__route__origin", "flight__route__destination").get(id=booking_id)
        from notifications.services.notification_service import NotificationService

        context = {
            "pnr": booking.pnr,
            "flight_number": booking.flight.flight_number,
            "origin": booking.flight.route.origin.code,
            "destination": booking.flight.route.destination.code,
            "departure_time": booking.flight.departure_time.strftime("%Y-%m-%d %H:%M"),
            "total_amount": str(booking.total_amount),
            "currency": booking.currency,
        }

        NotificationService.send(
            user=booking.user,
            recipient_email=booking.contact_email,
            event_code="BOOKING_CREATED",
            context=context,
            reference_type="booking",
            reference_id=booking.id,
            custom_subject=f"Booking Confirmation - PNR {booking.pnr}",
            custom_body=f"Your booking {booking.pnr} for flight {booking.flight.flight_number} from {booking.flight.route.origin.code} to {booking.flight.route.destination.code} is created. Status: {booking.booking_status}.",
        )
        return {"booking_id": booking_id, "status": "created_email_queued"}
    except Booking.DoesNotExist:
        logger.error("Booking %s not found for created email", booking_id)
        return {"error": "not_found", "booking_id": booking_id}


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_booking_confirmed_email(self, booking_id):
    logger.info("send_booking_confirmed_email booking_id=%s", booking_id)
    try:
        booking = Booking.objects.select_related("user", "flight", "flight__route__origin", "flight__route__destination").get(id=booking_id)
        from notifications.services.notification_service import NotificationService

        context = {
            "pnr": booking.pnr,
            "flight_number": booking.flight.flight_number,
            "origin": booking.flight.route.origin.code,
            "destination": booking.flight.route.destination.code,
            "departure_time": booking.flight.departure_time.strftime("%Y-%m-%d %H:%M"),
            "total_amount": str(booking.total_amount),
            "currency": booking.currency,
        }

        NotificationService.send(
            user=booking.user,
            recipient_email=booking.contact_email,
            event_code="BOOKING_CONFIRMED",
            context=context,
            reference_type="booking",
            reference_id=booking.id,
            custom_subject=f"Booking Confirmed - PNR {booking.pnr}",
            custom_body=f"Great news! Your booking {booking.pnr} for flight {booking.flight.flight_number} is confirmed.",
        )
        return {"booking_id": booking_id, "status": "confirmed_email_queued"}
    except Booking.DoesNotExist:
        logger.error("Booking %s not found for confirmed email", booking_id)
        return {"error": "not_found", "booking_id": booking_id}


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def generate_ticket_artifact(self, booking_id):
    logger.info("generate_ticket_artifact booking_id=%s", booking_id)
    from tickets.services.ticket_service import TicketService
    ticket_url = TicketService.generate_and_save(booking_id)
    return {"booking_id": booking_id, "ticket_url": ticket_url, "status": "ticket_generation_done"}



@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def create_booking_audit_log(self, booking_id, action, note="", metadata=None, actor_id=None):
    logger.info(
        "create_booking_audit_log booking_id=%s action=%s meta=%s",
        booking_id,
        action,
        metadata or {},
    )
    from bookings.models import BookingAudit
    BookingAudit.objects.create(
        booking_id=booking_id,
        action=action,
        note=note,
        metadata=metadata or {},
        actor_id=actor_id,
    )
    return {"booking_id": booking_id, "action": action}