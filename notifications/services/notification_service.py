import logging
from django.utils import timezone
from notifications.models import (
    Notification,
    NotificationTemplate,
    NotificationChannel,
    NotificationStatus,
)

logger = logging.getLogger(__name__)


class NotificationService:
    @staticmethod
    def send(
        user=None,
        recipient_email=None,
        event_code=None,
        context=None,
        channel=NotificationChannel.EMAIL,
        reference_type="",
        reference_id=None,
        custom_subject=None,
        custom_body=None,
    ):
        context = context or {}
        subject = custom_subject or ""
        body = custom_body or ""
        body_html = ""

        template = None
        if event_code:
            try:
                template = NotificationTemplate.objects.get(code=event_code, channel=channel)
                subject = template.subject.format(**context) if template.subject else subject
                body = template.body_text.format(**context) if template.body_text else body
                body_html = template.body_html.format(**context) if template.body_html else ""
            except NotificationTemplate.DoesNotExist:
                logger.warning("NotificationTemplate with code '%s' and channel '%s' not found.", event_code, channel)

        metadata = {
            "recipient_email": recipient_email or (user.email if user else None),
            "event_code": event_code,
            "context": context,
            "body_html": body_html,
        }

        notification = Notification.objects.create(
            user=user,
            channel=channel,
            template=template,
            subject=subject,
            body=body,
            status=NotificationStatus.PENDING,
            reference_type=reference_type,
            reference_id=reference_id,
            metadata=metadata,
        )

        from notifications.tasks import send_notification_task
        send_notification_task.delay(str(notification.id))

        return notification
