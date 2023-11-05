from django.test import TestCase, Client
from django.urls import reverse
from .models import Event, Location, EventJoin
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class UpdateEventViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.location = Location.objects.create(location_name="Test Location")
        self.event = Event.objects.create(
            event_name="Test Event",
            start_time=timezone.now() + timedelta(days=5),
            end_time=timezone.now() + timedelta(days=6),
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
            "start_time": timezone.now() + timedelta(hours=30),
            "end_time": timezone.now() + timedelta(hours=35),
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
            start_time=timezone.now() + timedelta(hours=10),
            end_time=timezone.now() + timedelta(hours=15),
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
        self.event = Event.objects.create(
            event_name="Test Event",
            event_location=self.location,
            start_time=timezone.now() + timedelta(hours=3),
            end_time=timezone.now() + timedelta(hours=5),
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
        self.assertEqual(join.status, "pending")
        # Make the POST request again to toggle the status to 'withdrawn'
        response = self.client.post(url)
        # Fetch the updated join object and check its status
        join.refresh_from_db()
        self.assertEqual(join.status, "withdrawn")
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
        self.event = Event.objects.create(
            event_name="Test Event",
            event_location=self.location,
            start_time=timezone.now() + timedelta(hours=12),
            end_time=timezone.now() + timedelta(hours=15),
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
        self.assertEqual(self.join_request.status, "approved")

    def test_reject_join_request(self):
        self.client.login(username="testcreator", password="testpassword")
        url = reverse("events:reject-request", args=[self.event.id, self.user.id])
        response = self.client.post(url)
        self.join_request.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.join_request.status, "rejected")

    def test_non_creator_cannot_approve(self):
        self.client.logout()
        self.client.login(username="testuser", password="testpassword")
        url = reverse("events:approve-request", args=[self.event.id, self.user.id])
        response = self.client.post(url)
        self.join_request.refresh_from_db()
        self.assertNotEqual(self.join_request.status, "approved")
        self.assertEqual(response.status_code, 302)  # redirect

    def test_non_creator_cannot_reject(self):
        self.client.logout()
        self.client.login(username="testuser", password="testpassword")
        url = reverse("events:reject-request", args=[self.event.id, self.user.id])
        response = self.client.post(url)
        self.join_request.refresh_from_db()
        self.assertNotEqual(self.join_request.status, "rejected")
        self.assertEqual(response.status_code, 302)


class EventCreatorApproveLimistTest(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            username="testcreator", password="testpassword"
        )
        self.location = Location.objects.create(
            location_name="Test Location",
        )
        self.event = Event.objects.create(
            event_name="Test Event",
            event_location=self.location,
            start_time=timezone.now() + timedelta(hours=4),
            end_time=timezone.now() + timedelta(hours=5),
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
                self.assertEqual(self.join_requests[i].status, "approved")
            else:
                self.assertEqual(self.join_requests[i].status, "pending")


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
        self.event = Event.objects.create(
            event_name="Test Event",
            event_location=self.location,
            start_time=timezone.now() + timedelta(hours=50),
            end_time=timezone.now() + timedelta(hours=52),
            capacity=5,
            is_active=True,
            creator=self.creator,
        )
        self.join_request = EventJoin.objects.create(
            user=self.user, event=self.event, status="approved"
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
        self.assertEqual(self.join_request.status, "removed")

    def test_non_creator_cannot_remove(self):
        self.client.logout()
        self.client.login(username="testuser", password="testpassword")
        url = reverse(
            "events:remove-approved-request", args=[self.event.id, self.user.id]
        )
        response = self.client.post(url)
        self.join_request.refresh_from_db()
        self.assertNotEqual(self.join_request.status, "removed")
        self.assertEqual(response.status_code, 302)  # redirect
