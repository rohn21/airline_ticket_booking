from django.utils import timezone
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response

from notifications.models import Notification, NotificationTemplate, NotificationStatus
from notifications.serializers import NotificationSerializer, NotificationTemplateSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["subject", "body", "reference_type"]

    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user,
            is_deleted=False
        ).order_by("-created_at")

    @action(detail=True, methods=["patch"], url_path="read")
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        if not notification.read_at:
            notification.read_at = timezone.now()
            notification.status = NotificationStatus.READ
            notification.save(update_fields=["read_at", "status", "updated_at"])
        serializer = self.get_serializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="read-all")
    def mark_all_as_read(self, request):
        now = timezone.now()
        count = self.get_queryset().filter(read_at__isnull=True).update(
            read_at=now,
            status=NotificationStatus.READ,
            updated_at=now,
        )
        return Response({"detail": f"Marked {count} notifications as read."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        count = self.get_queryset().filter(read_at__isnull=True).count()
        return Response({"unread_count": count}, status=status.HTTP_200_OK)


class NotificationTemplateViewSet(viewsets.ModelViewSet):
    queryset = NotificationTemplate.objects.filter(is_deleted=False)
    serializer_class = NotificationTemplateSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [filters.SearchFilter]
    search_fields = ["code", "subject", "channel"]
