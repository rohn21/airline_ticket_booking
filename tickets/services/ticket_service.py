import os
import logging
from django.conf import settings
from bookings.models import Booking
from tickets.services.pdf_service import PDFService

logger = logging.getLogger(__name__)


class TicketService:
    @staticmethod
    def generate_and_save(booking_id: str) -> str:
        """
        Builds ticket PDF for the booking, saves it to media/tickets/{pnr}.pdf,
        updates Booking.ticket_url, and returns the relative media URL.
        """
        try:
            booking = Booking.objects.select_related(
                "flight",
                "flight__airline",
                "flight__route__origin",
                "flight__route__destination",
                "fare_rule__fare_class",
            ).prefetch_related("passengers").get(id=booking_id)
        except Booking.DoesNotExist:
            logger.error("Booking %s not found for ticket generation.", booking_id)
            raise ValueError(f"Booking {booking_id} not found")

        passengers_data = []
        for p in booking.passengers.all():
            passengers_data.append({
                "name": f"{p.first_name} {p.last_name}",
                "seat": p.seat_number or "Unassigned",
                "type": p.get_passenger_type_display(),
            })

        context = {
            "pnr": booking.pnr,
            "airline_name": booking.flight.airline.name,
            "airline_code": booking.flight.airline.code,
            "flight_number": booking.flight.flight_number,
            "origin": f"{booking.flight.route.origin.code} ({booking.flight.route.origin.city})",
            "destination": f"{booking.flight.route.destination.code} ({booking.flight.route.destination.city})",
            "departure_time": booking.flight.departure_time.strftime("%d %b %Y, %H:%M"),
            "arrival_time": booking.flight.arrival_time.strftime("%d %b %Y, %H:%M"),
            "gate": booking.flight.gate or "TBD",
            "terminal": booking.flight.terminal or "TBD",
            "fare_class": booking.fare_rule.fare_class.name,
            "passengers": passengers_data,
            "total_amount": str(booking.total_amount),
            "currency": booking.currency,
            "status": booking.get_booking_status_display(),
        }

        pdf_bytes = PDFService.generate_ticket_pdf(context)

        relative_path = f"tickets/ticket_{booking.pnr}.pdf"
        media_tickets_dir = os.path.join(settings.MEDIA_ROOT, "tickets")
        os.makedirs(media_tickets_dir, exist_ok=True)

        full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
        with open(full_path, "wb") as f:
            f.write(pdf_bytes)

        media_url = f"{settings.MEDIA_URL.rstrip('/')}/{relative_path}"
        booking.ticket_url = media_url
        booking.save(update_fields=["ticket_url", "updated_at"])

        logger.info("Generated ticket PDF for booking %s at %s", booking.pnr, media_url)
        return media_url
