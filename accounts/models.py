from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import AbstractUser
from django.db.models.functions import Lower
import re

class CustomUser(AbstractUser):
    username = models.CharField(
        max_length=15,
        unique=True,
        help_text="Required. 15 characters or fewer.",
        error_messages={
            "unique": "A user with that username already exists."
        },
    )
    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("username"), name="unique_username_case_insensitive"
            )
        ]
    def clean(self):
        super().clean()
        if len(self.username) < 5:
            raise ValidationError('Username must be at least 5 characters long')

        if not re.match(r'^[a-zA-Z0-9_]+$', self.username):
            raise ValidationError("Username can only contain letters, numbers, and underscores.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    def __str__(self):
        return f"Profile for user: {self.user}"

@receiver(post_save, sender=CustomUser)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=CustomUser)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()
