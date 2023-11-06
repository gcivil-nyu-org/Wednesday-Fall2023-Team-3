from django.test import TestCase
from django.urls import reverse
from .models import Event, Location
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime
from django.contrib.auth import authenticate
import pytz


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
        isloggedin = self.client.login(username="testuser", password="testpassword")
        print(isloggedin)
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
        response = self.client.post(url, updated_data)

        self.assertEqual(response.status_code, 200)  # Should redirect
        self.assertEqual(
            Event.objects.get(pk=self.event.id).event_name, "Test Event"
        )  # Verify data was updated


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


class EventValidationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.location = Location.objects.create(location_name="Location 1")

    def test_update_event_with_valid_data(self):
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
        self.assertEqual(updated_event.event_name, "Event 1")

    def test_update_event_with_invalid_data(self):
        user = User.objects.create_user("testuser2", password="testpassword")
        user = authenticate(username="testuser", password="testpassword")
        self.client.login(request=None, user=user)
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

        self.assertEqual(response.status_code, 302)  # Should stay on the same page

    def test_save_event_with_valid_data(self):
        all_users = User.objects.all()

        # Iterate through the users and print their details
        for user in all_users:
            print(f"User ID: {user.id}")
            print(f"Username: {user.username}")
            login_successful = self.client.login(request=None, user=user)
        print(login_successful)
        # new_york_tz = pytz.timezone("America/New_York")
        # current_time_ny = datetime.now(new_york_tz)
        # start_time = current_time_ny + timezone.timedelta(hours=1)
        # end_time = current_time_ny + timezone.timedelta(hours=2)
        # start_time = start_time.strftime("%Y-%m-%dT%H:%M")
        # end_time = end_time.strftime("%Y-%m-%dT%H:%M")
        # user = authenticate(username="testuser", password="testpassword")
        # response = self.client.post(
        #     reverse("events:save-event"),
        #     {
        #         "event_location_id": self.location.id,
        #         "event_name": "New Event",
        #         "start_time": start_time,
        #         "end_time": end_time,
        #         "capacity": 50,
        #     },
        # )
        # redirected_url = response.url

        # Use client to make another GET request to the redirected URL
        # redirected_response = self.client.get(redirected_url)
        # print(response.content)
        # print(redirected_response.content)
        # self.assertEqual(response.status_code, 200)  # Redirects to events:index

        # Check if a new event was created in the database
        # new_event = Event.objects.get(event_name='New Event')
        # self.assertEqual(new_event.capacity, 50)

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
        self.assertEqual(response.status_code, 302)  # Should stay on the same page
