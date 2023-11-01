from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from .forms import ProfilePictureForm
from .models import UserProfile
from .models import Event
from django.http import Http404
from .models import UserProfile

class ProfileView(TemplateView):
    template_name = 'profiles/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        try:
            user_profile = UserProfile.objects.get(user_id=user_id)
            context['user_profile'] = user_profile
            context['created_events'] = Event.objects.filter(user=user)
            context['profile_picture_form'] = ProfilePictureForm(instance=user_profile)
        except UserProfile.DoesNotExist:
            raise Http404("UserProfile does not exist")

        return context

    def post(self, request, *args, **kwargs):
        user_profile = UserProfile.objects.get(user=request.user)
        profile_picture_form = ProfilePictureForm(request.POST, request.FILES, instance=user_profile)
        if profile_picture_form.is_valid():
            profile_picture_form.save()
            # Redirect back to the profile page after a successful upload
            return redirect('profile')
        else:
            # Handle form validation errors here
            pass
