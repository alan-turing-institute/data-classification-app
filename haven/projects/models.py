from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Case, Q, When
from django.urls import reverse
from easyaudit.models import CRUDEvent

from data.models import ClassificationQuestion, Dataset
from data.tiers import TIER_CHOICES, Tier
from identity.models import User

from .managers import ProjectQuerySet
from .roles import ProjectRole


def validate_role(role):
    """Validator for assigning a participant's role in a project"""
    if not ProjectRole.is_valid_assignable_participant_role(role):
        raise ValidationError('Not a valid ProjectRole string')


class CreatedByModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='+')

    class Meta:
        abstract = True


class Project(CreatedByModel):
    name = models.CharField(max_length=256)
    description = models.TextField()

    datasets = models.ManyToManyField(Dataset, related_name='projects', through='ProjectDataset',
                                      blank=True)

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
    def add_dataset(self, dataset, representative, creator):
        participant = representative.get_participant(self)
        if not participant or participant.role != ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value:
            raise ValidationError(f"User is not a {ProjectRole.DATA_PROVIDER_REPRESENTATIVE}")
        ProjectDataset.objects.create(project=self, dataset=dataset,
                                      representative=representative, created_by=creator)

    def ordered_participants(self):
        """Order participants on this project by their ProjectRole"""
        ordered_role_list = ProjectRole.ordered_display_role_list()
        order = Case(*[When(role=role, then=pos) for pos, role in
                       enumerate(ordered_role_list)])
        return self.participants.filter(
            role__in=ordered_role_list).order_by(order)

    def get_datasets(self, representative):
        return [pd.dataset for pd in self.get_project_datasets(representative=representative)]

    def get_representative(self, dataset):
        dataset = self.get_project_datasets(dataset=dataset).first()
        if dataset:
            return dataset.representative
        return None

    def has_dataset(self, dataset):
        return self.get_project_datasets(dataset=dataset).exists()

    def get_project_datasets(self, **kwargs):
        return ProjectDataset.objects.filter(project=self, **kwargs)

    def get_audit_history(self):
        this_object = Q(content_type=ContentType.objects.get_for_model(self), object_id=self.pk)
        # This is a bit of a hack - if the model uses a different field name for example, it
        # won't be picked up, it doesn't catch transitive relationships,
        # and it relies on how the json has been formatted
        # A more robust approach would involve basing decisions on the content type, and possibly
        # storing the data as actual JSON and using the JSON operators, but that's database-specific
        related = Q(object_json_repr__regex=f'"project": {self.pk}[,}}]')
        return CRUDEvent.objects.filter(this_object | related)


