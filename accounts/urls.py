from django.urls import path

from .views import SignUpView
from . import views

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path('', views.homepage, name='homepage'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
]
