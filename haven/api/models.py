from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from oauth2_provider.models import Application


class ApplicationProfile(models.Model):
    """Model to track extra information about an Oauth Client Application"""

    application = models.OneToOneField(
        Application, on_delete=models.CASCADE, related_name="profile"
    )
    maximum_tier = models.PositiveSmallIntegerField(
        default=4, validators=[MinValueValidator(0), MaxValueValidator(4)]
    )

    def __str__(self):
        return self.application.name
