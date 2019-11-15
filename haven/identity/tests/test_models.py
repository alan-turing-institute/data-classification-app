import pytest

from core import recipes
from identity.models import User
from identity.roles import UserRole
from projects.roles import ProjectRole


@pytest.mark.django_db
class TestUser:
    def test_user_has_role(self, programme_manager):
        assert programme_manager.user_role is UserRole.PROGRAMME_MANAGER

    def test_get_participant(self, researcher):
        assert researcher.user.get_participant(researcher.project) == researcher

    def test_get_participant_returns_None_for_non_involved_project(self, researcher):
        assert researcher.user.get_participant(recipes.project.make()) is None

    def test_project_role_for_participant(self, researcher):
        assert researcher.user.project_role(researcher.project).role is ProjectRole.RESEARCHER
        assert researcher.user.project_participation_role(researcher.project) is ProjectRole.RESEARCHER

    def test_system_manager_does_not_get_participation_for_non_involed_projects(self, system_manager):
        assert system_manager.get_participant(recipes.project.make()) == None
        assert system_manager.project_participation_role(recipes.project.make()) is None

    def test_project_owner_is_not_participant_when_not_involved(self, programme_manager):
        project = recipes.project.make(created_by=programme_manager)
        assert programme_manager.get_participant(project) == None
        assert programme_manager.project_participation_role(project) is None

    def test_project_owner_is_participant_when_involved(self, programme_manager):
        project = recipes.project.make(created_by=programme_manager)
        project.add_user(user=programme_manager, role=ProjectRole.INVESTIGATOR.value, creator=programme_manager)
        assert programme_manager.get_participant(project).user == programme_manager
        assert programme_manager.project_participation_role(project) is ProjectRole.INVESTIGATOR

    def test_project_owner_does_not_get_role_on_other_project_when_not_participating(self, programme_manager):
        recipes.project.make(created_by=programme_manager)
        project = recipes.project.make()
        assert programme_manager.get_participant(project) is None
        assert programme_manager.project_participation_role(project) is None

    def test_project_role_is_None_for_non_involved_project(self, researcher):
        assert researcher.user.project_role(recipes.project.make()).role is None

    def test_project_participation_role_is_None_for_non_involved_project(self, researcher):
        assert researcher.user.project_participation_role(recipes.project.make()) is None

    @pytest.mark.parametrize("first,last,expected", [
        ("Caroline", "Herschel", "caroline.herschel"),
        ("Paul", " Erdös", "paul.erdos"),
        ("Marie-Sophie ", "Germain", "marie-sophie.germain"),
        ("Joan  Elisabeth Lowther", "Clarke", "joan.elisabeth.lowther.clarke"),
        ("Jocelyn", " Bell Burnell", "jocelyn.bell.burnell"),
        ("Henri", "Poincaré", "henri.poincare"),
        ("Walter R.", "Talbot  ", "walter.r.talbot"),
        ("", "Hypatia  ", "hypatia"),
    ])
    def test_generate_username(self, first, last, expected):
        user1 = User(
            first_name=first,
            last_name=last,
        )
        user1.generate_username()
        user1.save()
        assert user1.username == f"{expected}@example.com"

        user2 = User(
            first_name=first,
            last_name=last,
        )
        user2.generate_username()
        user2.save()
        assert user2.username == f"{expected}2@example.com"

        user3 = User(
            first_name=first,
            last_name=last,
        )
        user3.generate_username()
        user3.save()
        assert user3.username == f"{expected}3@example.com"
