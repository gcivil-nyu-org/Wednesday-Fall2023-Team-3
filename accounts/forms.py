from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError


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
        fields = (
            "first_name",
            "last_name",
            "username",
            "email",
            "password1",
            "password2",
        )

    def clean_email(self):
        email = self.cleaned_data["email"]
        if not email.endswith("@nyu.edu"):
            raise ValidationError("Only @nyu.edu email addresses are allowed.")
        return email

    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="",
    )
    password2 = forms.CharField(
        label="Password confirmation",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        strip=False,
        help_text="",
    )

    class Meta:
        model = get_user_model()  # Use get_user_model() to support custom user models
        fields = (
            "first_name",
            "last_name",
            "username",
            "email",
            "password1",
            "password2",
        )
