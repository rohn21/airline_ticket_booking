from django.http import HttpResponse
from rest_framework import views, permissions, status
from rest_framework.response import Response
from bookings.models import Booking
from tickets.services.ticket_service import TicketService
from tickets.services.qr_service import QRService


class TicketDownloadView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pnr):
        try:
            booking = Booking.objects.select_related(
                "flight",
                "flight__airline",
                "flight__route__origin",
                "flight__route__destination",
                "fare_rule__fare_class",
            ).prefetch_related("passengers").get(pnr__iexact=pnr, is_deleted=False)
        except Booking.DoesNotExist:
            return Response({"detail": "Booking not found."}, status=status.HTTP_404_NOT_FOUND)

        if not request.user.is_staff and booking.user != request.user:
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        try:
            media_url = TicketService.generate_and_save(str(booking.id))
        except Exception as e:
            return Response({"detail": f"Failed to generate ticket: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
            "passengers": [
                {
                    "name": f"{p.first_name} {p.last_name}",
                    "seat": p.seat_number or "Unassigned",
                    "type": p.get_passenger_type_display(),
                }
                for p in booking.passengers.all()
            ],
            "total_amount": str(booking.total_amount),
            "currency": booking.currency,
            "status": booking.get_booking_status_display(),
        }

        from tickets.services.pdf_service import PDFService
        pdf_bytes = PDFService.generate_ticket_pdf(context)

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="ticket_{booking.pnr}.pdf"'
        return response


class TicketQRView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pnr):
        try:
            booking = Booking.objects.get(pnr__iexact=pnr, is_deleted=False)
        except Booking.DoesNotExist:
            return Response({"detail": "Booking not found."}, status=status.HTTP_404_NOT_FOUND)

        if not request.user.is_staff and booking.user != request.user:
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        qr_bytes = QRService.generate_qr_bytes(booking.pnr)
        response = HttpResponse(qr_bytes, content_type="image/png")
        response["Content-Disposition"] = f'inline; filename="qr_{booking.pnr}.png"'
        return response
