import pytest

from haven.core import recipes
from haven.identity.roles import UserRole
from haven.projects.roles import ProjectRole, UserPermissions


class TestUserPermissions:
    def test_researcher_permissions(self):
        perms = UserPermissions(ProjectRole.RESEARCHER, UserRole.NONE)
        assert not perms.can_view_all_projects
        assert not perms.can_edit_all_projects
        assert not perms.can_create_projects
        assert not perms.can_create_users
        assert not perms.can_view_all_users
        assert not perms.can_export_users
        assert not perms.can_import_users
        assert not perms.can_edit_users
        assert not perms.can_assign_sm
        assert not perms.can_assign_pgm
        assert not perms.can_assign_usr
        assert not perms.can_assign_pm
        assert not perms.can_assign_dpr
        assert not perms.can_assign_pi
        assert not perms.can_assign_ref
        assert not perms.can_assign_res
        assert not perms.can_add_participants
        assert not perms.can_approve_participants
        assert not perms.can_edit_project
        assert not perms.can_archive_project
        assert not perms.can_view_project_history
        assert not perms.can_add_datasets
        assert not perms.can_edit_datasets
        assert not perms.can_delete_datasets
        assert not perms.can_add_work_packages
        assert perms.can_list_participants
        assert not perms.can_edit_participants
        assert not perms.can_view_classification
        assert not perms.can_classify_data
        assert not perms.can_open_classification
        assert not perms.can_close_classification

    def test_referee_permissions(self):
        perms = UserPermissions(ProjectRole.REFEREE, UserRole.NONE)
        assert not perms.can_view_all_projects
        assert not perms.can_edit_all_projects
        assert not perms.can_create_projects
        assert not perms.can_create_users
        assert not perms.can_view_all_users
        assert not perms.can_export_users
        assert not perms.can_import_users
        assert not perms.can_edit_users
        assert not perms.can_assign_sm
        assert not perms.can_assign_pgm
        assert not perms.can_assign_usr
        assert not perms.can_assign_pm
        assert not perms.can_assign_dpr
        assert not perms.can_assign_pi
        assert not perms.can_assign_ref
        assert not perms.can_assign_res
        assert not perms.can_add_participants
        assert not perms.can_approve_participants
        assert not perms.can_edit_project
        assert not perms.can_archive_project
        assert not perms.can_view_project_history
        assert not perms.can_add_datasets
        assert not perms.can_edit_datasets
        assert not perms.can_delete_datasets
        assert not perms.can_add_work_packages
        assert perms.can_list_participants
        assert not perms.can_edit_participants
        assert perms.can_view_classification
        assert perms.can_classify_data
        assert not perms.can_open_classification
        assert not perms.can_close_classification

    def test_investigator_permissions(self):
        perms = UserPermissions(ProjectRole.INVESTIGATOR, UserRole.NONE)
        assert not perms.can_view_all_projects
        assert not perms.can_edit_all_projects
        assert not perms.can_create_projects
        assert not perms.can_create_users
        assert not perms.can_view_all_users
        assert not perms.can_export_users
        assert not perms.can_import_users
        assert not perms.can_edit_users
        assert not perms.can_assign_sm
        assert not perms.can_assign_pgm
        assert not perms.can_assign_usr
        assert not perms.can_assign_pm
        assert not perms.can_assign_dpr
        assert not perms.can_assign_pi
        assert not perms.can_assign_ref
        assert perms.can_assign_res
        assert not perms.can_add_participants
        assert not perms.can_approve_participants
        assert not perms.can_edit_project
        assert not perms.can_archive_project
        assert not perms.can_view_project_history
        assert not perms.can_add_datasets
        assert not perms.can_edit_datasets
        assert not perms.can_delete_datasets
        assert not perms.can_add_work_packages
        assert perms.can_list_participants
        assert perms.can_edit_participants
        assert perms.can_view_classification
        assert perms.can_classify_data
        assert not perms.can_open_classification
        assert not perms.can_close_classification

    def test_dpr_permissions(self):
        perms = UserPermissions(ProjectRole.DATA_PROVIDER_REPRESENTATIVE, UserRole.NONE)
        assert not perms.can_view_all_projects
        assert not perms.can_edit_all_projects
        assert not perms.can_create_projects
        assert not perms.can_create_users
        assert not perms.can_view_all_users
        assert not perms.can_export_users
        assert not perms.can_import_users
        assert not perms.can_edit_users
        assert not perms.can_assign_sm
        assert not perms.can_assign_pgm
        assert not perms.can_assign_usr
        assert not perms.can_assign_pm
        assert not perms.can_assign_dpr
        assert not perms.can_assign_pi
        assert not perms.can_assign_ref
        assert not perms.can_assign_res
        assert not perms.can_add_participants
        assert perms.can_approve_participants
        assert not perms.can_edit_project
        assert not perms.can_archive_project
        assert not perms.can_view_project_history
        assert not perms.can_add_datasets
        assert not perms.can_edit_datasets
        assert not perms.can_delete_datasets
        assert not perms.can_add_work_packages
        assert perms.can_list_participants
        assert not perms.can_edit_participants
        assert perms.can_view_classification
        assert perms.can_classify_data
        assert not perms.can_open_classification
        assert not perms.can_close_classification

    def test_pm_permissions(self):
        perms = UserPermissions(ProjectRole.PROJECT_MANAGER, UserRole.NONE)
        assert not perms.can_view_all_projects
        assert not perms.can_edit_all_projects
        assert not perms.can_create_projects
        assert not perms.can_create_users
        assert perms.can_view_all_users
        assert not perms.can_export_users
        assert not perms.can_import_users
        assert not perms.can_edit_users
        assert not perms.can_assign_sm
        assert not perms.can_assign_pgm
        assert not perms.can_assign_usr
        assert perms.can_assign_pm
        assert perms.can_assign_dpr
        assert perms.can_assign_pi
        assert perms.can_assign_ref
        assert perms.can_assign_res
        assert perms.can_add_participants
        assert not perms.can_approve_participants
        assert perms.can_edit_project
        assert perms.can_archive_project
        assert perms.can_view_project_history
        assert perms.can_add_datasets
        assert perms.can_edit_datasets
        assert perms.can_delete_datasets
        assert perms.can_add_work_packages
        assert perms.can_list_participants
        assert perms.can_edit_participants
        assert perms.can_view_classification
        assert not perms.can_classify_data
        assert perms.can_open_classification
        assert perms.can_close_classification

    def test_pgm_permissions(self):
        perms = UserPermissions(None, UserRole.PROGRAMME_MANAGER)
        assert perms.can_view_all_projects
        assert perms.can_edit_all_projects
        assert perms.can_create_projects
        assert perms.can_create_users
        assert perms.can_view_all_users
        assert perms.can_export_users
        assert perms.can_import_users
        assert perms.can_edit_users
        assert not perms.can_assign_sm
        assert not perms.can_assign_pgm
        assert perms.can_assign_usr
        assert perms.can_assign_pm
        assert perms.can_assign_dpr
        assert perms.can_assign_pi
        assert perms.can_assign_ref
        assert perms.can_assign_res
        assert perms.can_add_participants
        assert not perms.can_approve_participants
        assert perms.can_edit_project
        assert perms.can_archive_project
        assert perms.can_view_project_history
        assert perms.can_add_datasets
        assert perms.can_edit_datasets
        assert perms.can_delete_datasets
        assert perms.can_add_work_packages
        assert perms.can_list_participants
        assert perms.can_edit_participants
        assert perms.can_view_classification
        assert not perms.can_classify_data
        assert perms.can_open_classification
        assert perms.can_close_classification

    def test_sm_permissions(self):
        perms = UserPermissions(None, UserRole.SYSTEM_MANAGER)
        assert perms.can_view_all_projects
        assert perms.can_edit_all_projects
        assert perms.can_create_projects
        assert perms.can_create_users
        assert perms.can_view_all_users
        assert perms.can_export_users
        assert perms.can_import_users
        assert perms.can_edit_users
        assert not perms.can_assign_sm
        assert perms.can_assign_pgm
        assert perms.can_assign_usr
        assert perms.can_assign_pm
        assert perms.can_assign_dpr
        assert perms.can_assign_pi
        assert perms.can_assign_ref
        assert perms.can_assign_res
        assert perms.can_add_participants
        assert not perms.can_approve_participants
        assert perms.can_edit_project
        assert perms.can_archive_project
        assert perms.can_view_project_history
        assert perms.can_add_datasets
        assert perms.can_edit_datasets
        assert perms.can_delete_datasets
        assert perms.can_add_work_packages
        assert perms.can_list_participants
        assert perms.can_edit_participants
        assert perms.can_view_classification
        assert not perms.can_classify_data
        assert perms.can_open_classification
        assert perms.can_close_classification

    def test_invalid_permissions(self):
        perms = UserPermissions(None, UserRole.SYSTEM_MANAGER)
        with pytest.raises(AttributeError):
            perms.can_do_anything


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
class TestProjectPermissions:
    def test_user_gets_permissions_on_correct_project(self, programme_manager, project_participant):
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

        permissions = project_participant.project_permissions(project1)
        assert permissions.can_edit_project

        permissions = project_participant.project_permissions(project2)
        assert not permissions.can_edit_project
