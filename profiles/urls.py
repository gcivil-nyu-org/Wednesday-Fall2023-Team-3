# profiles/urls.py
from django.urls import path
from .views import view_profile, edit_profile
from . import views

urlpatterns = [
    path("<int:userprofile_id>", view_profile, name="view_profile"),
    path(
        "<int:userprofile_id>/toggle-join/,",
        views.toggleFriendRequest,
        name="toggle-friend-request",
    ),
    path(
        "<int:userprofile_id>/approve/<int:user_id>/",
        views.userApproveRequest,
        name="approve-request",
    ),
    path(
        "<int:userprofile_id>/reject/<int:user_id>/",
        views.userRejectRequest,
        name="reject-request",
    ),
    path(
        "<int:userprofile_id>/remove/<int:user_id>/",
        views.userRemoveApprovedRequest,
        name="remove-approved-request",
    ),
    path("profile/edit/", edit_profile, name="edit_profile"),
    path("notifications/", views.display_notifications, name="display_notifications"),
]
