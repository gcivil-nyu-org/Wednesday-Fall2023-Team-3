# profiles/models.py
from django.contrib.auth.models import User
from django.db import models
from events.models import Event
from events.constants import STATUS_CHOICES, PENDING


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(
        upload_to="profile_pics/", blank=True, null=True
    )
    created_events = models.ManyToManyField(Event, blank=True)

    def __str__(self):
        return self.user.username


class UserFriends(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    friends = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)

    class Meta:
        unique_together = ("user", "friends")

    def __str__(self):
        return f"{self.user.username} - {self.friends.user.username} - {self.get_status_display()}"


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)


def save_user_profile(sender, instance, **kwargs):
    try:
        instance.userprofile.save()
    except UserProfile.DoesNotExist:
        # If the UserProfile doesn't exist yet, create it
        UserProfile.objects.get_or_create(user=instance)


# Connect the signals
models.signals.post_save.connect(create_user_profile, sender=User)
models.signals.post_save.connect(save_user_profile, sender=User)
