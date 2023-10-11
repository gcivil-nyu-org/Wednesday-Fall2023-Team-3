from django.db import models

# Create your models here.
class Event(models.Model):
    event_name = models.CharField(max_length=200)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    capacity = models.IntegerField()

    def __str__(self):
        return self.event_name
    