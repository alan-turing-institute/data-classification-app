from django.db import models

from data import tiers
from identity.models import User

from .managers import ClassificationQuestionQuerySet


class Dataset(models.Model):
    name = models.CharField(max_length=256)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)


class ClassificationQuestion(models.Model):
    name = models.CharField(max_length=256, unique=True)
    question = models.TextField()
    yes_question = models.ForeignKey(
        'ClassificationQuestion', on_delete=models.PROTECT, related_name='+',
        null=True, blank=True)
    no_question = models.ForeignKey(
        'ClassificationQuestion', on_delete=models.PROTECT, related_name='+',
        null=True, blank=True)
    yes_tier = models.IntegerField(choices=tiers.TIER_CHOICES, null=True, blank=True)
    no_tier = models.IntegerField(choices=tiers.TIER_CHOICES, null=True, blank=True)

    objects = ClassificationQuestionQuerySet.as_manager()

    def __str__(self):
        return self.question

    def answer_yes(self):
        return self.yes_question or self.yes_tier

    def answer_no(self):
        return self.no_question or self.no_tier
