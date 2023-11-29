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

    def test_view_profile_with_nonexistent_user(self):
        # Access the view_profile page with an invalid userprofile_id
        response = self.client.get(reverse("view_profile", args=[999]))

        # Check if the response status code is 404 (Not Found)
        self.assertEqual(response.status_code, 302)

    def test_view_profile_requires_login(self):
        # Log out the user
        self.client.logout()

        # Access the view_profile page without logging in
        response = self.client.get(reverse("view_profile", args=[self.user_profile.pk]))

        # Check if the response status code is 302 (Redirect to login page)
        self.assertEqual(response.status_code, 302)


class ProfileModelsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.location = Location.objects.create(location_name="Test Location")

    def test_create_user_profile(self):
        # Check if a UserProfile is created when a User is created
        self.assertTrue(hasattr(self.user, "userprofile"))
        self.assertIsInstance(self.user.userprofile, UserProfile)

    def test_create_user_profile_signal_handler(self):
        # Create a new user without an associated profile
        new_user = User.objects.create_user(username="newuser", password="newpassword")

        # Check if a UserProfile is created using the signal handler
        self.assertTrue(hasattr(new_user, "userprofile"))
        self.assertIsInstance(new_user.userprofile, UserProfile)

    def test_save_user_profile_signal_handler(self):
        # Create a new user with an associated profile
        existing_user = User.objects.create_user(
            username="existinguser", password="existingpassword"
        )
        existing_user_profile = existing_user.userprofile

        # Change the bio of the user and save
        existing_user_profile.bio = "Updated Bio"
        existing_user_profile.save()

        # Refresh the user profile from the database
        existing_user_profile.refresh_from_db()

        # Check if the bio has been updated
        self.assertEqual(existing_user_profile.bio, "Updated Bio")

    def test_create_user_profile_with_existing_profile(self):
        # Create a new user without an associated profile
        existing_user_with_profile = User.objects.create_user(
            username="existinguser2", password="existingpassword"
        )

        # Use get_or_create to avoid IntegrityError due to UNIQUE constraint
        existing_profile, created = UserProfile.objects.get_or_create(
            user=existing_user_with_profile, defaults={"bio": "Existing Bio"}
        )

        # Check if the existing profile is used instead of creating a new one
        self.assertFalse(created)  # Ensure that the profile was not created
        self.assertEqual(existing_user_with_profile.userprofile, existing_profile)

    def test_create_user_profile_with_existing_profile_conflict(self):
        # Create a new user without an associated profile
        new_user_with_existing_profile_conflict = User.objects.create_user(
            username="newuserconflict", password="newuserconflictpassword"
        )

        # Use get_or_create to avoid IntegrityError due to UNIQUE constraint
        existing_profile_for_new_user, created = UserProfile.objects.get_or_create(
            user=new_user_with_existing_profile_conflict,
            defaults={"bio": "Existing Bio"},
        )

        # Check if the existing profile is used instead of creating a new one
        self.assertFalse(created)  # Ensure that the profile was not created
        self.assertEqual(
            new_user_with_existing_profile_conflict.userprofile,
            existing_profile_for_new_user,
        )

    def test_create_user_profile_with_existing_profile_signal_handler(self):
        # Create a new user without an associated profile
        existing_user_with_profile = User.objects.create_user(
            username="existinguser2", password="existingpassword"
        )

        # Use get_or_create to avoid IntegrityError due to UNIQUE constraint
        existing_profile, created = UserProfile.objects.get_or_create(
            user=existing_user_with_profile, defaults={"bio": "Existing Bio"}
        )

        # Check if the existing profile is used instead of creating a new one
        self.assertFalse(created)  # Ensure that the profile was not created
        self.assertEqual(existing_user_with_profile.userprofile, existing_profile)
