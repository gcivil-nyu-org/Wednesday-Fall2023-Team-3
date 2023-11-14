# Register your models here.
from django.contrib import admin

from .models import Event, EventJoin, Comment

admin.site.register(Event)
admin.site.register(EventJoin)
admin.site.register(Comment)
