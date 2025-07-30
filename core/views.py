from django.shortcuts import render, redirect
from django.views.generic import View
from .forms import SearchUrlForm
from django.contrib.auth.mixins import LoginRequiredMixin
from scraper.models import Job
from scraper.tasks import start_scrape_job
from django.conf import settings
import os

class DashboardView(LoginRequiredMixin, View):
    template_name = "core/dashboard.html"
    form_class = SearchUrlForm

    def get(self, request):
        form = self.form_class()
        jobs = Job.objects.filter(profile=request.user.profile)
        context = {"form": form, "jobs": jobs}
        return render(request, self.template_name, context)

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            reverb_url = form.cleaned_data["reverb_url"]
            job = Job.objects.create(
                profile=request.user.profile,
                search_url=reverb_url,
            )

            start_scrape_job.delay(job.id)
            jobs = Job.objects.filter(profile=request.user.profile)
            return redirect("core:dashboard")

        jobs = Job.objects.filter(profile=request.user.profile)
        context = {"form": form, "jobs": jobs}
        return render(request, self.template_name, context)

def download_job_json(request, job_id):
    filepath = os.path.join(settings.MEDIA_ROOT, "job_json", f"job_{job_id}.json")
    if os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            json_data = f.read()

        response = HttpResponse(json_data, content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="job_{job_id}.json"'
        return response
    else:
        return HttpResponse("File not found", status=404)
