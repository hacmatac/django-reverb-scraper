from django.urls import path
from .views import DashboardView, download_job_json
from django.views.generic.base import RedirectView

app_name = 'core'
urlpatterns = [
    path("", RedirectView.as_view(pattern_name='accounts:login', permanent=False)),
    path("dashboard/", DashboardView.as_view(), name='dashboard'),
    path("dashboard/download_job_json/<int:job_id>/", download_job_json, name="download_job_json"),
]
