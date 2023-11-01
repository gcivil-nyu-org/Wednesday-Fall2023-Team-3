from django.db import models
from location.models import Location
from django.contrib.auth.models import User
from profiles.models import (
    Event as ProfileEvent,
)  # Import the 'Event' model from the 'profiles' app

# Create your models here.


class Event(models.Model):
    event_name = models.CharField(max_length=200)
    event_location = models.ForeignKey(Location, on_delete=models.CASCADE, default=261)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    capacity = models.IntegerField()
    is_active = models.BooleanField(default=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    creator = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_events"
    )
    profile_event = models.ForeignKey(
        ProfileEvent,
        on_delete=models.CASCADE,
        related_name="related_profile_events",
        null=True,
        blank=True,
    )

    class Meta:
        app_label = "events"

    def __str__(self):
        return self.event_name
