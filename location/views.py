from django.shortcuts import render
from django.http import JsonResponse
from .models import Location
def Location_autocomplete(request):
    query = request.GET.get('term', '')
    results = Location.objects.filter(location_name__icontains=query)  # Adjust the filtering based on your model's fields
    print(results)
    data = [{'id': location.id, 'text': location.location_name} for location in results]
    return JsonResponse(data, safe=False)
