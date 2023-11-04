from django.test import TestCase
from django.urls import reverse
from .models import Event, Location
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class EventListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase
        user = User.objects.create_user(username="testuser", password="testpassword")
        location = Location.objects.create(location_name="Test Location")
        now = timezone.now()
        
        events = [
            Event(event_name="Past Event", event_location=location, start_time=now - timedelta(days=2), end_time=now - timedelta(days=1), capacity=50, creator=user),
            Event(event_name="Future Event", event_location=location, start_time=now + timedelta(days=1), end_time=now + timedelta(days=2), capacity=50, creator=user),
        ]
        Event.objects.bulk_create(events)

    def test_filter_events_by_date(self):
        login = self.client.login(username='testuser', password='testpassword')
        self.assertTrue(login)

        url = reverse('events:index')
        now = timezone.now()
        
        # Filter parameters should be based on your actual form fields
        response = self.client.get(url, {'start_time': now.date(), 'end_time': now.date() + timedelta(days=1)})
        
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context['events'],
            ['<Event: Future Event>'],
            ordered=False
        )
        self.assertNotContains(response, 'Past Event')

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
