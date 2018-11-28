from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.text import slugify

from projects.roles import ProjectRole

from .roles import UserRole


class User(AbstractUser):
    """
    Represents a user that can log in to the system
    """
    role = models.CharField(
        max_length=50,
        choices=UserRole.choices(),
        blank=True,
        help_text="The user's role in the system"
    )

    # No created_at field here since `AbstractUser` already stores this
    created_by = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        related_name='+',
        help_text='User who created this user',
    )

    email = models.EmailField(
        max_length=254,
        verbose_name='email address',
        unique=True
    )

    first_name = models.CharField(max_length=30, verbose_name='first name')
    last_name = models.CharField(max_length=150, verbose_name='last name')

    AAD_STATUS_FAILED_TO_CREATE = 'failed_to_create'
    AAD_STATUS_PENDING = 'pending'
    AAD_STATUS_CREATED = 'created'
    AAD_STATUS_ACTIVATED = 'activated'
    AAD_STATUS_CHOICES = (
        (AAD_STATUS_FAILED_TO_CREATE, 'Creation failed'),    # AD creation failed
        (AAD_STATUS_PENDING, 'Pending'),  # has been creatd in AD and awaiting sync to AAD
        (AAD_STATUS_CREATED, 'Created'),  # has been found in AAD and sent email
        (AAD_STATUS_ACTIVATED, 'Activated'),  # has been activated / password set
    )
    aad_status = models.CharField(
        max_length=16,
        choices=AAD_STATUS_CHOICES,
        blank=True
    )

    @property
    def user_role(self):
        if self.is_superuser:
            return UserRole.SUPERUSER
        return UserRole(self.role)

    def set_role(self, role):
        self.role = role.value
        self.save()

    def set_aad_status(self, status):
        self.aad_status = status
        self.save()

    def generate_username(self):
        prefix = '{0}.{1}'.format(slugify(self.first_name), slugify(self.last_name))

        inc = 0
        while True:
            proposed_username = '{prefix}{inc}@{domain}'.format(
                prefix=prefix,
                inc=inc or '',
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
        from projects.models import Participant
        try:
            return self.participant_set.get(project=project)
        except Participant.DoesNotExist:
            return None

    def project_role(self, project):
        """
        Return the role of a user on this project

        :return: ProjectRole or None if user is not involved in project
        """
        if ((self.is_superuser or
             self.user_role is UserRole.SYSTEM_CONTROLLER or
             self == project.created_by)):
            return ProjectRole.PROJECT_ADMIN
        else:
            participant = self.get_participant(project)
            return ProjectRole(participant.role) if participant else None
