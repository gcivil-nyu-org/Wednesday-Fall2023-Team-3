# notifications/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Notification


@login_required
def notifications(request):
    user_notifications = Notification.objects.filter(user=request.user, is_read=False)
    return render(
        request,
        "notifications/notifications.html",
        {"notifications": user_notifications},
    )


@login_required
def mark_notification_as_read(request, notification_id):
    notification = Notification.objects.get(pk=notification_id)
    notification.is_read = True
    notification.save()
    return redirect("notifications:view-notifications")
