from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .forms import CustomUserCreationForm

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

class SignupViewTestCase(TestCase):
    def test_form_valid(self):
        # Test if form_valid logs in the user
        data = {
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "email": "newuser@nyu.edu",
            "password1": "securepassword123",
            "password2": "securepassword123",
        }

        response = self.client.post(reverse("signup"), data)
        self.assertEqual(
            response.status_code, 302
        )  # 302 is the HTTP status code for a redirect

        # Retrieve the user and check if they are logged in
        new_user = User.objects.get(username="newuser")
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user, new_user)

    def test_clean_email_valid(self):
        # Test if clean_email allows a valid email
        data = {
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "email": "newuser@nyu.edu",
            "password1": "securepassword123",
            "password2": "securepassword123",
        }

        form = CustomUserCreationForm(data)

        if not form.is_valid():
            print(form.errors)

        self.assertTrue(form.is_valid())

    def test_clean_email_invalid(self):
        # Test if clean_email raises ValidationError for an invalid email
        data = {
            "username": "newuser",
            "email": "newuser@example.com",  # This should be an invalid email
            "password1": "securepassword123",
            "password2": "securepassword123",
        }

        form = CustomUserCreationForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertEqual(form.errors["email"], ["Email must end with @nyu.edu"])