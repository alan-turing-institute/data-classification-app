from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Case, When

from data.models import ClassificationQuestion, Dataset
from data.tiers import TIER_CHOICES, Tier
from identity.models import User

from .managers import ProjectQuerySet
from .roles import ProjectRole


class Project(models.Model):
    name = models.CharField(max_length=256)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)

    datasets = models.ManyToManyField(Dataset, related_name='projects', blank=True)

    objects = ProjectQuerySet.as_manager()

    def __str__(self):
        return self.name

    @transaction.atomic
    def add_user(self, user, role, creator):
        """
        Add participant to this project
        User must already exist in the database

        :param user: user to add
        :param role: Role user will have on the project
        :param creator: `User` who is doing the adding
        """

        # Verify if user already exists on project
        if user.get_participant(self):
            raise ValidationError("User is already on project")

        return Participant.objects.create(
            user=user,
            role=role,
            created_by=creator,
            project=self,
        )

    @transaction.atomic
    def add_dataset(self, dataset, creator):
        self.datasets.add(dataset)
        user = dataset.default_representative
        if user:
            self.add_user(user, ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value, creator)

    def ordered_participant_set(self):
        """Order participants on this project by their ProjectRole"""
        ordered_role_list = ProjectRole.ordered_display_role_list()
        order = Case(*[When(role=role, then=pos) for pos, role in
                       enumerate(ordered_role_list)])
        return self.participant_set.filter(
            role__in=ordered_role_list).order_by(order)


def validate_role(role):
    """Validator for assigning a participant's role in a project"""
    if not ProjectRole.is_valid_assignable_participant_role(role):
        raise ValidationError('Not a valid ProjectRole string')


class WorkPackage(models.Model):
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE,
                                related_name='work_packages')
    name = models.CharField(max_length=256)
    description = models.TextField()

    # Classification occurs at the work package level because combinations of individual
    # datasets might have a different tier to their individual tiers
    # None means tier is unknown
    tier = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        choices=TIER_CHOICES,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Time the work package was added to the project',
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='+',
        help_text='User who added this work package to the project',
    )

    @property
    def is_classification_ready(self):
        """
        Is the project ready for classification yet?

        i.e. have all the required users been through the classification process

        :return: True if ready for classification, False otherwise.
        """
        required_roles = {
            ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value,
            ProjectRole.INVESTIGATOR.value,
        }
        required_users = {
            p.user
            for p in self.project.participant_set.all()
            if p.role == ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value
        }

        roles = set()
        users = set()

        for c in self.classifications.all():
            roles.add(c.role)
            users.add(c.user)
            if c.role == ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value and c.tier >= Tier.TWO:
                required_roles.add(ProjectRole.REFEREE.value)

        return roles >= required_roles and users >= required_users

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

    def classify_as(self, tier, by_user, questions=None):
        """
        Add a user's opinion of the project classification

        :param tier: Tier the user thinks the project is
        :param by_user: User object
        :param questions: Sequence of (ClassificationQuestion, bool) items
            representing the user's classification answers

        :return: `ClassificationOpinion` object
        """
        if not by_user:
            raise ValidationError("No user provided")
        role = by_user.project_participation_role(self.project)
        if not role:
            raise ValidationError("User not a participant of project")
        classification = ClassificationOpinion.objects.create(
            work_package=self,
            user=by_user,
            role=role.value,
            tier=tier,
        )

        if questions:
            for i, q in enumerate(questions):
                ClassificationOpinionQuestion.objects.create(
                    opinion=classification,
                    order=i,
                    question=q[0],
                    question_version=q[0].history.latest().history_id,
                    answer=q[1],
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

    def get_policies(self):
        if not self.has_tier:
            return []

        return PolicyAssignment.objects.filter(tier=self.tier)

    def __str__(self):
        return f'{self.project} - {self.name}'


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
    Represents a user's opinion about the data tier classification of a work package
    """
    work_package = models.ForeignKey(WorkPackage, related_name='classifications',
                                     on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    tier = models.PositiveSmallIntegerField(choices=TIER_CHOICES)
    role = models.CharField(
        max_length=50,
        choices=ProjectRole.choices(),
        validators=[validate_role],
        help_text="The participant's role on this project at the time classification was made"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Time the classification was made',
    )

    class Meta:
        unique_together = ('user', 'work_package')

    def __str__(self):
        return f'{self.user}: {self.work_package} (tier {self.tier})'


class ClassificationOpinionQuestion(models.Model):
    opinion = models.ForeignKey(ClassificationOpinion, on_delete=models.CASCADE,
                                related_name='questions')
    order = models.SmallIntegerField()
    question = models.ForeignKey(ClassificationQuestion, on_delete=models.PROTECT, related_name='+')
    question_version = models.IntegerField()
    answer = models.BooleanField()

    @property
    def question_at_time(self):
        return self.question.history.get(history_id=self.question_version)


class PolicyGroup(models.Model):
    name = models.CharField(max_length=256)
    description = models.TextField()


class Policy(models.Model):
    name = models.CharField(max_length=256)
    group = models.ForeignKey(PolicyGroup, on_delete=models.PROTECT)
    description = models.TextField()


class PolicyAssignment(models.Model):
    tier = models.PositiveSmallIntegerField(choices=TIER_CHOICES)
    policy = models.ForeignKey(Policy, on_delete=models.PROTECT)
