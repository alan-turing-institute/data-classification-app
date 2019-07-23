import pytest

from core import recipes
from identity.roles import UserRole
from projects.roles import ProjectRole


@pytest.mark.django_db
class TestUser:
    def test_superuser_gets_superuser_role(self, superuser):
        assert superuser.user_role is UserRole.SUPERUSER

    def test_user_has_role(self, programme_manager):
        assert programme_manager.user_role is UserRole.PROGRAMME_MANAGER

    def test_get_participant(self, researcher):
        assert researcher.user.get_participant(researcher.project) == researcher

    def test_get_participant_returns_None_for_non_involved_project(self, researcher):
        assert researcher.user.get_participant(recipes.project.make()) is None

    def test_project_role_for_participant(self, researcher):
        assert researcher.user.project_role(researcher.project).role is ProjectRole.RESEARCHER
        assert researcher.user.project_participation_role(researcher.project) is ProjectRole.RESEARCHER

    def test_superuser_gets_project_admin_role(self, superuser):
        assert superuser.project_role(recipes.project.make()).is_project_admin

    def test_superuser_does_not_get_participation_for_non_involed_projects(self, superuser):
        assert superuser.get_participant(recipes.project.make()) is None
        assert superuser.project_participation_role(recipes.project.make()) is None

    def test_system_manager_gets_project_admin_role(self, system_manager):
        assert system_manager.project_role(recipes.project.make()).is_project_admin

    def test_system_manager_does_not_get_participation_for_non_involed_projects(self, system_manager):
        assert system_manager.get_participant(recipes.project.make()) == None
        assert system_manager.project_participation_role(recipes.project.make()) is None

    def test_project_owner_gets_project_admin_role_when_not_involved(self, programme_manager):
        project = recipes.project.make(created_by=programme_manager)
        assert programme_manager.project_role(project).is_project_admin

    def test_project_owner_gets_project_admin_role_when_involved(self, programme_manager):
        project = recipes.project.make(created_by=programme_manager)
        project.add_user(user=programme_manager, role=ProjectRole.INVESTIGATOR.value, creator=programme_manager)
        assert programme_manager.project_role(project).is_project_admin

    def test_project_owner_is_not_participant_when_not_involved(self, programme_manager):
        project = recipes.project.make(created_by=programme_manager)
        assert programme_manager.get_participant(project) == None
        assert programme_manager.project_participation_role(project) is None

    def test_project_owner_is_participant_when_involved(self, programme_manager):
        project = recipes.project.make(created_by=programme_manager)
        project.add_user(user=programme_manager, role=ProjectRole.INVESTIGATOR.value, creator=programme_manager)
        assert programme_manager.get_participant(project).user == programme_manager
        assert programme_manager.project_participation_role(project) is ProjectRole.INVESTIGATOR

    def test_project_owner_does_not_get_admin_on_other_project_when_not_participating(self, standard_user):
        recipes.project.make(created_by=standard_user)
        project = recipes.project.make()
        assert not standard_user.project_role(project).is_project_admin
        assert standard_user.project_participation_role(project) is None

    def test_project_owner_does_not_get_role_on_other_project_when_not_participating(self, programme_manager):
        recipes.project.make(created_by=programme_manager)
        project = recipes.project.make()
        assert programme_manager.get_participant(project) is None
        assert programme_manager.project_participation_role(project) is None

    def test_project_owner_does_not_get_admin_on_other_project_when_participating(self, standard_user):
        recipes.project.make(created_by=standard_user)
        project = recipes.project.make()
        project.add_user(user=standard_user, role=ProjectRole.INVESTIGATOR.value, creator=standard_user)
        assert not standard_user.project_role(project).is_project_admin

    def test_project_role_is_None_for_non_involved_project(self, researcher):
        assert researcher.user.project_role(recipes.project.make()).role is None

    def test_project_participation_role_is_None_for_non_involved_project(self, researcher):
        assert researcher.user.project_participation_role(recipes.project.make()) is None
