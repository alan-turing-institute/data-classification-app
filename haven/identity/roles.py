from enum import Enum


class UserRole(Enum):
    """
    User roles global to the system
    """

    # Roles which are assignable to users on the `role` field
    SYSTEM_MANAGER = 'system_manager'
    PROGRAMME_MANAGER = 'programme_manager'

    # Django admin superuser
    SUPERUSER = 'superuser'

    # No user role - this means an unprivileged user who will most likely have
    # roles on individual projects but has no global / system-level role.
    NONE = ''

    @classmethod
    def choices(cls):
        """Dropdown choices for user roles"""
        return [
            (cls.SYSTEM_MANAGER.value, 'System Manager'),
            (cls.PROGRAMME_MANAGER.value, 'Programme Manager'),
            (cls.NONE.value, 'Standard user'),
        ]

    @classmethod
    def display_name(cls, role):
        """User-visible string describing the role"""
        return dict(cls.choices())[role]

    @classmethod
    def ordered_display_role_list(cls):
        """List of roles in a suitable display order"""
        return [
            cls.SYSTEM_MANAGER.value,
            cls.PROGRAMME_MANAGER.value,
            cls.NONE.value
        ]

    @property
    def creatable_roles(self):
        """
        User Roles which this role is allowed to create

        :return: list of `UserRole` objects
        """
        if self is self.SUPERUSER:
            return [
                self.SYSTEM_MANAGER,
                self.PROGRAMME_MANAGER,
            ]
        elif self is self.SYSTEM_MANAGER:
            return [
                self.PROGRAMME_MANAGER,
            ]
        return []

    @property
    def can_view_all_projects(self):
        """Can a user with this role view all projects?"""
        return self in [
            self.SUPERUSER,
            self.SYSTEM_MANAGER,
        ]

    @property
    def can_edit_all_projects(self):
        """Can a user with this role edit all projects?"""
        return self in [
            self.SUPERUSER,
            self.SYSTEM_MANAGER,
        ]

    @property
    def can_create_projects(self):
        """Can a user with this role create projects?"""
        return self in [
            self.SUPERUSER,
            self.SYSTEM_MANAGER,
            self.PROGRAMME_MANAGER,
        ]

    @property
    def can_create_users(self):
        """Can a user with this role create other users?"""
        return self in [
            self.SUPERUSER,
            self.SYSTEM_MANAGER,
        ]

    @property
    def can_view_all_users(self):
        """Can a user with this role view all users?"""
        return self in [
            self.SUPERUSER,
            self.PROGRAMME_MANAGER,
            self.SYSTEM_MANAGER,
        ]

    @property
    def can_export_users(self):
        """Can a user with this role export a user list?"""
        return self in [
            self.SUPERUSER,
            self.SYSTEM_MANAGER,
        ]

    @property
    def can_import_users(self):
        """Can a user with this role create users from an imported file?"""
        return self in [
            self.SUPERUSER,
            self.SYSTEM_MANAGER,
        ]

    @property
    def can_edit_users(self):
        """Can a user with this role edit other users?"""
        return self.can_create_users

    def can_create(self, role):
        """
        Can a user with this role create other users with the given role?

        :param role: `UserRole` to be created
        :return `True` if can create role, `False` if not
        """
        return (
            role is self.NONE and self.can_create_users or
            role in self.creatable_roles
        )

    def can_assign_role(self, role):
        """
        Can this role assign the given system role?

        :param role: `UserRole` to be assigned
        :return `True` if can assign role, `False` if not
        """
        return role in self.creatable_roles
