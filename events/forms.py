from django import forms
from .models import Event
from tags.models import Tag


class EventsForm(forms.Form):
    model = Event
    fields = ["event_name", "start_time", "end_time", "capacity", "tags"]


class EventFilterForm(forms.Form):
    start_time = forms.DateTimeField(required=False)
    end_time = forms.DateTimeField(required=False)
    min_capacity = forms.IntegerField(min_value=0, required=False)
    max_capacity = forms.IntegerField(min_value=0, required=False)
    tags = forms.ModelChoiceField(
        queryset=Tag.objects.all(), empty_label="Select a Tag", required=False
    )
