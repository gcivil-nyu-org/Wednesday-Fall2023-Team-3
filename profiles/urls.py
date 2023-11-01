from django.urls import path
from .views import ProfileView

urlpatterns = [
    path('profile/', ProfileView.as_view(), name='profile'),
    # Add more URL patterns for tabs/events the user is going to
]