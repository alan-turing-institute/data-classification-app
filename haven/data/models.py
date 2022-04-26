from django.db import models
from simple_history.models import HistoricalRecords

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

    def __str__(self):
        return self.name


class ClassificationQuestionSet(models.Model):
    name = models.CharField(max_length=256, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.name


class ClassificationQuestion(models.Model):

    class Meta:
        unique_together = [["name", "question_set"]]

    name = models.CharField(max_length=256)
    question_set = models.ForeignKey(
        "ClassificationQuestionSet",
        on_delete=models.CASCADE,  # delete this if question_set is deleted
        related_name="questions"
    )
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
