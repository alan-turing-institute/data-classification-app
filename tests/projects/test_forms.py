import pytest

from haven.core import recipes
from haven.projects.forms import ProjectAddUserForm, ProjectForUserInlineForm
from haven.projects.roles import ProjectRole


@pytest.mark.django_db
class TestProjectAddUserForm:
    def test_cannot_add_nonexisting_user(self, programme_manager):
        project = recipes.project.make(created_by=programme_manager)

        form = ProjectAddUserForm(
            {
                "role": ProjectRole.RESEARCHER.value,
                "user": "some_unknown_user",
            },
            user=programme_manager,
            project_id=project.pk,
        )
        form.project = project
        assert not form.is_valid()

    def test_add_existing_user(self, programme_manager, project_participant):
        project = recipes.project.make(created_by=programme_manager)

        form = ProjectAddUserForm(
            {
                "role": ProjectRole.RESEARCHER.value,
                "user": project_participant.pk,
            },
            user=programme_manager,
            project_id=project.pk,
        )
        form.project = project

        assert form.is_valid()

        form.save()
        participant = project.participants.get()

        assert participant.user == project_participant

    def test_cannot_add_user_to_project_twice(self, programme_manager, project_participant):
        project = recipes.project.make(created_by=programme_manager)

        project.add_user(project_participant, ProjectRole.RESEARCHER, programme_manager)

        form = ProjectAddUserForm(
            {
                "role": ProjectRole.INVESTIGATOR.value,
                "user": project_participant.pk,
            },
            user=programme_manager,
            project_id=project.pk,
        )
        form.project = project

        assert not form.is_valid()
        assert "user" in form.errors

        assert project.participants.count() == 1


@pytest.mark.django_db
class TestAddUserForm:
    def test_project_dropdown_is_restricted(self, investigator):
        user = investigator.user
        involved_project = investigator.project
        # Another project on which the user is a researcher
        read_only_project = recipes.researcher.make(user=user).project
        other_project = recipes.project.make()

        form = ProjectForUserInlineForm(user=user)
        field = form.fields["project"]
        assert field.valid_value(involved_project.pk)
        assert not field.valid_value(other_project.pk)
        assert not field.valid_value(read_only_project.pk)

    def test_add_user_to_project(self, investigator, project_participant):
        project = investigator.project
        form = ProjectForUserInlineForm(
            {
                "project": project.pk,
                "role": ProjectRole.RESEARCHER.value,
            },
            user=investigator.user,
        )
        assert form.is_valid()

        form.instance.user = project_participant
        form.save()

        assert project_participant.project_participation_role(project) == ProjectRole.RESEARCHER

    def test_cannot_add_restricted_project_role_combination(self, investigator):
        form = ProjectForUserInlineForm(
            {
                "project": investigator.project.pk,
                "role": ProjectRole.INVESTIGATOR.value,
            },
            user=investigator.user,
        )

        assert not form.is_valid()
        assert form.errors["__all__"]

    def test_project_dropdown_no_archived(self, investigator, programme_manager):
        user = investigator.user
        involved_project = investigator.project
        unarchived_project = recipes.project.make()
        unarchived_project.add_user(user, ProjectRole.INVESTIGATOR.value, programme_manager)
        archived_project = recipes.project.make()
        archived_project.add_user(user, ProjectRole.INVESTIGATOR.value, programme_manager)
        archived_project.archive()

        form = ProjectForUserInlineForm(user=user)
        field = form.fields["project"]
        assert field.valid_value(involved_project.pk)
        assert not field.valid_value(archived_project.pk)
        assert field.valid_value(unarchived_project.pk)
