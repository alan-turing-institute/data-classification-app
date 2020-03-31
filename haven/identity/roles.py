from enum import Enum


class UserRole(Enum):
    """
    User roles global to the system
    """

    # Roles which are assignable to users on the `role` field
    SYSTEM_MANAGER = 'system_manager'
    PROGRAMME_MANAGER = 'programme_manager'

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
