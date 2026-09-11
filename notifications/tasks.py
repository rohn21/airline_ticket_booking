from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone
from notifications.models import Notification, NotificationStatus, NotificationChannel
from notifications.services.email_service import EmailService

logger = get_task_logger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_notification_task(self, notification_id):
    try:
        notification = Notification.objects.select_related("user", "template").get(id=notification_id)
    except Notification.DoesNotExist:
        logger.error("Notification %s not found.", notification_id)
        return {"error": "not_found", "notification_id": notification_id}

    if notification.status == NotificationStatus.SENT:
        return {"status": "already_sent", "notification_id": notification_id}

    try:
        if notification.channel == NotificationChannel.EMAIL:
            recipient = notification.metadata.get("recipient_email") or (notification.user.email if notification.user else None)
            if not recipient:
                raise ValueError(f"No recipient email specified for notification {notification_id}")

            body_html = notification.metadata.get("body_html") or None
            EmailService.send_email(
                recipient_list=[recipient],
                subject=notification.subject,
                message=notification.body,
                html_message=body_html,
            )

        notification.status = NotificationStatus.SENT
        notification.sent_at = timezone.now()
        notification.save(update_fields=["status", "sent_at", "updated_at"])
        logger.info("Successfully sent notification %s", notification_id)
        return {"status": "sent", "notification_id": notification_id}

    except Exception as exc:
        notification.status = NotificationStatus.FAILED
        notification.save(update_fields=["status", "updated_at"])
        logger.error("Error processing notification %s: %s", notification_id, exc)
        raise exc
