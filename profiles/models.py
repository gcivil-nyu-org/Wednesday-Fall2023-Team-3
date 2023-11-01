from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pics', null=True, blank=True)

    class Meta:
        app_label = 'profiles' 
class Event(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profile_events')
    event_name = models.CharField(max_length=255)

    class Meta:
        app_label = 'profiles'
    # Add more fields as needed for events

