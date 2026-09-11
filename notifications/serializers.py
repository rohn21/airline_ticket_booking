from rest_framework import serializers
from notifications.models import Notification, NotificationTemplate


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = (
            "id",
            "channel",
            "subject",
            "body",
            "status",
            "sent_at",
            "read_at",
            "reference_type",
            "reference_id",
            "metadata",
            "created_at",
        )
        read_only_fields = fields


class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = (
            "id",
            "code",
            "channel",
            "subject",
            "body_text",
            "body_html",
            "created_at",
            "updated_at",
        )
