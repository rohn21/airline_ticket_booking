from django.contrib import admin
from notifications.models import Notification, NotificationTemplate


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ("code", "channel", "subject", "created_at")
    list_filter = ("channel",)
    search_fields = ("code", "subject")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "channel", "subject", "status", "sent_at", "read_at", "created_at")
    list_filter = ("channel", "status")
    search_fields = ("subject", "body", "user__email")
