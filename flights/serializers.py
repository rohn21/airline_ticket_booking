from rest_framework import serializers
from .models import Airport, Airline, Aircraft, Route, Flight, FareClass, FareRule


class AirportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = ("id", "name", "code", "city", "country")


class AirlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airline
        fields = ("id", "name", "code", "country")


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
