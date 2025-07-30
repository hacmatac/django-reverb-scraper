from django.db import models

class Job(models.Model):

    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_FAILED = "failed"
    STATUS_COMPLETED = "completed"

    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_RUNNING, "Running"),
        (STATUS_FAILED, "Failed"),
        (STATUS_COMPLETED, "Completed"),    
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )

    profile = models.ForeignKey(
        "accounts.Profile",
        on_delete=models.CASCADE,
        related_name="jobs",
    )

    search_url = models.URLField(
        help_text="URL entered by the user for scraping",
    )

    json_file_url = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, help_text="Error details if job failed") 

    def __str__(self):
        return f"Job {self.id} by {self.profile.user.username} - {self.status}"

    class Meta:
        ordering = ["-created_at"]

class Listing(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="listings")
    url = models.URLField()
    title = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    seller = models.TextField()
    location = models.TextField(blank=True)
    condition = models.CharField(max_length=50, blank=True)
    listed = models.CharField(max_length=50, blank=True)
    fetched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Listing #{self.id} for Job #{self.job.id} by {self.job.profile.user.username}"
