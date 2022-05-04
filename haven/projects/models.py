from enum import Enum

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import BooleanField, Case, Q, Value, When
from django.urls import reverse
from easyaudit.models import CRUDEvent
from taggit.managers import TaggableManager

from haven.core.utils import BooleanTextTable
from haven.data.models import ClassificationQuestion, Dataset
from haven.data.tiers import TIER_CHOICES, Tier
from haven.identity.models import User
from haven.projects.managers import ProjectQuerySet, WorkPackageQuerySet
from haven.projects.roles import ProjectRole


def validate_role(role):
    """Validator for assigning a participant's role in a project"""
    if not ProjectRole.is_valid_assignable_participant_role(role):
        raise ValidationError("Not a valid ProjectRole string")


def a_or_an(following_text, capitalize=True):
    """Returns text with A/An/a/an prefixed as appropriate"""
    prefix = "A" if capitalize else "a"
    suffix = "n" if following_text.lower()[0] in "aeiou" else ""
    return f"{prefix}{suffix} {following_text}"


class CreatedByModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+")

    class Meta:
        abstract = True


class Project(CreatedByModel):
    name = models.CharField(max_length=256, unique=True)
    description = models.TextField()

    datasets = models.ManyToManyField(
        Dataset, related_name="projects", through="ProjectDataset", blank=True
    )
    archived = models.BooleanField(default=False)
    programmes = TaggableManager(blank=True)

    objects = ProjectQuerySet.as_manager()

    def __str__(self):
        return self.name

    @transaction.atomic
    def add_user(self, user, role, created_by, work_packages=None):
        """
        Add participant to this project
        User must already exist in the database

        :param user: user to add
        :param role: Role user will have on the project
        :param created_by: `User` who is doing the adding
        """

        # Verify if user already exists on project
        if user.get_participant(self):
            raise ValidationError("User is already on project")

        participant = Participant.objects.create(
            user=user,
            role=role,
            created_by=created_by,
            project=self,
        )
        if role == ProjectRole.INVESTIGATOR.value:
            work_packages = self.work_packages.all()
        if work_packages:
            for work_package in work_packages:
                work_package.add_user(user, created_by)
        return participant

    @transaction.atomic
    def add_dataset(self, dataset, representative, created_by):
        participant = representative.get_participant(self)
        if not participant:
            self.add_user(
                representative,
                ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value,
                created_by,
            )
        elif participant.role != ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value:
            raise ValidationError(f"User is not a {ProjectRole.DATA_PROVIDER_REPRESENTATIVE}")
        return ProjectDataset.objects.create(
            project=self,
            dataset=dataset,
            representative=representative,
            created_by=created_by,
        )

    @transaction.atomic
    def add_work_package(self, work_package, created_by):
        work_package.project = self
        work_package.created_by = created_by
        work_package.save()
        for participant in self.get_all_participants(ProjectRole.INVESTIGATOR.value):
            work_package.add_user(participant.user, created_by)

    def add_default_work_packages(self, created_by=None):
        ingress = WorkPackage(
            name="Ingress",
            description=(
                "<p>When considering a project, you'll need to consider all the tools and datasets "
                "you'll be using (in combination or separately) in a single research environment, "
                "as well as what work you'll be doing on the data, to consider the potential "
                "sensitivity of the data you'll be using / creating, and how securely it should "
                "be handled. Once you're finished with the project, you'll need to carry out "
                "separate classifications on the data you'll be taking out of the environment.</p>"
                "<p>Datasets: All inputs, including tools, data and potential products of linking "
                "/ filtering data.</p>"
            ),
        )
        egress1 = WorkPackage(
            name="Egress – Reports",
            description=(
                "<p>When you're finishing a project, you'll need to complete reports and any other "
                "outputs that might be pertinent to the presentation of the research you've done. "
                "In this workpackage, you'll be egressing the documents, graphs, pictures and any "
                "other data you might need to make it easier to finish the report.</p><p>If there "
                "are images or details within these outputs that might constitute a tier of 2 or "
                "above, these should be removed temporarily for the purposes of the report "
                "writing process, to allow you to work outside of the secure environment. A "
                "separate discussion should be had between the lead investigator and the data "
                "provider representative as to how such items can be suitably redacted so that "
                "they can be included in the final document. If the report itself is classified "
                "as Tier 2, it will need to be completed and presented within a secure "
                "environment.</p><p>Datasets: Report inputs including text, images and code "
                "snippets.</p>"
            ),
        )
        egress2 = WorkPackage(
            name="Egress – Full",
            description=(
                "<p>In this work package, you'll need to include all other outputs, including "
                "derived data sets and full code to be returned to the Data Provider for "
                "archiving. If this returns a high tier then a conversation needs to take place "
                "about where it should be stored, and whether some outputs should be redacted "
                "prior to release.</p><p>Datasets: All outputs, including text, images, code and "
                "any derived datasets.</p>"
            ),
        )
        self.add_work_package(ingress, created_by=created_by)
        self.add_work_package(egress1, created_by=created_by)
        self.add_work_package(egress2, created_by=created_by)

    @transaction.atomic
    def update_representative(self, dataset, creator):
        for pd in self.get_project_datasets(dataset=dataset):
            pd.representative = dataset.default_representative
            pd.save()

        user = dataset.default_representative
        if not user.get_participant(self):
            self.add_user(user, ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value, creator)

        for wpd in self.get_work_package_datasets(dataset=dataset):
            wp = wpd.work_package
            if not wp.get_work_package_participant(user).exists():
                wp.add_user(user, creator)

    def archive(self):
        self.archived = True
        self.save()

    def ordered_participants(self):
        """Order participants on this project by their ProjectRole"""
        ordered_role_list = ProjectRole.ordered_display_role_list()
        order = Case(*[When(role=role, then=pos) for pos, role in enumerate(ordered_role_list)])
        return self.participants.filter(role__in=ordered_role_list).order_by(order)

    def get_participant(self, role):
        return self.get_all_participants(role).first()

    def get_all_participants(self, role):
        return self.participants.filter(role=role)

    def get_datasets(self, representative):
        project_datasets = self.get_project_datasets(representative=representative).select_related(
            "dataset"
        )
        return [pd.dataset for pd in project_datasets]

    def get_representative(self, dataset):
        dataset = self.get_project_datasets(dataset=dataset).first()
        if dataset:
            return dataset.representative
        return None

    def has_dataset(self, dataset):
        return self.get_project_datasets(dataset=dataset).exists()

    def get_project_datasets(self, **kwargs):
        return ProjectDataset.objects.filter(project=self, **kwargs)

    def get_work_package_datasets(self, **kwargs):
        return WorkPackageDataset.objects.filter(work_package__project=self, **kwargs)

    @transaction.atomic
    def delete_dataset(self, project_dataset):
        project_dataset.delete()
        self.get_work_package_datasets(dataset=project_dataset.dataset).delete()

    def can_edit_dataset(self, dataset):
        return self._can_edit_dataset(dataset, "edit_datasets")

    def can_edit_dataset_dpr(self, dataset):
        return self._can_edit_dataset(dataset, "edit_datasets_dpr")

    def can_delete_dataset(self, dataset):
        return self._can_edit_dataset(dataset, "delete_datasets")

    def _can_edit_dataset(self, dataset, permission):
        work_packages = self.work_packages.filter_by_permission(permission, exclude=True)
        datasets = self.get_work_package_datasets(dataset=dataset, work_package__in=work_packages)
        return not datasets.exists()

    def get_audit_history(self):
        this_object = Q(content_type=ContentType.objects.get_for_model(self), object_id=self.pk)
        # This is a bit of a hack - if the model uses a different field name for example, it
        # won't be picked up, it doesn't catch transitive relationships,
        # and it relies on how the json has been formatted
        # A more robust approach would involve basing decisions on the content type, and possibly
        # storing the data as actual JSON and using the JSON operators, but that's database-specific
        related = Q(object_json_repr__regex=f'"project": {self.pk}[,}}]')
        return CRUDEvent.objects.filter(this_object | related)


