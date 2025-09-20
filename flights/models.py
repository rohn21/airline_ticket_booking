from django.db import models
from decimal import Decimal
from core.models import BaseModel


class Airport(BaseModel):
    """
    Represents an airport (IATA/ICAO codes, location).
    """
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=10, unique=True)  # IATA or ICAO code
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.code} - {self.city}, {self.country}"


class Airline(BaseModel):
    """
    Represents an airline company.
    """
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=10, unique=True)  # IATA airline code
    country = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.code})"


class Aircraft(BaseModel):
    """
    Represents an aircraft type/registration.
    """
    model = models.CharField(max_length=100)  # e.g., Boeing 737
    registration = models.CharField(max_length=50, unique=True)  # e.g., VT-ABC
    seat_capacity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.model} ({self.registration})"


class Route(BaseModel):
    """
    Route between two airports.
    """
    FLIGHT_TYPE_CHOICES = [
        ("domestic", "Domestic"),
        ("international", "International"),
        ("regional", "Regional"),
        ("longhaul", "Long Haul"),
    ]

    code = models.CharField(max_length=16, blank=True, null=True, help_text="Optional route code")
    origin = models.ForeignKey(Airport, on_delete=models.PROTECT, related_name="departing_routes")
    destination = models.ForeignKey(Airport, on_delete=models.PROTECT, related_name="arriving_routes")
    flight_type = models.CharField(max_length=20, choices=FLIGHT_TYPE_CHOICES, default="domestic")
    distance_km = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    estimated_duration = models.DurationField(null=True, blank=True)

    class Meta:
        unique_together = ("origin", "destination", "flight_type")
        indexes = [models.Index(fields=["origin", "destination", "flight_type"])]

    def __str__(self):
        return f"{self.origin.code} → {self.destination.code} ({self.flight_type})"


class Flight(BaseModel):
    """
    Scheduled flight instance (a specific departure).
    """
    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("active", "Active"),
        ("delayed", "Delayed"),
        ("cancelled", "Cancelled"),
        ("landed", "Landed"),
    ]

    flight_number = models.CharField(max_length=10)
    airline = models.ForeignKey(Airline, on_delete=models.PROTECT, related_name="flights")
    route = models.ForeignKey(Route, on_delete=models.PROTECT, related_name="flights")
    aircraft = models.ForeignKey(Aircraft, on_delete=models.PROTECT, related_name="flights", null=True, blank=True)

    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()

    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="scheduled")
    total_seats = models.PositiveIntegerField(default=0)
    seats_available = models.PositiveIntegerField(default=0)

    gate = models.CharField(max_length=8, blank=True, null=True)
    terminal = models.CharField(max_length=8, blank=True, null=True)

    class Meta:
        unique_together = ("airline", "flight_number", "departure_time")
        indexes = [models.Index(fields=["departure_time", "status"])]

    def __str__(self):
        return f"{self.airline.code} {self.flight_number} ({self.route})"

    def allocate_seats(self, num=1):
        """
        Reserve seats. (Use transactions in production)
        """
        if self.seats_available >= num:
            self.seats_available -= num
            self.save(update_fields=["seats_available"])
            return True
        return False

    def release_seats(self, num=1):
        self.seats_available = min(self.total_seats, self.seats_available + num)
        self.save(update_fields=["seats_available"])


class FareClass(BaseModel):
    """
    Fare class (Economy, Business, First).
    """
    code = models.CharField(max_length=5)  # Y, J, F
    name = models.CharField(max_length=50)  # Economy, Business, First

    class Meta:
        unique_together = ("code", "name")

    def __str__(self):
        return f"{self.name} ({self.code})"


class FareRule(BaseModel):
    """
    Fare rules/prices for a flight and fare class.
    """
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name="fare_rules")
    fare_class = models.ForeignKey(FareClass, on_delete=models.PROTECT, related_name="fare_rules")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=3, default="INR")
    refundable = models.BooleanField(default=False)
    baggage_allowance_kg = models.PositiveIntegerField(default=15)
    seat_count = models.PositiveIntegerField(default=0)  # allocated seats for this fare class

    class Meta:
        unique_together = ("flight", "fare_class")
        indexes = [models.Index(fields=["flight", "fare_class"])]

    def __str__(self):
        return f"{self.flight} - {self.fare_class} @ {self.price} {self.currency}"
