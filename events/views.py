from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from .forms import EventsForm
from django.urls import reverse
from .models import Event

# Create your views here.

def index(request):
    return HttpResponse("Hello, world. You're at the Events index.")

def saveEvent(request):
    event = Event()
    try:
        event_name = request.POST['event_name']
        capacity = request.POST['capacity']
    except (KeyError, Event.DoesNotExist):
        # Redisplay the question voting form.
        return redirect('events:index')
    else:
        event.event_name = event_name
        event.capacity = capacity
        event.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse('events:index'))
    
def createEvent(request):
    if request.method == 'POST':
        form = EventsForm(request.POST)
        if form.is_valid():
            return redirect('events:index')
    else:
        form = EventsForm()
    return render(request, 'events/create-event.html', {'form': form})
    