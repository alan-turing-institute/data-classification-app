from identity.roles import UserRole
from projects.roles import ProjectRole, UserPermissions
import pytest

from core import recipes


class TestProjectRoleAddParticipants:
    def test_project_manager_can_add_participants(self):
        perms = UserPermissions(ProjectRole.PROJECT_MANAGER, UserRole.NONE)
        assert perms.can_add_participants

    def test_investigator_cannot_add_participants(self):
        perms = UserPermissions(ProjectRole.INVESTIGATOR, UserRole.NONE)
        assert not perms.can_add_participants

    def test_researcher_cannot_add_participants(self):
        perms = UserPermissions(ProjectRole.RESEARCHER, UserRole.NONE)
        assert not perms.can_add_participants

    def test_referee_cannot_add_participants(self):
        perms = UserPermissions(ProjectRole.REFEREE, UserRole.NONE)
        assert not perms.can_add_participants

    def test_system_manager_can_add_participants(self):
        perms = UserPermissions(ProjectRole.RESEARCHER, UserRole.SYSTEM_MANAGER)
        assert perms.can_add_participants

    def test_programme_manager_can_add_participants(self):
        perms = UserPermissions(ProjectRole.REFEREE, UserRole.PROGRAMME_MANAGER)
        assert perms.can_add_participants


class TestProjectRoleAssignableRoles:
    def test_programme_manager_can_assign_any_roles(self):
        # Use RESEARCHER because we are verifying that system-wide PROGRAMME_MANAGER overrides
        # researchers with lower permissions
        permissions = UserPermissions(ProjectRole.RESEARCHER, UserRole.PROGRAMME_MANAGER)
        assert permissions.can_assign_role(ProjectRole.PROJECT_MANAGER)
        assert permissions.can_assign_role(ProjectRole.INVESTIGATOR)
        assert permissions.can_assign_role(ProjectRole.RESEARCHER)
        assert permissions.can_assign_role(ProjectRole.REFEREE)

    def test_project_manager_can_assign_any_roles(self):
        permissions = UserPermissions(ProjectRole.PROJECT_MANAGER, UserRole.NONE)
        assert permissions.can_assign_role(ProjectRole.PROJECT_MANAGER)
        assert permissions.can_assign_role(ProjectRole.INVESTIGATOR)
        assert permissions.can_assign_role(ProjectRole.RESEARCHER)
        assert permissions.can_assign_role(ProjectRole.REFEREE)

    def test_system_manager_can_assign_any_roles(self):
        permissions = UserPermissions(ProjectRole.RESEARCHER, UserRole.SYSTEM_MANAGER)
        assert permissions.can_assign_role(ProjectRole.PROJECT_MANAGER)
        assert permissions.can_assign_role(ProjectRole.INVESTIGATOR)
        assert permissions.can_assign_role(ProjectRole.RESEARCHER)
        assert permissions.can_assign_role(ProjectRole.REFEREE)

    def test_investigator_can_only_assign_researchers(self):
        permissions = UserPermissions(ProjectRole.INVESTIGATOR, UserRole.NONE)
        assert permissions.can_assign_role(ProjectRole.RESEARCHER)
        assert not permissions.can_assign_role(ProjectRole.INVESTIGATOR)
        assert not permissions.can_assign_role(ProjectRole.REFEREE)

    def test_researcher_cannot_assign_roles(self):
        permissions = UserPermissions(ProjectRole.RESEARCHER, UserRole.NONE)
        assert permissions.assignable_roles == []
        assert not permissions.can_assign_role(ProjectRole.RESEARCHER)

    def test_referee_cannot_assign_roles(self):
        permissions = UserPermissions(ProjectRole.REFEREE, UserRole.NONE)
        assert permissions.assignable_roles == []
        assert not permissions.can_assign_role(ProjectRole.REFEREE)