class WorkPackageStatus(Enum):
    NEW = "new"
    UNDERWAY = "underway"
    CLASSIFIED = "classified"

    @classmethod
    def choices(cls):
        """Dropdown choices for user roles"""
        return [
            (cls.NEW.value, "New"),
            (cls.UNDERWAY.value, "Classification Underway"),
            (cls.CLASSIFIED.value, "Classified"),
        ]


class WorkPackage(CreatedByModel):
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="work_packages"
    )
    name = models.CharField(max_length=256)
    description = models.TextField()
    # uuid = models.UUIDField(default=uuid4, unique=True)

    participants = models.ManyToManyField(
        "Participant",
        related_name="work_packages",
        through="WorkPackageParticipant",
        blank=True,
    )
    datasets = models.ManyToManyField(
        Dataset, related_name="work_packages", through="WorkPackageDataset", blank=True
    )
    status = models.CharField(
        max_length=32,
        choices=WorkPackageStatus.choices(),
        default=WorkPackageStatus.NEW.value,
    )

    # Classification occurs at the work package level because combinations of individual
    # datasets might have a different tier to their individual tiers
    # None means tier is unknown
    tier = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        choices=TIER_CHOICES,
    )

    permissions = BooleanTextTable(
        definition="""
                             | new underway classified | Extra
        edit_work_package    |   Y        .          . |
        delete_work_package  |   Y        .          . |
        add_participants     |   Y        Y          Y |
        list_participants    |   Y        Y          Y |
        edit_participants    |   Y        Y          Y |
        approve_participants |   .        Y          Y |
        add_datasets         |   Y        .          . |
        edit_datasets        |   Y        .          . |
        edit_datasets_dpr    |   Y        Y          Y |
        delete_datasets      |   Y        .          . |
        view_classification  |   .        Y          Y |
        open_classification  |   Y        .          . | *
        clear_classification |   .        Y          . |
        close_classification |   .        Y          . | *
        classify_data        |   .        Y          . |
        """,
        ignore=["Extra"],
    )

    objects = WorkPackageQuerySet.as_manager()

    def __getattr__(self, name):
        if name.startswith("can_"):
            permission = name.replace("can_", "")
            try:
                return self._can(permission)
            except ValueError as e:
                raise AttributeError(name) from e
        raise AttributeError(name)

    @classmethod
    def _get_permission_dict(cls, permission):
        try:
            return cls.permissions.as_dict()[permission]
        except KeyError as e:
            raise ValueError(f"{permission} not a valid permission") from e

    def _can(self, permission):
        permission_dict = self._get_permission_dict(permission)
        return permission_dict[self.status]

    @transaction.atomic
    def add_dataset(self, dataset, created_by):
        # Verify if dataset exists on project
        project_dataset = self.project.get_project_datasets(dataset=dataset).first()
        if not project_dataset:
            raise ValidationError("Dataset not assigned to project")

        if self.get_work_package_datasets().filter(dataset=dataset).exists():
            raise ValidationError("Dataset already assigned to work package")

        wpd = WorkPackageDataset.objects.create(
            work_package=self, dataset=dataset, created_by=created_by
        )
        representative = project_dataset.representative
        if not self.get_work_package_participant(representative).exists():
            self.add_user(representative, created_by)
        return wpd

    @transaction.atomic
    def add_user(self, user, created_by):
        """
        Add user to this work package
        User must already exist on project, and not on work package

        :param user: user to add
        :param created_by: `User` who is doing the adding
        """

        participant = user.get_participant(self.project)
        if participant is None:
            raise ValidationError("User is not on project")

        if self.get_work_package_participant(user).exists():
            raise ValidationError("User is already on work package")

        qs = WorkPackageParticipant.objects
        return qs.create(work_package=self, participant=participant, created_by=created_by)

    def get_work_package_datasets(self, representative=None, dataset=None):
        qs = WorkPackageDataset.objects.filter(work_package=self)
        if dataset:
            qs = qs.filter(dataset=dataset)
        if representative:
            qs = qs.filter(dataset__in=self.project.get_datasets(representative))
        return qs

    def get_work_package_participant(self, user):
        participant = user.get_participant(self.project)
        return WorkPackageParticipant.objects.filter(work_package=self, participant=participant)

    @property
    def can_open_classification(self):
        return self._can("open_classification") and self.has_datasets

    def open_classification(self):
        self.status = WorkPackageStatus.UNDERWAY.value
        self.save()

    @property
    def can_close_classification(self):
        return self._can("close_classification") and self.is_classification_ready

    def close_classification(self):
        self.status = WorkPackageStatus.CLASSIFIED.value
        self.calculate_tier()
        self.save()

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
        require_approval = False

        roles = set()
        pending_classifications = set()
        datasets = set()
        roles_required_in_wp = set()

        for c in self.classifications.all():
            if c.role != ProjectRole.REFEREE.value:
                roles.add(c.role)
            else:
                pending_classifications.add(c)
            if c.role == ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value and c.tier >= Tier.TWO:
                required_roles.add(ProjectRole.REFEREE.value)
                roles_required_in_wp.add(ProjectRole.REFEREE.value)
                if c.tier >= Tier.THREE:
                    require_approval = True
            for d in c.datasets:
                datasets.add(d)

        for c in pending_classifications:
            if require_approval:
                participant = c.created_by.get_participant(self.project)
                if self.is_participant_approved(participant):
                    roles.add(c.role)
            else:
                roles.add(c.role)

        missing_requirements = []
        missing_roles = required_roles - roles

        missing_datasets = required_datasets - datasets

        # No need to report a missing DPR classification twice
        if missing_datasets:
            missing_roles.discard(ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value)

        for r in missing_roles:
            # If a required user has not been assigned
            warn_no_roles_assigned = r in roles_required_in_wp
            warn_no_roles_approved = require_approval
            for participant in self.participants.filter(role=r):
                warn_no_roles_assigned = False
                if self.is_participant_approved(participant):
                    warn_no_roles_approved = False
            role = ProjectRole.display_name(r)

            if warn_no_roles_assigned:
                # Warn if Work Package doesn't contain user with required role
                missing_requirements.append(
                    f"{a_or_an(role)} needs to be added to this Work Package."
                )

            elif warn_no_roles_approved:
                # Warn if role approval is required and has not been granted
                approver = ProjectRole.display_name(ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value)
                missing_requirements.append(
                    f"Each {approver} for this Work Package needs to approve the {role}."
                )

            else:
                # Warn if classifications haven't been made by all roles
                if require_approval:
                    role = "approved " + role

                missing_requirements.append(
                    f"{a_or_an(role)} still needs to classify this Work Package."
                )

        for d in missing_datasets:
            role = ProjectRole.display_name(ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value)
            missing_requirements.append(
                f"{a_or_an(role)} for dataset {d} still needs to classify this Work Package."
            )

        if not self.has_datasets:
            missing_requirements.append("No datasets have been added to this Work Package")

        return missing_requirements

    @property
    def tier_conflict(self):
        """
        Do users disagree on project data tier?

        This has meaning even if not all required users have done the classification yet.

        :return: True if there is conflict, False otherwise
        """
        tiers = self.classifications.values("tier").distinct()
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
        participant = by_user.get_participant(self.project)
        wpp = participant.get_work_package_participant(self)
        if not wpp:
            raise ValidationError("User not a participant of work package")
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

        return classification

    def classification_for(self, user):
        return self.classifications.filter(created_by=user)

    def clear_classifications(self):
        self.status = WorkPackageStatus.NEW.value
        for c in self.classifications.all():
            c.delete()
        self.save()

    def show_approve_participants(self, approver):
        if not self.can_approve_participants:
            return False
        participant = approver.get_participant(self.project)
        if not participant:
            return False
        if not participant.permissions.can_approve_participants:
            return False
        return self.get_work_package_participants_to_approve(approver).exists()

    def get_work_package_participants_to_approve(self, approver=None):
        """
        Find users who are not yet approved for this work package

        Users must be approved by a DPR for every dataset in the work package

        Returns a QuerySet of WorkPackageParticipant objects
        Will be empty if this work package is classified as low tier, or there are no datasets
        """
        if self.has_tier and self.tier <= Tier.TWO:
            # Low-tier work packages don't require anyone to be approved
            return WorkPackageParticipant.objects.none()

        q = None
        for d in self.get_work_package_datasets(representative=approver):
            # Find anyone who is not approved for this dataset
            q2 = ~Q(approvals__dataset=d.dataset)
            if q is None:
                q = q2
            else:
                # If there's multiple datasets, we want anyone who is not approved for at least
                # one of them
                q = q | q2

        if q is None:
            # If there are no datasets, nobody can be approved
            return WorkPackageParticipant.objects.none()

        return WorkPackageParticipant.objects.filter(
            q,
            work_package=self,
            participant__role__in=ProjectRole.non_approved_roles(),
        )

    def is_participant_approved(self, participant):
        wpp = participant.get_work_package_participant(self)
        if not wpp:
            return False

        participants_to_approve = self.get_work_package_participants_to_approve()
        return not participants_to_approve.filter(participant=participant).exists()

    def get_participants_with_approval(self, approver):
        """
        Find all users on this work package, and their approval status

        Returns a QuerySet of WorkPackageParticipant objects
        Will be annotated with an 'approved' field if they are approved (see
        get_work_package_participants_to_approve for definition)
        If an 'approver' params is provided, will also be annotated with an
        'approved_by_you' field indicating if they are approved for all the datasets relevant
        to that user
        """

        has_datasets = self.datasets.exists()

        def approved_annotation(user=None):
            if self.has_tier and self.tier <= Tier.TWO:
                return Value(True, output_field=BooleanField())
            participants_to_approve = self.get_work_package_participants_to_approve(approver=user)
            ids = [p.id for p in participants_to_approve]
            return Case(
                When(participant__role__in=ProjectRole.approved_roles(), then=Value(True)),
                When(id__in=ids, then=Value(False)),
                default=Value(has_datasets),
                output_field=BooleanField(),
            )

        qs = WorkPackageParticipant.objects.filter(work_package=self)
        qs = qs.annotate(approved=approved_annotation())

        if approver:
            participant = approver.get_participant(self.project)
            if participant and participant.permissions.can_approve_participants:
                qs = qs.annotate(approved_by_you=approved_annotation(approver))
        return qs

    def get_users_to_approve(self, approver):
        work_package_participants = self.get_work_package_participants_to_approve(
            approver
        ).select_related("participant__user")
        return [p.participant.user for p in work_package_participants]

    @property
    def has_tier(self):
        """Has this work package's data been classified?"""
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
        return reverse("projects:work_package_detail", args=[self.project.id, self.pk])

    def __str__(self):
        return self.name


