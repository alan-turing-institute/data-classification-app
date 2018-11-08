import pytest

from core import recipes
from identity.roles import ProjectRole, UserRole


@pytest.mark.django_db
class TestUser:
    def test_superuser_gets_superuser_role(self, superuser):
        assert superuser.user_role is UserRole.SUPERUSER

    def test_user_has_role(self, research_coordinator):
        assert research_coordinator.user_role is UserRole.RESEARCH_COORDINATOR

    def test_get_participant(self, researcher):
        assert researcher.user.get_participant(researcher.project) == researcher

    def test_get_participant_returns_None_for_non_involved_project(self, researcher):
        assert researcher.user.get_participant(recipes.project.make()) is None

    def test_project_role_for_participant(self, researcher):
        assert researcher.user.project_role(researcher.project) is ProjectRole.RESEARCHER

    def test_superuser_gets_project_admin_role(self, superuser):
        assert superuser.project_role(recipes.project.make()) is ProjectRole.PROJECT_ADMIN

    def test_system_controller_gets_project_admin_role(self, system_controller):
        assert system_controller.project_role(recipes.project.make()) is ProjectRole.PROJECT_ADMIN

    def test_project_owner_gets_project_admin_role(self, research_coordinator):
        project = recipes.project.make(created_by=research_coordinator)
        assert research_coordinator.project_role(project) is ProjectRole.PROJECT_ADMIN

    def test_project_owner_does_not_get_admin_on_other_project(self, research_coordinator):
        project = recipes.project.make()
        assert research_coordinator.project_role(project) is None

    def test_project_role_is_None_for_non_involved_project(self, researcher):
        assert researcher.user.project_role(recipes.project.make()) is None
