from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from flights.models import Flight, FareRule
from flights.serializers import FlightReadSerializer, FareRuleReadSerializer
from .models import (
    Booking,
    Passenger,
    SeatAssignment,
    BookingAudit,
    BookingStatus,
    PaymentStatus,
)


class PassengerReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Passenger
        fields = (
            "id",
            "passenger_type",
            "gender",
            "first_name",
            "last_name",
            "date_of_birth",
            "email",
            "phone_number",
            "nationality",
            "passport_number",
            "passport_expiry",
            "seat_number",
            "meal_preference",
            "special_assistance",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class PassengerWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Passenger
        fields = (
            "passenger_type",
            "gender",
            "first_name",
            "last_name",
            "date_of_birth",
            "email",
            "phone_number",
            "nationality",
            "passport_number",
            "passport_expiry",
            "seat_number",
            "meal_preference",
            "special_assistance",
        )

    def validate(self, attrs):
        passenger_type = attrs.get("passenger_type")
        passport_number = attrs.get("passport_number")

        if passenger_type in ["adult", "child"] and not attrs.get("date_of_birth"):
            raise serializers.ValidationError({
                "date_of_birth": "Date of birth is required for adult or child passengers."
            })

        if passport_number and len(passport_number.strip()) < 5:
            raise serializers.ValidationError({
                "passport_number": "Passport number looks too short."
            })

        return attrs


class SeatAssignmentSerializer(serializers.ModelSerializer):
    passenger = PassengerReadSerializer(read_only=True)

    class Meta:
        model = SeatAssignment
        fields = (
            "id",
            "passenger",
            "seat_number",
            "is_confirmed",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class BookingAuditSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source="actor.email", read_only=True)

    class Meta:
        model = BookingAudit
        fields = (
            "id",
            "action",
            "note",
            "metadata",
            "actor_email",
            "created_at",
        )
        read_only_fields = fields


class BookingReadSerializer(serializers.ModelSerializer):
    flight = FlightReadSerializer(read_only=True)
    fare_rule = FareRuleReadSerializer(read_only=True)
    passengers = PassengerReadSerializer(many=True, read_only=True)
    seat_assignments = SeatAssignmentSerializer(many=True, read_only=True)
    audits = BookingAuditSerializer(many=True, read_only=True)

    class Meta:
        model = Booking
        fields = (
            "id",
            "pnr",
            "user",
            "flight",
            "fare_rule",
            "booking_status",
            "payment_status",
            "contact_email",
            "contact_phone",
            "total_passengers",
            "total_amount",
            "currency",
            "expires_at",
            "confirmed_at",
            "cancelled_at",
            "remarks",
            "passengers",
            "seat_assignments",
            "audits",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class BookingCreateSerializer(serializers.ModelSerializer):
    flight_id = serializers.PrimaryKeyRelatedField(
        queryset=Flight.objects.filter(is_deleted=False),
        source="flight",
        write_only=True,
    )
    fare_rule_id = serializers.PrimaryKeyRelatedField(
        queryset=FareRule.objects.filter(is_deleted=False),
        source="fare_rule",
        write_only=True,
    )
    passengers = PassengerWriteSerializer(many=True, write_only=True)

    class Meta:
        model = Booking
        fields = (
            "id",
            "flight_id",
            "fare_rule_id",
            "contact_email",
            "contact_phone",
            "remarks",
            "passengers",
        )
        read_only_fields = ("id",)

    def validate_passengers(self, value):
        if not value:
            raise serializers.ValidationError("At least one passenger is required.")
        return value

    def validate(self, attrs):
        flight = attrs.get("flight")
        fare_rule = attrs.get("fare_rule")
        passengers = attrs.get("passengers", [])

        if fare_rule and flight and fare_rule.flight_id != flight.id:
            raise serializers.ValidationError({
                "fare_rule_id": "Selected fare rule does not belong to the selected flight."
            })

        passenger_count = len(passengers)

        if passenger_count <= 0:
            raise serializers.ValidationError({
                "passengers": "At least one passenger is required."
            })

        if fare_rule and fare_rule.seat_count < passenger_count:
            raise serializers.ValidationError({
                "passengers": "Selected fare rule does not have enough seat inventory."
            })

        if flight and flight.seats_available < passenger_count:
            raise serializers.ValidationError({
                "flight_id": "Not enough seats available on this flight."
            })

        seat_numbers = [p.get("seat_number") for p in passengers if p.get("seat_number")]
        if len(seat_numbers) != len(set(seat_numbers)):
            raise serializers.ValidationError({
                "passengers": "Duplicate seat numbers are not allowed in the same booking request."
            })

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        passengers_data = validated_data.pop("passengers")
        request = self.context.get("request")
        flight = validated_data["flight"]
        fare_rule = validated_data["fare_rule"]

        passenger_count = len(passengers_data)
        total_amount = Decimal(fare_rule.price) * passenger_count

        booking = Booking.objects.create(
            user=request.user if request and request.user.is_authenticated else None,
            total_passengers=passenger_count,
            total_amount=total_amount,
            currency=fare_rule.currency,
            booking_status=BookingStatus.HELD,
            payment_status=PaymentStatus.PENDING,
            **validated_data,
        )

        passenger_objs = [
            Passenger(booking=booking, **passenger_data)
            for passenger_data in passengers_data
        ]
        Passenger.objects.bulk_create(passenger_objs)

        BookingAudit.objects.create(
            booking=booking,
            actor=request.user if request and request.user.is_authenticated else None,
            action="booking_created",
            note="Booking created successfully.",
            metadata={
                "flight_id": str(flight.id),
                "fare_rule_id": str(fare_rule.id),
                "passenger_count": passenger_count,
            },
        )

        return booking

    def to_representation(self, instance):
        return BookingReadSerializer(instance, context=self.context).data


class BookingContactUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = (
            "contact_email",
            "contact_phone",
            "remarks",
        )

    def validate(self, attrs):
        instance = self.instance

        if instance.booking_status in [
            BookingStatus.CANCELLED,
            BookingStatus.EXPIRED,
            BookingStatus.TICKETED,
        ]:
            raise serializers.ValidationError(
                "Contact details cannot be updated for cancelled, expired, or ticketed bookings."
            )

        return attrs

    def update(self, instance, validated_data):
        request = self.context.get("request")

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        BookingAudit.objects.create(
            booking=instance,
            actor=request.user if request and request.user.is_authenticated else None,
            action="booking_contact_updated",
            note="Booking contact details updated.",
            metadata=validated_data,
        )

        return instance

    def to_representation(self, instance):
        return BookingReadSerializer(instance, context=self.context).data


class BookingCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs):
        booking = self.instance

        if booking.booking_status in [BookingStatus.CANCELLED, BookingStatus.EXPIRED]:
            raise serializers.ValidationError("This booking is already cancelled or expired.")

        if booking.booking_status == BookingStatus.TICKETED:
            raise serializers.ValidationError("Ticketed booking cannot be cancelled from this endpoint.")

        return attrs

    def save(self, **kwargs):
        booking = self.instance
        request = self.context.get("request")
        reason = self.validated_data.get("reason")

        booking.booking_status = BookingStatus.CANCELLED
        booking.cancelled_at = timezone.now()
        booking.save(update_fields=["booking_status", "updated_at", "cancelled_at"])

        BookingAudit.objects.create(
            booking=booking,
            actor=request.user if request and request.user.is_authenticated else None,
            action="booking_cancelled",
            note=reason or "Booking cancelled.",
            metadata={"reason": reason or ""},
        )

        return booking

    # def to_representation(self, instance):
    #     return BookingReadSerializer(instance, context=self.context).data


class BookingConfirmSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs):
        booking = self.instance

        if booking.booking_status in [BookingStatus.CANCELLED, BookingStatus.EXPIRED]:
            raise serializers.ValidationError("Cancelled or expired bookings cannot be confirmed.")

        if booking.booking_status in [BookingStatus.CONFIRMED, BookingStatus.TICKETED]:
            raise serializers.ValidationError("This booking is already confirmed.")

        return attrs

    def save(self, **kwargs):
        from django.utils import timezone

        booking = self.instance
        request = self.context.get("request")
        note = self.validated_data.get("note")

        booking.booking_status = BookingStatus.CONFIRMED
        booking.payment_status = PaymentStatus.SUCCESS
        booking.confirmed_at = timezone.now()
        booking.save(update_fields=["booking_status", "payment_status", "confirmed_at", "updated_at"])

        BookingAudit.objects.create(
            booking=booking,
            actor=request.user if request and request.user.is_authenticated else None,
            action="booking_confirmed",
            note=note or "Booking confirmed.",
            metadata={"note": note or ""},
        )

        return booking

    # def to_representation(self, instance):
    #     return BookingReadSerializer(instance, context=self.context).data
