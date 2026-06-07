from django.db import transaction
from rest_framework import permissions, status, viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters import rest_framework as dj_filters
from flights.models import Airport, Airline, Aircraft, Route, Flight, FareClass, FareRule
from flights.serializers import (
    AirportSerializer,
    AirlineSerializer,
    AircraftSerializer,
    RouteSerializer,
    FlightReadSerializer,
    FlightWriteSerializer,
    FareClassSerializer,
    FareRuleReadSerializer,
    FareRuleWriteSerializer,
)
from flights.tasks import (
    refresh_flight_cache,
    refresh_flight_fare_rules,
    create_flight_audit_log,
    bulk_refresh_flights,
    warm_flight_list_cache,
    warm_flight_detail_cache,
)

FLIGHT_LIST_CACHE_KEY  = "flights:list:all"
FLIGHT_DETAIL_CACHE_KEY = "flights:detail:{flight_id}"

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
    filter_backends = [filters.SearchFilter]
    search_fields = ["model", "registration"]

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
                {"detail": "Use /aircrafts/bulk-update/ for bulk update."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @action(detail=False, methods=["put"], url_path="bulk-update")
    def bulk_update(self, request):
        if not isinstance(request.data, list):
            return Response(
                {"detail": "Expected a list of aircraft objects."},
                status=status.HTTP_400_BAD_REQUEST
            )

        ids = [item.get("id") for item in request.data if item.get("id")]
        instances = list(Aircraft.objects.filter(id__in=ids, is_deleted=False))

        serializer = self.get_serializer(
            instances,
            data=request.data,
            many=True,
            partial=False
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.filter(is_deleted=False).select_related("origin", "destination")
    serializer_class = RouteSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = [
        "code",
        "flight_type",
        "origin__name",
        "origin__code",
        "origin__city",
        "destination__name",
        "destination__code",
        "destination__city",
    ]

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
                {"detail": "Use /routes/bulk-update/ for bulk update."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @action(detail=False, methods=["put"], url_path="bulk-update")
    def bulk_update(self, request):
        if not isinstance(request.data, list):
            return Response(
                {"detail": "Expected a list of route objects."},
                status=status.HTTP_400_BAD_REQUEST
            )

        ids = [item.get("id") for item in request.data if item.get("id")]
        instances = list(
            Route.objects.filter(id__in=ids, is_deleted=False).select_related("origin", "destination")
        )

        serializer = self.get_serializer(
            instances,
            data=request.data,
            many=True,
            partial=False
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class FlightFilter(dj_filters.FilterSet):
    origin = dj_filters.UUIDFilter(field_name="route__origin__id")
    destination = dj_filters.UUIDFilter(field_name="route__destination__id")
    airline = dj_filters.UUIDFilter(field_name="airline__id")
    flight_type = dj_filters.CharFilter(field_name="route__flight_type")
    departure_date = dj_filters.DateFilter(field_name="departure_time", lookup_expr="date")

    class Meta:
        model = Flight
        fields = ["origin", "destination", "airline", "flight_type", "departure_date", "status"]


class FareClassViewSet(viewsets.ModelViewSet):
    queryset = FareClass.objects.filter(is_deleted=False)
    serializer_class = FareClassSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ["code", "name"]

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
                {"detail": "Use /fare-classes/bulk-update/ for bulk update."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().update(request, *args, **kwargs)

    @action(detail=False, methods=["put"], url_path="bulk-update")
    def bulk_update(self, request):
        if not isinstance(request.data, list):
            return Response(
                {"detail": "Expected a list of fare class objects."},
                status=status.HTTP_400_BAD_REQUEST
            )

        ids = [item.get("id") for item in request.data if item.get("id")]
        instances = list(FareClass.objects.filter(id__in=ids, is_deleted=False))

        serializer = self.get_serializer(instances, data=request.data, many=True, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class FareRuleViewSet(viewsets.ModelViewSet):
    queryset = FareRule.objects.filter(is_deleted=False).select_related("fare_class", "flight")
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ["currency", "fare_class__code", "fare_class__name", "flight__flight_number"]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return FareRuleReadSerializer
        return FareRuleWriteSerializer

    def create(self, request, *args, **kwargs):
        if isinstance(request.data, list):
            serializer = self.get_serializer(data=request.data, many=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            read_serializer = FareRuleReadSerializer(serializer.instance, many=True)
            return Response(read_serializer.data, status=status.HTTP_201_CREATED)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        read_serializer = FareRuleReadSerializer(instance)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        if isinstance(request.data, list):
            return Response(
                {"detail": "Use /fare-rules/bulk-update/ for bulk update."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        read_serializer = FareRuleReadSerializer(instance)
        return Response(read_serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["put"], url_path="bulk-update")
    def bulk_update(self, request):
        if not isinstance(request.data, list):
            return Response(
                {"detail": "Expected a list of fare rule objects."},
                status=status.HTTP_400_BAD_REQUEST
            )

        ids = [item.get("id") for item in request.data if item.get("id")]
        instances = list(FareRule.objects.filter(id__in=ids, is_deleted=False))

        serializer = self.get_serializer(instances, data=request.data, many=True, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        read_serializer = FareRuleReadSerializer(serializer.instance, many=True)
        return Response(read_serializer.data, status=status.HTTP_200_OK)


class FlightViewSet(viewsets.ModelViewSet):
    queryset = Flight.objects.filter(is_deleted=False).select_related(
        "airline", "route__origin", "route__destination", "aircraft"
    ).prefetch_related("fare_rules").order_by("-id")
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = [
        "flight_number",
        "status",
        "gate",
        "terminal",
        "airline__name",
        "airline__code",
        "route__code",
        "route__origin__code",
        "route__destination__code",
        "aircraft__registration",
    ]
    ordering_fields = ["id", "flight_number", "departure_time", "status"]
    ordering = ["-id"]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return FlightReadSerializer
        return FlightWriteSerializer

    def list(self, request, *args, **kwargs):
        # Bypass cache when search is active — always fresh results
        if request.query_params.get("search"):
            return super().list(request, *args, **kwargs)

        cached = cache.get(FLIGHT_LIST_CACHE_KEY)
        if cached:
            return Response(json.loads(cached), status=status.HTTP_200_OK)

        # Cache MISS → query DB via super(), then store result
        response = super().list(request, *args, **kwargs)
        cache.set(
            FLIGHT_LIST_CACHE_KEY,
            json.dumps(response.data, default=str),
            60 * 15  # 15 min TTL
        )
        return response

    def retrieve(self, request, *args, **kwargs):
        cache_key = FLIGHT_DETAIL_CACHE_KEY.format(flight_id=kwargs.get("pk"))

        cached = cache.get(cache_key)
        if cached:
            return Response(json.loads(cached), status=status.HTTP_200_OK)

        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, json.dumps(response.data, default=str), 60 * 15)
        return response

    def create(self, request, *args, **kwargs):
        if isinstance(request.data, list):
            serializer = self.get_serializer(data=request.data, many=True)
            serializer.is_valid(raise_exception=True)

            with transaction.atomic():
                serializer.save()
                instances = serializer.instance
                flight_ids = [obj.id for obj in instances]

                transaction.on_commit(
                    lambda flight_ids=flight_ids: bulk_refresh_flights.delay(flight_ids)
                )
                transaction.on_commit(
                    lambda flight_ids=flight_ids: create_flight_audit_log.delay(
                        None,
                        "FLIGHT_BULK_CREATED",
                        {"flight_ids": flight_ids}
                    )
                )

            read_serializer = FlightReadSerializer(instances, many=True)
            return Response(read_serializer.data, status=status.HTTP_201_CREATED)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            instance = serializer.save()

            transaction.on_commit(
                lambda flight_id=instance.id: refresh_flight_cache.delay(flight_id)
            )
            transaction.on_commit(
                lambda flight_id=instance.id: refresh_flight_fare_rules.delay(flight_id)
            )
            transaction.on_commit(
                lambda flight_id=instance.id, flight_number=instance.flight_number: create_flight_audit_log.delay(
                    flight_id,
                    "FLIGHT_CREATED",
                    {"flight_number": flight_number}
                )
            )

        read_serializer = FlightReadSerializer(instance)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        if isinstance(request.data, list):
            return Response(
                {"detail": "Use /flights/bulk-update/ for bulk update."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            instance = serializer.save()

            transaction.on_commit(
                lambda flight_id=instance.id: refresh_flight_cache.delay(flight_id)
            )
            transaction.on_commit(
                lambda flight_id=instance.id: refresh_flight_fare_rules.delay(flight_id)
            )
            transaction.on_commit(
                lambda flight_id=instance.id, flight_number=instance.flight_number: create_flight_audit_log.delay(
                    flight_id,
                    "FLIGHT_UPDATED",
                    {"flight_number": flight_number}
                )
            )

        read_serializer = FlightReadSerializer(instance)
        return Response(read_serializer.data, status=status.HTTP_200_OK)

    def perform_update(self, serializer):
        serializer.save()

    def finalize_response_data(self, instance):
        return FlightReadSerializer(instance).data

    @action(detail=False, methods=["put"], url_path="bulk-update")
    def bulk_update(self, request):
        if not isinstance(request.data, list):
            return Response(
                {"detail": "Expected a list of flight objects."},
                status=status.HTTP_400_BAD_REQUEST
            )

        ids = [item.get("id") for item in request.data if item.get("id")]
        instances = list(Flight.objects.filter(id__in=ids, is_deleted=False))

        serializer = self.get_serializer(
            instances,
            data=request.data,
            many=True,
            partial=False
        )
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            serializer.save()
            updated_instances = serializer.instance
            updated_ids = [obj.id for obj in updated_instances]

            transaction.on_commit(
                lambda flight_ids=updated_ids: bulk_refresh_flights.delay(flight_ids)
            )
            transaction.on_commit(
                lambda flight_ids=updated_ids: create_flight_audit_log.delay(
                    None,
                    "FLIGHT_BULK_UPDATED",
                    {"flight_ids": flight_ids}
                )
            )

        read_serializer = FlightReadSerializer(updated_instances, many=True)
        return Response(read_serializer.data, status=status.HTTP_200_OK)
