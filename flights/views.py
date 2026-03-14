from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters import rest_framework as dj_filters
from flights.models import Airport, Airline, Aircraft, Route, Flight
from flights.serializers import (
    AirportSerializer,
    AirlineSerializer,
    AircraftSerializer,
    RouteSerializer,
    FlightSerializer,
)

# AIRPORTS
class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.filter(is_deleted=False)
    serializer_class = AirportSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "code", "city", "country"]

    def create(self, request, *args, **kwargs):
        # Check if data is a list (bulk create)
        if isinstance(request.data, list):
            serializer = self.get_serializer(data=request.data, many=True)
            serializer.is_valid(raise_exception=True)
            self.perform_bulk_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return super().create(request, *args, **kwargs)

    def perform_bulk_create(self, serializer):
        serializer.save()

    def update(self, request, *args, **kwargs):
        if isinstance(request.data, list):
            return Response(
                {"detail": "Use /airports/bulk-update/ for bulk update."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @action(detail=False, methods=["put"], url_path="bulk-update")
    def bulk_update(self, request):
        if not isinstance(request.data, list):
            return Response(
                {"detail": "Expected a list of objects."},
                status=status.HTTP_400_BAD_REQUEST
            )

        ids = [item.get("id") for item in request.data if item.get("id")]
        instances = list(Airport.objects.filter(id__in=ids, is_deleted=False))

        serializer = self.get_serializer(instances, data=request.data, many=True, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

# AIRLINES
class AirlineViewSet(viewsets.ModelViewSet):
    queryset = Airline.objects.filter(is_deleted=False)
    serializer_class = AirlineSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "code", "country"]

    def create(self, request, *args, **kwargs):
        if isinstance(request.data, list):
            serializer = self.get_serializer(data=request.data, many=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if isinstance(request.data, list):
            return Response(
                {"detail": "Use /airlines/bulk-update/ for bulk update."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @action(detail=False, methods=["put"], url_path="bulk-update")
    def bulk_update(self, request):
        if not isinstance(request.data, list):
            return Response(
                {"detail": "Expected a list of airline objects."},
                status=status.HTTP_400_BAD_REQUEST
            )

        ids = [item.get("id") for item in request.data if item.get("id")]
        instances = list(Airline.objects.filter(id__in=ids, is_deleted=False))

        serializer = self.get_serializer(
            instances,
            data=request.data,
            many=True,
            partial=False
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)



class AircraftViewSet(viewsets.ModelViewSet):
    queryset = Aircraft.objects.filter(is_deleted=False)
    serializer_class = AircraftSerializer
    permission_classes = [permissions.AllowAny]


class RouteViewSet(viewsets.ModelViewSet):
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


class FlightViewSet(viewsets.ModelViewSet):
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
