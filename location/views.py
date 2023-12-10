from django.http import JsonResponse
from .models import Location
from django.contrib.auth.decorators import login_required
from events.models import FavoriteLocation
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseBadRequest


def Location_autocomplete(request):
    query = request.GET.get("term", "")
    results = Location.objects.filter(
        location_name__icontains=query
    )  # Adjust the filtering based on your model's fields
    print(results)
    data = [{"id": location.id, "text": location.location_name} for location in results]
    return JsonResponse(data, safe=False)


@login_required
def manage_favorite_locations(request):
    user = request.user
    favorite_locations = FavoriteLocation.objects.filter(user=user)

    # Handle form submission to add/remove locations from favorites

    context = {
        "favorite_locations": favorite_locations,
    }
    return render(request, "profiles/manage_favorite_locations.html", context)


@login_required
def add_favorite_location(request):
    if request.method == "POST":
        user = request.user
        location_id = request.POST.get(
            "location_id"
        )  # Assuming the select input's name is 'location'
        location = get_object_or_404(Location, pk=location_id)
        # Check if the location is already a favorite
        existing_favorite = FavoriteLocation.objects.filter(
            user=user, location=location
        ).exists()

        if existing_favorite:
            return redirect("profiles:view_profile", user.userprofile.id)
        FavoriteLocation.objects.create(user=user, location=location)
        return redirect("profiles:view_profile", user.userprofile.id)
    else:
        return HttpResponseBadRequest("Invalid request method")


@login_required
def remove_favorite_location(request, location_id):
    if request.method == "POST":
        user = request.user
        fav_location = get_object_or_404(FavoriteLocation, pk=location_id, user=user)
        fav_location.delete()
        return redirect("profiles:view_profile", user.userprofile.id)
    else:
        return HttpResponseBadRequest("Invalid request method")
