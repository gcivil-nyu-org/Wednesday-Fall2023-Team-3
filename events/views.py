from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from .forms import EventsForm
from django.urls import reverse
from .models import Event, Location


# Create your views here.


def index(request):
    events = Event.objects.filter(is_active=True)
    return render(request, "events/events.html", {"events": events})


def saveEvent(request):
    event = Event()
    try:
        event_name = request.POST["event_name"]
        event_location_id = request.POST["event_location_id"]
        location_object = Location.objects.get(id=event_location_id)

        start_time = request.POST["start_time"]
        end_time = request.POST["end_time"]
        capacity = request.POST["capacity"]
    except (KeyError, Event.DoesNotExist):
        # Redisplay the question voting form.
        return redirect("events:index")
    else:
        event.event_name = event_name
        event.event_location = location_object
        event.start_time = start_time
        event.end_time = end_time
        event.capacity = capacity
        event.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse("events:index"))


def createEvent(request):
    if request.method == "POST":
        form = EventsForm(request.POST)
        if form.is_valid():
            return redirect("events:index")
    else:
        form = EventsForm()
    return render(request, "events/create-event.html", {"form": form})


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
