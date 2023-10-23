from django.db import models


# Create your models here.
class Location(models.Model):
    location_name = models.CharField(max_length=200, default="Prospect Park")
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)
    zipcode = models.IntegerField(default=0)
    address = models.CharField(max_length=400, default="Prospect Road")
    url = models.CharField(max_length=400, default="https://example.com")
    category = models.CharField(max_length=100, default="park")

    def __str__(self):
        return self.location_name
