from enum import Enum


class ProjectRole(Enum):
    """
    Roles which a user can take in the context of a project.
    """

    # Roles which are assignable to users on a project
    REFEREE = 'referee'
    RESEARCH_COORDINATOR = 'research_coordinator'
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
            (cls.RESEARCH_COORDINATOR.value, 'Research Coordinator'),
            (cls.INVESTIGATOR.value, 'Investigator'),
            (cls.RESEARCHER.value, 'Researcher'),
            (cls.DATA_PROVIDER_REPRESENTATIVE.value, 'Data Provider Representative'),
        ]


class UserProjectPermissions:
    """
    Determine the permissions a User has on a particular project.
    """

    def __init__(self, project_role, is_project_admin):
        self.role = project_role
        self.is_project_admin = is_project_admin

    @property
    def assignable_roles(self):
        """
        Roles this role is allowed to assign on the same project

        :return: list of `ProjectRole` objects
        """
        if self.is_project_admin or self.role is ProjectRole.RESEARCH_COORDINATOR:
            return [ProjectRole.RESEARCH_COORDINATOR,
                    ProjectRole.DATA_PROVIDER_REPRESENTATIVE,
                    ProjectRole.INVESTIGATOR,
                    ProjectRole.RESEARCHER]
        elif self.role is ProjectRole.INVESTIGATOR:
            return [ProjectRole.RESEARCHER]
        return []

    @property
    def can_add_participants(self):
        """Is this role able to add new participants to the project?"""
        return self.is_project_admin or self.role in [
            ProjectRole.RESEARCH_COORDINATOR,
            ProjectRole.INVESTIGATOR,
        ]

    @property
    def can_add_datasets(self):
        """Is this role able to add new datasets to the project?"""
        return self.is_project_admin or self.role in [
            ProjectRole.RESEARCH_COORDINATOR,
            ProjectRole.INVESTIGATOR,
        ]

    @property
    def can_list_participants(self):
        """Is this role able to list participants?"""
        return self.is_project_admin or self.role in [
            ProjectRole.RESEARCH_COORDINATOR,
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
