from django import forms
from django.contrib.auth.forms import AuthenticationForm, UsernameField

class CustomAuthenticationForm(AuthenticationForm):
    username = UsernameField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Username",
                "autocomplete": "off",
                "autofocus": True,
            },
        ),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Password",
                "autocomplete": "new-password",
            },
        ),
    )