class Participant(CreatedByModel):
    """
    Represents a user's participation in a project
    """

    role = models.CharField(
        max_length=50,
        choices=ProjectRole.choices(),
        validators=[validate_role],
        help_text="The participant's role on this project",
    )

    user = models.ForeignKey(User, related_name="participants", on_delete=models.CASCADE)
    project = models.ForeignKey(Project, related_name="participants", on_delete=models.CASCADE)

    class Meta(CreatedByModel.Meta):
        unique_together = ("user", "project")

    def __str__(self):
        return f"{self.user} ({self.get_role_display()} on {self.project})"

    @property
    def permissions(self):
        return self.user.project_permissions(self.project, participant=self)

    def get_work_package_participant(self, work_package):
        qs = WorkPackageParticipant.objects.filter(participant=self, work_package=work_package)
        if qs.exists():
            return qs.first()
        return None


class ClassificationOpinion(CreatedByModel):
    """
    Represents a user's opinion about the data tier classification of a work package
    """

    work_package = models.ForeignKey(
        WorkPackage, related_name="classifications", on_delete=models.CASCADE
    )
    tier = models.PositiveSmallIntegerField(choices=TIER_CHOICES)
    role = models.CharField(
        max_length=50,
        choices=ProjectRole.choices(),
        validators=[validate_role],
        help_text="The participant's role on this project at the time classification was made",
    )

    class Meta(CreatedByModel.Meta):
        unique_together = ("created_by", "work_package")

    def __str__(self):
        return f"{self.created_by}: {self.work_package} (tier {self.tier})"

    @property
    def datasets(self):
        return [wpd.dataset for wpd in WorkPackageDataset.objects.filter(opinion=self)]


