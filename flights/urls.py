from rest_framework.routers import DefaultRouter
from .views import AirportViewSet, AirlineViewSet, AircraftViewSet, RouteViewSet, FlightViewSet

router = DefaultRouter()
# airports
router.register(r"airports", AirportViewSet, basename="airport")
router.register(r"airports/bulk-update/", AirportViewSet, basename="airport-update-bulk")

# airlines
router.register(r"airlines", AirlineViewSet, basename="airline")
router.register(r"airlines/bulk-update/", AirlineViewSet, basename="airline-update-bulk")

# aircraft
router.register(r"aircrafts", AircraftViewSet, basename="aircraft")

# route
router.register(r"routes", RouteViewSet, basename="route")

# flights
router.register(r"flights", FlightViewSet, basename="flight")

urlpatterns = router.urls
