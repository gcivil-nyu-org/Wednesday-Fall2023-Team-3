from django.db import models
from location.models import Location
from django.contrib.auth.models import User

# Create your models here.


class Event(models.Model):
    event_name = models.CharField(max_length=200)
    event_location = models.ForeignKey(Location, on_delete=models.CASCADE, default=261)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    capacity = models.IntegerField()
    is_active = models.BooleanField(default=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, default=1)

    def __str__(self):
        return self.event_name

class EventJoin(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('removed', 'Removed'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default='pending')

    class Meta:
        unique_together = ('user', 'event')

