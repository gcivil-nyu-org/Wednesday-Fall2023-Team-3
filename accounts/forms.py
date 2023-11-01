from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import UserProfile  # Import the UserProfile model

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(
        label="First Name",
        widget=forms.TextInput(attrs={"autocomplete": "First Name"}),
        help_text="",
    )
    last_name = forms.CharField(
        label="Last Name",
        widget=forms.TextInput(attrs={"autocomplete": "Last Name"}),
        help_text="",
    )
    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(attrs={"autocomplete": "username"}),
        help_text="",
    )
    email = forms.EmailField(  # Add this email field
        label="Email",
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
        help_text="",
    )

    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name', 'username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email']
        if not email.endswith('@nyu.edu'):
            raise ValidationError("Only @nyu.edu email addresses are allowed.")
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()

            # Create the associated UserProfile
            UserProfile.objects.create(user=user)

        return user
