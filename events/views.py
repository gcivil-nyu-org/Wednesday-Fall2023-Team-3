from django.shortcuts import render, redirect, get_object_or_404
from django.http import (
    HttpResponseRedirect,
    Http404,
    JsonResponse,
    HttpResponseBadRequest,
)
from .forms import EventsForm, CommentForm
from django.urls import reverse
from .models import Event, Location, EventJoin, Comment
from tags.models import Tag
from django.contrib.auth.decorators import login_required
from django.core.serializers import serialize
import json
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from .constants import PENDING, APPROVED, WITHDRAWN, REJECTED, REMOVED
from django.utils import timezone
from .forms import EventFilterForm
from datetime import datetime
import pytz
from django.db.models import Q


# Existing imports and index view function...


def index(request):
    # Set the timezone to New York and get the current time
    ny_timezone = pytz.timezone("America/New_York")
    current_time_ny = timezone.now().astimezone(ny_timezone)

    # Filter events that are active and whose end time is greater than the current time in NY
    search_query = request.GET.get(
        "search", ""
    )  # Get the search query from the URL parameter
    locations = Location.objects.filter(location_name__icontains=search_query)
    event_ids = [location.id for location in locations]
    events = Event.objects.filter(
        Q(event_name__icontains=search_query) | Q(event_location__in=event_ids)
    )
    events = events.filter(end_time__gt=current_time_ny, is_active=True).order_by(
        "-start_time"
    )

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

        # Tag Filter
        tags = form.cleaned_data.get("tags")
        if tags is None:
            events = events
        else:
            events = events.filter(tags=tags)

    # If the form was not submitted or is not valid, instantiate a new form
    else:
        form = EventFilterForm()
    # Filter events that are active and end time is greater than current time in NY

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
    tag = Tag.objects.all()
    event = get_object_or_404(Event, pk=event_id)

    if request.method == "POST":
        # Update the event with data from the form
        event_location_id = request.POST.get("event_location_id")
        event_name = request.POST.get("event_name")
        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")
        capacity = request.POST.get("capacity")
        selectedtags = request.POST.getlist("selected_tags")
        tags = Tag.objects.filter(tag_name__in=selectedtags)

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
                new_capacity = int(capacity)
                if new_capacity < 0:
                    errors["capacity"] = "Capacity must be a non-negative number."
                else:
                    # New capacity check against approved participants
                    approved_participants_count = EventJoin.objects.filter(
                        event=event, status=APPROVED
                    ).count()
                    if new_capacity < approved_participants_count:
                        errors[
                            "capacity"
                        ] = "Capacity cannot be less than the number of approved participants"
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
                    if (
                        Event.objects.filter(
                            event_name=event_name,
                            event_location=location_object,
                            start_time=start_time,
                            end_time=end_time,
                            is_active=True,
                        )
                        .exclude(pk=event_id)
                        .exists()
                    ):
                        errors[
                            "similar_event_error"
                        ] = "An event with these details already exists."
            except ValueError:
                errors["event_location_id"] = "Invalid event location."

        description = request.POST.get("description", "")

        if errors:
            # Return a JSON response with a 400 status code and the error messages
            return JsonResponse(errors, status=400)
        location_object = Location.objects.get(id=event_location_id)
        event.event_location = location_object
        event.event_name = event_name
        event.start_time = start_time
        event.end_time = end_time
        event.capacity = capacity
        event.description = description
        event.save()
        event.tags.set(tags)
        return redirect("events:index")  # Redirect to the event list or a success page

    return render(request, "events/update-event.html", {"event": event, "tags": tag})


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

        selectedtags = request.POST.getlist("selected_tags")
        tags = Tag.objects.filter(tag_name__in=selectedtags)
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

        description = request.POST.get("description", "")

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
            description=description,
        )

        event.save()
        event.tags.set(tags)

        return HttpResponseRedirect(reverse("events:index"))

    except KeyError:
        return JsonResponse({"error": "Invalid request data."}, status=400)


@login_required
def createEvent(request):
    tag = Tag.objects.all()
    if request.method == "POST":
        form = EventsForm(request.POST)
        if form.is_valid():
            return redirect("events:index")
    else:
        form = EventsForm()
    return render(request, "events/create-event.html", {"form": form, "tags": tag})


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

    comment_form = CommentForm()
    creator_comments_only = request.GET.get("creator_comments_only") == "true"

    if creator_comments_only:
        comments = (
            event.comments.filter(parent__isnull=True)
            .filter(is_active=True)
            .filter(user=event.creator)
        )
    else:
        comments = event.comments.filter(parent__isnull=True).filter(is_active=True)
    comments_with_replies = []
    for comment in comments:
        if request.user == event.creator or request.user == comment.user:
            replies = comment.replies.filter(is_active=True)
        else:
            replies = comment.replies.filter(is_active=True).filter(is_private=False)
        comments_with_replies.append((comment, replies))

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
        "comment_form": comment_form,
        "comments_with_replies": comments_with_replies,
        "creator_comments_only": creator_comments_only,
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


# Comment related views
@login_required
@require_POST
def addComment(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    parent_id = request.POST.get("parent_id")
    if parent_id:
        # handle the case when it's a reply of a reply
        return HttpResponseBadRequest("Cantnot reply to a nested comment")
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.user = request.user
        comment.event = event
        comment.save()
        return redirect(
            "events:event-detail", event_id=event.id
        )  # redirect to event detail page
    else:
        for error in form.errors:
            messages.warning(request, f"{error}: :{form.errors[error]}")
        return redirect(
            "events:event-detail", event_id=event.id
        )  # redirect to event detail page


@login_required
@require_POST
def addReply(request, event_id, comment_id):
    event = get_object_or_404(Event, id=event_id)
    parent_comment = get_object_or_404(Comment, id=comment_id)
    form = CommentForm(request.POST)
    if not parent_comment.is_active:
        messages.warning(request, "You cannot reply to a deleted comment.")
        return redirect("events:event-detail", event_id=event.id)
    if form.is_valid():
        reply = form.save(commit=False)
        reply.user = request.user
        reply.event = event
        # make sure that the parent comment is a comment not a reply
        if parent_comment.parent is None:
            reply.parent = parent_comment
            if parent_comment.is_private:
                reply.is_private = True
        else:
            # handle the case when it's a reply of a reply
            return HttpResponseBadRequest("Cantnot reply to a nested comment")
        reply.save()
        return redirect(
            "events:event-detail", event_id=event.id
        )  # redirect to event detail page
    else:
        for error in form.errors:
            messages.warning(request, f"{error}: :{form.errors[error]}")
        return redirect(
            "events:event-detail", event_id=event.id
        )  # redirect to event detail page


@login_required
@require_POST
def deleteComment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    # only commenter and event creator can delete a comment/reply
    if request.user != comment.user and request.user != comment.event.creator:
        return redirect("events:event-detail", event_id=comment.event.id)

    if request.POST.get("action") == "delete":
        # only comment with no replies can be deleted
        if not comment.replies.exists():
            comment.is_active = False
            comment.save()
            return redirect("events:event-detail", event_id=comment.event.id)
        else:
            messages.warning(
                request,
                "You can't delete this comment. There're replies under this comment.",
            )
            return redirect("events:event-detail", event_id=comment.event.id)
    return redirect("events:event-detail", event_id=comment.event.id)
