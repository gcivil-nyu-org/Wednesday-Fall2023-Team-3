from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from .models import Notification


class NotificationsTests(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )

        # Create some notifications for the test user
        self.notification1 = Notification.objects.create(
            user=self.user, message="Test Notification 1"
        )
        self.notification2 = Notification.objects.create(
            user=self.user, message="Test Notification 2", is_read=True
        )

    def test_notifications_view(self):
        # Log in the test user
        self.client.login(username="testuser", password="testpassword")

        # Access the notifications view
        response = self.client.get(reverse("notifications:view-notifications"))

        # Check that the response is successful
        self.assertEqual(response.status_code, 200)

        # Update the assertion to compare Notification instances
        expected_notifications = [self.notification1, self.notification2]

        self.assertQuerysetEqual(
            response.context["notifications"], expected_notifications, ordered=False
        )

    def test_mark_notification_as_read_view(self):
        # Log in the test user
        self.client.login(username="testuser", password="testpassword")

        # Access the mark_notification_as_read view for the first notification
        response = self.client.post(
            reverse(
                "notifications:mark-notification-as-read", args=[self.notification1.id]
            )
        )

        # Check that the response redirects to the notifications view
        self.assertRedirects(response, reverse("notifications:view-notifications"))

        # Refresh the notification instance from the database
        updated_notification = Notification.objects.get(id=self.notification1.id)

        # Check that the notification is marked as read
        self.assertTrue(updated_notification.is_read)
