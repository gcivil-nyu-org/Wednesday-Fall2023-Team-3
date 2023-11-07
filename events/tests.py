from django.test import TestCase, Client
from django.urls import reverse
from .models import Event, Location, EventJoin
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from datetime import datetime
import json
import pytz
from .constants import PENDING, APPROVED, WITHDRAWN, REJECTED, REMOVED


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
        }
        url = reverse("events:update-event", args=(self.event.id,))
        self.client.login(username="testuser", password="testpassword")
        self.client.post(url, updated_data)
        self.assertEqual(
            Event.objects.get(pk=self.event.id).event_name, "Updated Event"
        )  # Verify data was updated


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

    def test_update_event_with_duplicate_data(self):
        self.client.login(username="testuser", password="testpassword")
        existing_event = Event.objects.get(pk=self.event.id)
        response = self.client.post(
            reverse("events:update-event", args=[existing_event.id]),
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
        )

    def test_event_detail_view(self):
        url = reverse("events:event-detail", args=(self.event.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Event")
        self.assertContains(response, "Test Location")
        self.assertContains(response, "100")
        self.assertContains(response, "testuser")


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
        # Make the POST request again to toggle the status to 'withdrawn'
        response = self.client.post(url)
        # Fetch the updated join object and check its status
        join.refresh_from_db()
        self.assertEqual(join.status, WITHDRAWN)
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
        self.assertEqual(self.join_request.status, APPROVED)

    def test_reject_join_request(self):
        self.client.login(username="testcreator", password="testpassword")
        url = reverse("events:reject-request", args=[self.event.id, self.user.id])
        response = self.client.post(url)
        self.join_request.refresh_from_db()
        self.assertEqual(response.status_code, 302)
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
        self.client.login(username="testuser", password="testpassword")
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
