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


@login_required
def view_profile(request, userprofile_id):
    user_profile = get_object_or_404(UserProfile, pk=userprofile_id)
    events = user_profile.user.event_set.filter(is_active=True)

    join_status = None
    if request.user.is_authenticated:
        try:
            join = UserFriends.objects.get(user=request.user, friends=user_profile)
            join_status = join.status
        except UserFriends.DoesNotExist:
            # if the user has no join record
            pass
    approved_join = user_profile.userfriends_set.filter(status=APPROVED)
    pending_join = approved_join
    if request.user == user_profile.user:
        pending_join = user_profile.userfriends_set.filter(status=PENDING)
    approved_join_count = approved_join.count()
    pending_join_count = pending_join.count()

    context = {
        "user_profile": user_profile,
        "events": events,
        "join_status": join_status,
        "pending_join": pending_join,
        "approved_join": approved_join,
        "approved_join_count": approved_join_count,
        "pending_join_count": pending_join_count,
        "APPROVED": APPROVED,
        "PENDING": PENDING,
        "WITHDRAWN": WITHDRAWN,
        "REJECTED": REJECTED,
        "REMOVED": REMOVED,
    }

    return render(request, "profiles/view_profile.html", context)


@login_required
@require_POST
def toggleFriendRequest(request, userprofile_id):
    receiver_user = get_object_or_404(UserProfile, id=userprofile_id)
    # Prevent the creator from joining their own event
    join, created = UserFriends.objects.get_or_create(
        user=request.user, friends=receiver_user
    )
    # If a request was just created, it's already in 'pending' state
    # If it exists, toggle between 'pending' and 'withdrawn'
    if not created:
        if join.status == PENDING:
            join.status = WITHDRAWN
        else:
            join.status = PENDING
        join.save()
    return redirect("profiles:view_profile", userprofile_id=userprofile_id)


@login_required
@require_POST
def userApproveRequest(request, userprofile_id, user_id):
    with transaction.atomic():
        try:
            # Lock the participant row for updating
            join = UserFriends.objects.select_for_update().get(
                friends_id=userprofile_id, user_id=user_id
            )

        except UserFriends.DoesNotExist:
            raise Http404("User not found.")
        sender_user = get_object_or_404(UserProfile, user=join.user)
        selfjoin, created = UserFriends.objects.get_or_create(
            user=join.friends.user, friends=sender_user
        )

        if join.status == PENDING:
            join.status = APPROVED
            join.save()
            selfjoin.status = APPROVED
            selfjoin.save()
        return redirect("profiles:view_profile", userprofile_id=userprofile_id)


@login_required
@require_POST
def userRejectRequest(request, userprofile_id, user_id):
    receiver_user = get_object_or_404(UserProfile, id=userprofile_id)
    user = get_object_or_404(User, id=user_id)
    join = get_object_or_404(UserFriends, friends=receiver_user, user=user)
    sender_user = get_object_or_404(UserProfile, user=join.user)
    selfjoin = get_object_or_404(
        UserFriends, friends=sender_user, user=join.friends.user
    )

    if selfjoin.status == PENDING:
        selfjoin.status = REJECTED
        selfjoin.save()
    if join.status == PENDING:
        join.status = REJECTED
        join.save()
    return redirect("profiles:view_profile", userprofile_id=userprofile_id)


@login_required
@require_POST
def userRemoveApprovedRequest(request, userprofile_id, user_id):
    receiver_user = get_object_or_404(UserProfile, id=userprofile_id)
    user = get_object_or_404(User, id=user_id)
    join = get_object_or_404(UserFriends, friends=receiver_user, user=user)
    sender_user = get_object_or_404(UserProfile, user=join.user)
    selfjoin = get_object_or_404(
        UserFriends, friends=sender_user, user=join.friends.user
    )

    if selfjoin.status == APPROVED:
        selfjoin.status = REMOVED
        selfjoin.save()
    if join.status == APPROVED:
        join.status = REMOVED
        join.save()
    return redirect("profiles:view_profile", userprofile_id=userprofile_id)


"""
@login_required
def edit_profile(request):
    user_profile = request.user.userprofile

    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            # You can add a success message here if needed
            return redirect(
                "view_profile"
            )  # Redirect to the view profile page after successful update
    else:
        form = ProfileForm(instance=user_profile)

    return render(
        request,
        "profiles/edit_profile.html",
        {"user_profile": user_profile, "form": form},
    )
"""
