from core import recipes
from projects.roles import ProjectRole, UserProjectPermissions


class TestProjectRoleAddParticipants:
    def test_project_admin_can_add_participants(self):
        assert UserProjectPermissions(ProjectRole.RESEARCHER.value, True).can_add_participants

    def test_research_coordinator_can_add_participants(self):
        assert UserProjectPermissions(ProjectRole.RESEARCH_COORDINATOR, False).can_add_participants

    def test_investigator_can_add_participants(self):
        assert UserProjectPermissions(ProjectRole.INVESTIGATOR, False).can_add_participants

    def test_researcher_cannot_add_participants(self):
        assert not UserProjectPermissions(ProjectRole.RESEARCHER, False).can_add_participants


class TestProjectRoleAssignableRoles:
    def test_project_admin_can_assign_any_roles(self):
        # Use RESEARCHER because we are verifying that PROJECT_ADMIN overrides researchers with lower permissions
        assert UserProjectPermissions(ProjectRole.RESEARCHER.value, True).can_assign_role(ProjectRole.RESEARCH_COORDINATOR)
        assert UserProjectPermissions(ProjectRole.RESEARCHER.value, True).can_assign_role(ProjectRole.INVESTIGATOR)
        assert UserProjectPermissions(ProjectRole.RESEARCHER.value, True).can_assign_role(ProjectRole.RESEARCHER)

    def test_research_coordinator_can_assign_any_roles(self):
        assert UserProjectPermissions(ProjectRole.RESEARCH_COORDINATOR, False).can_assign_role(ProjectRole.RESEARCH_COORDINATOR)
        assert UserProjectPermissions(ProjectRole.RESEARCH_COORDINATOR, False).can_assign_role(ProjectRole.INVESTIGATOR)
        assert UserProjectPermissions(ProjectRole.RESEARCH_COORDINATOR, False).can_assign_role(ProjectRole.RESEARCHER)

    def test_investigator_can_only_assign_researchers(self):
        assert UserProjectPermissions(ProjectRole.INVESTIGATOR, False).can_assign_role(ProjectRole.RESEARCHER)
        assert not UserProjectPermissions(ProjectRole.INVESTIGATOR, False).can_assign_role(ProjectRole.INVESTIGATOR)

    def test_researcher_cannot_assign_roles(self):
        assert UserProjectPermissions(ProjectRole.RESEARCHER.value, False).assignable_roles == []
        assert not UserProjectPermissions(ProjectRole.RESEARCHER.value, False).can_assign_role(ProjectRole.RESEARCHER)


class TestProjectRoleListParticipants:
    def test_project_admin_can_list_participants(self):
        assert UserProjectPermissions(ProjectRole.RESEARCHER, True).can_list_participants

    def test_research_coordinator_can_list_participants(self):
        assert UserProjectPermissions(ProjectRole.RESEARCH_COORDINATOR, False).can_list_participants

    def test_investigator_can_list_participants(self):
        assert UserProjectPermissions(ProjectRole.INVESTIGATOR, False).can_list_participants

    def test_researcher_cannot_list_participants(self):
        assert not UserProjectPermissions(ProjectRole.RESEARCHER, False).can_list_participants


class TestIsValidAssignableParticipantRole:
    def test_valid_roles(self):
        assert ProjectRole.is_valid_assignable_participant_role('referee')
        assert ProjectRole.is_valid_assignable_participant_role('research_coordinator')
        assert ProjectRole.is_valid_assignable_participant_role('investigator')
        assert ProjectRole.is_valid_assignable_participant_role('researcher')
        assert ProjectRole.is_valid_assignable_participant_role('data_provider_representative')

    def test_project_admin_is_not_valid_assignable_role(self):
        assert not ProjectRole.is_valid_assignable_participant_role('project_admin')

    def test_labels_are_not_valid_roles(self):
        assert not ProjectRole.is_valid_assignable_participant_role('Research Coordinator')
        assert not ProjectRole.is_valid_assignable_participant_role('Data Provider Representative')

    def test_invalid_roles(self):
        assert not ProjectRole.is_valid_assignable_participant_role('')
        assert not ProjectRole.is_valid_assignable_participant_role(None)
        assert not ProjectRole.is_valid_assignable_participant_role('data')
        assert not ProjectRole.is_valid_assignable_participant_role('inv')
