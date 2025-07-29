from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from .forms import CustomAuthenticationForm

app_name = "accounts"
urlpatterns = [
    path(
        "login/",
        LoginView.as_view(
            template_name="accounts/login.html",
            authentication_form=CustomAuthenticationForm,
        ),
        name="login",
    ),
    path("logout/", LogoutView.as_view(), name="logout"),
]
