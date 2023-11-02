from django.http import JsonResponse
from events.models import Event
from location.models import Location
from django.shortcuts import render
from django.core.serializers import serialize
import json


def show_map(request):
    # return render(request, 'show_map.html')
    return render(request, "show_map.html")


def get_data(request):
    location_data = Event.objects.all()
    serialized_data = serialize("json", location_data)
    serialized_data = json.loads(serialized_data)
    return JsonResponse({"location_data": serialized_data})


def get_locations(request):
    locations = Location.objects.all()
    serialized_data = serialize("json", locations)
    serialized_data = json.loads(serialized_data)
    return JsonResponse({"locations": serialized_data})


# Map id = 9a7e26117f10196d
