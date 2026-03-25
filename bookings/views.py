from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters import rest_framework as dj_filters
from bookings.models import Booking, Passenger, BookingAudit, SeatAssignment
from bookings.serializers import BookingReadSerializer, BookingCreateSerializer, BookingCancelSerializer, \
    BookingConfirmSerializer, BookingContactUpdateSerializer


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

    # default, will be overridden by get_serializer_class
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
        booking = serializer.save()
        read_serializer = BookingReadSerializer(booking, context=self.get_serializer_context())
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        # we only support partial updates for contact details; full PUT is discouraged
        kwargs["partial"] = True
        return self.partial_update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        booking = self.get_object()
        serializer = self.get_serializer(booking, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()
        read_serializer = BookingReadSerializer(booking, context=self.get_serializer_context())
        return Response(read_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        booking = self.get_object()
        serializer = self.get_serializer(booking, data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()
        read_serializer = BookingReadSerializer(booking, context=self.get_serializer_context())
        return Response(read_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="confirm")
    def confirm(self, request, pk=None):
        booking = self.get_object()
        serializer = self.get_serializer(booking, data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()
        read_serializer = BookingReadSerializer(booking, context=self.get_serializer_context())
        return Response(read_serializer.data, status=status.HTTP_200_OK)

