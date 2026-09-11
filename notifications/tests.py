from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from notifications.models import (
    Notification,
    NotificationTemplate,
    NotificationChannel,
    NotificationStatus,
)
from notifications.services.notification_service import NotificationService
from notifications.tasks import send_notification_task

User = get_user_model()


class NotificationServiceTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="Testpassword123!",
        )
        self.template = NotificationTemplate.objects.create(
            code="BOOKING_CREATED",
            channel=NotificationChannel.EMAIL,
            subject="Booking {pnr} Created",
            body_text="Your booking {pnr} for flight {flight_number} is created.",
            body_html="<p>Your booking <b>{pnr}</b> is created.</p>",
        )

    @patch("notifications.tasks.send_notification_task.delay")
    def test_notification_service_send(self, mock_task_delay):
        notification = NotificationService.send(
            user=self.user,
            event_code="BOOKING_CREATED",
            context={"pnr": "ABC123", "flight_number": "AI101"},
            reference_type="booking",
        )
        self.assertIsNotNone(notification)
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.subject, "Booking ABC123 Created")
        self.assertIn("AI101", notification.body)
        self.assertEqual(notification.status, NotificationStatus.PENDING)
        mock_task_delay.assert_called_once_with(str(notification.id))

    @patch("notifications.services.email_service.EmailService.send_email", return_value=True)
    def test_send_notification_task(self, mock_send_email):
        notification = Notification.objects.create(
            user=self.user,
            channel=NotificationChannel.EMAIL,
            subject="Test Subject",
            body="Test Body",
            status=NotificationStatus.PENDING,
            metadata={"recipient_email": "testuser@example.com"},
        )
        res = send_notification_task(str(notification.id))
        self.assertEqual(res["status"], "sent")

        notification.refresh_from_db()
        self.assertEqual(notification.status, NotificationStatus.SENT)
        self.assertIsNotNone(notification.sent_at)
        mock_send_email.assert_called_once()


class NotificationAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="apiuser@example.com",
            password="Testpassword123!",
        )
        self.other_user = User.objects.create_user(
            email="otheruser@example.com",
            password="Testpassword123!",
        )
        self.client.force_authenticate(user=self.user)

        self.notif1 = Notification.objects.create(
            user=self.user,
            subject="Notif 1",
            body="Body 1",
            status=NotificationStatus.SENT,
        )
        self.notif2 = Notification.objects.create(
            user=self.user,
            subject="Notif 2",
            body="Body 2",
            status=NotificationStatus.SENT,
        )
        self.other_notif = Notification.objects.create(
            user=self.other_user,
            subject="Other Notif",
            body="Other Body",
            status=NotificationStatus.SENT,
        )

    def test_list_notifications(self):
        url = reverse("notification-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 2)

    def test_unread_count(self):
        url = reverse("notification-unread-count")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["unread_count"], 2)

    def test_mark_as_read(self):
        url = reverse("notification-mark-as-read", kwargs={"pk": self.notif1.id})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notif1.refresh_from_db()
        self.assertEqual(self.notif1.status, NotificationStatus.READ)
        self.assertIsNotNone(self.notif1.read_at)

    def test_mark_all_as_read(self):
        url = reverse("notification-mark-all-as-read")
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.notif1.refresh_from_db()
        self.notif2.refresh_from_db()
        self.assertEqual(self.notif1.status, NotificationStatus.READ)
        self.assertEqual(self.notif2.status, NotificationStatus.READ)
