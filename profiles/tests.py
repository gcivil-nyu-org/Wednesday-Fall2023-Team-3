# profiles/tests.py
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import UserProfile
from events.models import Event, Location
from .forms import ProfileForm
from django.utils import timezone
from datetime import timedelta
from datetime import datetime


class ProfileViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.location = Location.objects.create(location_name="Test Location")

        # Check if a profile already exists for the user
        if not hasattr(self.user, "userprofile"):
            # Create a new user profile
            self.user_profile = UserProfile.objects.create(
                user=self.user,
                bio="Test Bio",
                # Add other required fields as needed
            )
        else:
            # Use the existing user profile
            self.user_profile = self.user.userprofile

        # Create event with past date for testing
        self.event = Event.objects.create(
            event_name="Test Event",
            start_time=timezone.now() - timedelta(days=1),
            end_time=timezone.now() - timedelta(days=1, hours=1),
            capacity=50,
            event_location=self.location,
            is_active=True,
            creator=self.user,
        )

    def test_view_profile(self):
        # Log in the user
        self.client.login(username="testuser", password="testpassword")

        # Access the view_profile page
        response = self.client.get(reverse("view_profile", args=[self.user_profile.pk]))

        # Check if the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)

        # Check if the correct user profile and events are in the context
        self.assertEqual(response.context["user_profile"], self.user_profile)
        self.assertIn(self.event, response.context["events"])

        # Check if the correct template is used
        self.assertTemplateUsed(response, "profiles/view_profile.html")
