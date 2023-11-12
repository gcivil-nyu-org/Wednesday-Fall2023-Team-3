from django.urls import path
from . import views

app_name = "chats"
urlpatterns = [
    path("<str:recipient_id>/", views.chatting, name="chat-with-user"),
    # Add other chat app URLs here
]
