from django.conf import settings
from django.core.exceptions import ValidationError
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

    @classmethod
    def get_default_id(cls):
        q_set, created = cls.objects.get_or_create(name=settings.DEFAULT_QUESTION_SET_NAME)
        return q_set.id


class ClassificationQuestion(models.Model):
    class Meta:
        unique_together = [["name", "question_set"]]

    name = models.CharField(max_length=256)
    question_set = models.ForeignKey(
        "ClassificationQuestionSet",
        on_delete=models.CASCADE,  # delete this if question_set is deleted
        related_name="questions",
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
        return f"{self.question_set.name}: {self.question}"

    def answer_yes(self):
        return self.yes_question or self.yes_tier

    def answer_no(self):
        return self.no_question or self.no_tier

    def clean(self):
        """Don't allow questions to link to questions from another question set
        and questions should have one of yes_question and yes_tier but not both,
        likewise for no_question and no_tier"""

        def check_one_not_both(question, tier, yes_no: str):
            tier = False if tier == None else True
            if bool(question) == tier:  # Effectively XNOR
                msg = f"Questions must have a {yes_no} question or a {yes_no} tier, but not both."
                raise ValidationError(
                    {
                        f"{yes_no}_question": msg,
                        f"{yes_no}_tier": msg,
                    }
                )

        def check_no_foreign_question_sets(question_set, linked_question, yes_no: str):
            if linked_question and question_set != linked_question.question_set:
                msg = f"{yes_no.capitalize()} question cannot be from another question set"
                raise ValidationError({f"{yes_no}_question": msg})

        check_one_not_both(self.yes_question, self.yes_tier, "yes")
        check_one_not_both(self.no_question, self.no_tier, "no")
        check_no_foreign_question_sets(self.question_set, self.yes_question, "yes")
        check_no_foreign_question_sets(self.question_set, self.no_question, "no")


class ClassificationGuidance(models.Model):
    name = models.CharField(max_length=256, unique=True)
    guidance = models.TextField()
    question_set = models.ForeignKey(
        "ClassificationQuestionSet",
        on_delete=models.CASCADE,  # delete this if question_set is deleted
        related_name="guidance",
    )

    def __str__(self):
        return f"{self.question_set.name}: {self.guidance}"