class WorkPackage(CreatedByModel):
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE,
                                related_name='work_packages')
    name = models.CharField(max_length=256)
    description = models.TextField()

    datasets = models.ManyToManyField(Dataset, related_name='work_packages',
                                      through='WorkPackageDataset', blank=True)

    # Classification occurs at the work package level because combinations of individual
    # datasets might have a different tier to their individual tiers
    # None means tier is unknown
    tier = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        choices=TIER_CHOICES,
    )

    @transaction.atomic
    def add_dataset(self, dataset, creator):
        # Verify if dataset exists on project
        if not self.project.has_dataset(dataset):
            raise ValidationError('Dataset not assigned to project')

        WorkPackageDataset.objects.create(work_package=self, dataset=dataset,
                                          created_by=creator)

    def get_work_package_datasets(self, representative):
        datasets = []
        for dataset in self.project.get_datasets(representative):
            for wpd in WorkPackageDataset.objects.filter(work_package=self, dataset=dataset):
                datasets.append(wpd)
        return datasets

    @property
    def is_classification_ready(self):
        """
        Is the project ready for classification yet?

        i.e. have all the required users been through the classification process

        :return: True if ready for classification, False otherwise.
        """

        return self.missing_classification_requirements == []

    @property
    def missing_classification_requirements(self):
        """
        What conditions need to be fulfilled before the work package is ready for classification?

        i.e. have all the required users been through the classification process

        :return: List (possibly empty) of required changes
        """

        required_roles = {
            ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value,
            ProjectRole.INVESTIGATOR.value,
        }
        required_datasets = set(self.datasets.all())

        roles = set()
        datasets = set()

        for c in self.classifications.all():
            roles.add(c.role)
            if c.role == ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value and c.tier >= Tier.TWO:
                required_roles.add(ProjectRole.REFEREE.value)
            for d in c.datasets:
                datasets.add(d)

        missing_requirements = []
        missing_roles = required_roles - roles
        for r in missing_roles:
            role = ProjectRole.display_name(r)
            missing_requirements.append(f"Not classified by {role}")

        missing_datasets = required_datasets - datasets
        for d in missing_datasets:
            missing_requirements.append(f"Not classified by representative for {d}")

        return missing_requirements

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
        if not self.has_datasets:
            raise ValidationError("No datasets in work package")

        classification = ClassificationOpinion.objects.create(
            work_package=self,
            created_by=by_user,
            role=role.value,
            tier=tier,
        )

        if role == ProjectRole.DATA_PROVIDER_REPRESENTATIVE:
            for wpd in self.get_work_package_datasets(by_user):
                wpd.opinion = classification
                wpd.save()

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
            created_by=user
        )

    @property
    def has_tier(self):
        """Has this project's data been classified?"""
        return self.tier is not None

    @property
    def has_datasets(self):
        return self.datasets.exists()

    def has_user_classified(self, user):
        return self.classification_for(user).exists()

    def get_policies(self):
        if not self.has_tier:
            return []

        return PolicyAssignment.objects.filter(tier=self.tier)

    def get_absolute_url(self):
        return reverse('projects:work_package_detail', args=[self.project.id, self.id])

    def __str__(self):
        return f'{self.project} - {self.name}'


class Participant(CreatedByModel):
    """
    Represents a user's participation in a project
    """
    role = models.CharField(
        max_length=50,
        choices=ProjectRole.choices(),
        validators=[validate_role],
        help_text="The participant's role on this project"
    )

    user = models.ForeignKey(User, related_name='participants', on_delete=models.CASCADE)
    project = models.ForeignKey(Project, related_name='participants', on_delete=models.CASCADE)

    class Meta(CreatedByModel.Meta):
        unique_together = ('user', 'project')

    def __str__(self):
        return f'{self.user} ({self.get_role_display()} on {self.project})'


class ClassificationOpinion(CreatedByModel):
    """
    Represents a user's opinion about the data tier classification of a work package
    """
    work_package = models.ForeignKey(WorkPackage, related_name='classifications',
                                     on_delete=models.CASCADE)
    tier = models.PositiveSmallIntegerField(choices=TIER_CHOICES)
    role = models.CharField(
        max_length=50,
        choices=ProjectRole.choices(),
        validators=[validate_role],
        help_text="The participant's role on this project at the time classification was made"
    )

    class Meta(CreatedByModel.Meta):
        unique_together = ('created_by', 'work_package')

    def __str__(self):
        return f'{self.created_by}: {self.work_package} (tier {self.tier})'

    @property
    def datasets(self):
        return [wpd.dataset for wpd in WorkPackageDataset.objects.filter(opinion=self)]


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


class ProjectDataset(CreatedByModel):
    project = models.ForeignKey(Project, related_name='+', on_delete=models.CASCADE)
    dataset = models.ForeignKey(Dataset, related_name='+', on_delete=models.PROTECT)
    representative = models.ForeignKey(User, related_name='+', on_delete=models.PROTECT, null=False)


class WorkPackageDataset(CreatedByModel):
    work_package = models.ForeignKey(WorkPackage, related_name='+', on_delete=models.CASCADE)
    dataset = models.ForeignKey(Dataset, related_name='+', on_delete=models.PROTECT)
    opinion = models.ForeignKey('ClassificationOpinion', null=True,
                                related_name='+', on_delete=models.SET_NULL)
