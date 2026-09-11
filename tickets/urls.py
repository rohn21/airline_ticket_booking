from django.urls import path
from tickets.views import TicketDownloadView, TicketQRView

urlpatterns = [
    path("tickets/<str:pnr>/download/", TicketDownloadView.as_view(), name="ticket-download"),
    path("tickets/<str:pnr>/qr/", TicketQRView.as_view(), name="ticket-qr"),
]
