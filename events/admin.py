# Register your models here.
from django.contrib import admin

from .models import Event, EventJoin, Comment, Reaction, FavoriteLocation

admin.site.register(Event)
admin.site.register(EventJoin)
admin.site.register(Comment)
admin.site.register(Reaction)
admin.site.register(FavoriteLocation)
