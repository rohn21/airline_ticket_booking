from rest_framework import serializers, status
from rest_framework.response import Response
from .models import Airport, Airline, Aircraft, Route, Flight, FareClass, FareRule


class AirportBulkListSerializer(serializers.ListSerializer):
    def update(self, instances, validated_data):
        instance_map = {str(instance.id): instance for instance in instances}
        updated_instances = []

        for item in validated_data:
            instance = instance_map.get(str(item.get("id")))
            if not instance:
                continue

            for attr, value in item.items():
                setattr(instance, attr, value)
            updated_instances.append(instance)

        if updated_instances:
            Airport.objects.bulk_update(
                updated_instances,
                ["name", "code", "city", "country"]
            )
        return updated_instances


class AirportSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)

    class Meta:
        model = Airport
        fields = ["id", "name", "code", "city", "country"]
        list_serializer_class = AirportBulkListSerializer
        extra_kwargs = {
            "code": {"validators": []}
        }

    def validate_code(self, value):
        qs = Airport.objects.filter(code=value, is_deleted=False)
        if self.instance is not None and not isinstance(self.instance, list):
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Airport code already exists.")
        return value


class AirlineBulkListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        objs = [Airline(**item) for item in validated_data]
        return Airline.objects.bulk_create(objs)

    def update(self, instances, validated_data):
        instance_map = {str(instance.id): instance for instance in instances}
        updated_instances = []

        for item in validated_data:
            airline = instance_map.get(str(item.get("id")))
            if not airline:
                continue

            for attr, value in item.items():
                setattr(airline, attr, value)
            updated_instances.append(airline)

        if updated_instances:
            Airline.objects.bulk_update(
                updated_instances,
                ["name", "code", "country"]
            )
        return updated_instances


class AirlineSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)

    class Meta:
        model = Airline
        fields = ("id", "name", "code", "country")
        list_serializer_class = AirlineBulkListSerializer
        extra_kwargs = {
            "code": {"validators": []}
        }

    def validate_code(self, value):
        qs = Airline.objects.filter(code=value, is_deleted=False)
        if self.instance is not None and not isinstance(self.instance, list):
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Airline code already exists.")
        return value


class AircraftBulkListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        objs = [Aircraft(**item) for item in validated_data]
        return Aircraft.objects.bulk_create(objs)

    def update(self, instances, validated_data):
        instance_map = {str(instance.id): instance for instance in instances}
        updated_instances = []

        for item in validated_data:
            aircraft = instance_map.get(str(item.get("id")))
            if not aircraft:
                continue

            for attr, value in item.items():
                setattr(aircraft, attr, value)
            updated_instances.append(aircraft)

        if updated_instances:
            Aircraft.objects.bulk_update(
                updated_instances,
                ["model", "registration", "seat_capacity"]
            )
        return updated_instances


class AircraftSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)

    class Meta:
        model = Aircraft
        fields = ("id", "model", "registration", "seat_capacity")
        list_serializer_class = AircraftBulkListSerializer
        extra_kwargs = {
            "registration": {"validators": []}
        }

    def validate_seat_capacity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Seat capacity must be greater than 0.")
        return value

    def validate_registration(self, value):
        qs = Aircraft.objects.filter(registration=value, is_deleted=False)
        if self.instance is not None and not isinstance(self.instance, list):
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Aircraft registration already exists.")
        return value


class RouteBulkListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        objs = [Route(**item) for item in validated_data]
        return Route.objects.bulk_create(objs)

    def update(self, instances, validated_data):
        instance_map = {str(instance.id): instance for instance in instances}
        updated_instances = []

        for item in validated_data:
            route = instance_map.get(str(item.get("id")))
            if not route:
                continue

            for attr, value in item.items():
                setattr(route, attr, value)
            updated_instances.append(route)

        if updated_instances:
            Route.objects.bulk_update(
                updated_instances,
                [
                    "code",
                    "origin",
                    "destination",
                    "flight_type",
                    "distance_km",
                    "estimated_duration",
                ]
            )
        return updated_instances


