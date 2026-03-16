from django.urls import path, include

urlpatterns = [
    # path("", include("travel_core.urls")),
    path("", include("flights.urls")),
    path("", include("accounts.urls")),
    # path("", include("bookings.urls")),
    # path("", include("payments.urls")),
]
