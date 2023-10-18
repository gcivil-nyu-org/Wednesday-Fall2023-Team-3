from django.urls import path

from . import views

app_name = 'events'
urlpatterns = [

    path('', views.index, name='index'),
    path('create-event', views.createEvent, name='create-event'),
    path('save-event/', views.saveEvent, name='save-event'),
    path('delete/<int:event_id>/', views.deleteEvent, name='delete-event'),
    path('my-events/', views.myEvents, name='my-events'),
]