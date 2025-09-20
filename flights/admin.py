from django.contrib import admin
from .models import Airport, Airline, Aircraft, Route, Flight, FareClass, FareRule

@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "city", "country")
    search_fields = ("name", "code", "city", "country")

@admin.register(Airline)
class AirlineAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "country")
    search_fields = ("name", "code")

@admin.register(Aircraft)
class AircraftAdmin(admin.ModelAdmin):
    list_display = ("model", "registration", "seat_capacity")

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ("origin", "destination", "flight_type", "code")
    list_filter = ("flight_type",)

@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = ("flight_number", "airline", "route", "departure_time", "status", "seats_available")
    list_filter = ("airline", "status", "route__flight_type")
    search_fields = ("flight_number",)

@admin.register(FareClass)
class FareClassAdmin(admin.ModelAdmin):
    list_display = ("code", "name")

@admin.register(FareRule)
class FareRuleAdmin(admin.ModelAdmin):
    list_display = ("flight", "fare_class", "price", "currency", "seat_count")
