from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from .forms import EventsForm
from django.urls import reverse
from .models import Event, Location
from django.contrib.auth.decorators import login_required
from django.utils import timezone

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
        if not event_name:
            return HttpResponse("Event name cannot be empty.")

        if not start_time:
            return HttpResponse("Start time is required.")

        start_time = timezone.make_aware(
            timezone.datetime.strptime(start_time, "%Y-%m-%dT%H:%M")
        )
        if start_time < timezone.now():
            return HttpResponse("Start time cannot be in the past.")

        if not end_time:
            return HttpResponse("End time is required.")

        end_time = timezone.make_aware(
            timezone.datetime.strptime(end_time, "%Y-%m-%dT%H:%M")
        )
        if end_time < start_time:
            return HttpResponse("End time cannot be earlier than start time.")

        if not capacity:
            return HttpResponse("Capacity is required.")
        try:
            capacity = int(capacity)
            if capacity < 0:
                return HttpResponse("Capacity must be a non-negative number.")
        except ValueError:
            return HttpResponse("Capacity must be a valid number.")

        if not event_location_id:
            return HttpResponse("Event location is required.")

        try:
            event_location_id = int(event_location_id)
            if event_location_id <= 0:
                return HttpResponse("Event location must be selected.")
        except ValueError:
            return HttpResponse("Invalid event location.")
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

        # Validate the data
        if not event_name:
            return redirect("events:index", error_message="Event name cannot be empty.")

        if not event_location_id:
            return redirect("events:index", error_message="Event location is required.")
        try:
            location_object = Location.objects.get(id=event_location_id)
        except Location.DoesNotExist:
            return redirect("events:index", error_message="Invalid event location.")

        if not start_time:
            return redirect("events:index", error_message="Start time is required.")
        start_time = timezone.make_aware(
            timezone.datetime.strptime(start_time, "%Y-%m-%dT%H:%M")
        )
        if start_time < timezone.now():
            return redirect(
                "events:index", error_message="Start time cannot be in the past."
            )

        if not end_time:
            return redirect("events:index", error_message="End time is required.")
        end_time = timezone.make_aware(
            timezone.datetime.strptime(end_time, "%Y-%m-%dT%H:%M")
        )
        if end_time < start_time:
            return redirect(
                "events:index",
                error_message="End time cannot be earlier than start time.",
            )

        if not capacity:
            return redirect("events:index", error_message="Capacity is required.")
        try:
            capacity = int(capacity)
            if capacity < 0:
                return redirect(
                    "events:index",
                    error_message="Capacity must be a non-negative number.",
                )
        except ValueError:
            return redirect(
                "events:index", error_message="Capacity must be a valid number."
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
        return redirect("events:index")


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
    print(request)
    print(event)
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
