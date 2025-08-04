from django.urls import path, include
from accounts.views import ProfileDetailUpdateView


urlpatterns = [
    path("auth/", include("dj_rest_auth.urls")),
    path("auth/registration/", include("dj_rest_auth.registration.urls")),
    path("me/", ProfileDetailUpdateView.as_view(), name="account-profile"),
]