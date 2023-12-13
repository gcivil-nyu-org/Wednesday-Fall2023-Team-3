from django.test import TestCase, Client
from django.urls import reverse
from .models import (
    Event,
    Location,
    EventJoin,
    Comment,
    Notification,
    Reaction,
    FavoriteLocation,
)
from profiles.models import UserFriends, UserProfile
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from datetime import datetime
import json
import pytz
from .constants import (
    PENDING,
    APPROVED,
    WITHDRAWN,
    REJECTED,
    REMOVED,
    CHEER_UP,
    HEART,
    SMALL_CAPACITY,
    MEDIUM_CAPACITY,
    LARGE_CAPACITY,
)

from tags.models import Tag
from django.contrib.messages import get_messages


class EventIndexViewCapacityFilterTest(TestCase):
    def setUp(self):
        # Set up user and location
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.location = Location.objects.create(location_name="Test Location")

        # Create events with varying capacities
        self.event_low_capacity = Event.objects.create(
            event_name="Low Capacity Event",
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=2),
            capacity=10,
            event_location=self.location,
            is_active=True,
            creator=self.user,
        )

        self.event_high_capacity = Event.objects.create(
            event_name="High Capacity Event",
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=2),
            capacity=60,
            event_location=self.location,
            is_active=True,
            creator=self.user,
        )

    def test_event_index_view_with_inverted_capacity_filter(self):
        # Filter with minimum capacity higher than maximum capacity
        min_capacity = 150
        max_capacity = 50

        url = reverse("events:index")
        response = self.client.get(
            url, {"min_capacity": min_capacity, "max_capacity": max_capacity}
        )
        # Check if the error message is as expected
        self.assertEqual(
            response.context.get("error"),
            "Minimum capacity cannot be greater than maximum capacity.",
        )

    def test_event_index_view_with_valid_capacity_filter(self):
        # Filter with a valid range where min_capacity is less than max_capacity
        min_capacity = 20
        max_capacity = 120

        url = reverse("events:index")
        response = self.client.get(
            url, {"min_capacity": min_capacity, "max_capacity": max_capacity}
        )

        # Check that only events within the specified capacity range are in the context
        self.assertIn(self.event_high_capacity, response.context.get("events", []))
        self.assertNotIn(self.event_low_capacity, response.context.get("events", []))

        # Check if there is no error message
        self.assertIsNone(response.context.get("error", None))

        # Additionally, check if the form is valid
        self.assertTrue(response.context.get("form").is_valid())

    def test_reset_filters_redirects(self):
        min_capacity = 20
        max_capacity = 120
        url = reverse("events:index")
        self.client.get(
            url, {"min_capacity": min_capacity, "max_capacity": max_capacity}
        )

        reset_response = self.client.get(url, {"reset_filters": "1"}, follow=True)
        self.assertRedirects(reset_response, reverse("events:index"))
        fresh_response = self.client.get(url)

        all_events = Event.objects.filter(is_active=True).order_by("-start_time")
        self.assertEqual(
            len(fresh_response.context.get("events", [])), all_events.count()
        )
        self.assertIsNone(fresh_response.context.get("error", None))


class EventIndexViewFilterNegativeTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.location = Location.objects.create(location_name="Test Location")

        # Create event with past date for testing
        self.past_event = Event.objects.create(
            event_name="Past Event",
            start_time=timezone.now() - timedelta(days=1),
            end_time=timezone.now() - timedelta(days=1, hours=1),
            capacity=50,
            event_location=self.location,
            is_active=True,
            creator=self.user,
        )

    def test_event_index_view_with_past_start_time_filter(self):
        # Attempt to filter events with a start time that is in the past
        past_start_date_str = (timezone.now() - timedelta(days=1)).strftime(
            "%Y-%m-%dT%H:%M"
        )
        url = reverse("events:index")
        response = self.client.get(url, {"start_time": past_start_date_str})
        self.assertNotIn(self.past_event, response.context.get("events", []))
        # Assuming your error message is passed to the template under the context variable 'error'
        self.assertEqual(
            response.context.get("error"), "Start time cannot be in the past."
        )

    def test_filter_events_based_on_favorite_locations(self):
        # Simulate a POST request with form data
        form_data = {
            "favorite_location_events": True  # Simulate the checkbox value
            # Add other form data as needed
        }

        # Authenticate the user in the test client
        self.client.login(username="testuser", password="testpassword")

        # Make a POST request to your view
        response = self.client.post(reverse("events:index"), data=form_data)

        # Check if the response status is 200 (or any other expected status)
        self.assertEqual(response.status_code, 200)


class UpdateEventViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.location = Location.objects.create(location_name="Test Location")
        new_york_tz = pytz.timezone("America/New_York")
        current_time_ny = datetime.now(new_york_tz)
        start_time = current_time_ny + timezone.timedelta(hours=1)
        end_time = current_time_ny + timezone.timedelta(hours=2)
        start_time = start_time.strftime("%Y-%m-%dT%H:%M")
        end_time = end_time.strftime("%Y-%m-%dT%H:%M")
        self.event = Event.objects.create(
            event_name="Test Event",
            start_time=start_time,
            end_time=end_time,
            capacity=100,
            event_location=self.location,
            creator=self.user,
            description="Initial Test Event Description",
        )

    def test_update_event_view_get(self):
        self.client.login(username="testuser", password="testpassword")
        url = reverse("events:update-event", args=(self.event.id,))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Event")  # Replace with expected content

    def test_update_event_view_post(self):
        new_location = Location.objects.create(location_name="New Location")
        new_york_tz = pytz.timezone("America/New_York")
        current_time_ny = datetime.now(new_york_tz)
        start_time = current_time_ny + timezone.timedelta(hours=1)
        end_time = current_time_ny + timezone.timedelta(hours=2)
        start_time = start_time.strftime("%Y-%m-%dT%H:%M")
        end_time = end_time.strftime("%Y-%m-%dT%H:%M")
        updated_data = {
            "event_name": "Updated Event",
            "start_time": start_time,
            "end_time": end_time,
            "capacity": 150,
            "event_location_id": new_location.id,
            "description": "This is an updated description.",
        }
        url = reverse("events:update-event", args=(self.event.id,))
        self.client.login(username="testuser", password="testpassword")
        self.client.post(url, updated_data)
        self.assertEqual(
            Event.objects.get(pk=self.event.id).event_name, "Updated Event"
        )  # Verify data was updated

    def test_other_user_cannot_update_event(self):
        User.objects.create_user(username="anotheruser", password="testpassword")
        self.client.login(username="anotheruser", password="testpassword")
        url = reverse("events:update-event", args=(self.event.id,))
        response = self.client.post(url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            "You're not allowed to update this event.",
        )
        self.assertRedirects(response, reverse("events:index"))

    def test_update_event_capacity_too_low(self):
        self.client.login(username="testuser", password="testpassword")

        # Set up approved participants
        for i in range(10):  # Assuming 10 participants have joined
            user = User.objects.create_user(
                username=f"user{i}", password="testpassword"
            )
            EventJoin.objects.create(user=user, event=self.event, status=APPROVED)

        # Prepare update data with a capacity lower than the number of approved participants
        updated_data = {
            "event_name": "Updated Event",
            "start_time": self.event.start_time,
            "end_time": self.event.end_time,
            "capacity": 5,  # Less than the 10 approved participants
            "event_location_id": self.location.id,
        }

        # Perform the update
        url = reverse("events:update-event", args=(self.event.id,))
        response = self.client.post(url, updated_data, follow=True)
        # Assert the response status code if you expect a 200 from a template render or a 302 from a redirect
        self.assertEqual(response.status_code, 400)

        # Check for error message in response
        error_message = (
            "Capacity cannot be less than the number of approved participants"
        )
        self.assertEqual(response["Content-Type"], "application/json")
        content = json.loads(response.content)
        self.assertEqual(
            content["capacity"],
            error_message,
        )  # Replace with expected content


class DuplicateEventTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.location = Location.objects.create(
            location_name="Test Location",
        )
        new_york_tz = pytz.timezone("America/New_York")
        current_time_ny = datetime.now(new_york_tz)
        start_time = current_time_ny + timezone.timedelta(hours=1)
        end_time = current_time_ny + timezone.timedelta(hours=2)
        self.start_time = start_time.strftime("%Y-%m-%dT%H:%M")
        self.end_time = end_time.strftime("%Y-%m-%dT%H:%M")
        self.event = Event.objects.create(
            event_name="Test Event",
            event_location=self.location,
            start_time=self.start_time,
            end_time=self.end_time,
            capacity=100,
            is_active=True,
            creator=self.user,
        )
        self.event2 = Event.objects.create(
            event_name="Test Event2",
            event_location=self.location,
            start_time=self.start_time,
            end_time=self.end_time,
            capacity=100,
            is_active=True,
            creator=self.user,
        )

    def test_update_event_with_duplicate_data(self):
        self.client.login(username="testuser", password="testpassword")
        existing_event = Event.objects.get(pk=self.event.id)
        existing_event2 = Event.objects.get(pk=self.event2.id)
        response = self.client.post(
            reverse("events:update-event", args=[existing_event2.id]),
            {
                "event_location_id": self.location.id,
                "event_name": existing_event.event_name,
                "start_time": self.start_time,
                "end_time": self.end_time,
                "capacity": 100,
            },
        )
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.status_code, 400)  # Should stay on the same page
        content = json.loads(response.content)
        self.assertEqual(
            content["similar_event_error"],
            "An event with these details already exists.",
        )  # Replace with expected content

    def test_create_event_with_duplicate_data(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.post(
            reverse("events:save-event"),
            {
                "event_location_id": self.location.id,  # Missing event location
                "event_name": "Test Event",  # Missing event name
                "start_time": self.start_time,  # Missing start time
                "end_time": self.end_time,  # Missing end time
                "capacity": 10,
                "creator": self.user,
            },
        )
        self.assertEqual(response.status_code, 302)  # Should stay on the same page
        self.assertIn(
            r"An%20event%20with%20these%20details%20already%20exists.", response.url
        )  # Should stay on the same page


class EventDetailPageTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.location = Location.objects.create(
            location_name="Test Location",
        )
        new_york_tz = pytz.timezone("America/New_York")
        current_time_ny = datetime.now(new_york_tz)
        start_time = current_time_ny + timezone.timedelta(hours=1)
        end_time = current_time_ny + timezone.timedelta(hours=2)
        start_time = start_time.strftime("%Y-%m-%dT%H:%M")
        end_time = end_time.strftime("%Y-%m-%dT%H:%M")
        self.event = Event.objects.create(
            event_name="Test Event",
            event_location=self.location,
            start_time=start_time,
            end_time=end_time,
            capacity=100,
            is_active=True,
            creator=self.user,
            description="This is a test description.",
        )

    def test_event_detail_view(self):
        url = reverse("events:event-detail", args=(self.event.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Event")
        self.assertContains(response, "Test Location")
        self.assertContains(response, "100")
        self.assertContains(response, "testuser")
        self.assertContains(response, self.event.description)

    def test_share_event_button(self):
        response = self.client.get(
            reverse("events:event-detail", args=(self.event.id,))
        )
        self.assertContains(response, "Share Event")
        self.assertContains(response, "function copyEventUrl()")
        self.assertContains(response, 'onclick="copyEventUrl()"')


class MapGetDataTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.location1 = Location.objects.create(location_name="Test Location 1")
        self.location2 = Location.objects.create(location_name="Test Location 2")
        self.event1 = Event.objects.create(
            event_name="Test Event",
            start_time="2023-11-01T12:00",
            end_time="2023-11-01T14:00",
            capacity=100,
            is_active=True,
            event_location=self.location1,
            creator=self.user,
        )
        self.event1 = Event.objects.create(
            event_name="Test Event 2",
            start_time="2023-11-01T12:00",
            end_time="2023-11-01T14:00",
            capacity=100,
            is_active=False,
            event_location=self.location2,
            creator=self.user,
        )

    def test_get_events_view(self):
        response = self.client.get(reverse("events:events"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("location_data", data)

        # Check the content of the location_data
        location_data = data["location_data"]
        self.assertEqual(len(location_data), 1)

    def test_get_location_view(self):
        response = self.client.get(
            reverse("events:locations")
        )  # Replace "get_locations" with your actual URL name

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Check the JSON response structure
        self.assertIn("locations", data)

        # Check the content of the locations
        locations = data["locations"]
        self.assertEqual(len(locations), 2)


class EventJoinRequestTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.creator = User.objects.create_user(
            username="testcreator", password="testpassword"
        )
        self.location = Location.objects.create(
            location_name="Test Location",
        )
        new_york_tz = pytz.timezone("America/New_York")
        current_time_ny = datetime.now(new_york_tz)
        self.event = Event.objects.create(
            event_name="Test Event",
            event_location=self.location,
            start_time=current_time_ny + timedelta(hours=3),
            end_time=current_time_ny + timedelta(hours=5),
            capacity=10,
            is_active=True,
            creator=self.creator,
        )
        self.client = Client()

    def test_toggle_join_request_create(self):
        self.client.login(username="testuser", password="testpassword")
        url = reverse("events:toggle-join-request", args=[self.event.id])
        # Initially, the user has not joined the event
        response = self.client.post(url)
        # Check that the EventJoin was created with the status 'pending'
        join = EventJoin.objects.get(user=self.user, event=self.event)
        self.assertEqual(join.status, PENDING)
        self.assertEqual(Notification.objects.count(), 1)
        # Make the POST request again to toggle the status to 'withdrawn'
        response = self.client.post(url)
        # Fetch the updated join object and check its status
        join.refresh_from_db()
        self.assertEqual(join.status, WITHDRAWN)
        self.assertEqual(Notification.objects.count(), 2)
        # Check the response to ensure the user is redirected to the event detail page
        self.assertRedirects(
            response, reverse("events:event-detail", args=[self.event.id])
        )

    def test_creator_cannot_join_own_event(self):
        self.client.logout()
        # The URL to which the request to join an event is sent
        url = reverse("events:toggle-join-request", args=[self.event.id])
        self.client.login(username="testcreator", password="testpassword")
        # Attempt to create an EventJoin record as the creator
        response = self.client.post(url)
        # Now check if an EventJoin record exists for the creator and this event
        # We expect this to be False, as the creator should not be able to join their own event
        self.assertFalse(
            EventJoin.objects.filter(user=self.creator, event=self.event).exists()
        )
        # For example, if you have a condition to redirect the user with an error:
        self.assertEqual(
            response.status_code, 302
        )  # or 403 if you handle it as forbidden

    def test_event_join_str_representation(self):
        event_join = EventJoin.objects.create(user=self.user, event=self.event)
        expected_str = f"{self.user.username} - {self.event.event_name} - {event_join.get_status_display()}"
        self.assertEqual(str(event_join), expected_str)


class EventCreatorManageRequestTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.creator = User.objects.create_user(
            username="testcreator", password="testpassword"
        )
        self.location = Location.objects.create(
            location_name="Test Location",
        )
        new_york_tz = pytz.timezone("America/New_York")
        current_time_ny = datetime.now(new_york_tz)
        self.event = Event.objects.create(
            event_name="Test Event",
            event_location=self.location,
            start_time=current_time_ny + timedelta(hours=12),
            end_time=current_time_ny + timedelta(hours=15),
            capacity=5,
            is_active=True,
            creator=self.creator,
        )
        self.join_request = EventJoin.objects.create(user=self.user, event=self.event)
        self.client = Client()

    def test_approve_join_request(self):
        self.client.login(username="testcreator", password="testpassword")
        url = reverse("events:approve-request", args=[self.event.id, self.user.id])
        response = self.client.post(url)
        self.join_request.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(self.join_request.status, APPROVED)

    def test_reject_join_request(self):
        self.client.login(username="testcreator", password="testpassword")
        url = reverse("events:reject-request", args=[self.event.id, self.user.id])
        response = self.client.post(url)
        self.join_request.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(self.join_request.status, REJECTED)

    def test_non_creator_cannot_approve(self):
        self.client.logout()
        self.client.login(username="testuser", password="testpassword")
        url = reverse("events:approve-request", args=[self.event.id, self.user.id])
        response = self.client.post(url)
        self.join_request.refresh_from_db()
        self.assertNotEqual(self.join_request.status, APPROVED)
        self.assertEqual(response.status_code, 302)  # redirect

    def test_non_creator_cannot_reject(self):
        self.client.logout()
        self.client.login(username="testuser", password="testpassword")
        url = reverse("events:reject-request", args=[self.event.id, self.user.id])
        response = self.client.post(url)
        self.join_request.refresh_from_db()
        self.assertNotEqual(self.join_request.status, REJECTED)
        self.assertEqual(response.status_code, 302)


class EventCreatorApproveLimistTest(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            username="testcreator", password="testpassword"
        )
        self.location = Location.objects.create(
            location_name="Test Location",
        )
        new_york_tz = pytz.timezone("America/New_York")
        current_time_ny = datetime.now(new_york_tz)
        self.event = Event.objects.create(
            event_name="Test Event",
            event_location=self.location,
            start_time=current_time_ny + timedelta(hours=4),
            end_time=current_time_ny + timedelta(hours=5),
            capacity=5,
            is_active=True,
            creator=self.creator,
        )
        self.users = [
            User.objects.create_user(f"user{i}", f"testuser{i}", "testpassword")
            for i in range(5)
        ]
        self.join_requests = [
            EventJoin.objects.create(user=self.users[i], event=self.event)
            for i in range(5)
        ]
        self.client = Client()

    def test_creator_approve_limit(self):
        self.client.logout()
        self.client.login(username="testcreator", password="testpassword")
        for i in range(5):
            url = reverse(
                "events:approve-request", args=[self.event.id, self.users[i].id]
            )
            response = self.client.post(url)
            self.join_requests[i].refresh_from_db()
            self.assertEqual(response.status_code, 302)
            if i < self.event.capacity - 1:
                self.assertEqual(self.join_requests[i].status, APPROVED)
            else:
                self.assertEqual(self.join_requests[i].status, PENDING)


class EventCreatorRemoveApprovedRequestTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.creator = User.objects.create_user(
            username="testcreator", password="testpassword"
        )
        self.location = Location.objects.create(
            location_name="Test Location",
        )
        new_york_tz = pytz.timezone("America/New_York")
        current_time_ny = datetime.now(new_york_tz)
        self.event = Event.objects.create(
            event_name="Test Event",
            event_location=self.location,
            start_time=current_time_ny + timedelta(hours=50),
            end_time=current_time_ny + timedelta(hours=52),
            capacity=5,
            is_active=True,
            creator=self.creator,
        )
        self.join_request = EventJoin.objects.create(
            user=self.user, event=self.event, status=APPROVED
        )
        self.client = Client()

    def test_removed_approved_request(self):
        self.client.login(username="testcreator", password="testpassword")
        url = reverse(
            "events:remove-approved-request", args=[self.event.id, self.user.id]
        )
        response = self.client.post(url)
        self.join_request.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(self.join_request.status, REMOVED)

    def test_non_creator_cannot_remove(self):
        self.client.logout()
        self.client.login(username="testuser", password="testpassword")
        url = reverse(
            "events:remove-approved-request", args=[self.event.id, self.user.id]
        )
        response = self.client.post(url)
        self.join_request.refresh_from_db()
        self.assertNotEqual(self.join_request.status, REMOVED)
        self.assertEqual(response.status_code, 302)  # redirect


class EventValidationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.location = Location.objects.create(location_name="Location 1")

    def test_update_event_with_valid_data(self):
        self.client.login(username="testuser", password="testpassword")
        new_york_tz = pytz.timezone("America/New_York")
        current_time_ny = datetime.now(new_york_tz)
        start_time = current_time_ny + timezone.timedelta(hours=1)
        end_time = current_time_ny + timezone.timedelta(hours=2)
        start_time = start_time.strftime("%Y-%m-%dT%H:%M")
        end_time = end_time.strftime("%Y-%m-%dT%H:%M")
        event = Event.objects.create(
            event_name="Event 1",
            is_active=True,
            event_location=self.location,
            start_time=start_time,  # Provide a valid start_time
            end_time=end_time,  # Provide a valid end_time
            capacity=100,
        )
        start_time = datetime.now(new_york_tz) + timezone.timedelta(hours=4)
        end_time = start_time + timezone.timedelta(hours=3)
        self.client.login(username="testuser", password="testpassword")
        response = self.client.post(
            reverse("events:update-event", args=[event.id]),
            {
                "event_location_id": self.location.id,
                "event_name": "Updated Event",
                "start_time": start_time.strftime("%Y-%m-%dT%H:%M"),
                "end_time": end_time.strftime("%Y-%m-%dT%H:%M"),
                "capacity": 100,
            },
        )

        self.assertEqual(response.status_code, 302)  # Redirects to events:index

        # Check if the event was updated in the database
        updated_event = Event.objects.get(pk=event.id)
        self.assertEqual(updated_event.event_name, "Updated Event")

    def test_update_event_with_invalid_data(self):
        user = User.objects.create_user("testuser2", password="testpassword")
        self.client.login(username="testuser2", password="testpassword")
        # Create an instance of Event with valid data and set the creator
        new_york_tz = pytz.timezone("America/New_York")
        current_time_ny = datetime.now(new_york_tz)
        start_time = current_time_ny + timezone.timedelta(hours=1)
        end_time = current_time_ny + timezone.timedelta(hours=2)
        start_time = start_time.strftime("%Y-%m-%dT%H:%M")
        end_time = end_time.strftime("%Y-%m-%dT%H:%M")
        event = Event.objects.create(
            event_name="Event 2",
            is_active=True,
            event_location=self.location,
            start_time=start_time,
            end_time=end_time,
            capacity=100,
            creator=user,  # Set the creator to the created user
        )

        response = self.client.post(
            reverse("events:update-event", args=[event.id]),
            {
                "event_location_id": "",  # Missing event location
                "event_name": "",  # Missing event name
                "start_time": "",  # Missing start time
                "end_time": "",  # Missing end time
                "capacity": "abc",  # Invalid capacity
                "event_location": 10,
                "creator": 1,
            },
        )
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.status_code, 400)  # Should stay on the same page
        content = json.loads(response.content)
        self.assertEqual(
            content["event_name"], "Event name cannot be empty."
        )  # Replace with expected content
        self.assertEqual(
            content["event_location_id"], "Event location is required."
        )  # Replace with expected content
        self.assertEqual(
            content["start_time"], "Start time is required."
        )  # Replace with expected content
        self.assertEqual(
            content["end_time"], "End time is required."
        )  # Replace with expected content
        self.assertEqual(
            content["capacity"], "Capacity must be a valid number."
        )  # Replace with expected conten

    def test_update_event_with_missing_data(self):
        user = User.objects.create_user("testuser2", password="testpassword")
        self.client.login(username="testuser2", password="testpassword")
        # Create an instance of Event with valid data and set the creator
        new_york_tz = pytz.timezone("America/New_York")
        current_time_ny = datetime.now(new_york_tz)
        start_time = current_time_ny + timezone.timedelta(hours=1)
        start_time2 = current_time_ny - timezone.timedelta(hours=1)
        end_time = current_time_ny + timezone.timedelta(hours=2)
        start_time2 = start_time2.strftime("%Y-%m-%dT%H:%M")
        start_time = start_time.strftime("%Y-%m-%dT%H:%M")
        end_time = end_time.strftime("%Y-%m-%dT%H:%M")
        event = Event.objects.create(
            event_name="Event 2",
            is_active=True,
            event_location=self.location,
            start_time=start_time,
            end_time=end_time,
            capacity=2,
            creator=user,  # Set the creator to the created user
        )

        response = self.client.post(
            reverse("events:update-event", args=[event.id]),
            {
                "event_name": "MET",  # Missing event name
                "start_time": start_time2,  # Missing start time
                "end_time": end_time,  # Missing end time
                "event_location": 10,
                "creator": 1,
            },
        )
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.status_code, 400)  # Should stay on the same page
        content = json.loads(response.content)
        self.assertEqual(content["start_time"], "Start time cannot be in the past.")
        self.assertEqual(content["capacity"], "Capacity is required.")

    def test_save_event_with_valid_data(self):
        new_york_tz = pytz.timezone("America/New_York")
        current_time_ny = datetime.now(new_york_tz)
        start_time = current_time_ny + timezone.timedelta(hours=1)
        end_time = current_time_ny + timezone.timedelta(hours=2)
        start_time = start_time.strftime("%Y-%m-%dT%H:%M")
        end_time = end_time.strftime("%Y-%m-%dT%H:%M")
        self.client.login(username="testuser", password="testpassword")
        self.client.post(
            reverse("events:save-event"),
            {
                "event_location_id": self.location.id,
                "event_name": "New Event",
                "start_time": start_time,
                "end_time": end_time,
                "capacity": 50,
            },
        )
        # Check if a new event was created in the database
        new_event = Event.objects.get(event_name="New Event")
        self.assertEqual(new_event.capacity, 50)

    def test_save_event_with_invalid_data(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.post(
            reverse("events:save-event"),
            {
                "event_location_id": "",  # Missing event location
                "event_name": "",  # Missing event name
                "start_time": "",  # Missing start time
                "end_time": "",  # Missing end time
                "capacity": "xyz",
                "event_location": 10,
                "creator": 1,
            },
        )
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.status_code, 400)  # Should stay on the same page
        content = json.loads(response.content)
        self.assertEqual(
            content["event_name"], "Event name cannot be empty."
        )  # Replace with expected content
        self.assertEqual(
            content["event_location_id"], "Event location is required."
        )  # Replace with expected content
        self.assertEqual(
            content["start_time"], "Start time is required."
        )  # Replace with expected content
        self.assertEqual(
            content["end_time"], "End time is required."
        )  # Replace with expected content
        self.assertEqual(
            content["capacity"], "Capacity must be a valid number."
        )  # Replace with expected content

    def test_save_event_with_misssing_data(self):
        new_york_tz = pytz.timezone("America/New_York")
        current_time_ny = datetime.now(new_york_tz)
        self.client.login(username="testuser", password="testpassword")
        start_time = current_time_ny - timezone.timedelta(hours=1)
        end_time = current_time_ny - timezone.timedelta(hours=1)
        end_time = end_time.strftime("%Y-%m-%dT%H:%M")
        start_time = start_time.strftime("%Y-%m-%dT%H:%M")
        response = self.client.post(
            reverse("events:save-event"),
            {
                "event_location_id": "",  # Missing event location
                "event_name": "",  # Missing event name
                "start_time": start_time,  # Missing start time
                "end_time": end_time,  # Missing end time
                "event_location": 10,
                "creator": 1,
            },
        )
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.status_code, 400)  # Should stay on the same page
        content = json.loads(response.content)
        self.assertEqual(content["start_time"], "Start time cannot be in the past.")
        self.assertEqual(content["capacity"], "Capacity is required.")


class NavbarTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.location = Location.objects.create(
            location_name="Test Location",
        )
        new_york_tz = pytz.timezone("America/New_York")
        current_time_ny = datetime.now(new_york_tz)
        self.event = Event.objects.create(
            event_name="Test Event",
            event_location=self.location,
            start_time=current_time_ny + timedelta(hours=40),
            end_time=current_time_ny + timedelta(hours=45),
            capacity=8,
            is_active=True,
            creator=self.user,
        )
        self.login_url = reverse("login")
        self.logout_url = reverse("logout")

    def test_navbar_contains_login_when_logged_out(self):
        # Get the response from the events index page
        response = self.client.get(reverse("events:index"))
        # Check that the response contains the login link
        self.assertContains(response, "Log in")
        self.assertNotContains(response, "Log out")

    def test_navbar_contains_logout_when_logged_in(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get(reverse("events:index"))
        self.assertContains(response, "Log out")
        self.assertNotContains(response, "Log in")

    def test_navbar_shows_username_when_logged_in(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get(reverse("events:index"))
        self.assertContains(response, "Hello testuser")

    def test_logout_stays_on_current_page(self):
        self.client.login(username="testuser", password="testpassword")
        current_page = reverse("events:event-detail", args=(self.event.id,))
        self.client.get(current_page)
        response = self.client.get(
            reverse("logout") + "?next=" + current_page, follow=True
        )
        # Check if the response redirects to the same page
        self.assertRedirects(response, current_page)
        # Ensure the user has been logged out
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_redirects_to_home_not_signup(self):
        # Simulate being on the signup page
        self.client.get(reverse("signup"))
        # Then simulate clicking the log in link from the signup page
        login_response = self.client.get(
            reverse("login"), {"next": reverse("signup")}, follow=True
        )
        # Check if the next parameter is set to redirect to 'events:index' instead of 'signup'
        self.assertTrue(login_response.context["next"], reverse("events:index"))
        # Perform the login with the overridden next parameter
        login_response = self.client.post(
            reverse("login"),
            {
                "username": "testuser",
                "password": "testpassword",
                "next": reverse("events:index"),
            },
            follow=True,
        )
        # Check that after login, the user is redirected to 'events:index' page and not back to the signup page
        self.assertRedirects(login_response, reverse("events:index"))

    def tearDown(self):
        # Clean up after each test case
        self.user.delete()


class CommentTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.creator = User.objects.create_user(
            username="testcreator", password="testpassword"
        )
        self.location = Location.objects.create(
            location_name="Test Location",
        )
        new_york_tz = pytz.timezone("America/New_York")
        current_time_ny = datetime.now(new_york_tz)
        self.event = Event.objects.create(
            event_name="Test Event",
            event_location=self.location,
            start_time=current_time_ny + timedelta(days=50),
            end_time=current_time_ny + timedelta(days=52),
            capacity=5,
            is_active=True,
            creator=self.creator,
        )
        self.client = Client()

    def test_create_comment(self):
        self.client.login(username="testuser", password="testpassword")
        url = reverse("events:add-comment", args=[self.event.id])
        response = self.client.post(url, {"content": "Test comment"})
        # Check that the Comment was created
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(Notification.objects.count(), 1)
        comment = Comment.objects.latest("id")
        self.assertEqual(comment.content, "Test comment")
        self.assertEqual(comment.user, self.user)
        self.assertEqual(comment.event, self.event)
        self.assertRedirects(
            response, reverse("events:event-detail", args=[self.event.id])
        )

    def test_private_comment_not_visible_to_other(self):
        private_comment = Comment.objects.create(
            user=self.user, event=self.event, content="Private comment", is_private=True
        )
        self.client.login(username="anotheruser", password="anotherpassword")
        response = self.client.get(reverse("events:event-detail", args=[self.event.id]))
        self.assertNotContains(response, private_comment.content)

    def test_private_comment_visible_to_event_creator(self):
        private_comment = Comment.objects.create(
            user=self.user, event=self.event, content="Private comment", is_private=True
        )
        self.client.login(username="testcreator", password="testpassword")
        response = self.client.get(reverse("events:event-detail", args=[self.event.id]))
        self.assertContains(response, private_comment.content)

    def test_event_creator_comments_only_filter(self):
        creator_comment = Comment.objects.create(
            user=self.creator, event=self.event, content="Creator comment"
        )
        user_comment = Comment.objects.create(
            user=self.user, event=self.event, content="User comment"
        )
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get(
            reverse("events:event-detail", args=[self.event.id])
            + "?creator_comments_only=true"
        )
        self.assertContains(response, creator_comment.content)
        self.assertNotContains(response, user_comment.content)
        response = self.client.get(
            reverse("events:event-detail", args=[self.event.id])
            + "?creator_comments_only=false"
        )
        self.assertContains(response, creator_comment.content)
        self.assertContains(response, user_comment.content)

    def test_comment_author_can_see_private_reply(self):
        self.client.login(username="testuser", password="testpassword")
        user_comment = Comment.objects.create(
            user=self.user,
            event=self.event,
            content="User private comment",
            is_private=True,
        )
        private_reply = Comment.objects.create(
            user=self.creator,
            event=self.event,
            content="Private reply",
            is_private=True,
            parent=user_comment,
        )
        response = self.client.get(reverse("events:event-detail", args=[self.event.id]))
        self.assertContains(response, private_reply.content)

    def test_not_logged_in_comment_attempt(self):
        self.client.logout()  # Ensure the user is logged out
        self.client.post(
            reverse("events:add-comment", args=[self.event.id]),
            {
                "content": "Unauthorized reply attempt",
            },
        )

        self.assertEqual(Comment.objects.count(), 0)  # No new comment should be added

    def test_comment_str_representation(self):
        self.comment = Comment.objects.create(
            user=self.user, event=self.event, content="This is a test comment"
        )
        expected_str = f'{self.user.username}\'s comment: "This is a test comment..."'
        self.assertEqual(str(self.comment), expected_str)


class ReplyTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.creator = User.objects.create_user(
            username="testcreator", password="testpassword"
        )
        self.location = Location.objects.create(
            location_name="Test Location",
        )
        new_york_tz = pytz.timezone("America/New_York")
        current_time_ny = datetime.now(new_york_tz)
        self.event = Event.objects.create(
            event_name="Test Event",
            event_location=self.location,
            start_time=current_time_ny + timedelta(hours=100),
            end_time=current_time_ny + timedelta(hours=104),
            capacity=5,
            is_active=True,
            creator=self.creator,
        )
        self.parent = Comment.objects.create(
            user=self.user,
            event=self.event,
            content="Parent comment",
            is_private=True,
            parent=None,
        )
        self.add_reply_url = reverse(
            "events:add-reply", args=[self.event.id, self.parent.id]
        )

    def test_create_reply(self):
        self.client.logout()
        self.client.login(username="testuser", password="testpassword")
        reply_content = "This is a reply"
        response = self.client.post(
            reverse("events:add-reply", args=[self.event.id, self.parent.id]),
            {
                "content": reply_content,
            },
        )

        self.assertEqual(
            response.status_code, 302
        )  # Assuming a redirect after successful posting
        self.assertEqual(Comment.objects.count(), 2)
        self.assertEqual(Notification.objects.count(), 1)
        reply = Comment.objects.latest("id")
        self.assertEqual(reply.content, reply_content)
        self.assertEqual(reply.parent, self.parent)

    def test_reply_to_nonexistent_comment(self):
        self.client.logout()
        self.client.login(username="testuser", password="testpassword")
        response = self.client.post(
            reverse("events:add-reply", args=[self.event.id, 99999]),
            {
                "content": "Reply to non-existent comment",
            },
        )
        self.assertEqual(
            response.status_code, 404
        )  # Expected to fail with a 404 Not Found

    def test_reply_to_private_comment(self):
        self.client.logout()
        self.client.login(username="testuser", password="testpassword")

        response = self.client.post(
            reverse("events:add-reply", args=[self.event.id, self.parent.id]),
            {
                "content": "Reply to private comment",
            },
        )
        self.assertEqual(response.status_code, 302)
        reply = Comment.objects.latest("id")
        self.assertEqual(reply.parent, self.parent)
        self.assertTrue(
            reply.is_private
        )  # Assuming replies inherit the privacy of the parent comment

    def test_cannot_reply_to_a_reply(self):
        self.client.login(username="testuser", password="testpassword")
        reply = Comment.objects.create(
            user=self.user,
            event=self.event,
            content="Existing comment",
            is_private=True,
            parent=self.parent,
        )
        response = self.client.post(
            reverse("events:add-reply", args=[self.event.id, reply.id]),
            {"content": "Nested reply attempt"},
        )
        # Check if the response is HttpResponseBadRequest
        self.assertEqual(response.status_code, 400)

    def test_cannot_reply_to_a_deleted_comment(self):
        self.client.login(username="testuser", password="testpassword")
        self.parent.is_active = False
        reply = Comment.objects.create(
            user=self.user,
            event=self.event,
            content="Deleted comment",
            is_private=True,
            is_active=False,
        )
        response = self.client.post(
            reverse("events:add-reply", args=[self.event.id, reply.id]),
            {"content": "Reply to a deleted comment attempt"},
        )
        self.assertEqual(response.status_code, 302)
        # Check if the response is redirect
        self.assertRedirects(
            response, reverse("events:event-detail", args=[self.event.id])
        )

    def test_not_logged_in_reply_attempt(self):
        self.client.logout()  # Ensure the user is logged out
        self.client.post(
            reverse("events:add-reply", args=[self.event.id, self.parent.id]),
            {
                "content": "Unauthorized reply attempt",
            },
        )
        self.assertEqual(Comment.objects.count(), 1)  # No new comment should be added


class TagFilterTest(TestCase):
    def setUp(self):
        # Set up user and location
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.location = Location.objects.create(location_name="Test Location")
        Tag.objects.create(tag_name="Hobbies")
        self.tags = Tag.objects.all()
        # Create events with varying capacities
        self.hobbies_event = Event.objects.create(
            event_name="Hobbies Event",
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=2),
            capacity=10,
            event_location=self.location,
            is_active=True,
            creator=self.user,
        )
        self.hobbies_event.tags.set(self.tags)

        self.no_tag_event = Event.objects.create(
            event_name="No Tag Event",
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=2),
            capacity=60,
            event_location=self.location,
            is_active=True,
            creator=self.user,
        )

    def test_event_tags_positve_filter(self):
        # Filter with a valid range where min_capacity is less than max_capacity
        tags = 1

        url = reverse("events:index")
        response = self.client.get(url, {"tags": tags})
        # Check that only events within the specified capacity range are in the context
        self.assertEqual(response.status_code, 200)
        # print(response.context)
        self.assertContains(response, "Hobbies Event")
        self.assertNotContains(response, "No Tag Event")
        # Check if there is no error message

    def test_event_tags_negative_filter(self):
        url = reverse("events:index")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hobbies Event")
        self.assertContains(response, "No Tag Event")


class DeleteCommentReplyTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.creator = User.objects.create_user(
            username="testcreator", password="testpassword"
        )
        self.anotheruser = User.objects.create_user(
            username="anotheruser", password="testpassword"
        )
        self.location = Location.objects.create(
            location_name="Test Location",
        )
        new_york_tz = pytz.timezone("America/New_York")
        current_time_ny = datetime.now(new_york_tz)
        self.event = Event.objects.create(
            event_name="Test Event",
            event_location=self.location,
            start_time=current_time_ny + timedelta(hours=200),
            end_time=current_time_ny + timedelta(hours=205),
            capacity=5,
            is_active=True,
            creator=self.creator,
        )
        self.comment = Comment.objects.create(
            user=self.user,
            event=self.event,
            content="Test comment",
            is_private=True,
        )
        self.reply = Comment.objects.create(
            user=self.user,
            event=self.event,
            content="Test reply",
            parent=self.comment,
            is_private=True,
        )

    def test_delete_by_comment_user(self):
        self.client.login(username="testuser", password="testpassword")
        self.client.post(
            reverse("events:delete-comment", args=[self.reply.id]), {"action": "delete"}
        )
        self.reply.refresh_from_db()
        self.assertFalse(self.reply.is_active)

    def test_delete_by_event_creator(self):
        self.client.login(username="testcreator", password="testpassword")
        self.client.post(
            reverse("events:delete-comment", args=[self.reply.id]), {"action": "delete"}
        )
        self.reply.refresh_from_db()
        self.assertFalse(self.reply.is_active)

    def test_cannot_delete_by_other_user(self):
        self.client.login(username="anotheruser", password="testpassword")
        response = self.client.post(
            reverse("events:delete-comment", args=[self.reply.id]), {"action": "delete"}
        )
        self.reply.refresh_from_db()
        self.assertTrue(self.reply.is_active)
        self.assertAlmostEqual(response.status_code, 302)

    def test_cannot_delete_by_not_logged_in_user(self):
        self.client.logout()
        response = self.client.post(
            reverse("events:delete-comment", args=[self.reply.id]), {"action": "delete"}
        )
        self.reply.refresh_from_db()
        self.assertTrue(self.reply.is_active)
        self.assertAlmostEqual(response.status_code, 302)

    def test_cannot_delete_comment_with_reply(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.post(
            reverse("events:delete-comment", args=[self.comment.id]),
            {"action": "delete"},
        )
        self.reply.refresh_from_db()
        self.assertTrue(self.comment.is_active)
        self.assertAlmostEqual(response.status_code, 302)


class ReactionTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.creator = User.objects.create_user(
            username="testcreator", password="testpassword"
        )
        self.location = Location.objects.create(
            location_name="Test Location",
        )
        new_york_tz = pytz.timezone("America/New_York")
        current_time_ny = datetime.now(new_york_tz)
        self.event = Event.objects.create(
            event_name="Test Event",
            event_location=self.location,
            start_time=current_time_ny + timedelta(hours=19),
            end_time=current_time_ny + timedelta(hours=21),
            capacity=10,
            is_active=True,
            creator=self.creator,
        )
        self.emoji = CHEER_UP
        self.client = Client()

    def test_toggle_reaction(self):
        self.client.login(username="testuser", password="testpassword")
        url = reverse("events:toggle-reaction", args=[self.event.id, self.emoji])
        # Initially, the user has not reacted to the event
        response = self.client.post(url)
        reaction = Reaction.objects.get(user=self.user, event=self.event)
        self.assertEqual(reaction.emoji, CHEER_UP)
        self.assertTrue(reaction.is_active)
        # Make the POST request again to withdraw the reaction
        response = self.client.post(url)
        reaction.refresh_from_db()
        self.assertEqual(Notification.objects.count(), 2)
        self.assertFalse(reaction.is_active)
        self.assertRedirects(
            response, reverse("events:event-detail", args=[self.event.id])
        )

    def test_creator_cannot_react_to_own_event(self):
        self.client.logout()
        url = reverse("events:toggle-reaction", args=[self.event.id, self.emoji])
        self.client.login(username="testcreator", password="testpassword")
        response = self.client.post(url)
        self.assertFalse(
            Reaction.objects.filter(user=self.creator, event=self.event).exists()
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, reverse("events:event-detail", args=[self.event.id])
        )
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            "As the creator of the event, you cannot react to your own event.",
        )

    def test_reaction_str_representation(self):
        reaction = Reaction.objects.create(
            user=self.user, event=self.event, emoji=self.emoji
        )
        expected_str = f"{self.user.username} - {self.event.event_name} - {reaction.get_emoji_display()}"
        self.assertEqual(str(reaction), expected_str)

    def test_non_logged_in_cannot_react(self):
        self.client.logout()
        url = reverse("events:toggle-reaction", args=[self.event.id, self.emoji])
        response = self.client.post(url)
        self.assertFalse(
            Reaction.objects.filter(user=self.creator, event=self.event).exists()
        )
        self.assertEqual(response.status_code, 302)

    def test_can_not_have_multiple_reaction_to_one_event(self):
        self.client.logout()
        self.client.login(username="testuser", password="testpassword")
        Reaction.objects.create(user=self.user, event=self.event, emoji=self.emoji)
        url = reverse("events:toggle-reaction", args=[self.event.id, HEART])
        response = self.client.post(url)
        self.assertFalse(
            Reaction.objects.filter(
                user=self.creator, event=self.event, emoji=HEART
            ).exists()
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, reverse("events:event-detail", args=[self.event.id])
        )
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            f"You have already reacted with {self.emoji}. You can only react with one emoji per event.",
        )

    def test_creator_see_reaction_username_list(self):
        self.client.logout()
        url = reverse("events:event-detail", args=[self.event.id])
        self.client.login(username="testcreator", password="testpassword")
        Reaction.objects.create(user=self.user, event=self.event, emoji=self.emoji)
        response = self.client.post(url)
        self.assertContains(response, "testuser")

    def test_not_logged_in_user_cannot_see_reaction_username_list(self):
        self.client.logout()
        url = reverse("events:event-detail", args=[self.event.id])
        Reaction.objects.create(user=self.user, event=self.event, emoji=self.emoji)
        response = self.client.post(url)
        self.assertNotContains(response, "testuser")

    def test_another_user_cannot_see_reaction_username_list(self):
        self.client.logout()
        User.objects.create_user(username="anotheruser", password="testpassword")
        url = reverse("events:event-detail", args=[self.event.id])
        Reaction.objects.create(user=self.user, event=self.event, emoji=self.emoji)
        self.client.login(username="anotheruser", password="testpassword")
        response = self.client.post(url)
        self.assertNotContains(response, "testuser")

    def test_reaction_count(self):
        self.client.logout()
        url = reverse("events:event-detail", args=[self.event.id])
        self.client.login(username="testcreator", password="testpassword")
        Reaction.objects.create(user=self.user, event=self.event, emoji=self.emoji)
        response = self.client.post(url)
        self.assertContains(response, "testuser")


class AccessDeletedEventTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.creator = User.objects.create_user(
            username="testcreator", password="testpassword"
        )
        self.location = Location.objects.create(
            location_name="Test Location",
        )
        new_york_tz = pytz.timezone("America/New_York")
        current_time_ny = datetime.now(new_york_tz)
        self.event = Event.objects.create(
            event_name="Test Event",
            event_location=self.location,
            start_time=current_time_ny + timedelta(hours=14),
            end_time=current_time_ny + timedelta(hours=25),
            capacity=10,
            is_active=False,
            creator=self.creator,
        )
        self.emoji = CHEER_UP
        self.client = Client()

    def test_cannot_update_deleted_event(self):
        self.client.login(username="testcreator", password="testpassword")
        url = reverse("events:update-event", args=[self.event.id])
        response = self.client.post(url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            "The event is deleted. Try some other events!",
        )
        self.assertRedirects(response, reverse("events:index"))

    def test_cannot_delete_deleted_event(self):
        self.client.login(username="testcreator", password="testpassword")
        url = reverse("events:delete-event", args=[self.event.id])
        response = self.client.post(url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            "The event is deleted. Try some other events!",
        )
        self.assertRedirects(response, reverse("events:index"))

    def test_cannot_access_deleted_event_detail(self):
        url = reverse("events:event-detail", args=[self.event.id])
        response = self.client.post(url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            "The event is deleted. Try some other events!",
        )
        self.assertRedirects(response, reverse("events:index"))

    def test_cannot_toggle_join_request_to_deleted_event(self):
        url = reverse("events:toggle-join-request", args=[self.event.id])
        self.client.login(username="testuser", password="testpassword")
        response = self.client.post(url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            "The event is deleted. Try some other events!",
        )
        self.assertRedirects(response, reverse("events:index"))

    def test_cannot_approve_join_request_to_deleted_event(self):
        EventJoin.objects.create(user=self.user, event=self.event)
        self.client.login(username="testcreator", password="testpassword")
        url = reverse("events:approve-request", args=[self.event.id, self.user.id])
        response = self.client.post(url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            "The event is deleted. Try some other events!",
        )
        self.assertRedirects(response, reverse("events:index"))

    def test_cannot_reject_join_request_to_deleted_event(self):
        EventJoin.objects.create(user=self.user, event=self.event)
        self.client.login(username="testcreator", password="testpassword")
        url = reverse("events:reject-request", args=[self.event.id, self.user.id])
        response = self.client.post(url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            "The event is deleted. Try some other events!",
        )
        self.assertRedirects(response, reverse("events:index"))

    def test_cannot_remove_approved_request_of_deleted_event(self):
        EventJoin.objects.create(user=self.user, event=self.event, status=APPROVED)
        self.client.login(username="testcreator", password="testpassword")
        url = reverse(
            "events:remove-approved-request", args=[self.event.id, self.user.id]
        )
        response = self.client.post(url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            "The event is deleted. Try some other events!",
        )
        self.assertRedirects(response, reverse("events:index"))

    def test_cannot_comment_deleted_event(self):
        url = reverse("events:add-comment", args=[self.event.id])
        self.client.login(username="testuser", password="testpassword")
        response = self.client.post(url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            "The event is deleted. Try some other events!",
        )
        self.assertRedirects(response, reverse("events:index"))

    def test_cannot_reply_to_comment_of_deleted_event(self):
        comment = Comment.objects.create(
            user=self.user,
            event=self.event,
            content="Test comment",
            is_private=True,
        )
        url = reverse("events:add-reply", args=[self.event.id, comment.id])
        self.client.login(username="testuser", password="testpassword")
        response = self.client.post(url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            "The event is deleted. Try some other events!",
        )
        self.assertRedirects(response, reverse("events:index"))

    def test_cannot_delete_comment_of_deleted_event(self):
        comment = Comment.objects.create(
            user=self.user,
            event=self.event,
            content="Test comment",
            is_private=True,
        )
        url = reverse("events:delete-comment", args=[comment.id])
        self.client.login(username="testuser", password="testpassword")
        response = self.client.post(url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            "The event is deleted. Try some other events!",
        )
        self.assertRedirects(response, reverse("events:index"))

    def test_cannot_react_to_deleted_event(self):
        self.client.login(username="testuser", password="testpassword")
        url = reverse("events:toggle-reaction", args=[self.event.id, self.emoji])
        response = self.client.post(url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            "The event is deleted. Try some other events!",
        )
        self.assertRedirects(response, reverse("events:index"))


class DeleteEventTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.creator = User.objects.create_user(
            username="testcreator", password="testpassword"
        )
        self.location = Location.objects.create(
            location_name="Test Location",
        )
        new_york_tz = pytz.timezone("America/New_York")
        current_time_ny = datetime.now(new_york_tz)
        self.event = Event.objects.create(
            event_name="Test Event",
            event_location=self.location,
            start_time=current_time_ny + timedelta(hours=2),
            end_time=current_time_ny + timedelta(hours=25),
            capacity=10,
            is_active=True,
            creator=self.creator,
        )
        self.client = Client()

    def test_event_creator_can_delete_event(self):
        self.client.login(username="testcreator", password="testpassword")
        url = reverse("events:delete-event", args=[self.event.id])
        response = self.client.post(url, {"action": "delete"})
        self.event.refresh_from_db()
        self.assertFalse(self.event.is_active)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("events:index"))

    def test_other_user_cannot_delete_event(self):
        self.client.login(username="testuser", password="testpassword")
        url = reverse("events:delete-event", args=[self.event.id])
        response = self.client.post(url, {"action": "delete"})
        self.event.refresh_from_db()
        self.assertTrue(self.event.is_active)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            "You're not allowed to delete this event.",
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("events:index"))

    def test_not_logged_in_user_cannot_delete_event(self):
        self.client.logout()
        url = reverse("events:delete-event", args=[self.event.id])
        response = self.client.post(url, {"action": "delete"})
        self.event.refresh_from_db()
        self.assertTrue(self.event.is_active)
        self.assertEqual(response.status_code, 302)


class HomepageViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_homepage_view(self):
        response = self.client.get(reverse("root-homepage"))
        self.assertEqual(response.status_code, 200)


class HomepageTimeLabelFilterTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.creator = User.objects.create_user(
            username="testcreator", password="testpassword"
        )
        self.location = Location.objects.create(
            location_name="Test Location",
        )
        tag = Tag.objects.create(tag_name="Test Tag")
        new_york_tz = pytz.timezone("America/New_York")
        self.current_time_ny = datetime.now(new_york_tz)
        self.event1 = Event.objects.create(
            event_name="Test Event 1",
            event_location=self.location,
            start_time=self.current_time_ny + timedelta(hours=7),
            end_time=self.current_time_ny + timedelta(hours=9),
            capacity=20,
            is_active=True,
            creator=self.creator,
        )
        self.event1.tags.set([tag])
        self.event2 = Event.objects.create(
            event_name="Test Event 2",
            event_location=self.location,
            start_time=self.current_time_ny + timedelta(hours=7),
            end_time=self.current_time_ny + timedelta(days=5),
            capacity=20,
            is_active=True,
            creator=self.creator,
        )
        self.event2.tags.set([tag])
        self.event3 = Event.objects.create(
            event_name="Test Event 3",
            event_location=self.location,
            start_time=self.current_time_ny + timedelta(hours=7),
            end_time=self.current_time_ny + timedelta(days=10),
            capacity=20,
            is_active=True,
            creator=self.creator,
        )
        self.event3.tags.set([tag])
        self.client = Client()

    def test_filter_event_today_label(self):
        response = self.client.get(reverse("root-homepage") + "?filter_time=today")
        self.assertEqual(response.status_code, 302)
        start_time = self.current_time_ny + timedelta(minutes=1)
        end_time = start_time + timedelta(days=1)
        self.assertRedirects(
            response,
            reverse("events:index")
            + f'?start_time={start_time.strftime("%Y-%m-%dT%H:%M")}&end_time={end_time.strftime("%Y-%m-%dT%H:%M")}',
        )
        response = self.client.get(
            reverse("events:index")
            + f'?start_time={start_time.strftime("%Y-%m-%dT%H:%M")}&end_time={end_time.strftime("%Y-%m-%dT%H:%M")}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Event 1")
        self.assertNotContains(response, "Test Event 2")
        self.assertNotContains(response, "Test Event 3")

    def test_filter_event_this_week_label(self):
        response = self.client.get(reverse("root-homepage") + "?filter_time=this_week")
        self.assertEqual(response.status_code, 302)
        start_time = self.current_time_ny + timedelta(minutes=1)
        end_time = start_time + timedelta(days=7)
        self.assertRedirects(
            response,
            reverse("events:index")
            + f'?start_time={start_time.strftime("%Y-%m-%dT%H:%M")}&end_time={end_time.strftime("%Y-%m-%dT%H:%M")}',
        )
        response = self.client.get(
            reverse("events:index")
            + f'?start_time={start_time.strftime("%Y-%m-%dT%H:%M")}&end_time={end_time.strftime("%Y-%m-%dT%H:%M")}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Event 1")
        self.assertContains(response, "Test Event 2")
        self.assertNotContains(response, "Test Event 3")

    def test_filter_event_this_month_label(self):
        response = self.client.get(reverse("root-homepage") + "?filter_time=this_month")
        self.assertEqual(response.status_code, 302)
        start_time = self.current_time_ny + timedelta(minutes=1)
        end_time = start_time + timedelta(days=30)
        self.assertRedirects(
            response,
            reverse("events:index")
            + f'?start_time={start_time.strftime("%Y-%m-%dT%H:%M")}&end_time={end_time.strftime("%Y-%m-%dT%H:%M")}',
        )
        response = self.client.get(
            reverse("events:index")
            + f'?start_time={start_time.strftime("%Y-%m-%dT%H:%M")}&end_time={end_time.strftime("%Y-%m-%dT%H:%M")}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Event 1")
        self.assertContains(response, "Test Event 2")
        self.assertContains(response, "Test Event 3")

    def test_filter_event_invalid_time_label(self):
        response = self.client.get(
            reverse("root-homepage") + "?filter_time=invalid_time"
        )
        self.assertRedirects(response, reverse("root-homepage"))


class HomepageTagLabelFilterTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.creator = User.objects.create_user(
            username="testcreator", password="testpassword"
        )
        self.location = Location.objects.create(
            location_name="Test Location",
        )
        self.tag1 = Tag.objects.create(tag_name="Test Tag 1")
        self.tag2 = Tag.objects.create(tag_name="Test Tag 2")
        new_york_tz = pytz.timezone("America/New_York")
        self.current_time_ny = datetime.now(new_york_tz)
        self.event1 = Event.objects.create(
            event_name="Test Event 1",
            event_location=self.location,
            start_time=self.current_time_ny + timedelta(hours=7),
            end_time=self.current_time_ny + timedelta(hours=9),
            capacity=20,
            is_active=True,
            creator=self.creator,
        )
        self.event1.tags.set([self.tag1])
        self.event2 = Event.objects.create(
            event_name="Test Event 2",
            event_location=self.location,
            start_time=self.current_time_ny + timedelta(hours=10),
            end_time=self.current_time_ny + timedelta(hours=14),
            capacity=50,
            is_active=True,
            creator=self.creator,
        )
        self.event2.tags.set([self.tag2])
        self.client = Client()

    def test_filter_event_tag_label(self):
        response = self.client.get(
            reverse("root-homepage") + f"?filter_tag={self.tag1.id}"
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, reverse("events:index") + f"?tags={self.tag1.id}"
        )
        response = self.client.get(reverse("events:index") + f"?tags={self.tag1.id}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Event 1")
        self.assertNotContains(response, "Test Event 2")

    def test_filter_event_invalid_tag_label(self):
        response = self.client.get(reverse("root-homepage") + "?filter_tag=9999")
        self.assertEqual(response.status_code, 404)


class HomepageCapacityLabelFilterTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.creator = User.objects.create_user(
            username="testcreator", password="testpassword"
        )
        self.location = Location.objects.create(
            location_name="Test Location",
        )
        self.tag = Tag.objects.create(tag_name="Test Tag")
        new_york_tz = pytz.timezone("America/New_York")
        self.current_time_ny = datetime.now(new_york_tz)
        self.event1 = Event.objects.create(
            event_name="Test Event 1",
            event_location=self.location,
            start_time=self.current_time_ny + timedelta(hours=7),
            end_time=self.current_time_ny + timedelta(hours=9),
            capacity=3,
            is_active=True,
            creator=self.creator,
        )
        self.event1.tags.set([self.tag])
        self.event2 = Event.objects.create(
            event_name="Test Event 2",
            event_location=self.location,
            start_time=self.current_time_ny + timedelta(hours=10),
            end_time=self.current_time_ny + timedelta(hours=14),
            capacity=15,
            is_active=True,
            creator=self.creator,
        )
        self.event2.tags.set([self.tag])
        self.event3 = Event.objects.create(
            event_name="Test Event 3",
            event_location=self.location,
            start_time=self.current_time_ny + timedelta(hours=15),
            end_time=self.current_time_ny + timedelta(hours=17),
            capacity=30,
            is_active=True,
            creator=self.creator,
        )
        self.event3.tags.set([self.tag])
        self.event4 = Event.objects.create(
            event_name="Test Event 4",
            event_location=self.location,
            start_time=self.current_time_ny + timedelta(hours=20),
            end_time=self.current_time_ny + timedelta(hours=22),
            capacity=100,
            is_active=True,
            creator=self.creator,
        )
        self.event4.tags.set([self.tag])
        self.client = Client()

    def test_filter_event_small_capacity_label(self):
        response = self.client.get(reverse("root-homepage") + "?filter_capacity=s")
        self.assertEqual(response.status_code, 302)
        min_capacity = 0
        max_capacity = SMALL_CAPACITY
        self.assertRedirects(
            response,
            reverse("events:index")
            + f"?min_capacity={min_capacity}&max_capacity={max_capacity}",
        )
        response = self.client.get(
            reverse("events:index")
            + f"?min_capacity={min_capacity}&max_capacity={max_capacity}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Event 1")
        self.assertNotContains(response, "Test Event 2")
        self.assertNotContains(response, "Test Event 3")
        self.assertNotContains(response, "Test Event 4")

    def test_filter_event_medium_capacity_label(self):
        response = self.client.get(reverse("root-homepage") + "?filter_capacity=m")
        self.assertEqual(response.status_code, 302)
        min_capacity = SMALL_CAPACITY + 1
        max_capacity = MEDIUM_CAPACITY
        self.assertRedirects(
            response,
            reverse("events:index")
            + f"?min_capacity={min_capacity}&max_capacity={max_capacity}",
        )
        response = self.client.get(
            reverse("events:index")
            + f"?min_capacity={min_capacity}&max_capacity={max_capacity}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Test Event 1")
        self.assertContains(response, "Test Event 2")
        self.assertNotContains(response, "Test Event 3")
        self.assertNotContains(response, "Test Event 4")

    def test_filter_event_large_capacity_label(self):
        response = self.client.get(reverse("root-homepage") + "?filter_capacity=l")
        self.assertEqual(response.status_code, 302)
        min_capacity = MEDIUM_CAPACITY + 1
        max_capacity = LARGE_CAPACITY
        self.assertRedirects(
            response,
            reverse("events:index")
            + f"?min_capacity={min_capacity}&max_capacity={max_capacity}",
        )
        response = self.client.get(
            reverse("events:index")
            + f"?min_capacity={min_capacity}&max_capacity={max_capacity}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Test Event 1")
        self.assertNotContains(response, "Test Event 2")
        self.assertContains(response, "Test Event 3")
        self.assertNotContains(response, "Test Event 4")

    def test_filter_event_extra_large_capacity_label(self):
        response = self.client.get(reverse("root-homepage") + "?filter_capacity=xl")
        self.assertEqual(response.status_code, 302)
        min_capacity = LARGE_CAPACITY + 1
        max_capacity = 5000
        self.assertRedirects(
            response,
            reverse("events:index")
            + f"?min_capacity={min_capacity}&max_capacity={max_capacity}",
        )
        response = self.client.get(
            reverse("events:index")
            + f"?min_capacity={min_capacity}&max_capacity={max_capacity}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Test Event 1")
        self.assertNotContains(response, "Test Event 2")
        self.assertNotContains(response, "Test Event 3")
        self.assertContains(response, "Test Event 4")

    def test_filter_event_invalid_capacity_label(self):
        response = self.client.get(
            reverse("root-homepage") + "?filter_capacity=invalid_capacity"
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("root-homepage"))


class EventDeatilPageTagLabelFilterTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.creator = User.objects.create_user(
            username="testcreator", password="testpassword"
        )
        self.location = Location.objects.create(
            location_name="Test Location",
        )
        self.tag1 = Tag.objects.create(tag_name="Test Tag 1")
        self.tag2 = Tag.objects.create(tag_name="Test Tag 2")
        new_york_tz = pytz.timezone("America/New_York")
        self.current_time_ny = datetime.now(new_york_tz)
        self.event1 = Event.objects.create(
            event_name="Test Event 1",
            event_location=self.location,
            start_time=self.current_time_ny + timedelta(hours=7),
            end_time=self.current_time_ny + timedelta(hours=9),
            capacity=30,
            is_active=True,
            creator=self.creator,
        )
        self.event1.tags.set([self.tag1])
        self.event2 = Event.objects.create(
            event_name="Test Event 2",
            event_location=self.location,
            start_time=self.current_time_ny + timedelta(hours=18),
            end_time=self.current_time_ny + timedelta(hours=30),
            capacity=50,
            is_active=True,
            creator=self.creator,
        )
        self.event2.tags.set([self.tag2])
        self.client = Client()

    def test_filter_event_tag_pill(self):
        response = self.client.get(
            reverse("events:event-detail", args=[self.event1.id])
            + f"?filter_tag={self.tag1.id}"
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, reverse("events:index") + f"?tags={self.tag1.id}"
        )
        response = self.client.get(reverse("events:index") + f"?tags={self.tag1.id}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Event 1")
        self.assertNotContains(response, "Test Event 2")

    def test_filter_event_invalid_tag_pill(self):
        response = self.client.get(
            reverse("events:event-detail", args=[self.event1.id]) + "?filter_tag=9999"
        )
        self.assertEqual(response.status_code, 404)


class ProfanityCheckTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.location = Location.objects.create(
            location_name="Test Location",
        )
        new_york_tz = pytz.timezone("America/New_York")
        current_time_ny = datetime.now(new_york_tz)
        start_time = current_time_ny + timezone.timedelta(hours=1)
        end_time = current_time_ny + timezone.timedelta(hours=2)
        self.start_time = start_time.strftime("%Y-%m-%dT%H:%M")
        self.end_time = end_time.strftime("%Y-%m-%dT%H:%M")
        self.event = Event.objects.create(
            event_name="Test Event",
            event_location=self.location,
            start_time=self.start_time,
            end_time=self.end_time,
            capacity=100,
            is_active=True,
            creator=self.user,
        )

    def test_update_event_with_profane_name(self):
        self.client.login(username="testuser", password="testpassword")
        existing_event = Event.objects.get(pk=self.event.id)
        response = self.client.post(
            reverse("events:update-event", args=[existing_event.id]),
            {
                "event_location_id": self.location.id,
                "event_name": "Fuck you Event",
                "start_time": self.start_time,
                "end_time": self.end_time,
                "capacity": 100,
            },
        )
        self.assertContains(
            response,
            "Event Name contains profanity",
        )  # Replace with expected content

    def test_create_event_with_profane_name(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.post(
            reverse("events:save-event"),
            {
                "event_location_id": self.location.id,  # Missing event location
                "event_name": "Test Event Fuck",  # Missing event name
                "start_time": self.start_time,  # Missing start time
                "end_time": self.end_time,  # Missing end time
                "capacity": 10,
                "creator": self.user,
            },
        )
        self.assertContains(
            response,
            "Event Name contains profanity",
        )

    def test_create_event_with_profane_description(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.post(
            reverse("events:save-event"),
            {
                "event_location_id": self.location.id,  # Missing event location
                "event_name": "Test Event",  # Missing event name
                "start_time": self.start_time,  # Missing start time
                "end_time": self.end_time,  # Missing end time
                "capacity": 10,
                "description": "Fuck you",
                "creator": self.user,
            },
        )
        self.assertContains(
            response,
            "Description contains profanity",
        )

    def test_update_event_with_profane_description(self):
        self.client.login(username="testuser", password="testpassword")
        existing_event = Event.objects.get(pk=self.event.id)
        response = self.client.post(
            reverse("events:update-event", args=[existing_event.id]),
            {
                "event_location_id": self.location.id,
                "event_name": "Test Event",
                "start_time": self.start_time,
                "end_time": self.end_time,
                "description": "Fuck you",
                "capacity": 100,
            },
        )
        self.assertContains(
            response,
            "Description contains profanity",
        )  # Replace with expected content


class CommentProfanityTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.creator = User.objects.create_user(
            username="testcreator", password="testpassword"
        )
        self.location = Location.objects.create(
            location_name="Test Location",
        )
        new_york_tz = pytz.timezone("America/New_York")
        current_time_ny = datetime.now(new_york_tz)
        self.event = Event.objects.create(
            event_name="Test Event",
            event_location=self.location,
            start_time=current_time_ny + timedelta(days=50),
            end_time=current_time_ny + timedelta(days=52),
            capacity=5,
            is_active=True,
            creator=self.creator,
        )
        self.client = Client()

    def test_create_comment_profanity(self):
        self.client.login(username="testuser", password="testpassword")
        url = reverse("events:add-comment", args=[self.event.id])
        self.client.post(url, {"content": "Fuck you"})
        self.assertEqual(Comment.objects.count(), 0)


class ReplyProfanityTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.creator = User.objects.create_user(
            username="testcreator", password="testpassword"
        )
        self.location = Location.objects.create(
            location_name="Test Location",
        )
        new_york_tz = pytz.timezone("America/New_York")
        current_time_ny = datetime.now(new_york_tz)
        self.event = Event.objects.create(
            event_name="Test Event",
            event_location=self.location,
            start_time=current_time_ny + timedelta(hours=100),
            end_time=current_time_ny + timedelta(hours=104),
            capacity=5,
            is_active=True,
            creator=self.creator,
        )
        self.parent = Comment.objects.create(
            user=self.user,
            event=self.event,
            content="Parent comment",
            is_private=True,
            parent=None,
        )
        self.add_reply_url = reverse(
            "events:add-reply", args=[self.event.id, self.parent.id]
        )

    def test_profanity_create_reply(self):
        self.client.logout()
        self.client.login(username="testuser", password="testpassword")
        reply_content = "This is a reply fuck"
        self.client.post(
            reverse("events:add-reply", args=[self.event.id, self.parent.id]),
            {
                "content": reply_content,
            },
        )
        self.assertEqual(Comment.objects.count(), 1)


class RecommendEventTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username="testuser1", password="testpassword"
        )
        self.user2 = User.objects.create_user(
            username="testuser2", password="testpassword"
        )
        self.creator = User.objects.create_user(
            username="testcreator", password="testpassword"
        )
        self.location1 = Location.objects.create(
            location_name="Test Location 1",
        )
        self.location2 = Location.objects.create(
            location_name="Test Location 2",
        )
        self.location3 = Location.objects.create(
            location_name="Test Location 3",
        )
        self.tag1 = Tag.objects.create(tag_name="Test Tag 1")
        self.tag2 = Tag.objects.create(tag_name="Test Tag 2")
        self.tag3 = Tag.objects.create(tag_name="Test Tag 3")
        new_york_tz = pytz.timezone("America/New_York")
        self.current_time_ny = datetime.now(new_york_tz)
        self.event1 = Event.objects.create(
            event_name="Test Event 1",
            event_location=self.location1,
            start_time=self.current_time_ny + timedelta(hours=14),
            end_time=self.current_time_ny + timedelta(hours=17),
            capacity=30,
            is_active=True,
            creator=self.creator,
        )
        self.event1.tags.set([self.tag1])
        self.event2 = Event.objects.create(
            event_name="Test Event 2",
            event_location=self.location2,
            start_time=self.current_time_ny + timedelta(hours=25),
            end_time=self.current_time_ny + timedelta(hours=29),
            capacity=50,
            is_active=True,
            creator=self.creator,
        )
        self.event2.tags.set([self.tag2])
        self.event3 = Event.objects.create(
            event_name="Test Event 3",
            event_location=self.location1,
            start_time=self.current_time_ny + timedelta(hours=21),
            end_time=self.current_time_ny + timedelta(hours=28),
            capacity=5,
            is_active=True,
            creator=self.user2,
        )
        self.event3.tags.set([self.tag2])
        self.client = Client()

    def test_logged_in_user_with_record_can_see_recommend_page(self):
        self.client.login(username="testcreator", password="testpassword")
        response = self.client.get(reverse("events:recommend-event"))
        self.assertEqual(response.status_code, 200)

    def test_logged_in_user_with_no_record_direct_to_events_page(self):
        self.client.login(username="testuser1", password="testpassword")
        response = self.client.get(reverse("events:recommend-event"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("events:index"))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            "Sorry we haven't found any match! See all the events here!",
        )

    def test_not_logged_in_user_cannot_see_recommend_page(self):
        self.client.logout()
        response = self.client.get(reverse("events:recommend-event"))
        self.assertEqual(response.status_code, 302)

    def test_logged_in_user_see_other_events_by_location_by_tag(self):
        self.client.login(username="testuser2", password="testpassword")
        response = self.client.get(reverse("events:recommend-event"))
        self.assertContains(response, "Test Event 1")
        self.assertContains(response, "Test Event 2")
        self.assertNotContains(response, "Test Event 3")
        event4 = Event.objects.create(
            event_name="Test Event 4",
            event_location=self.location1,
            start_time=self.current_time_ny + timedelta(hours=9),
            end_time=self.current_time_ny + timedelta(hours=10),
            capacity=8,
            is_active=True,
            creator=self.creator,
        )
        event4.tags.set([self.tag3])
        event5 = Event.objects.create(
            event_name="Test Event 5",
            event_location=self.location1,
            start_time=self.current_time_ny + timedelta(hours=15),
            end_time=self.current_time_ny + timedelta(hours=30),
            capacity=2,
            is_active=True,
            creator=self.creator,
        )
        event5.tags.set([self.tag3])
        EventJoin.objects.create(user=self.user2, event=event5)
        response = self.client.get(reverse("events:recommend-event"))
        self.assertContains(response, "Test Event 1")
        self.assertContains(response, "Test Event 2")
        self.assertContains(response, "Test Event 4")
        self.assertNotContains(response, "Test Event 3")
        self.assertNotContains(response, "Test Event 5")

    def test_logged_in_user_see_events_created_by_friend(self):
        event4 = Event.objects.create(
            event_name="Test Event 4",
            event_location=self.location3,
            start_time=self.current_time_ny + timedelta(hours=30),
            end_time=self.current_time_ny + timedelta(hours=35),
            capacity=25,
            is_active=True,
            creator=self.user1,
        )
        event4.tags.set([self.tag3])
        self.client.login(username="testuser2", password="testpassword")
        response = self.client.get(reverse("events:recommend-event"))
        self.assertNotContains(response, "Test Event 4")
        user2_userprofile = UserProfile.objects.get(user=self.user2)
        user1_userprofile = UserProfile.objects.get(user=self.user1)
        UserFriends.objects.create(
            user=self.user2, friends=user1_userprofile, status=APPROVED
        )
        UserFriends.objects.create(
            user=self.user1, friends=user2_userprofile, status=APPROVED
        )
        response = self.client.get(reverse("events:recommend-event"))
        self.assertContains(response, "Test Event 4")


class AddToFavoritesTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test_user", password="test_password"
        )
        self.location = Location.objects.create(
            location_name="Test Location", address="Test Address"
        )

    def test_authenticated_user_add_to_favorites(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("events:add_to_favorites", args=[self.location.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            FavoriteLocation.objects.filter(
                user=self.user, location=self.location
            ).exists()
        )
        self.assertJSONEqual(
            str(response.content, encoding="utf8"),
            {"success": "Location added to favorites"},
        )

    def test_unauthenticated_user_add_to_favorites(self):
        response = self.client.post(
            reverse("events:add_to_favorites", args=[self.location.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            FavoriteLocation.objects.filter(
                user=self.user, location=self.location
            ).exists()
        )
        self.assertJSONEqual(
            str(response.content, encoding="utf8"),
            {"error": "User is not authenticated"},
        )

    def test_already_favorited_location(self):
        self.client.force_login(self.user)
        FavoriteLocation.objects.create(user=self.user, location=self.location)
        response = self.client.post(
            reverse("events:add_to_favorites", args=[self.location.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding="utf8"),
            {"success": "Location is already a favorite"},
        )
