from django.db import models
from simple_history.models import HistoricalRecords

from haven.core.utils import adler32_hash_ns
from haven.data import tiers
from haven.data.managers import ClassificationQuestionQuerySet
from haven.identity.models import User


class Dataset(models.Model):
    name = models.CharField(max_length=256)
    description = models.TextField()
    default_representative = models.ForeignKey(
        User, on_delete=models.PROTECT, null=True, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    unique_id = models.CharField(unique=True, max_length=256, null=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Save method which generates a unique identifier for the dataset"""
        # Attempt 5 times to generate a unique id, if 5 clashes are seen in a row let save method
        # error, this is likely an issue with the unique ID generation if this is the case
        for _ in range(5):
            # Including an app ID decreases to chances of global collisions if multiple instances
            # of this app are in use
            self.unique_id = adler32_hash_ns(extra_info=self.name)
            if Dataset.objects.filter(unique_id=self.unique_id).exists():
                break

        super().save(*args, **kwargs)


class ClassificationQuestion(models.Model):
    name = models.CharField(max_length=256, unique=True)
    question = models.TextField()
    yes_question = models.ForeignKey(
        "ClassificationQuestion",
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
        blank=True,
    )
    no_question = models.ForeignKey(
        "ClassificationQuestion",
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
        blank=True,
    )
    yes_tier = models.IntegerField(choices=tiers.TIER_CHOICES, null=True, blank=True)
    no_tier = models.IntegerField(choices=tiers.TIER_CHOICES, null=True, blank=True)
    hidden = models.BooleanField(default=False)

    history = HistoricalRecords()
    objects = ClassificationQuestionQuerySet.as_manager()

    def __str__(self):
        return self.question

    def answer_yes(self):
        return self.yes_question or self.yes_tier

    def answer_no(self):
        return self.no_question or self.no_tier


class ClassificationGuidance(models.Model):
    name = models.CharField(max_length=256, unique=True)
    guidance = models.TextField()

    def __str__(self):
        return self.guidance
