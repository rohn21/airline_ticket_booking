import datetime
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from flights.models import Airport, Airline, Aircraft, Route, Flight, FareClass, FareRule
from bookings.models import Booking, Passenger, BookingStatus, PaymentStatus, PassengerType, GenderChoices
from tickets.services import QRService, PDFService, TicketService

User = get_user_model()


class TicketServiceTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="ticketuser@example.com",
            password="Testpassword123!",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="Testpassword123!",
        )

        amd = Airport.objects.create(code="AMD", name="Ahmedabad", city="Ahmedabad", country="India")
        del_apt = Airport.objects.create(code="DEL", name="Delhi", city="Delhi", country="India")
        route = Route.objects.create(origin=amd, destination=del_apt, flight_type="domestic")
        airline = Airline.objects.create(code="AI", name="Air India", country="India")
        aircraft = Aircraft.objects.create(model="A320", registration="VT-TEST", seat_capacity=180)

        dep = timezone.now() + datetime.timedelta(days=1)
        arr = dep + datetime.timedelta(hours=2)

        self.flight = Flight.objects.create(
            airline=airline,
            flight_number="AI999",
            route=route,
            aircraft=aircraft,
            departure_time=dep,
            arrival_time=arr,
            total_seats=180,
            seats_available=179,
        )

        fc = FareClass.objects.create(code="Y", name="Economy")
        self.fare_rule = FareRule.objects.create(flight=self.flight, fare_class=fc, price=Decimal("3500.00"))

        self.booking = Booking.objects.create(
            user=self.user,
            flight=self.flight,
            fare_rule=self.fare_rule,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.SUCCESS,
            contact_email="ticketuser@example.com",
            contact_phone="+919999999999",
            total_passengers=1,
            total_amount=Decimal("3500.00"),
        )

        self.passenger = Passenger.objects.create(
            booking=self.booking,
            passenger_type=PassengerType.ADULT,
            gender=GenderChoices.MALE,
            first_name="Test",
            last_name="Passenger",
            date_of_birth=datetime.date(1995, 1, 1),
            seat_number="15B",
        )

    def test_qr_service(self):
        qr_bytes = QRService.generate_qr_bytes(self.booking.pnr)
        self.assertIsNotNone(qr_bytes)
        self.assertTrue(len(qr_bytes) > 0)

        qr_b64 = QRService.generate_qr_base64(self.booking.pnr)
        self.assertTrue(isinstance(qr_b64, str))

    def test_pdf_service(self):
        context = {
            "pnr": self.booking.pnr,
            "airline_name": "Air India",
            "airline_code": "AI",
            "flight_number": "AI999",
            "origin": "AMD (Ahmedabad)",
            "destination": "DEL (Delhi)",
            "departure_time": "12 Sep 2026, 08:30",
            "arrival_time": "12 Sep 2026, 10:30",
            "gate": "A1",
            "terminal": "T1",
            "fare_class": "Economy",
            "passengers": [{"name": "Test Passenger", "seat": "15B", "type": "Adult"}],
            "total_amount": "3500.00",
            "currency": "INR",
            "status": "Confirmed",
        }
        pdf_bytes = PDFService.generate_ticket_pdf(context)
        self.assertIsNotNone(pdf_bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_ticket_service_generate_and_save(self):
        media_url = TicketService.generate_and_save(str(self.booking.id))
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.ticket_url, media_url)
        self.assertIn(self.booking.pnr, media_url)

    def test_api_ticket_download_success(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("ticket-download", kwargs={"pnr": self.booking.pnr})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_api_ticket_download_permission_denied(self):
        self.client.force_authenticate(user=self.other_user)
        url = reverse("ticket-download", kwargs={"pnr": self.booking.pnr})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_api_ticket_qr(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("ticket-qr", kwargs={"pnr": self.booking.pnr})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "image/png")
