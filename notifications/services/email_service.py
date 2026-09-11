import logging
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


class EmailService:
    @staticmethod
    def send_email(recipient_list, subject, message, html_message=None):
        try:
            from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@airline.com")
            sent_count = send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=recipient_list,
                html_message=html_message,
                fail_silently=False,
            )
            logger.info("Email sent to %s. Subject: %s", recipient_list, subject)
            return sent_count > 0
        except Exception as e:
            logger.error("Failed to send email to %s: %s", recipient_list, str(e))
            raise e
