# appname/urls.py
from django.urls import path
from .views import Location_autocomplete

urlpatterns = [
    path("autocomplete/", Location_autocomplete, name="location-autocomplete"),
]