class ClassificationOpinionQuestion(models.Model):
    opinion = models.ForeignKey(
        ClassificationOpinion, on_delete=models.CASCADE, related_name="questions"
    )
    order = models.SmallIntegerField()
    question = models.ForeignKey(ClassificationQuestion, on_delete=models.PROTECT, related_name="+")
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
    project = models.ForeignKey(Project, related_name="project_datasets", on_delete=models.CASCADE)
    dataset = models.ForeignKey(Dataset, related_name="+", on_delete=models.PROTECT)
    representative = models.ForeignKey(User, related_name="+", on_delete=models.PROTECT, null=False)

    def get_absolute_url(self):
        return reverse("projects:dataset_detail", args=[self.project.id, self.dataset.pk])


class WorkPackageDataset(CreatedByModel):
    work_package = models.ForeignKey(
        WorkPackage, related_name="work_package_datasets", on_delete=models.CASCADE
    )
    dataset = models.ForeignKey(Dataset, related_name="+", on_delete=models.PROTECT)
    opinion = models.ForeignKey(
        "ClassificationOpinion", null=True, related_name="+", on_delete=models.SET_NULL
    )

    class Meta(CreatedByModel.Meta):
        unique_together = ("work_package", "dataset")


class WorkPackageParticipant(CreatedByModel):
    work_package = models.ForeignKey(
        WorkPackage, related_name="work_package_participants", on_delete=models.CASCADE
    )
    participant = models.ForeignKey(Participant, related_name="+", on_delete=models.CASCADE)

    class Meta(CreatedByModel.Meta):
        unique_together = ("participant", "work_package")

    def approve(self, approver):
        approver_participant = approver.get_participant(self.work_package.project)

        if approver_participant.role != ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value:
            raise ValidationError("Only Data Provider Representatives can approve users")

        for pd in ProjectDataset.objects.filter(
            project=self.work_package.project, representative=approver
        ):
            for wpd in WorkPackageDataset.objects.filter(
                work_package=self.work_package, dataset=pd.dataset
            ):
                WorkPackageParticipantApproval.objects.create(
                    work_package_participant=self,
                    dataset=pd.dataset,
                    created_by=approver,
                )

        self.work_package.calculate_tier()


class WorkPackageParticipantApproval(CreatedByModel):
    work_package_participant = models.ForeignKey(
        WorkPackageParticipant, on_delete=models.CASCADE, related_name="approvals"
    )
    dataset = models.ForeignKey(Dataset, related_name="+", on_delete=models.CASCADE)
