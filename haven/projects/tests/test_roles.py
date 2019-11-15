from identity.roles import UserRole
from projects.roles import ProjectRole, UserProjectPermissions


class TestProjectRoleAddParticipants:
    def test_project_manager_cannot_add_participants(self):
        perms = UserProjectPermissions(ProjectRole.PROJECT_MANAGER, UserRole.NONE)
        assert not perms.can_add_participants

    def test_investigator_cannot_add_participants(self):
        perms = UserProjectPermissions(ProjectRole.INVESTIGATOR, UserRole.NONE)
        assert not perms.can_add_participants

    def test_researcher_cannot_add_participants(self):
        perms = UserProjectPermissions(ProjectRole.RESEARCHER, UserRole.NONE)
        assert not perms.can_add_participants

    def test_referee_cannot_add_participants(self):
        perms = UserProjectPermissions(ProjectRole.REFEREE, UserRole.NONE)
        assert not perms.can_add_participants

    def test_system_manager_can_add_participants(self):
        perms = UserProjectPermissions(ProjectRole.RESEARCHER, UserRole.SYSTEM_MANAGER)
        assert perms.can_add_participants

    def test_programme_manager_can_add_participants(self):
        perms = UserProjectPermissions(ProjectRole.REFEREE, UserRole.PROGRAMME_MANAGER)
        assert perms.can_add_participants


class TestProjectRoleAssignableRoles:
    def test_programme_manager_can_assign_any_roles(self):
        # Use RESEARCHER because we are verifying that system-wide PROGRAMME_MANAGER overrides
        # researchers with lower permissions
        permissions = UserProjectPermissions(ProjectRole.RESEARCHER, UserRole.PROGRAMME_MANAGER)
        assert permissions.can_assign_role(ProjectRole.PROJECT_MANAGER)
        assert permissions.can_assign_role(ProjectRole.INVESTIGATOR)
        assert permissions.can_assign_role(ProjectRole.RESEARCHER)
        assert permissions.can_assign_role(ProjectRole.REFEREE)

    def test_project_manager_can_assign_any_roles(self):
        permissions = UserProjectPermissions(ProjectRole.PROJECT_MANAGER, UserRole.NONE)
        assert permissions.can_assign_role(ProjectRole.PROJECT_MANAGER)
        assert permissions.can_assign_role(ProjectRole.INVESTIGATOR)
        assert permissions.can_assign_role(ProjectRole.RESEARCHER)
        assert permissions.can_assign_role(ProjectRole.REFEREE)

    def test_system_manager_can_assign_any_roles(self):
        permissions = UserProjectPermissions(ProjectRole.RESEARCHER, UserRole.SYSTEM_MANAGER)
        assert permissions.can_assign_role(ProjectRole.PROJECT_MANAGER)
        assert permissions.can_assign_role(ProjectRole.INVESTIGATOR)
        assert permissions.can_assign_role(ProjectRole.RESEARCHER)
        assert permissions.can_assign_role(ProjectRole.REFEREE)

    def test_investigator_can_only_assign_researchers(self):
        permissions = UserProjectPermissions(ProjectRole.INVESTIGATOR, UserRole.NONE)
        assert permissions.can_assign_role(ProjectRole.RESEARCHER)
        assert not permissions.can_assign_role(ProjectRole.INVESTIGATOR)
        assert not permissions.can_assign_role(ProjectRole.REFEREE)

    def test_researcher_cannot_assign_roles(self):
        permissions = UserProjectPermissions(ProjectRole.RESEARCHER, UserRole.NONE)
        assert permissions.assignable_roles == []
        assert not permissions.can_assign_role(ProjectRole.RESEARCHER)

    def test_referee_cannot_assign_roles(self):
        permissions = UserProjectPermissions(ProjectRole.REFEREE, UserRole.NONE)
        assert permissions.assignable_roles == []
        assert not permissions.can_assign_role(ProjectRole.REFEREE)


class TestProjectRoleListParticipants:
    def test_project_manager_can_list_participants(self):
        perms = UserProjectPermissions(ProjectRole.PROJECT_MANAGER, UserRole.NONE)
        assert perms.can_list_participants

    def test_investigator_can_list_participants(self):
        perms = UserProjectPermissions(ProjectRole.INVESTIGATOR, UserRole.NONE)
        assert perms.can_list_participants

    def test_researcher_cannot_list_participants(self):
        perms = UserProjectPermissions(ProjectRole.RESEARCHER, UserRole.NONE)
        assert perms.can_list_participants

    def test_referee_cannot_list_participants(self):
        perms = UserProjectPermissions(ProjectRole.REFEREE, UserRole.NONE)
        assert perms.can_list_participants

    def test_programme_manager_can_list_participants(self):
        perms = UserProjectPermissions(ProjectRole.RESEARCHER, UserRole.PROGRAMME_MANAGER)
        assert perms.can_list_participants

    def test_system_manager_can_list_participants(self):
        perms = UserProjectPermissions(ProjectRole.RESEARCHER, UserRole.SYSTEM_MANAGER)
        assert perms.can_list_participants


class TestProjectRoleEditProject:
    def test_project_manager_can_edit(self):
        perms = UserProjectPermissions(ProjectRole.PROJECT_MANAGER, UserRole.NONE)
        assert perms.can_edit

    def test_investigator_can_edit(self):
        perms = UserProjectPermissions(ProjectRole.INVESTIGATOR, UserRole.NONE)
        assert not perms.can_edit

    def test_researcher_cannot_list_participants(self):
        perms = UserProjectPermissions(ProjectRole.RESEARCHER, UserRole.NONE)
        assert not perms.can_edit

    def test_referee_cannot_list_participants(self):
        perms = UserProjectPermissions(ProjectRole.REFEREE, UserRole.NONE)
        assert not perms.can_edit

    def test_programme_manager_can_edit(self):
        perms = UserProjectPermissions(ProjectRole.RESEARCHER, UserRole.PROGRAMME_MANAGER)
        assert perms.can_edit

    def test_system_manager_can_edit(self):
        perms = UserProjectPermissions(ProjectRole.RESEARCHER, UserRole.SYSTEM_MANAGER)
        assert perms.can_edit


class TestIsValidAssignableParticipantRole:
    def test_valid_roles(self):
        assert ProjectRole.is_valid_assignable_participant_role('referee')
        assert ProjectRole.is_valid_assignable_participant_role('project_manager')
        assert ProjectRole.is_valid_assignable_participant_role('investigator')
        assert ProjectRole.is_valid_assignable_participant_role('researcher')
        assert ProjectRole.is_valid_assignable_participant_role('data_provider_representative')

    def test_labels_are_not_valid_roles(self):
        assert not ProjectRole.is_valid_assignable_participant_role('Project Manager')
        assert not ProjectRole.is_valid_assignable_participant_role('Data Provider Representative')

    def test_invalid_roles(self):
        assert not ProjectRole.is_valid_assignable_participant_role('')
        assert not ProjectRole.is_valid_assignable_participant_role(None)
        assert not ProjectRole.is_valid_assignable_participant_role('data')
        assert not ProjectRole.is_valid_assignable_participant_role('inv')
