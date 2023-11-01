# from django.db import models
# Create your models here.
from django.contrib.auth.models import User  # Import the User model
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="accounts_userprofile"
    )
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(
        upload_to="profile_pictures/", blank=True, null=True
    )

    # Add any other fields specific to your user profile

    def __str__(self):
        return self.user.username
