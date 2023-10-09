from django.db import models

# Create your models here.
class Location(models.Model):
    location_name = models.CharField(max_length=200)
    latitude = models.FloatField()
    longitude = models.FloatField()
    zipcode = models.IntegerField()
    address = models.CharField(max_length=400)
    url = models.CharField(max_length=400)
    category = models.CharField(max_length=100)