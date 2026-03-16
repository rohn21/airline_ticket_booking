from rest_framework.routers import DefaultRouter
from .views import AirportViewSet, AirlineViewSet, AircraftViewSet, RouteViewSet, FlightViewSet

router = DefaultRouter()
# airports
router.register(r"airports", AirportViewSet, basename="airport")
router.register(r"airports/bulk-update/", AirportViewSet, basename="airport-update-bulk")

# airlines
router.register(r"airlines", AirlineViewSet, basename="airline")
router.register(r"airlines/bulk-update/", AirlineViewSet, basename="airline-update-bulk")

# aircrafts
router.register(r"aircrafts", AircraftViewSet, basename="aircraft")
router.register(r"aircrafts/bulk-update/", AircraftViewSet, basename="aircraft-update-bulk")

# route
router.register(r"routes", RouteViewSet, basename="route")
router.register(r"routes/bulk-update/", RouteViewSet, basename="routes-update-bulk")

# flights
router.register(r"flights", FlightViewSet, basename="flight")

urlpatterns = router.urls
