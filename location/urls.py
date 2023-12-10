# appname/urls.py
from django.urls import path
from .views import Location_autocomplete, manage_favorite_locations, add_favorite_location, remove_favorite_location

app_name = "locations"

urlpatterns = [
    path("autocomplete/", Location_autocomplete, name="location-autocomplete"),
    path('manage-favorite-locations/', manage_favorite_locations, name='manage_favorite_locations'),
    path('add-favorite-location/', add_favorite_location, name='add_favorite_location'),
    path('remove-favorite-location/<int:location_id>/', remove_favorite_location, name='remove_favorite_location'),
]
