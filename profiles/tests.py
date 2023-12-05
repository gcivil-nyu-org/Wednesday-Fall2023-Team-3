# profiles/tests.py
from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import UserProfile, save_user_profile
from events.models import Event, Location
from .forms import ProfileForm
from django.utils import timezone
from datetime import timedelta
from datetime import datetime
import pytz
from .models import UserFriends
from .constants import (
    PENDING,
    APPROVED,
    WITHDRAWN,
    REJECTED,
    REMOVED,
)


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
        response = self.client.get(
            reverse("profiles:view_profile", args=[self.user_profile.pk])
        )

        # Check if the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)

        # Check if the correct user profile and events are in the context
        self.assertEqual(response.context["user_profile"], self.user_profile)
        self.assertIn(self.event, response.context["events"])

        # Check if the correct template is used
        self.assertTemplateUsed(response, "profiles/view_profile.html")

    def test_view_profile_with_nonexistent_user(self):
        # Access the view_profile page with an invalid userprofile_id
        response = self.client.get(reverse("profiles:view_profile", args=[999]))

        # Check if the response status code is 404 (Not Found)
        self.assertEqual(response.status_code, 302)

    def test_view_profile_requires_login(self):
        # Log out the user
        self.client.logout()

        # Access the view_profile page without logging in
        response = self.client.get(
            reverse("profiles:view_profile", args=[self.user_profile.pk])
        )

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

    def test_user_profile_string_representation(self):
        # Check if a profile already exists for the user
        existing_profile = UserProfile.objects.filter(user=self.user).first()

        if existing_profile:
            user_profile = existing_profile
        else:
            user_profile = UserProfile.objects.create(user=self.user, bio="Test Bio")

        self.assertEqual(str(user_profile), "testuser")

    def test_save_user_profile_creates_profile(self):
        # The UserProfile should be created automatically when the User is created
        user_profile = UserProfile.objects.get(user=self.user)

        user_profile

        # Check that the UserProfile has been created
        self.assertTrue(UserProfile.objects.filter(user=self.user).exists())

    def test_save_user_profile_does_not_create_duplicate_profiles(self):
        # The UserProfile should be created automatically when the User is created
        user_profile_instance = UserProfile.objects.get(user=self.user)

        user_profile_instance

        # Try to create another UserProfile, but it should not create a duplicate
        UserProfile.objects.get_or_create(user=self.user)

        # Check that only one UserProfile has been created
        self.assertEqual(UserProfile.objects.filter(user=self.user).count(), 1)


class UserProfileSaveTest(TestCase):
    def test_save_user_profile_when_profile_does_not_exist(self):
        user = User.objects.create(username="testuser")

        # Simulate a post_save signal by calling the save_user_profile method
        try:
            save_user_profile(sender=User, instance=user)
        except UserProfile.DoesNotExist:
            pass  # Catch the exception and proceed

        # Retrieve the UserProfile for the user
        user_profile = UserProfile.objects.get(user=user)

        # Assert that the UserProfile has been created
        self.assertIsNotNone(user_profile)
        self.assertEqual(user_profile.user, user)

    def test_save_user_profile_when_profile_exists(self):
        user = User.objects.create(username="existing_user")

        # Simulate a post_save signal by calling the save_user_profile method
        try:
            save_user_profile(sender=User, instance=user)
        except UserProfile.DoesNotExist:
            pass  # Catch the exception and proceed

        # Retrieve the UserProfile for the user
        user_profile = UserProfile.objects.get(user=user)

        # Assert that the existing UserProfile is not affected
        self.assertIsNotNone(user_profile)
        self.assertEqual(user_profile.user, user)


class SendFriendRequestTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.friend = User.objects.create_user(
            username="testcreator", password="testpassword"
        )
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
        if not hasattr(self.friend, "userprofile"):
            # Create a new user profile
            self.friend_profile = UserProfile.objects.create(
                user=self.friend,
                bio="Test Bio",
                # Add other required fields as needed
            )
        else:
            # Use the existing user profile
            self.friend_profile = self.friend.userprofile
        self.client = Client()

    def test_toggle_friend_request_create(self):
        self.client.login(username="testuser", password="testpassword")
        url = reverse("profiles:toggle-friend-request", args=[self.friend_profile.id])
        # Initially, the user has not been added as a friend
        response = self.client.post(url)
        # Check that the UserFriends was created with the status 'pending'
        friend_request = UserFriends.objects.get(
            user=self.user, friends=self.friend_profile
        )
        self.assertEqual(friend_request.status, PENDING)
        # Make the POST request again to toggle the status to 'withdrawn'
        response = self.client.post(url)
        # Fetch the updated join object and check its status
        friend_request.refresh_from_db()
        self.assertEqual(friend_request.status, WITHDRAWN)
        self.client.post(url)
        friend_request.refresh_from_db()
        self.assertEqual(friend_request.status, PENDING)
        # Check the response to ensure the user is redirected to the event detail page
        self.assertRedirects(
            response, reverse("profiles:view_profile", args=[self.friend_profile.id])
        )

    def test_toggle_send_friend_request_to_oneself(self):
        self.client.logout()
        # The URL to which the request to user is sent
        url = reverse("profiles:toggle-friend-request", args=[self.user_profile.id])
        self.client.login(username="testcreator", password="testpassword")
        # Attempt to send a friend request to your own user profile
        self.client.post(url)
        # Now check if an UserFriends record exists for the user
        # We expect this to be False, as the user should not be able to send a friend request to oneself
        self.assertFalse(
            UserFriends.objects.filter(
                user=self.user, friends=self.user_profile
            ).exists()
        )

    def test_friend_request_str_representation(self):
        friend_request = UserFriends.objects.create(
            user=self.user, friends=self.friend_profile
        )
        expected_str = f"{self.user.username} - {self.friend_profile.user} - {friend_request.get_status_display()}"
        self.assertEqual(str(friend_request), expected_str)


class FriendRequestManageTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.friend = User.objects.create_user(
            username="testcreator", password="testpassword"
        )
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
        if not hasattr(self.friend, "userprofile"):
            # Create a new user profile
            self.friend_profile = UserProfile.objects.create(
                user=self.friend,
                bio="Test Bio",
                # Add other required fields as needed
            )
        else:
            # Use the existing user profile
            self.friend_profile = self.friend.userprofile
        self.client = Client()

    def test_user_not_found_approve(self):
        UserFriends.objects.create(
            user=self.user, friends=self.friend_profile, status=PENDING
        )
        self.client.login(username="testcreator", password="testpassword")
        url = reverse("profiles:approve-request", args=[202, self.user.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_approve_friend_request(self):
        friend_request = UserFriends.objects.create(
            user=self.user, friends=self.friend_profile, status=PENDING
        )
        self.client.login(username="testcreator", password="testpassword")
        url = reverse(
            "profiles:approve-request", args=[self.friend_profile.id, self.user.id]
        )
        response = self.client.post(url)
        friend_request.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(friend_request.status, APPROVED)

    def test_reject_friend_request(self):
        self.client.logout()
        friend_request = UserFriends.objects.create(
            user=self.user, friends=self.friend_profile, status=PENDING
        )
        UserFriends.objects.create(
            user=self.friend_profile.user, friends=self.user_profile, status=PENDING
        )
        self.client.login(username="testcreator", password="testpassword")
        url = reverse(
            "profiles:reject-request", args=[self.friend_profile.id, self.user.id]
        )
        response = self.client.post(url)
        friend_request.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(friend_request.status, REJECTED)


class FriendRemoveTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.friend = User.objects.create_user(
            username="testcreator", password="testpassword"
        )
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
        if not hasattr(self.friend, "userprofile"):
            # Create a new user profile
            self.friend_profile = UserProfile.objects.create(
                user=self.friend,
                bio="Test Bio",
                # Add other required fields as needed
            )
        else:
            # Use the existing user profile
            self.friend_profile = self.friend.userprofile
        self.client = Client()

    def test_remove_friend(self):
        friend_request = UserFriends.objects.create(
            user=self.user, friends=self.friend_profile, status=APPROVED
        )
        user_request = UserFriends.objects.create(
            user=self.friend_profile.user, friends=self.user_profile, status=APPROVED
        )
        self.client.login(username="testcreator", password="testpassword")
        url = reverse(
            "profiles:remove-approved-request",
            args=[self.friend_profile.id, self.user.id],
        )
        response = self.client.post(url)
        friend_request.refresh_from_db()
        user_request.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(friend_request.status, REMOVED)
        self.assertEqual(user_request.status, REMOVED)
