from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, Http404
from .forms import EventsForm
from django.urls import reverse
from .models import Event, Location, EventJoin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.serializers import serialize
import json
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from .constants import PENDING, APPROVED, WITHDRAWN, REJECTED, REMOVED
from django.utils import timezone
from .forms import EventFilterForm
import pytz


# Existing imports and index view function...


def index(request):
    # Set the timezone to New York and get the current time
    ny_timezone = pytz.timezone("America/New_York")
    current_time_ny = timezone.now().astimezone(ny_timezone)

    # Filter events that are active and whose end time is greater than the current time in NY
    events = Event.objects.filter(
        end_time__gt=current_time_ny, is_active=True
    ).order_by("-start_time")

    # Initialize the form with request.GET or None
    form = EventFilterForm(request.GET or None)

    if request.GET and form.is_valid():
        start_time_ny = None
        end_time_ny = None

        # Start Time filter
        if form.cleaned_data["start_time"]:
            start_time_ny = form.cleaned_data["start_time"].astimezone(ny_timezone)
            if start_time_ny < current_time_ny:
                # Return an error message if start time is in the past
                return render(
                    request,
                    "events/events.html",
                    {
                        "events": events,
                        "form": form,
                        "error": "Start time cannot be in the past.",
                    },
                )
            events = events.filter(start_time__gte=start_time_ny)

        # End Time filter
        if form.cleaned_data["end_time"]:
            end_time_ny = form.cleaned_data["end_time"].astimezone(ny_timezone)
            if end_time_ny <= (start_time_ny or current_time_ny):
                # Return an error message if end time is before start time
                return render(
                    request,
                    "events/events.html",
                    {
                        "events": events,
                        "form": form,
                        "error": "End time cannot be before start time.",
                    },
                )
            events = events.filter(end_time__lte=end_time_ny)

        # Capacity filter
        min_capacity = form.cleaned_data.get("min_capacity")
        max_capacity = form.cleaned_data.get("max_capacity")

        if min_capacity is not None and max_capacity is not None:
            if min_capacity > max_capacity:
                # Return an error message if min capacity is greater than max capacity
                return render(
                    request,
                    "events/events.html",
                    {
                        "events": events,
                        "form": form,
                        "error": "Minimum capacity cannot be greater than maximum capacity.",
                    },
                )
            events = events.filter(
                capacity__gte=min_capacity, capacity__lte=max_capacity
            )

    # If the form was not submitted or is not valid, instantiate a new form
    else:
        form = EventFilterForm()

    # Prepare the context with events and form
    context = {
        "events": events,
        "form": form,
    }

    # If there are no events after filtering, add a message to the context
    if not events:
        context["message"] = "No events that fit your schedule? How about CREATING one?"

    # Render the events page with the context
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
    location = event.event_location
    join_status = None
    # attempt to see if the user has logged in
    if request.user.is_authenticated:
        try:
            join = EventJoin.objects.get(user=request.user, event=event)
            join_status = join.status
        except EventJoin.DoesNotExist:
            # if the user has no join record
            pass
    approved_join = event.eventjoin_set.filter(status=APPROVED)
    pending_join = event.eventjoin_set.filter(status=PENDING)
    approved_join_count = approved_join.count()
    pending_join_count = pending_join.count()

    context = {
        "event": event,
        "join_status": join_status,
        "pending_join": pending_join,
        "approved_join": approved_join,
        "approved_join_count": approved_join_count,
        "pending_join_count": pending_join_count,
        "location": location,
        "APPROVED": APPROVED,
        "PENDING": PENDING,
        "WITHDRAWN": WITHDRAWN,
        "REJECTED": REJECTED,
        "REMOVED": REMOVED,
    }
    return render(request, "events/event-detail.html", context)


@login_required
@require_POST
def toggleJoinRequest(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    # Prevent the creator from joining their own event
    if request.user == event.creator:
        messages.warning(
            request, "As the creator of the event, you cannot join it as a participant."
        )
        return redirect("events:event-detail", event_id=event.id)
    join, created = EventJoin.objects.get_or_create(user=request.user, event=event)
    # If a request was just created, it's already in 'pending' state
    # If it exists, toggle between 'pending' and 'withdrawn'
    if not created:
        if join.status == PENDING:
            join.status = WITHDRAWN
        else:
            join.status = PENDING
        join.save()

    return redirect("events:event-detail", event_id=event.id)


@login_required
@require_POST
def creatorApproveRequest(request, event_id, user_id):
    with transaction.atomic():
        event = get_object_or_404(Event, id=event_id)
        if request.user != event.creator:
            # handle the error when the user is not the creator of the event
            return redirect("events:event-detail", event_id=event.id)
        try:
            # Lock the participant row for updating
            join = EventJoin.objects.select_for_update().get(
                event_id=event_id, user_id=user_id
            )
        except EventJoin.DoesNotExist:
            raise Http404("Participant not found.")
        approved_join_count = EventJoin.objects.filter(
            event=event, status=APPROVED
        ).count()
        if approved_join_count + 1 >= event.capacity:
            messages.warning(request, "The event has reached its capacity.")
        else:
            if join.status == PENDING:
                join.status = APPROVED
                join.save()
                messages.success(request, "Request approved")
        return redirect("events:event-detail", event_id=event.id)


@login_required
@require_POST
def creatorRejectRequest(request, event_id, user_id):
    event = get_object_or_404(Event, id=event_id)
    user = get_object_or_404(User, id=user_id)
    if request.user != event.creator:
        # handle the error when the user is not the creator of the event
        return redirect("events:event-detail", event_id=event.id)
    join = get_object_or_404(EventJoin, event=event, user=user)
    if join.status == PENDING:
        join.status = REJECTED
        join.save()
    return redirect("events:event-detail", event_id=event.id)


@login_required
@require_POST
def creatorRemoveApprovedRequest(request, event_id, user_id):
    event = get_object_or_404(Event, id=event_id)
    user = get_object_or_404(User, id=user_id)
    if request.user != event.creator:
        # handle the error when the user is not the creator of the event
        return redirect("events:event-detail", event_id=event.id)
    join = get_object_or_404(EventJoin, event=event, user=user)
    if join.status == APPROVED:
        join.status = REMOVED
        join.save()
    return redirect("events:event-detail", event_id=event.id)
    return render(request, "events/event-detail.html", {"event": event})


# Map Code


def get_data(request):
    location_data = Event.objects.filter(is_active=True)
    serialized_data = serialize("json", location_data)
    serialized_data = json.loads(serialized_data)
    return JsonResponse({"location_data": serialized_data})


def get_locations(request):
    locations = Location.objects.all()
    serialized_data = serialize("json", locations)
    serialized_data = json.loads(serialized_data)
    return JsonResponse({"locations": serialized_data})
