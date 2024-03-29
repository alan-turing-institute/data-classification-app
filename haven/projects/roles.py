from enum import Enum

from haven.core.utils import BooleanTextTable
from haven.identity.roles import UserRole


class ProjectRole(Enum):
    """
    Roles which a user can take in the context of a project.
    """

    # Roles which are assignable to users on a project
    REFEREE = "referee"
    PROJECT_MANAGER = "project_manager"
    INVESTIGATOR = "investigator"
    RESEARCHER = "researcher"
    DATA_PROVIDER_REPRESENTATIVE = "data_provider_representative"

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
            (cls.REFEREE.value, "Referee"),
            (cls.PROJECT_MANAGER.value, "Project Manager"),
            (cls.INVESTIGATOR.value, "Investigator"),
            (cls.RESEARCHER.value, "Researcher"),
            (cls.DATA_PROVIDER_REPRESENTATIVE.value, "Data Provider Representative"),
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

    @classmethod
    def approved_roles(cls):
        """List of roles that don't require approval for higher-tier work packages"""
        return [
            ProjectRole.INVESTIGATOR.value,
            ProjectRole.PROJECT_MANAGER.value,
            ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value,
        ]

    @classmethod
    def non_approved_roles(cls):
        """List of roles that require approval for higher-tier work packages"""
        return list(set(cls.ordered_display_role_list()) - set(cls.approved_roles()))


class UserPermissions:
    """
    Determine the permissions a User has globally, or on a particular project.
    """

    permissions = BooleanTextTable(
        definition="""
                             | SM PgM | PM DPR PI Ref Res | Extra
        create_users         |  Y   Y |  .   .  .   .   . |     .
        import_users         |  Y   Y |  .   .  .   .   . |     .
        assign_sm            |  .   . |  .   .  .   .   . |     .
        assign_pgm           |  Y   . |  .   .  .   .   . |     .
        assign_usr           |  Y   Y |  .   .  .   .   . |     .
        view_all_users       |  Y   Y |  Y   .  .   .   . |     .
        export_users         |  Y   Y |  .   .  .   .   . |     .
        edit_users           |  Y   Y |  .   .  .   .   . |     .
        create_projects      |  Y   Y |  .   .  .   .   . |     .
        view_all_projects    |  Y   Y |  .   .  .   .   . |     .
        edit_all_projects    |  Y   Y |  .   .  .   .   . |     .
        manage_applications  |  Y   Y |  .   .  .   .   . |     .
        ---------------------+--------+-------------------+------
        view_project_history |  Y   Y |  Y   .  .   .   . |     .
        edit_project         |  Y   Y |  Y   .  .   .   . |     .
        archive_project      |  Y   Y |  Y   .  .   .   . |     .
        add_participants     |  Y   Y |  Y   .  Y   .   . |     *
        assign_pm            |  Y   Y |  Y   .  .   .   . |     .
        assign_dpr           |  Y   Y |  Y   .  .   .   . |     .
        assign_pi            |  Y   Y |  Y   .  .   .   . |     .
        assign_ref           |  Y   Y |  Y   .  .   .   . |     .
        assign_res           |  Y   Y |  Y   .  Y   .   . |     .
        list_participants    |  Y   Y |  Y   Y  Y   Y   Y |     .
        edit_participants    |  Y   Y |  Y   .  Y   .   . |     .
        approve_participants |  .   . |  .   Y  .   .   . |     .
        add_datasets         |  Y   Y |  Y   .  .   .   . |     .
        edit_datasets        |  Y   Y |  Y   .  .   .   . |     .
        edit_datasets_dpr    |  Y   Y |  Y   .  .   .   . |     .
        delete_datasets      |  Y   Y |  Y   .  .   .   . |     .
        add_work_packages    |  Y   Y |  Y   .  .   .   . |     .
        edit_work_package    |  Y   Y |  Y   .  .   .   . |     .
        delete_work_package  |  Y   Y |  Y   .  .   .   . |     .
        view_classification  |  Y   Y |  Y   Y  Y   Y   . |     .
        open_classification  |  Y   Y |  Y   .  .   .   . |     .
        clear_classification |  Y   Y |  Y   .  .   .   . |     .
        close_classification |  Y   Y |  Y   .  .   .   . |     .
        classify_data        |  .   . |  .   Y  Y   Y   . |     .
        """,
        abbreviations={
            "SM": UserRole.SYSTEM_MANAGER,
            "PgM": UserRole.PROGRAMME_MANAGER,
            "USR": UserRole.NONE,
            "PM": ProjectRole.PROJECT_MANAGER,
            "DPR": ProjectRole.DATA_PROVIDER_REPRESENTATIVE,
            "PI": ProjectRole.INVESTIGATOR,
            "Ref": ProjectRole.REFEREE,
            "Res": ProjectRole.RESEARCHER,
        },
        ignore=["Extra"],
        default=lambda: False,
    )

    def __init__(self, project_role, system_role):
        self.system_role = system_role
        self.role = project_role

    @property
    def assignable_roles(self):
        """
        Roles this role is allowed to assign on the same project

        :return: list of `ProjectRole` objects
        """
        roles = [
            ProjectRole.PROJECT_MANAGER,
            ProjectRole.DATA_PROVIDER_REPRESENTATIVE,
            ProjectRole.INVESTIGATOR,
            ProjectRole.REFEREE,
            ProjectRole.RESEARCHER,
        ]
        return [r for r in roles if self.can_assign_role(r)]

    @property
    def creatable_roles(self):
        """
        User Roles which this role is allowed to create

        :return: list of `UserRole` objects
        """
        roles = [
            UserRole.SYSTEM_MANAGER,
            UserRole.PROGRAMME_MANAGER,
            UserRole.NONE,
        ]
        return [] if not self.can_create_users else [r for r in roles if self.can_assign_role(r)]

    @property
    def can_add_participants(self):
        """Is this role able to add new participants to the project?"""

        # To add a new participant, the user must also have system-level access to view users
        return self._can("view_all_users") and self._can("add_participants")

    def __getattr__(self, name):
        if name.startswith("can_"):
            permission = name.replace("can_", "")
            try:
                return self._can(permission)
            except ValueError as e:
                raise AttributeError(name) from e
        raise AttributeError(name)

    def _can(self, permission):
        try:
            permission_dict = self.permissions.as_dict()[permission]
        except KeyError as e:
            raise ValueError(f"{permission} not a valid permission") from e
        return permission_dict[self.role] or permission_dict[self.system_role]

    def can_assign_role(self, role):
        """
        Can this role assign the given role on this project?

        :param role: `ProjectRole` to be assigned
        :return `True` if can assign role, `False` if not
        """
        abbr = self.permissions.abbreviations_inverse[role].lower()
        return self._can(f"assign_{abbr}")
