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
    path(
        "<int:event_id>/toggle-join/,",
        views.toggleJoinRequest,
        name="toggle-join-request",
    ),
    path(
        "<int:event_id>/approve/<int:user_id>/",
        views.creatorApproveRequest,
        name="approve-request",
    ),
    path(
        "<int:event_id>/reject/<int:user_id>/",
        views.creatorRejectRequest,
        name="reject-request",
    ),
    path(
        "<int:event_id>/remove/<int:user_id>/",
        views.creatorRemoveApprovedRequest,
        name="remove-approved-request",
    ),
    path("<int:event_id>/add-comment/", views.addComment, name="add-comment"),
    path(
        "<int:event_id>/comment/<int:comment_id>/reply/",
        views.addReply,
        name="add-reply",
    ),
    path('delete-comment/<int:comment_id>/', views.deleteComment, name='delete-comment'),
]
