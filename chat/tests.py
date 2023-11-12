# chat/tests.py

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Message


class ChatViewTests(TestCase):
    def setUp(self):
        # Create users for testing
        self.user1 = User.objects.create_user(username="user1", password="password1")
        self.user2 = User.objects.create_user(username="user2", password="password2")

        # Create a message for testing
        self.message = Message.objects.create(
            sender=self.user1, recipient=self.user2, content="Test message"
        )

        # URL for the chat view
        self.url = reverse(
            "chats:chat-with-user", kwargs={"recipient_id": self.user2.id}
        )

    def test_chat_view_requires_authentication(self):
        # Ensure the view requires authentication
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)  # Redirect to login page

    def test_chat_view_accessible_after_authentication(self):
        # Log in user1
        self.client.login(username="user1", password="password1")

        # Ensure the view is accessible after authentication
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_chat_view_displays_messages(self):
        # Log in user1
        self.client.login(username="user1", password="password1")

        # Ensure the view displays messages
        response = self.client.get(self.url)
        self.assertContains(response, "Test message")

    def test_chat_post_form_creates_message(self):
        # Log in user1
        self.client.login(username="user1", password="password1")

        # Ensure posting the form creates a new message
        response = self.client.post(self.url, {"message": "New test message"})
        self.assertEqual(response.status_code, 302)  # Redirect after successful post

        # Verify that the new message exists in the database
        new_message = Message.objects.get(content="New test message")
        self.assertEqual(new_message.sender, self.user1)
        self.assertEqual(new_message.recipient, self.user2)

    def test_chat_post_form_redirects_correctly(self):
        # Log in user1
        self.client.login(username="user1", password="password1")

        # Ensure posting the form redirects to the correct chat page
        response = self.client.post(self.url, {"message": "Another message"})
        self.assertEqual(response.status_code, 302)  # Redirect after successful post
        expected_redirect_url = reverse(
            "chats:chat-with-user", kwargs={"recipient_id": self.user2.id}
        )
        self.assertRedirects(response, expected_redirect_url)
