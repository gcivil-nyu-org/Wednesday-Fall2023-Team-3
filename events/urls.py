from django.urls import path

from . import views

app_name = "events"
urlpatterns = [
    path("", views.index, name="index"),
    path("create-event", views.createEvent, name="create-event"),
    path("save-event/", views.saveEvent, name="save-event"),
    path("delete/<int:event_id>/", views.deleteEvent, name="delete-event"),
    path("update/<int:event_id>/", views.updateEvent, name="update-event"),
    path("<int:event_id>/", views.eventDetail, name="event-detail"),
    path("events/", views.get_data, name="events"),
    path("locations/", views.get_locations, name="locations"),
]
