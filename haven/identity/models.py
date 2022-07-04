import re
import unicodedata

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Case, When
from django.utils.safestring import mark_safe
from phonenumber_field.modelfields import PhoneNumberField

from haven.identity.managers import CustomUserManager
from haven.identity.roles import UserRole


class User(AbstractUser):
    """
    Represents a user that can log in to the system
    """

    role = models.CharField(
        max_length=50,
        choices=UserRole.choices(),
        blank=True,
        help_text="The user's role in the system",
    )

    # No created_at field here since `AbstractUser` already stores this
    created_by = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        related_name="+",
        help_text="User who created this user",
    )

    email = models.EmailField(
        max_length=254,
        verbose_name="email address",
        null=True,
    )

    mobile = PhoneNumberField(null=True)

    first_name = models.CharField(max_length=30, verbose_name="first name")
    last_name = models.CharField(max_length=150, verbose_name="last name")

    # AD creation failed
    AAD_STATUS_FAILED_TO_CREATE = "failed_to_create"
    # User created in AD and awaiting sync to AAD
    AAD_STATUS_PENDING = "pending"
    # User has been found in AAD and sent email
    AAD_STATUS_CREATED = "created"
    # User has been activated / password set
    AAD_STATUS_ACTIVATED = "activated"
    AAD_STATUS_CHOICES = (
        (AAD_STATUS_FAILED_TO_CREATE, "Creation failed"),
        (AAD_STATUS_PENDING, "Pending"),
        (AAD_STATUS_CREATED, "Created"),
        (AAD_STATUS_ACTIVATED, "Activated"),
    )

    # Status of user in active directory
    aad_status = models.CharField(max_length=16, choices=AAD_STATUS_CHOICES, blank=True)

    # Use a custom UserManager with our own QuerySet methods
    objects = CustomUserManager()

    @classmethod
    def ordered_participants(cls):
        """Order Users by their UserRole"""
        ordered_role_list = UserRole.ordered_display_role_list()
        order = Case(*[When(role=role, then=pos) for pos, role in enumerate(ordered_role_list)])
        return User.objects.filter(role__in=ordered_role_list).order_by(order)

    @property
    def user_role(self):
        return UserRole(self.role)

    def set_role(self, role):
        self.role = role.value
        self.save()

    def set_aad_status(self, status):
        self.aad_status = status
        self.save()

    @staticmethod
    def email_friendly(value):
        """
        Return a simplified form of the string suitable for use as part of an email username

        Hyphens and alphanumeric characters are preserved.
        Spaces between names are replaced by dots.
        """
        value = str(value)
        value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
        value = re.sub(r"[^\w\s-]", "", value).strip().lower()
        return mark_safe(re.sub(r"[\s]+", ".", value))

    def generate_username(self):
        """
        Return a suitable username for this user
        """
        prefix = self.email_friendly(f"{self.first_name} {self.last_name}")

        # If the username already exists, try adding 2,3,4 etc
        inc = 1
        while True:
            proposed_username = "{prefix}{inc}@{domain}".format(
                prefix=prefix,
                inc="" if inc < 2 else inc,
                domain=settings.SAFE_HAVEN_DOMAIN,
            )
            if not User.objects.filter(username=proposed_username).exists():
                break
            inc += 1

        self.username = proposed_username

    def get_participant(self, project):
        """
        Return a Participant object for a user on the project

        :return: `Participant` object or None if user is not involved in project
        """
        from haven.projects.models import Participant

        try:
            return self.participants.get(project=project)
        except Participant.DoesNotExist:
            return None

    def combined_permissions(self, project_id=None):
        """
        Return a UserPermissions object which may include project permissions for a particular
        project if the project_id is specified

        :return: UserPermissions object describing user permissions
        """

        from haven.projects.models import Project

        if project_id:
            project = Project.objects.get(pk=project_id)
            return self.project_permissions(project)
        else:
            return self.system_permissions

    @property
    def system_permissions(self):
        """
        Return object for determining the user's system-level permissions

        :return: UserPermissions object describing user permissions
        """

        from haven.projects.roles import UserPermissions

        return UserPermissions(None, self.user_role)

    def project_permissions(self, project, participant=None):
        """
        Return an object which can be used to determine user permissions relating to the user's
        role on a project and their system-level role.

        :return: UserPermissions
        """

        from haven.projects.roles import ProjectRole, UserPermissions

        if participant is None:
            participant = self.get_participant(project)
        project_role = ProjectRole(participant.role) if participant else None

        return UserPermissions(project_role, self.user_role)

    def project_participation_role(self, project):
        """
        Return the assigned project role of a user.

        Use this method for classification purposes.
        For determining project permissions, use project_permissions().

        :return: ProjectRole or None if user is not involved in project
        """
        from haven.projects.roles import ProjectRole

        participant = self.get_participant(project)
        return ProjectRole(participant.role) if participant else None

    def display_name(self):
        """
        Return a combined name and username for display

        :return:string combining the user's full name and username
        """

        full_name = self.get_full_name()
        username = self.username
        if full_name:
            return "{full_name}: {username}".format(full_name=full_name, username=username)
        else:
            return username
