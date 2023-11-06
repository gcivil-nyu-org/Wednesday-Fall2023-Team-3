from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, JsonResponse
from .forms import EventsForm
from django.urls import reverse
from .models import Event, Location
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import pytz
from datetime import datetime

# Create your views here.


def index(request):
    events = Event.objects.filter(is_active=True)
    return render(request, "events/events.html", {"events": events})


@login_required
def updateEvent(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    if request.method == "POST":
        # Update the event with data from the form
        event_location_id = request.POST.get("event_location_id")
        event_name = request.POST.get("event_name")
        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")
        capacity = request.POST.get("capacity")

        # Create a dictionary to store validation errors
        errors = {}

        if not event_name:
            errors["event_name"] = "Event name cannot be empty."

        if not start_time:
            errors["start_time"] = "Start time is required."
        else:
            start_time = timezone.make_aware(
                timezone.datetime.strptime(start_time, "%Y-%m-%dT%H:%M")
            )
            new_york_tz = pytz.timezone("America/New_York")
            current_time_ny = datetime.now(new_york_tz)
            if start_time < current_time_ny:
                errors["start_time"] = "Start time cannot be in the past."

        if not end_time:
            errors["end_time"] = "End time is required."
        else:
            end_time = timezone.make_aware(
                timezone.datetime.strptime(end_time, "%Y-%m-%dT%H:%M")
            )
            if end_time < start_time:
                errors["end_time"] = "End time cannot be earlier than start time."

        if not capacity:
            errors["capacity"] = "Capacity is required."
        else:
            try:
                capacity = int(capacity)
                if capacity < 0:
                    errors["capacity"] = "Capacity must be a non-negative number."
            except ValueError:
                errors["capacity"] = "Capacity must be a valid number."

        if not event_location_id:
            errors["event_location_id"] = "Event location is required."
        else:
            try:
                event_location_id = int(event_location_id)
                if event_location_id <= 0:
                    errors["event_location_id"] = "Event location must be selected."
                else:
                    location_object = Location.objects.get(id=event_location_id)
                    if Event.objects.filter(
                        event_name=event_name,
                        event_location=location_object,
                        start_time=start_time,
                        end_time=end_time,
                        is_active=True,
                    ).exists():
                        errors[
                            "similar_event_error"
                        ] = "An event with these details already exists."
            except ValueError:
                errors["event_location_id"] = "Invalid event location."
        if errors:
            # Return a JSON response with a 400 status code and the error messages
            return JsonResponse(errors, status=400)
        location_object = Location.objects.get(id=event_location_id)
        event.event_location = location_object
        event.event_name = event_name
        event.start_time = start_time
        event.end_time = end_time
        event.capacity = capacity
        event.save()

        return redirect("events:index")  # Redirect to the event list or a success page

    return render(request, "events/update-event.html", {"event": event})


@login_required
def saveEvent(request):
    event = Event()
    try:
        event_name = request.POST.get("event_name")
        event_location_id = request.POST.get("event_location_id")
        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")
        capacity = request.POST.get("capacity")
        creator = request.user
        # Create a dictionary to hold validation errors
        errors = {}
        # Validate the data
        if not event_name:
            errors["event_name"] = "Event name cannot be empty."

        if not event_location_id:
            errors["event_location_id"] = "Event location is required."
        else:
            try:
                location_object = Location.objects.get(id=event_location_id)
            except Location.DoesNotExist:
                errors["event_location_id"] = "Invalid event location."
        if not start_time:
            errors["start_time"] = "Start time is required."
        else:
            start_time = timezone.make_aware(
                timezone.datetime.strptime(start_time, "%Y-%m-%dT%H:%M")
            )
            new_york_tz = pytz.timezone("America/New_York")
            current_time_ny = datetime.now(new_york_tz)
            if start_time < current_time_ny:
                errors["start_time"] = "Start time cannot be in the past."

        if not end_time:
            errors["end_time"] = "End time is required."
        else:
            end_time = timezone.make_aware(
                timezone.datetime.strptime(end_time, "%Y-%m-%dT%H:%M")
            )
            if end_time < start_time:
                errors["end_time"] = "End time cannot be earlier than start time."

        if not capacity:
            errors["capacity"] = "Capacity is required."
        else:
            try:
                capacity = int(capacity)
                if capacity < 0:
                    errors["capacity"] = "Capacity must be a non-negative number."
            except ValueError:
                errors["capacity"] = "Capacity must be a valid number."

        if errors:
            # Return a 400 Bad Request response with JSON error messages
            return JsonResponse(errors, status=400)
        if Event.objects.filter(
            event_name=event_name,
            event_location=location_object,
            start_time=start_time,
            end_time=end_time,
            is_active=True,
        ).exists():
            error_message = "An event with these details already exists."
            return HttpResponseRedirect(
                reverse("events:index") + f"?error_message={error_message}"
            )
        # All validations passed; create the event
        event = Event(
            event_name=event_name,
            event_location=location_object,
            start_time=start_time,
            end_time=end_time,
            capacity=capacity,
            creator=creator,
        )
        event.save()

        return HttpResponseRedirect(reverse("events:index"))

    except KeyError:
        return JsonResponse({"error": "Invalid request data."}, status=400)


@login_required
def createEvent(request):
    if request.method == "POST":
        form = EventsForm(request.POST)
        if form.is_valid():
            return redirect("events:index")
    else:
        form = EventsForm()
    return render(request, "events/create-event.html", {"form": form})


@login_required
def deleteEvent(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    if request.method == "POST":
        if request.POST.get("action") == "delete":
            # Set is_active to False instead of deleting
            event.is_active = False
            event.save()
            return redirect("events:index")
    return redirect("events:index")


def eventDetail(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    return render(request, "events/event-detail.html", {"event": event})
