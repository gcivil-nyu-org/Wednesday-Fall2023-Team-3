from django.urls import path
from . import views

urlpatterns = [
    path("show_map/", views.show_map, name="show_map"),
    path("get_data/", views.get_data, name="get_data"),
    path("get_locations/", views.get_locations, name="get_locations"),
]
