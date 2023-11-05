# Register your models here.
from django.contrib import admin

from .models import Event, EventJoin

admin.site.register(Event)
admin.site.register(EventJoin)