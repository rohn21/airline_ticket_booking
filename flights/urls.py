from rest_framework.routers import DefaultRouter
from .views import AirportViewSet, AirlineViewSet, AircraftViewSet, RouteViewSet, FlightViewSet

router = DefaultRouter()
router.register(r"airports", AirportViewSet, basename="airport")
router.register(r"airlines", AirlineViewSet, basename="airline")
router.register(r"aircrafts", AircraftViewSet, basename="aircraft")
router.register(r"routes", RouteViewSet, basename="route")
router.register(r"flights", FlightViewSet, basename="flight")

urlpatterns = router.urls
