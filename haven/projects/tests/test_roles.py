from identity.roles import UserRole
from projects.roles import ProjectRole, UserProjectPermissions


class TestProjectRoleAddParticipants:
    def test_project_admin_cannot_add_participants(self):
        assert not UserProjectPermissions(ProjectRole.RESEARCHER, UserRole.NONE, True).can_add_participants

    def test_project_manager_cannot_add_participants(self):
        assert not UserProjectPermissions(ProjectRole.PROJECT_MANAGER, UserRole.NONE, False).can_add_participants

    def test_investigator_cannot_add_participants(self):
        assert not UserProjectPermissions(ProjectRole.INVESTIGATOR, UserRole.NONE, False).can_add_participants

    def test_researcher_cannot_add_participants(self):
        assert not UserProjectPermissions(ProjectRole.RESEARCHER, UserRole.NONE, False).can_add_participants

    def test_referee_cannot_add_participants(self):
        assert not UserProjectPermissions(ProjectRole.REFEREE, UserRole.NONE, False).can_add_participants

    def test_system_manager_can_add_participants(self):
        assert UserProjectPermissions(ProjectRole.RESEARCHER, UserRole.SYSTEM_MANAGER, True).can_add_participants

    def test_programme_manager_can_add_participants(self):
        assert UserProjectPermissions(ProjectRole.REFEREE, UserRole.PROGRAMME_MANAGER, True).can_add_participants


class TestProjectRoleAssignableRoles:
    def test_project_admin_can_assign_any_roles(self):
        # Use RESEARCHER because we are verifying that PROJECT_ADMIN overrides researchers with lower permissions
        permissions = UserProjectPermissions(ProjectRole.RESEARCHER, UserRole.NONE, True)
        assert permissions.can_assign_role(ProjectRole.PROJECT_MANAGER)
        assert permissions.can_assign_role(ProjectRole.INVESTIGATOR)
        assert permissions.can_assign_role(ProjectRole.RESEARCHER)
        assert permissions.can_assign_role(ProjectRole.REFEREE)

    def test_programme_manager_can_assign_any_roles(self):
        # Use RESEARCHER because we are verifying that system-wide PROGRAMME_MANAGER overrides researchers with lower permissions
        permissions = UserProjectPermissions(ProjectRole.RESEARCHER, UserRole.PROGRAMME_MANAGER, True)
        assert permissions.can_assign_role(ProjectRole.PROJECT_MANAGER)
        assert permissions.can_assign_role(ProjectRole.INVESTIGATOR)
        assert permissions.can_assign_role(ProjectRole.RESEARCHER)
        assert permissions.can_assign_role(ProjectRole.REFEREE)

    def test_project_manager_can_assign_any_roles(self):
        permissions = UserProjectPermissions(ProjectRole.PROJECT_MANAGER, UserRole.NONE, False)
        assert permissions.can_assign_role(ProjectRole.PROJECT_MANAGER)
        assert permissions.can_assign_role(ProjectRole.INVESTIGATOR)
        assert permissions.can_assign_role(ProjectRole.RESEARCHER)
        assert permissions.can_assign_role(ProjectRole.REFEREE)

    def test_system_manager_can_assign_any_roles(self):
        permissions = UserProjectPermissions(ProjectRole.RESEARCHER, UserRole.SYSTEM_MANAGER, True)
        assert permissions.can_assign_role(ProjectRole.PROJECT_MANAGER)
        assert permissions.can_assign_role(ProjectRole.INVESTIGATOR)
        assert permissions.can_assign_role(ProjectRole.RESEARCHER)
        assert permissions.can_assign_role(ProjectRole.REFEREE)

    def test_investigator_can_only_assign_researchers(self):
        permissions = UserProjectPermissions(ProjectRole.INVESTIGATOR, UserRole.NONE, False)
        assert permissions.can_assign_role(ProjectRole.RESEARCHER)
        assert not permissions.can_assign_role(ProjectRole.INVESTIGATOR)
        assert not permissions.can_assign_role(ProjectRole.REFEREE)

    def test_researcher_cannot_assign_roles(self):
        permissions = UserProjectPermissions(ProjectRole.RESEARCHER, UserRole.NONE, False)
        assert permissions.assignable_roles == []
        assert not permissions.can_assign_role(ProjectRole.RESEARCHER)

    def test_referee_cannot_assign_roles(self):
        permissions = UserProjectPermissions(ProjectRole.REFEREE, UserRole.NONE, False)
        assert permissions.assignable_roles == []
        assert not permissions.can_assign_role(ProjectRole.REFEREE)


class TestProjectRoleListParticipants:
    def test_project_admin_can_list_participants(self):
        assert UserProjectPermissions(ProjectRole.RESEARCHER, UserRole.NONE, True).can_list_participants

    def test_project_manager_can_list_participants(self):
        assert UserProjectPermissions(ProjectRole.PROJECT_MANAGER, UserRole.NONE, False).can_list_participants

    def test_investigator_can_list_participants(self):
        assert UserProjectPermissions(ProjectRole.INVESTIGATOR, UserRole.NONE, False).can_list_participants

    def test_researcher_cannot_list_participants(self):
        assert not UserProjectPermissions(ProjectRole.RESEARCHER, UserRole.NONE, False).can_list_participants

    def test_referee_cannot_list_participants(self):
        assert not UserProjectPermissions(ProjectRole.REFEREE, UserRole.NONE, False).can_list_participants

    def test_programme_manager_can_list_participants(self):
        assert not UserProjectPermissions(ProjectRole.RESEARCHER, UserRole.PROGRAMME_MANAGER, False).can_list_participants

    def test_system_manager_can_list_participants(self):
        assert not UserProjectPermissions(ProjectRole.RESEARCHER, UserRole.SYSTEM_MANAGER, False).can_list_participants


class TestIsValidAssignableParticipantRole:
    def test_valid_roles(self):
        assert ProjectRole.is_valid_assignable_participant_role('referee')
        assert ProjectRole.is_valid_assignable_participant_role('project_manager')
        assert ProjectRole.is_valid_assignable_participant_role('investigator')
        assert ProjectRole.is_valid_assignable_participant_role('researcher')
        assert ProjectRole.is_valid_assignable_participant_role('data_provider_representative')

    def test_project_admin_is_not_valid_assignable_role(self):
        assert not ProjectRole.is_valid_assignable_participant_role('project_admin')

    def test_labels_are_not_valid_roles(self):
        assert not ProjectRole.is_valid_assignable_participant_role('Project Manager')
        assert not ProjectRole.is_valid_assignable_participant_role('Data Provider Representative')

    def test_invalid_roles(self):
        assert not ProjectRole.is_valid_assignable_participant_role('')
        assert not ProjectRole.is_valid_assignable_participant_role(None)
        assert not ProjectRole.is_valid_assignable_participant_role('data')
        assert not ProjectRole.is_valid_assignable_participant_role('inv')
