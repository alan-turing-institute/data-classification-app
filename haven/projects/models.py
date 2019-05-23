from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction

from data.models import Dataset
from data.tiers import TIER_CHOICES, Tier
from identity.models import User
from identity.remote import create_user

from .managers import ProjectQuerySet
from .roles import ProjectRole


class Project(models.Model):
    name = models.CharField(max_length=256)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)

    datasets = models.ManyToManyField(Dataset, related_name='projects', blank=True)

    # Classification occurs at the project level because combinations of individual
    # datasets might have a different tier to their individual tiers
    # None means tier is unknown
    tier = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        choices=TIER_CHOICES,
    )

    objects = ProjectQuerySet.as_manager()

    def __str__(self):
        return self.name

    @transaction.atomic
    def add_user(self, username, role, creator):
        """
        Add user to this project
        Creates user if they do not already exist

        :param username: username of user to add
        :param role: Role user will have on the project
        :param creator: `User` who is doing the adding
        """
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={
                'created_by': creator,
            }
        )

        if settings.USE_LDAP:
            create_user(user)

        return Participant.objects.create(
            user=user,
            role=role,
            created_by=creator,
            project=self,
        )

    def add_dataset(self, dataset):
        self.datasets.add(dataset)

    @property
    def is_classification_ready(self):
        """
        Is the project ready for classification yet?

        i.e. have all the required users been through the classification process

        :return: True if ready for classification, False otherwise.
        """
        required_roles = {
            ProjectRole.DATA_PROVIDER_REPRESENTATIVE,
            ProjectRole.INVESTIGATOR,
        }
        roles = set()

        for c in self.classifications.all():
            role = c.user.project_participation_role(self)
            roles.add(role)
            if role == ProjectRole.DATA_PROVIDER_REPRESENTATIVE and c.tier >= Tier.TWO:
                required_roles.add(ProjectRole.REFEREE)

        return roles >= required_roles

    @property
    def tier_conflict(self):
        """
        Do users disagree on project data tier?

        This has meaning even if not all required users have done the classification yet.

        :return: True if there is conflict, False otherwise
        """
        tiers = self.classifications.values('tier').distinct()
        return tiers.count() > 1

    def calculate_tier(self):
        """
        Calculate the tier of the project based on classifications submitted
        by relevant users, and save the value in the database.

        Will only happen if a tier has not already been determined, and if
        it passes the relevant classification criteria (all required users have
        classified the project, and they all agree on the tier)
        """
        if self.has_tier:
            return

        if self.is_classification_ready and not self.tier_conflict:
            self.tier = self.classifications.first().tier
            self.save()

    def classify_as(self, tier, by_user):
        """
        Add a user's opinion of the project classification

        :param tier: Tier the user thinks the project is
        :param by_user: User object

        :return: `ClassificationOpinion` object
        """
        classification = ClassificationOpinion.objects.create(
            project=self,
            user=by_user,
            tier=tier,
        )

        # This might qualify the project for classification, so try
        self.calculate_tier()

        return classification

    def classification_for(self, user):
        return self.classifications.filter(
            user=user
        )

    @property
    def has_tier(self):
        """Has this project's data been classified?"""
        return self.tier is not None


def validate_role(role):
    """Validator for assigning a participant's role in a project"""
    if not ProjectRole.is_valid_assignable_participant_role(role):
        raise ValidationError('Not a valid ProjectRole string')


class Participant(models.Model):
    """
    Represents a user's participation in a project
    """
    role = models.CharField(
        max_length=50,
        choices=ProjectRole.choices(),
        validators=[validate_role],
        help_text="The participant's role on this project"
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE)

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Time the user was added to the project',
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='+',
        help_text='User who added this user to the project',
    )

    class Meta:
        unique_together = ('user', 'project')

    def __str__(self):
        return f'{self.user} ({self.get_role_display()} on {self.project})'


class ClassificationOpinion(models.Model):
    """
    Represents a user's opinion about the data tier classificaiton of a project
    """
    project = models.ForeignKey(Project, related_name='classifications', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    tier = models.PositiveSmallIntegerField(choices=TIER_CHOICES)
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Time the classification was made',
    )

    class Meta:
        unique_together = ('user', 'project')

    def __str__(self):
        return f'{self.user}: {self.project} (tier {self.tier})'
