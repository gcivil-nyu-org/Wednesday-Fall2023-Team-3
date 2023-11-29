# profiles/urls.py
from django.urls import path
from .views import view_profile  # ,edit_profile

urlpatterns = [
    path("profile/<int:userprofile_id>", view_profile, name="view_profile"),
    # path("profile/edit/", edit_profile, name="edit_profile"),
]
