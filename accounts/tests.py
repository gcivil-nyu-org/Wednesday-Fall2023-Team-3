from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User


class LoginViewTestCase(TestCase):
    def setUp(self):
        # Create a user for testing login
        self.username = "testuser"
        self.password = "securepassword123"
        User.objects.create_user(
            self.username, email="test@example.com", password=self.password
        )

    def test_login_page_renders(self):
        # Test if login page renders correctly
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/login.html")

    def test_form_displayed(self):
        # Test if the login form is in the context
        response = self.client.get(reverse("login"))
        self.assertIn("form", response.context)
