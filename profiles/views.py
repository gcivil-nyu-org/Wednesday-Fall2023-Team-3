# profiles/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import ProfileForm
from django.http import Http404
from .models import UserProfile
from events.models import Event
from django.views.decorators.http import require_POST
from django.db import transaction
from django.contrib import messages
from .constants import (
    PENDING,
    APPROVED,
    WITHDRAWN,
    REJECTED,
    REMOVED,
)
from django.contrib.auth.models import User
from .models import UserFriends
from events.models import Notification, FavoriteLocation
from django.db.models import Q
from location.models import Location
@login_required
def view_profile(request, userprofile_id):
    user_profile = get_object_or_404(UserProfile, pk=userprofile_id)
    events = user_profile.user.event_set.filter(is_active=True)

    friend_status = None
    if request.user.is_authenticated:
        try:
            add_friend = UserFriends.objects.get(
                user=request.user, friends=user_profile
            )
            friend_status = add_friend.status
        except UserFriends.DoesNotExist:
            # if the user has no join record
            pass
    approved_request = user_profile.userfriends_set.filter(status=APPROVED)
    pending_request = approved_request
    if request.user == user_profile.user:
        pending_request = user_profile.userfriends_set.filter(status=PENDING)
    approved_request_count = approved_request.count()
    pending_request_count = pending_request.count()
    cond1 = Q(user=request.user.id)
    cond2 = Q(is_read__lte=0)
    unread_notifications = Notification.objects.filter(cond1 & cond2).order_by("-id")
    favorite_locations = FavoriteLocation.objects.filter(user=request.user)
    favorite_location_ids = [favorite_location.location.id for favorite_location in favorite_locations]
    favorite_locations_details = Location.objects.filter(id__in=favorite_location_ids)
    context = {
        "user_profile": user_profile,
        "events": events,
        "friend_status": friend_status,
        "pending_request": pending_request,
        "approved_request": approved_request,
        "approved_request_count": approved_request_count,
        "pending_request_count": pending_request_count,
        "APPROVED": APPROVED,
        "PENDING": PENDING,
        "WITHDRAWN": WITHDRAWN,
        "REJECTED": REJECTED,
        "REMOVED": REMOVED,
        "unread_notifications": unread_notifications,
        'favorite_locations': favorite_locations_details,
    }

    return render(request, "profiles/view_profile.html", context)


@login_required
@require_POST
def toggleFriendRequest(request, userprofile_id):
    receiver_user = get_object_or_404(UserProfile, id=userprofile_id)
    # Prevent the creator from joining their own event
    add_friend, created = UserFriends.objects.get_or_create(
        user=request.user, friends=receiver_user
    )
    # If a request was just created, it's already in 'pending' state
    # If it exists, toggle between 'pending' and 'withdrawn'
    if not created:
        if add_friend.status == PENDING:
            add_friend.status = WITHDRAWN
            Notification.objects.create(
                user=receiver_user.user,
                message=f"'{request.user}' has removed their request to be your friend.",
            )
        else:
            add_friend.status = PENDING
            Notification.objects.create(
                user=receiver_user.user,
                message=f"'{request.user}' has requested to be your friend.",
            )
        add_friend.save()
    else:
        Notification.objects.create(
            user=receiver_user.user,
            message=f"'{request.user}' has requested to be your friend.",
        )
    return redirect("profiles:view_profile", userprofile_id=userprofile_id)


@login_required
@require_POST
def userApproveRequest(request, userprofile_id, user_id):
    with transaction.atomic():
        try:
            # Lock the participant row for updating
            add_friend = UserFriends.objects.select_for_update().get(
                friends_id=userprofile_id, user_id=user_id
            )

        except UserFriends.DoesNotExist:
            raise Http404("User not found.")
        sender_user = get_object_or_404(UserProfile, user=add_friend.user)
        selfjoin, created = UserFriends.objects.get_or_create(
            user=add_friend.friends.user, friends=sender_user
        )

        if add_friend.status == PENDING:
            add_friend.status = APPROVED
            Notification.objects.create(
                user=add_friend.user,
                message=f"'{request.user}' has accepted your friend request.",
            )
            add_friend.save()
            selfjoin.status = APPROVED
            selfjoin.save()
        return redirect("profiles:view_profile", userprofile_id=userprofile_id)


@login_required
@require_POST
def userRejectRequest(request, userprofile_id, user_id):
    receiver_user = get_object_or_404(UserProfile, id=userprofile_id)
    user = get_object_or_404(User, id=user_id)
    add_friend = get_object_or_404(UserFriends, friends=receiver_user, user=user)
    sender_user = get_object_or_404(UserProfile, user=add_friend.user)
    selfjoin = get_object_or_404(
        UserFriends, friends=sender_user, user=add_friend.friends.user
    )

    if selfjoin.status == PENDING:
        selfjoin.status = REJECTED
        selfjoin.save()
    if add_friend.status == PENDING:
        add_friend.status = REJECTED
        Notification.objects.create(
            user=add_friend.user,
            message=f"'{request.user}' has rejected your friend request.",
        )
        add_friend.save()
    return redirect("profiles:view_profile", userprofile_id=userprofile_id)


@login_required
@require_POST
def userRemoveApprovedRequest(request, userprofile_id, user_id):
    receiver_user = get_object_or_404(UserProfile, id=userprofile_id)
    user = get_object_or_404(User, id=user_id)
    add_friend = get_object_or_404(UserFriends, friends=receiver_user, user=user)
    sender_user = get_object_or_404(UserProfile, user=add_friend.user)
    selfjoin = get_object_or_404(
        UserFriends, friends=sender_user, user=add_friend.friends.user
    )

    if selfjoin.status == APPROVED:
        selfjoin.status = REMOVED
        selfjoin.save()
    if add_friend.status == APPROVED:
        add_friend.status = REMOVED
        Notification.objects.create(
            user=add_friend.user,
            message=f"'{request.user}' has removed you from the friend list.",
        )
        add_friend.save()
    return redirect("profiles:view_profile", userprofile_id=userprofile_id)


@login_required
def edit_profile(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)

    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("profiles:view_profile", userprofile_id=user_profile.id)
        else:
            messages.error(
                request, "Error updating profile. Please correct the errors below."
            )
    else:
        form = ProfileForm(instance=user_profile)
    return render(request, "profiles/edit_profile.html", {"form": form})


@login_required
def display_notifications(request):
    if request.method == "POST":
        notification_id = request.POST.get("notification_id")
        if notification_id:
            Notification.objects.filter(id=notification_id).delete()
            return redirect("profiles:display_notifications")
    for notification in Notification.objects.filter(user=request.user.id):
        is_read = notification.is_read + 1
        if is_read > 2:
            is_read = 2
        Notification.objects.filter(id=notification.id).update(is_read=is_read)
    notifications = Notification.objects.filter(user=request.user.id).order_by("-id")
    cond1 = Q(user=request.user.id)
    cond2 = Q(is_read__lte=0)
    unread_notifications = Notification.objects.filter(cond1 & cond2).order_by("-id")
    context = {
        "notifications": notifications,
        "unread_notifications": unread_notifications,
    }
    return render(request, "profiles/notifications.html", context)