class TestProjectRoleListParticipants:
    def test_project_manager_can_list_participants(self):
        perms = UserPermissions(ProjectRole.PROJECT_MANAGER, UserRole.NONE)
        assert perms.can_list_participants

    def test_investigator_can_list_participants(self):
        perms = UserPermissions(ProjectRole.INVESTIGATOR, UserRole.NONE)
        assert perms.can_list_participants

    def test_researcher_cannot_list_participants(self):
        perms = UserPermissions(ProjectRole.RESEARCHER, UserRole.NONE)
        assert perms.can_list_participants

    def test_referee_cannot_list_participants(self):
        perms = UserPermissions(ProjectRole.REFEREE, UserRole.NONE)
        assert perms.can_list_participants

    def test_programme_manager_can_list_participants(self):
        perms = UserPermissions(ProjectRole.RESEARCHER, UserRole.PROGRAMME_MANAGER)
        assert perms.can_list_participants

    def test_system_manager_can_list_participants(self):
        perms = UserPermissions(ProjectRole.RESEARCHER, UserRole.SYSTEM_MANAGER)
        assert perms.can_list_participants


class TestProjectRoleEditProject:
    def test_project_manager_can_edit(self):
        perms = UserPermissions(ProjectRole.PROJECT_MANAGER, UserRole.NONE)
        assert perms.can_edit

    def test_investigator_can_edit(self):
        perms = UserPermissions(ProjectRole.INVESTIGATOR, UserRole.NONE)
        assert not perms.can_edit

    def test_researcher_cannot_list_participants(self):
        perms = UserPermissions(ProjectRole.RESEARCHER, UserRole.NONE)
        assert not perms.can_edit

    def test_referee_cannot_list_participants(self):
        perms = UserPermissions(ProjectRole.REFEREE, UserRole.NONE)
        assert not perms.can_edit

    def test_programme_manager_can_edit(self):
        perms = UserPermissions(ProjectRole.RESEARCHER, UserRole.PROGRAMME_MANAGER)
        assert perms.can_edit

    def test_system_manager_can_edit(self):
        perms = UserPermissions(ProjectRole.RESEARCHER, UserRole.SYSTEM_MANAGER)
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


@pytest.mark.django_db
class TestPermissions:
    def test_project_manager_gets_permissions_on_projects(self, programme_manager, project_participant):
        project = recipes.project.make(created_by=programme_manager)

        project.add_user(
            project_participant,
            ProjectRole.PROJECT_MANAGER.value,
            programme_manager
        )

        permissions = project_participant.project_permissions(project)
        assert permissions.can_assign_pm
        assert permissions.can_assign_dpr
        assert permissions.can_assign_pi
        assert permissions.can_assign_ref
        assert permissions.can_assign_res
        assert permissions.can_add_participants
        assert not permissions.can_approve_participants
        assert permissions.can_edit
        assert permissions.can_archive
        assert permissions.can_view_history
        assert permissions.can_add_datasets
        assert permissions.can_add_work_packages
        assert permissions.can_list_participants
        assert permissions.can_edit_participants
        assert permissions.can_view_classification
        assert not permissions.can_classify_data
        assert not permissions.can_classify_if_approved

    def test_project_manager_does_not_get_permissions_on_other_projects(self, programme_manager, project_participant):
        project1 = recipes.project.make(created_by=programme_manager)
        project2 = recipes.project.make(created_by=programme_manager)

        project1.add_user(
            project_participant,
            ProjectRole.PROJECT_MANAGER.value,
            programme_manager
        )
        project2.add_user(
            project_participant,
            ProjectRole.RESEARCHER.value,
            programme_manager
        )

        permissions = project_participant.project_permissions(project2)
        assert not permissions.can_assign_pm
        assert not permissions.can_assign_dpr
        assert not permissions.can_assign_pi
        assert not permissions.can_assign_ref
        assert not permissions.can_assign_res
        assert not permissions.can_add_participants
        assert not permissions.can_approve_participants
        assert not permissions.can_edit
        assert not permissions.can_archive
        assert not permissions.can_view_history
        assert not permissions.can_add_datasets
        assert not permissions.can_add_work_packages
        assert permissions.can_list_participants  # Researcher can see other participants
        assert not permissions.can_edit_participants
        assert not permissions.can_view_classification
        assert not permissions.can_classify_data
        assert not permissions.can_classify_if_approved
