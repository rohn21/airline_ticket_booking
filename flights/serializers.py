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


class AircraftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aircraft
        fields = ("id", "model", "registration", "seat_capacity")


class RouteSerializer(serializers.ModelSerializer):
    origin = AirportSerializer()
    destination = AirportSerializer()

    class Meta:
        model = Route
        fields = ("id", "code", "origin", "destination", "flight_type", "distance_km", "estimated_duration")


class FareRuleSerializer(serializers.ModelSerializer):
    fare_class = serializers.StringRelatedField()

    class Meta:
        model = FareRule
        fields = ("id", "fare_class", "price", "currency", "refundable", "baggage_allowance_kg", "seat_count")


class FlightSerializer(serializers.ModelSerializer):
    airline = AirlineSerializer()
    route = RouteSerializer()
    aircraft = AircraftSerializer()
    fare_rules = FareRuleSerializer(many=True, read_only=True)

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
