from django.urls import reverse_lazy
from django.views import generic
from .forms import CustomUserCreationForm
from django.shortcuts import render
from django.contrib.auth.forms import PasswordResetForm

class SignUpView(generic.CreateView):
    form_class = CustomUserCreationForm  # Use the custom form instead of the default UserCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"

def homepage(request):
    return render(request, 'registration/homepage.html')

def forgot_password(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save(from_email='your_email@example.com', email_template_name='registration/password_reset_email.html')
            return render(request, 'password_reset_done.html')
    else:
        form = PasswordResetForm()
    return render(request, 'registration/forgot_password.html', {'form': form})