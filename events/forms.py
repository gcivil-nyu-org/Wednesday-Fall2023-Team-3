from django import forms
from .models import Event

class EventsForm(forms.Form):
    model = Event
    fields = ['event_name']

