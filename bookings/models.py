from decimal import Decimal
import random
import string

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from core.models import BaseModel
from flights.models import Flight, FareRule


def generate_pnr(length=6):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=length))


class BookingStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    HELD = "held", "Held"
    PAYMENT_PENDING = "payment_pending", "Payment Pending"
    CONFIRMED = "confirmed", "Confirmed"
    TICKETED = "ticketed", "Ticketed"
    CANCELLED = "cancelled", "Cancelled"
    EXPIRED = "expired", "Expired"


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SUCCESS = "success", "Success"
    FAILED = "failed", "Failed"
    REFUNDED = "refunded", "Refunded"


class PassengerType(models.TextChoices):
    ADULT = "adult", "Adult"
    CHILD = "child", "Child"
    INFANT = "infant", "Infant"


class GenderChoices(models.TextChoices):
    MALE = "male", "Male"
    FEMALE = "female", "Female"
    OTHER = "other", "Other"


class Booking(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings",
    )
    flight = models.ForeignKey(
        Flight,
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    fare_rule = models.ForeignKey(
        FareRule,
        on_delete=models.PROTECT,
        related_name="bookings",
    )

    pnr = models.CharField(max_length=10, unique=True, editable=False)
    booking_status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.DRAFT,
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )

    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)

    total_passengers = models.PositiveIntegerField(default=1)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=10, default="INR")

    expires_at = models.DateTimeField(null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    remarks = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["pnr"]),
            models.Index(fields=["booking_status"]),
            models.Index(fields=["payment_status"]),
            models.Index(fields=["flight"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return f"{self.pnr} - {self.flight.flight_number}"

    def clean(self):
        if self.fare_rule and self.flight and self.fare_rule.flight_id != self.flight_id:
            raise ValidationError({"fare_rule": "Selected fare rule does not belong to the selected flight."})

        if self.total_passengers <= 0:
            raise ValidationError({"total_passengers": "Total passengers must be greater than 0."})

    def save(self, *args, **kwargs):
        if not self.pnr:
            while True:
                pnr = generate_pnr()
                if not Booking.objects.filter(pnr=pnr).exists():
                    self.pnr = pnr
                    break
        self.full_clean()
        super().save(*args, **kwargs)


class Passenger(BaseModel):
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="passengers",
    )

    passenger_type = models.CharField(
        max_length=10,
        choices=PassengerType.choices,
        default=PassengerType.ADULT,
    )
    gender = models.CharField(
        max_length=10,
        choices=GenderChoices.choices,
        blank=True,
        null=True,
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()

    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    nationality = models.CharField(max_length=100, blank=True, null=True)
    passport_number = models.CharField(max_length=50, blank=True, null=True)
    passport_expiry = models.DateField(blank=True, null=True)

    seat_number = models.CharField(max_length=10, blank=True, null=True)
    meal_preference = models.CharField(max_length=50, blank=True, null=True)
    special_assistance = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["booking"]),
            models.Index(fields=["passport_number"]),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.booking.pnr}"


class SeatAssignment(BaseModel):
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="seat_assignments",
    )
    passenger = models.OneToOneField(
        Passenger,
        on_delete=models.CASCADE,
        related_name="seat_assignment",
    )
    flight = models.ForeignKey(
        Flight,
        on_delete=models.CASCADE,
        related_name="seat_assignments",
    )

    seat_number = models.CharField(max_length=10)
    is_confirmed = models.BooleanField(default=False)

    class Meta:
        unique_together = (
            ("flight", "seat_number"),
            ("passenger", "flight"),
        )
        indexes = [
            models.Index(fields=["flight", "seat_number"]),
            models.Index(fields=["booking"]),
        ]

    def __str__(self):
        return f"{self.flight.flight_number} - {self.seat_number}"


class BookingAudit(BaseModel):
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="audits",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="booking_audits",
    )

    action = models.CharField(max_length=100)
    note = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["booking"]),
            models.Index(fields=["action"]),
        ]

    def __str__(self):
        return f"{self.booking.pnr} - {self.action}"
