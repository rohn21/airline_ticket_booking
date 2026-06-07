from django.db import transaction
from rest_framework import status, permissions, viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response

from bookings.models import Booking
from bookings.serializers import (
    BookingCreateSerializer,
    BookingReadSerializer,
    BookingContactUpdateSerializer,
    BookingCancelSerializer,
    BookingConfirmSerializer,
)
from bookings.tasks import (
    send_booking_created_email,
    send_booking_confirmed_email,
    create_booking_audit_log,
    generate_ticket_artifact,
)
from flights.tasks import refresh_flight_cache


class BookingViewSet(viewsets.ModelViewSet):
    queryset = (
        Booking.objects
        .filter(is_deleted=False)
        .select_related("flight", "fare_rule", "user")
        .prefetch_related("passengers", "seat_assignments", "audits")
    )
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = [
        "pnr",
        "contact_email",
        "contact_phone",
        "flight__flight_number",
        "flight__route__origin__code",
        "flight__route__destination__code",
    ]

    serializer_class = BookingReadSerializer

    def get_serializer_class(self):
        if self.action == "create":
            return BookingCreateSerializer
        if self.action in ["partial_update", "update"]:
            return BookingContactUpdateSerializer
        if self.action == "cancel":
            return BookingCancelSerializer
        if self.action == "confirm":
            return BookingConfirmSerializer
        return BookingReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            booking = serializer.save()

            transaction.on_commit(
                lambda booking_id=booking.id: send_booking_created_email.delay(booking_id)
            )
            transaction.on_commit(
                lambda booking_id=booking.id, pnr=booking.pnr: create_booking_audit_log.delay(
                    booking_id,
                    "BOOKING_CREATED",
                    {"pnr": pnr}
                )
            )
            transaction.on_commit(
                lambda flight_id=booking.flight_id:     refresh_flight_cache.delay(flight_id)
            )

        read_serializer = BookingReadSerializer(booking, context=self.get_serializer_context())
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.partial_update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        booking = self.get_object()
        serializer = self.get_serializer(booking, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            booking = serializer.save()

            transaction.on_commit(
                lambda booking_id=booking.id: create_booking_audit_log.delay(
                    booking_id,
                    "BOOKING_CONTACT_UPDATED",
                    {
                        "contact_email": booking.contact_email,
                        "contact_phone": booking.contact_phone,
                    }
                )
            )

        read_serializer = BookingReadSerializer(booking, context=self.get_serializer_context())
        return Response(read_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        booking = self.get_object()
        serializer = self.get_serializer(booking, data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            booking = serializer.save()

            transaction.on_commit(
                lambda booking_id=booking.id, pnr=booking.pnr: create_booking_audit_log.delay(
                    booking_id,
                    "BOOKING_CANCELLED",
                    {"pnr": pnr}
                )
            )
            transaction.on_commit(
                lambda flight_id=booking.flight_id: refresh_flight_cache.delay(flight_id)
            )

        read_serializer = BookingReadSerializer(booking, context=self.get_serializer_context())
        return Response(read_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="confirm")
    def confirm(self, request, pk=None):
        booking = self.get_object()
        serializer = self.get_serializer(booking, data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            booking = serializer.save()

            transaction.on_commit(
                lambda booking_id=booking.id: send_booking_confirmed_email.delay(booking_id)
            )
            transaction.on_commit(
                lambda booking_id=booking.id: generate_ticket_artifact.delay(booking_id)
            )
            transaction.on_commit(
                lambda booking_id=booking.id, pnr=booking.pnr: create_booking_audit_log.delay(
                    booking_id,
                    "BOOKING_CONFIRMED",
                    {"pnr": pnr}
                )
            )
            transaction.on_commit(
                lambda flight_id=booking.flight_id: refresh_flight_cache.delay(flight_id)
            )

        read_serializer = BookingReadSerializer(booking, context=self.get_serializer_context())
        return Response(read_serializer.data, status=status.HTTP_200_OK)