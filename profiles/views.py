# profiles/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import ProfileForm
from django.http import Http404
from .models import UserProfile
from events.models import Event


@login_required
def view_profile(request, userprofile_id):
    user_profile = get_object_or_404(UserProfile, pk=userprofile_id)
    events = user_profile.user.event_set.filter(is_active=True)
    context = {"user_profile": user_profile, "events": events}

    return render(request, "profiles/view_profile.html", context)


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
