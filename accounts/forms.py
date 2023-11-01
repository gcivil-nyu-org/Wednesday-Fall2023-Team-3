from django.contrib.auth.forms import UserCreationForm
from django import forms


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
        model = UserCreationForm.Meta.model
        fields = UserCreationForm.Meta.fields
