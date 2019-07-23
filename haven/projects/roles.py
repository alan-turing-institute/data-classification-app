from enum import Enum


class ProjectRole(Enum):
    """
    Roles which a user can take in the context of a project.
    """

    # Roles which are assignable to users on a project
    REFEREE = 'referee'
    PROJECT_MANAGER = 'project_manager'
    INVESTIGATOR = 'investigator'
    RESEARCHER = 'researcher'
    DATA_PROVIDER_REPRESENTATIVE = 'data_provider_representative'

    @classmethod
    def is_valid_assignable_participant_role(cls, role):
        """Return True if role is a valid project assignment. Return False for
        any non-assignable roles such as PROJECT__ADMIN"""
        valid_role_names = [choice[0] for choice in ProjectRole.choices()]
        return role in valid_role_names

    @classmethod
    def choices(cls):
        """Dropdown choices for project roles"""
        return [
            (cls.REFEREE.value, 'Referee'),
            (cls.PROJECT_MANAGER.value, 'Project Manager'),
            (cls.INVESTIGATOR.value, 'Investigator'),
            (cls.RESEARCHER.value, 'Researcher'),
            (cls.DATA_PROVIDER_REPRESENTATIVE.value, 'Data Provider Representative'),
        ]

    @classmethod
    def display_name(cls, role):
        """User-visible string describing the role"""
        return dict(cls.choices())[role]

    @classmethod
    def ordered_display_role_list(cls):
        """List of roles in a suitable display order"""
        return [
            ProjectRole.INVESTIGATOR.value,
            ProjectRole.PROJECT_MANAGER.value,
            ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value,
            ProjectRole.REFEREE.value,
            ProjectRole.RESEARCHER.value,
        ]


class UserProjectPermissions:
    """
    Determine the permissions a User has on a particular project.
    """

    def __init__(self, project_role, system_role, is_project_admin):
        self.system_role = system_role
        self.role = project_role
        self.is_project_admin = is_project_admin

    @property
    def assignable_roles(self):
        """
        Roles this role is allowed to assign on the same project

        :return: list of `ProjectRole` objects
        """
        if self.is_project_admin or self.role is ProjectRole.PROJECT_MANAGER:
            return [ProjectRole.PROJECT_MANAGER,
                    ProjectRole.DATA_PROVIDER_REPRESENTATIVE,
                    ProjectRole.INVESTIGATOR,
                    ProjectRole.REFEREE,
                    ProjectRole.RESEARCHER]
        elif self.role is ProjectRole.INVESTIGATOR:
            return [ProjectRole.RESEARCHER]
        return []

    @property
    def can_add_participants(self):
        """Is this role able to add new participants to the project?"""

        # To add a new participant, the user must also have system-level access to view users
        return self.system_role.can_view_all_users and (self.is_project_admin or self.role in [
                    ProjectRole.PROJECT_MANAGER,
                    ProjectRole.INVESTIGATOR,
                ])

    @property
    def can_edit(self):
        """Is this role able to edit participants?"""
        return self.is_project_admin or self.role in [
            ProjectRole.PROJECT_MANAGER,
        ]

    @property
    def can_view_history(self):
        """Is this role able to view audit history?"""
        return self.is_project_admin or self.role in [
            ProjectRole.PROJECT_MANAGER,
        ]

    @property
    def can_add_datasets(self):
        """Is this role able to add new datasets to the project?"""
        return self.is_project_admin or self.role in [
            ProjectRole.PROJECT_MANAGER,
            ProjectRole.INVESTIGATOR,
        ]

    @property
    def can_add_work_packages(self):
        """Is this role able to add new work packages to the project?"""
        return self.is_project_admin or self.role in [
            ProjectRole.PROJECT_MANAGER,
            ProjectRole.INVESTIGATOR,
        ]

    @property
    def can_list_participants(self):
        """Is this role able to list participants?"""
        return self.is_project_admin or self.role in [
            ProjectRole.PROJECT_MANAGER,
            ProjectRole.INVESTIGATOR,
        ]

    @property
    def can_edit_participants(self):
        """Is this role able to edit participants?"""
        return self.is_project_admin or self.role in [
            ProjectRole.PROJECT_MANAGER,
            ProjectRole.INVESTIGATOR,
        ]

    @property
    def can_classify_data(self):
        """Is this role able to perform a data classification?"""

        # Does not include PROJECT_ADMIN because classification should only be done by appointed users
        return self.role in [
            ProjectRole.REFEREE,
            ProjectRole.DATA_PROVIDER_REPRESENTATIVE,
            ProjectRole.INVESTIGATOR,
        ]

    def can_assign_role(self, role):
        """
        Can this role assign the given role on this project?

        :param role: `ProjectRole` to be assigned
        :return `True` if can assign role, `False` if not
        """
        return role in self.assignable_roles
