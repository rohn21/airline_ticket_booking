from rest_framework.routers import DefaultRouter
from notifications.views import NotificationViewSet, NotificationTemplateViewSet

router = DefaultRouter()
router.register(r"notifications", NotificationViewSet, basename="notification")
router.register(r"notification-templates", NotificationTemplateViewSet, basename="notification-template")

urlpatterns = router.urls
