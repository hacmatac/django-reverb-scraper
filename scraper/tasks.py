from celery import shared_task
from .models import Job
from .scraper import run_scraper_for_job
from django.utils import timezone
from datetime import timedelta

@shared_task
def start_scrape_job(job_id):
    try:
        job = Job.objects.get(id=job_id)
        run_scraper_for_job(job)
    except Job.DoesNotExist:
        pass
