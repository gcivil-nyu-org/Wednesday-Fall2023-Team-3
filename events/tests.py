from django.test import TestCase
from django.urls import reverse
from .models import Event, Location
from django.contrib.auth.models import User
from django.utils import timezone



class EventIndexViewFilterTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpassword'
        )
        self.location = Location.objects.create(location_name='Test Location')

        self.future_event = Event.objects.create(
            event_name='Future Event',
            start_time="2024-01-01T12:00",
            end_time="2024-01-01T14:00",
            capacity=100,
            event_location=self.location,
            is_active=True,
            creator=self.user,
        )

    def test_event_index_view_with_date_filter(self):
        # Ensure the datetime format matches what your application expects
        start_date_str = "2024-01-01T12:00"
        end_date_str = "2024-01-01T14:00"
        url = reverse('events:index')
        response = self.client.get(url, {'start_time': start_date_str, 'end_time': end_date_str})
        self.assertEqual(response.status_code, 200)
        # Assuming your events are passed to the template under the context variable 'events'
        events = response.context['events']
        self.assertIn(self.future_event, events)



class UpdateEventViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.location = Location.objects.create(location_name="Test Location")
        self.event = Event.objects.create(
            event_name="Test Event",
            start_time="2023-11-01T12:00",
            end_time="2023-11-01T14:00",
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
        self.client.login(username="testuser", password="testpassword")
        new_location = Location.objects.create(location_name="New Location")
        updated_data = {
            "event_name": "Updated Event",
            "start_time": "2023-11-01T13:00",
            "end_time": "2023-11-01T15:00",
            "capacity": 150,
            "event_location_id": new_location.id,
        }
        url = reverse("events:update-event", args=(self.event.id,))
        response = self.client.post(url, updated_data)

        self.assertEqual(response.status_code, 302)  # Should redirect
        self.assertEqual(
            Event.objects.get(pk=self.event.id).event_name, "Updated Event"
        )  # Verify data was updated


class EventDetailPageTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.location = Location.objects.create(
            location_name="Test Location",
        )
        self.event = Event.objects.create(
            event_name="Test Event",
            event_location=self.location,
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-01-01T09:00:00Z",
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
