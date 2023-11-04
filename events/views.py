from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from .forms import EventsForm
from django.urls import reverse
from .models import Event, Location
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .forms import EventFilterForm

# Create your views here.

def index(request):
    events = Event.objects.filter(end_time__gt=timezone.now(), is_active=True).order_by('-start_time')

    # Process the filter form
    if request.GET:
        form = EventFilterForm(request.GET)
        if form.is_valid():
            if form.cleaned_data['start_time']:
                events = events.filter(start_time__gte=form.cleaned_data['start_time'])
            if form.cleaned_data['end_time']:
                if form.cleaned_data['end_time'] <= timezone.now():
                    # Return an error message
                    # Handle this appropriately in your template
                    return render(request, "events/events.html", {"error": "End time cannot be in the past."})
                events = events.filter(end_time__lte=form.cleaned_data['end_time'])
    else:
        form = EventFilterForm()

    context = {
        "events": events,
        "form": form,
    }

    # If there are no events after filtering, add a message to the context
    if not events:
        context["message"] = "No events that fit your schedule? How about CREATING one?"

    return render(request, "events/events.html", context)



@login_required
def updateEvent(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    if request.method == "POST":
        # Update the event with data from the form
        event_location_id = request.POST["event_location_id"]
        location_object = Location.objects.get(id=event_location_id)
        event.event_location = location_object
        event.event_name = request.POST.get("event_name")
        event.start_time = request.POST.get("start_time")
        event.end_time = request.POST.get("end_time")
        event.capacity = request.POST.get("capacity")
        # Save the updated event
        event.save()

        return redirect("events:index")  # Redirect to the event list or a success page

    return render(request, "events/update-event.html", {"event": event})


@login_required
def saveEvent(request):
    event = Event()
    try:
        event_name = request.POST["event_name"]
        event_location_id = request.POST["event_location_id"]
        location_object = Location.objects.get(id=event_location_id)

        start_time = request.POST["start_time"]
        end_time = request.POST["end_time"]
        capacity = request.POST["capacity"]
        creator = request.user
    except (KeyError, Event.DoesNotExist):
        # Redisplay the question voting form.
        return redirect("events:index")
    else:
        event.event_name = event_name
        event.event_location = location_object
        event.start_time = start_time
        event.end_time = end_time
        event.capacity = capacity
        event.creator = creator
        event.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse("events:index"))


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
