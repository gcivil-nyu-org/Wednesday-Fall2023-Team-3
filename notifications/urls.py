# notifications/urls.py
from django.urls import path
from . import views
from .views import notifications

app_name = "notifications"

urlpatterns = [
    path("", notifications, name="notifications"),
    path("view-notifications/", views.view_notifications, name="view-notifications"),
    path(
        "mark-as-read/<int:notification_id>/",
        views.mark_notification_as_read,
        name="mark-notification-as-read",
    ),
]