class RouteSerializer(serializers.ModelSerializer):
    origin = AirportSerializer(read_only=True)
    destination = AirportSerializer(read_only=True)

    origin_id = serializers.PrimaryKeyRelatedField(
        queryset=Airport.objects.filter(is_deleted=False),
        source="origin",
        write_only=True
    )
    destination_id = serializers.PrimaryKeyRelatedField(
        queryset=Airport.objects.filter(is_deleted=False),
        source="destination",
        write_only=True
    )

    id = serializers.UUIDField(required=False)

    class Meta:
        model = Route
        fields = (
            "id",
            "code",
            "origin",
            "destination",
            "origin_id",
            "destination_id",
            "flight_type",
            "distance_km",
            "estimated_duration",
        )
        list_serializer_class = RouteBulkListSerializer
        extra_kwargs = {
            "code": {"validators": []}
        }

    def validate_code(self, value):
        qs = Route.objects.filter(code=value, is_deleted=False)
        if self.instance is not None and not isinstance(self.instance, list):
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Route code already exists.")
        return value

    def validate(self, attrs):
        origin = attrs.get("origin")
        destination = attrs.get("destination")

        if not origin and self.instance:
            origin = self.instance.origin
        if not destination and self.instance:
            destination = self.instance.destination

        if origin and destination and origin == destination:
            raise serializers.ValidationError(
                {"destination_id": "Origin and destination cannot be the same."}
            )
        return attrs


class FareClassBulkListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        objs = [FareClass(**item) for item in validated_data]
        return FareClass.objects.bulk_create(objs)

    def update(self, instances, validated_data):
        instance_map = {str(instance.id): instance for instance in instances}
        updated_instances = []

        for item in validated_data:
            fare_class = instance_map.get(str(item.get("id")))
            if not fare_class:
                continue

            for attr, value in item.items():
                setattr(fare_class, attr, value)
            updated_instances.append(fare_class)

        if updated_instances:
            FareClass.objects.bulk_update(updated_instances, ["code", "name"])
        return updated_instances


class FareClassSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)

    class Meta:
        model = FareClass
        fields = ("id", "code", "name")
        list_serializer_class = FareClassBulkListSerializer
        validators = []

    def validate(self, attrs):
        code = attrs.get("code")
        name = attrs.get("name")

        if self.instance:
            code = code or self.instance.code
            name = name or self.instance.name

        qs = FareClass.objects.filter(code=code, name=name, is_deleted=False)
        if self.instance is not None and not isinstance(self.instance, list):
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError("Fare class with this code and name already exists.")
        return attrs



class FareRuleBulkListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        objs = [FareRule(**item) for item in validated_data]
        return FareRule.objects.bulk_create(objs)

    def update(self, instances, validated_data):
        instance_map = {str(instance.id): instance for instance in instances}
        updated_instances = []

        for item in validated_data:
            fare_rule = instance_map.get(str(item.get("id")))
            if not fare_rule:
                continue

            for attr, value in item.items():
                setattr(fare_rule, attr, value)
            updated_instances.append(fare_rule)

        if updated_instances:
            FareRule.objects.bulk_update(
                updated_instances,
                [
                    "flight",
                    "fare_class",
                    "price",
                    "currency",
                    "refundable",
                    "baggage_allowance_kg",
                    "seat_count",
                ]
            )
        return updated_instances


class FareRuleReadSerializer(serializers.ModelSerializer):
    fare_class = serializers.StringRelatedField()

    class Meta:
        model = FareRule
        fields = (
            "id",
            "fare_class",
            "price",
            "currency",
            "refundable",
            "baggage_allowance_kg",
            "seat_count",
        )


class FareRuleWriteSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)
    flight = serializers.PrimaryKeyRelatedField(
        queryset=Flight.objects.filter(is_deleted=False)
    )
    fare_class = serializers.PrimaryKeyRelatedField(
        queryset=FareClass.objects.filter(is_deleted=False)
    )

    class Meta:
        model = FareRule
        fields = (
            "id",
            "flight",
            "fare_class",
            "price",
            "currency",
            "refundable",
            "baggage_allowance_kg",
            "seat_count",
        )
        list_serializer_class = FareRuleBulkListSerializer

    def validate_seat_count(self, value):
        if value < 0:
            raise serializers.ValidationError("Seat count cannot be negative.")
        return value

    def validate_baggage_allowance_kg(self, value):
        if value < 0:
            raise serializers.ValidationError("Baggage allowance cannot be negative.")
        return value



class FlightReadSerializer(serializers.ModelSerializer):
    airline = AirlineSerializer(read_only=True)
    route = RouteSerializer(read_only=True)
    aircraft = AircraftSerializer(read_only=True)
    fare_rules = FareRuleReadSerializer(many=True, read_only=True)

    class Meta:
        model = Flight
        fields = (
            "id",
            "flight_number",
            "airline",
            "route",
            "aircraft",
            "departure_time",
            "arrival_time",
            "status",
            "total_seats",
            "seats_available",
            "gate",
            "terminal",
            "fare_rules",
        )


class FlightBulkListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        objs = [Flight(**item) for item in validated_data]
        return Flight.objects.bulk_create(objs)

    def update(self, instances, validated_data):
        instance_map = {str(instance.id): instance for instance in instances}
        updated_instances = []

        for item in validated_data:
            flight = instance_map.get(str(item.get("id")))
            if not flight:
                continue

            for attr, value in item.items():
                setattr(flight, attr, value)
            updated_instances.append(flight)

        if updated_instances:
            Flight.objects.bulk_update(
                updated_instances,
                [
                    "flight_number",
                    "airline",
                    "route",
                    "aircraft",
                    "departure_time",
                    "arrival_time",
                    "status",
                    "total_seats",
                    "seats_available",
                    "gate",
                    "terminal",
                ]
            )
        return updated_instances


class FlightWriteSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)

    airline_id = serializers.PrimaryKeyRelatedField(
        queryset=Airline.objects.filter(is_deleted=False),
        source="airline"
    )
    route_id = serializers.PrimaryKeyRelatedField(
        queryset=Route.objects.filter(is_deleted=False),
        source="route"
    )
    aircraft_id = serializers.PrimaryKeyRelatedField(
        queryset=Aircraft.objects.filter(is_deleted=False),
        source="aircraft"
    )

    class Meta:
        model = Flight
        fields = (
            "id",
            "flight_number",
            "airline_id",
            "route_id",
            "aircraft_id",
            "departure_time",
            "arrival_time",
            "status",
            "total_seats",
            "seats_available",
            "gate",
            "terminal",
        )
        list_serializer_class = FlightBulkListSerializer
        extra_kwargs = {
            "flight_number": {"validators": []}
        }

    def validate_flight_number(self, value):
        qs = Flight.objects.filter(flight_number=value, is_deleted=False)
        if self.instance is not None and not isinstance(self.instance, list):
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Flight number already exists.")
        return value

    def validate(self, attrs):
        departure_time = attrs.get("departure_time")
        arrival_time = attrs.get("arrival_time")
        total_seats = attrs.get("total_seats")
        seats_available = attrs.get("seats_available")

        if self.instance:
            departure_time = departure_time or self.instance.departure_time
            arrival_time = arrival_time or self.instance.arrival_time
            total_seats = total_seats if total_seats is not None else self.instance.total_seats
            seats_available = seats_available if seats_available is not None else self.instance.seats_available

        if departure_time and arrival_time and arrival_time <= departure_time:
            raise serializers.ValidationError(
                {"arrival_time": "Arrival time must be after departure time."}
            )

        if total_seats is not None and seats_available is not None and seats_available > total_seats:
            raise serializers.ValidationError(
                {"seats_available": "Seats available cannot exceed total seats."}
            )

        return attrs
