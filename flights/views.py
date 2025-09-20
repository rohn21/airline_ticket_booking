from rest_framework import viewsets, permissions, filters
from django_filters import rest_framework as dj_filters
from .models import Airport, Airline, Aircraft, Route, Flight
from .serializers import (
    AirportSerializer,
    AirlineSerializer,
    AircraftSerializer,
    RouteSerializer,
    FlightSerializer,
)


class AirportViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Airport.objects.filter(is_deleted=False)
    serializer_class = AirportSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "code", "city", "country"]


class AirlineViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Airline.objects.filter(is_deleted=False)
    serializer_class = AirlineSerializer
    permission_classes = [permissions.AllowAny]


class AircraftViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Aircraft.objects.filter(is_deleted=False)
    serializer_class = AircraftSerializer
    permission_classes = [permissions.AllowAny]


class RouteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Route.objects.filter(is_deleted=False)
    serializer_class = RouteSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [dj_filters.DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["origin__id", "destination__id", "flight_type"]
    search_fields = ["origin__name", "destination__name", "code"]


class FlightFilter(dj_filters.FilterSet):
    origin = dj_filters.UUIDFilter(field_name="route__origin__id")
    destination = dj_filters.UUIDFilter(field_name="route__destination__id")
    airline = dj_filters.UUIDFilter(field_name="airline__id")
    flight_type = dj_filters.CharFilter(field_name="route__flight_type")
    departure_date = dj_filters.DateFilter(field_name="departure_time", lookup_expr="date")

    class Meta:
        model = Flight
        fields = ["origin", "destination", "airline", "flight_type", "departure_date", "status"]


class FlightViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Flight.objects.filter(is_deleted=False).select_related("airline", "route", "aircraft").prefetch_related(
        "fare_rules__fare_class"
    )
    serializer_class = FlightSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [dj_filters.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = FlightFilter
    search_fields = ["flight_number", "airline__name", "route__origin__name", "route__destination__name"]
    ordering_fields = ["departure_time", "seats_available"]
    ordering = ["departure_time"]
