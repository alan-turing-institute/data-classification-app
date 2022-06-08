import csv
import io
from unittest import mock

import pytest

from haven.core import recipes
from haven.identity.models import User
from haven.identity.roles import UserRole
from haven.identity.views import csv_users
from haven.projects.roles import ProjectRole


@pytest.mark.django_db
class TestCreateUser:
    def test_anonymous_cannot_access_page(self, client, helpers):
        response = client.get("/users/new")
        helpers.assert_login_redirect(response)

        response = client.post("/users/new", {})
        helpers.assert_login_redirect(response)
        assert not User.objects.filter(username="testuser@example.com").exists()

    def test_view_page(self, as_system_manager):
        response = as_system_manager.get("/users/new")

        assert response.status_code == 200
        assert response.context["form"]
        assert response.context["formset"]

    def test_view_page_as_pm(self, as_programme_manager):
        response = as_programme_manager.get("/users/new")

        assert response.status_code == 200
        assert response.context["form"]
        assert response.context["formset"]

    def test_create_user(self, as_system_manager):
        response = as_system_manager.get("/users/new")
        assert "role" in response.context["form"].fields

        response = as_system_manager.post(
            "/users/new",
            {
                "email": "testuser@example.com",
                "role": UserRole.PROGRAMME_MANAGER.value,
                "first_name": "Test",
                "last_name": "User",
                "mobile": "+443338888888",
                "participants-TOTAL_FORMS": 1,
                "participants-MAX_NUM_FORMS": 1,
                "participants-MIN_NUM_FORMS": 0,
                "participants-INITIAL_FORMS": 0,
            },
            follow=True,
        )

        assert response.status_code == 200
        user = User.objects.get(email="testuser@example.com")
        assert user is not None
        assert user.role == UserRole.PROGRAMME_MANAGER.value

    def test_create_user_and_add_to_project(self, as_system_manager):
        project = recipes.project.make()
        response = as_system_manager.post(
            "/users/new",
            {
                "email": "testuser@example.com",
                "first_name": "Test",
                "last_name": "User",
                "mobile": "+443338888888",
                "participants-TOTAL_FORMS": 1,
                "participants-MAX_NUM_FORMS": 1,
                "participants-MIN_NUM_FORMS": 0,
                "participants-INITIAL_FORMS": 0,
                "participants-0-project": project.id,
                "participants-0-role": "researcher",
            },
            follow=True,
        )

        assert response.status_code == 200
        user = User.objects.filter(email="testuser@example.com").first()
        assert user
        assert user.project_participation_role(project) == ProjectRole.RESEARCHER

    def test_cannot_create_privileged_user(self, as_programme_manager):
        response = as_programme_manager.get("/users/new")
        assert "role" not in response.context["form"].fields

        response = as_programme_manager.post(
            "/users/new",
            {
                "email": "testuser@example.com",
                "role": UserRole.PROGRAMME_MANAGER.value,
                "first_name": "Test",
                "last_name": "User",
                "mobile": "+443338888888",
                "participants-TOTAL_FORMS": 1,
                "participants-MAX_NUM_FORMS": 1,
                "participants-MIN_NUM_FORMS": 0,
                "participants-INITIAL_FORMS": 0,
            },
            follow=True,
        )

        assert response.status_code == 200
        user = User.objects.get(email="testuser@example.com")
        assert user is not None
        assert user.role == UserRole.NONE.value

    def test_returns_403_if_cannot_create_users(self, as_project_participant):
        response = as_project_participant.get("/users/new")
        assert response.status_code == 403

        response = as_project_participant.post("/users/new", {})
        assert response.status_code == 403
        assert not User.objects.filter(email="testuser@example.com").exists()


@pytest.mark.django_db
class TestEditUser:
    def test_anonymous_cannot_access_page(self, client, helpers, project_participant):
        response = client.get("/users/%d/edit" % project_participant.id)
        helpers.assert_login_redirect(response)

        response = client.post("/users/%d/edit" % project_participant.id, {})
        helpers.assert_login_redirect(response)

    def test_view_page(self, as_system_manager, project_participant):
        response = as_system_manager.get("/users/%d/edit" % project_participant.id)
        assert response.status_code == 200
        assert response.context["formset"]

    def test_view_page_as_pm(self, as_programme_manager, project_participant):
        response = as_programme_manager.get("/users/%d/edit" % project_participant.id)
        assert response.status_code == 200
        assert response.context["formset"]

    def test_edit_details(self, as_system_manager, project_participant):
        response = as_system_manager.post(
            "/users/%d/edit" % project_participant.id,
            {
                "role": project_participant.role,
                "email": "new@example.com",
                "mobile": "+441357924680",
                "first_name": "New",
                "last_name": "New",
                "participants-TOTAL_FORMS": 1,
                "participants-MAX_NUM_FORMS": 1,
                "participants-MIN_NUM_FORMS": 0,
                "participants-INITIAL_FORMS": 0,
            },
            follow=True,
        )
        assert response.status_code == 200
        project_participant.refresh_from_db()
        assert project_participant.email == "new@example.com"
        assert project_participant.mobile == "+441357924680"
        assert project_participant.first_name == "New"
        assert project_participant.last_name == "New"

    def test_add_to_project(self, as_system_manager, project_participant):
        project = recipes.project.make()
        response = as_system_manager.post(
            "/users/%d/edit" % project_participant.id,
            {
                "role": project_participant.role,
                "email": project_participant.email,
                "mobile": project_participant.mobile,
                "first_name": project_participant.first_name,
                "last_name": project_participant.last_name,
                "participants-TOTAL_FORMS": 1,
                "participants-MAX_NUM_FORMS": 1,
                "participants-MIN_NUM_FORMS": 0,
                "participants-INITIAL_FORMS": 0,
                "participants-0-project": project.id,
                "participants-0-role": "researcher",
            },
            follow=True,
        )
        assert response.status_code == 200
        assert (
            project_participant.project_participation_role(project)
            == ProjectRole.RESEARCHER
        )

    def test_remove_from_project(self, as_system_manager, researcher):
        project = researcher.project
        user = researcher.user
        response = as_system_manager.post(
            "/users/%d/edit" % user.id,
            {
                "role": "",
                "email": "example@example.com",
                "mobile": "+441234567890",
                "first_name": "E",
                "last_name": "F",
                "participants-TOTAL_FORMS": 1,
                "participants-MAX_NUM_FORMS": 1,
                "participants-MIN_NUM_FORMS": 0,
                "participants-INITIAL_FORMS": 1,
                "participants-0-project": project.id,
                "participants-0-role": "researcher",
                "participants-0-id": researcher.id,
                "participants-0-DELETE": "on",
            },
            follow=True,
        )
        assert response.status_code == 200
        assert user.project_participation_role(project) is None

    def test_cannot_edit_privileged_user(self, as_programme_manager, system_manager):
        response = as_programme_manager.post(
            "/users/%d/edit" % system_manager.id,
            {
                "role": system_manager.role,
                "email": "my_new_email@example.com",
                "mobile": system_manager.mobile,
                "first_name": system_manager.first_name,
                "last_name": system_manager.last_name,
                "participants-TOTAL_FORMS": 0,
                "participants-MAX_NUM_FORMS": 0,
                "participants-MIN_NUM_FORMS": 0,
                "participants-INITIAL_FORMS": 0,
            },
            follow=True,
        )
        assert response.status_code == 200
        assert not response.context["form"].is_valid()
        assert response.context["form"].errors == {
            "__all__": ["You cannot edit users with the role System Manager"],
        }
        system_manager.refresh_from_db()
        assert system_manager.email == "controller@example.com"

    def test_edit_archived_project(self, as_system_manager, project_participant):
        project1 = recipes.project.make()
        participant1 = project1.add_user(
            project_participant, ProjectRole.RESEARCHER.value, as_system_manager._user
        )
        project2 = recipes.project.make()
        project2.add_user(
            project_participant, ProjectRole.RESEARCHER.value, as_system_manager._user
        )

        response = as_system_manager.get("/users/%d/edit" % project_participant.id)
        forms = response.context["formset"].forms
        choices = [c[0] for c in forms[0].fields["project"].choices]
        defaults = [f.initial.get("project") for f in forms]

        assert choices == ["", project1.pk, project2.pk]
        assert defaults == [project1.pk, project2.pk, None]

        project2.archive()

        response = as_system_manager.get("/users/%d/edit" % project_participant.id)
        forms = response.context["formset"].forms
        choices = [c[0] for c in forms[0].fields["project"].choices]
        defaults = [f.initial.get("project") for f in forms]

        assert choices == ["", project1.pk]
        assert defaults == [project1.pk, None]

        response = as_system_manager.post(
            "/users/%d/edit" % project_participant.id,
            {
                "role": project_participant.role,
                "email": project_participant.email,
                "mobile": project_participant.mobile,
                "first_name": project_participant.first_name,
                "last_name": project_participant.last_name,
                "participants-TOTAL_FORMS": 1,
                "participants-MAX_NUM_FORMS": 1,
                "participants-MIN_NUM_FORMS": 0,
                "participants-INITIAL_FORMS": 2,
                "participants-0-id": participant1.id,
                "participants-0-project": project1.id,
                "participants-0-role": "researcher",
            },
            follow=True,
        )
        assert response.status_code == 200
        assert (
            project_participant.project_participation_role(project1)
            == ProjectRole.RESEARCHER
        )
        assert (
            project_participant.project_participation_role(project2)
            == ProjectRole.RESEARCHER
        )

    def test_returns_403_for_unprivileged_user(
        self, as_project_participant, researcher
    ):
        response = as_project_participant.get("/users/%d/edit" % researcher.id)
        assert response.status_code == 403

        response = as_project_participant.post("/users/%d/edit" % researcher.id, {})
        assert response.status_code == 403


@pytest.mark.django_db
class TestExportUsers:
    def parse_csv_response(self, response):
        text = response.content.decode()
        reader = csv.reader(text.splitlines())
        return list(reader)

    def test_export_as_anonymous(self, client, helpers):
        response = client.get("/users/export")
        helpers.assert_login_redirect(response)

    def test_export_new_as_anonymous(self, client, helpers):
        response = client.get("/users/export?new=true")
        helpers.assert_login_redirect(response)

    def test_export_as_participant(self, as_project_participant):
        response = as_project_participant.get("/users/export")
        assert response.status_code == 403

    def test_export_new_as_participant(self, as_project_participant):
        response = as_project_participant.get("/users/export?new=true")
        assert response.status_code == 403

    def test_export_as_pm(
        self,
        as_programme_manager,
        system_manager,
        standard_user,
        project_participant,
        user1,
    ):
        response = as_programme_manager.get("/users/export")
        assert response.status_code == 200
        assert response["Content-Type"] == "text/csv"
        parsed = self.parse_csv_response(response)
        assert parsed[0] == ["SamAccountName", "GivenName", "Surname", "Mobile", "SecondaryEmail"]
        assert sorted(parsed) == sorted([
            ["SamAccountName", "GivenName", "Surname", "Mobile", "SecondaryEmail"],
            ["coordinator", "", "", "", "coordinator@example.com"],
            [
                "controller",
                "System",
                "Manager",
                "+441234567890",
                "controller@example.com",
            ],
            ["user", "", "", "", "user@example.com"],
            [
                "project_participant",
                "Angela",
                "Zala",
                "+441234567890",
                "project_participant@example.com",
            ],
            ["user1", "", "", "", "user@example.com"],
        ])

    def test_export_new_as_pm(
        self,
        as_programme_manager,
        system_manager,
        standard_user,
        project_participant,
        user1,
    ):
        with mock.patch(
            "haven.identity.views.get_system_user_list"
        ) as get_system_user_list:
            get_system_user_list.return_value = [
                "user1@example.com",
                "nonuser@example.com",
                "CONTROLLER@example.com",
            ]

            response = as_programme_manager.get("/users/export?new=true")
            assert response.status_code == 200
            assert response["Content-Type"] == "text/csv"
            parsed = self.parse_csv_response(response)
            assert parsed == [
                ["SamAccountName", "GivenName", "Surname", "Mobile", "SecondaryEmail"],
                ["coordinator", "", "", "", "coordinator@example.com"],
                ["user", "", "", "", "user@example.com"],
                [
                    "project_participant",
                    "Angela",
                    "Zala",
                    "+441234567890",
                    "project_participant@example.com",
                ],
            ]

    def test_export_by_project(
        self,
        as_programme_manager,
        system_manager,
        standard_user,
        project_participant,
        user1,
    ):
        project = recipes.project.make(created_by=as_programme_manager._user)
        project.add_user(
            user1,
            role=ProjectRole.PROJECT_MANAGER.value,
            created_by=as_programme_manager._user,
        )
        project.add_user(
            project_participant,
            role=ProjectRole.RESEARCHER.value,
            created_by=as_programme_manager._user,
        )
        response = as_programme_manager.get(f"/users/export?project={project.pk}")
        assert response.status_code == 200
        assert response["Content-Type"] == "text/csv"
        parsed = self.parse_csv_response(response)
        assert ["user1", "", "", "", "user@example.com"] in parsed
        assert [
                "project_participant",
                "Angela",
                "Zala",
                "+441234567890",
                "project_participant@example.com",
            ] in parsed
        assert len(parsed) == 3

    def test_export_new_by_project(
        self,
        as_programme_manager,
        system_manager,
        standard_user,
        project_participant,
        user1,
    ):
        with mock.patch(
            "haven.identity.views.get_system_user_list"
        ) as get_system_user_list:
            get_system_user_list.return_value = [
                "user1@example.com",
                "nonuser@example.com",
                "CONTROLLER@example.com",
            ]

            project = recipes.project.make(created_by=as_programme_manager._user)
            project.add_user(
                user1,
                role=ProjectRole.PROJECT_MANAGER.value,
                created_by=as_programme_manager._user,
            )
            project.add_user(
                project_participant,
                role=ProjectRole.RESEARCHER.value,
                created_by=as_programme_manager._user,
            )
            response = as_programme_manager.get(
                f"/users/export?project={project.pk}&new=true"
            )
            assert response.status_code == 200
            assert response["Content-Type"] == "text/csv"
            parsed = self.parse_csv_response(response)
            assert parsed == [
                ["SamAccountName", "GivenName", "Surname", "Mobile", "SecondaryEmail"],
                [
                    "project_participant",
                    "Angela",
                    "Zala",
                    "+441234567890",
                    "project_participant@example.com",
                ],
            ]


@pytest.mark.django_db
class TestImportUsers:
    def post_csv(self, client, follow=True):
        f = io.StringIO(
            "Email,Last Name,First Name,Mobile Phone,Other field\n"
            "em1@email.com,ln1,fn1,01234567890,other1\n"
            "em2@email.com,ln2,fn2,02345678901,other2\n"
            "em3@email.com,ln3,fn3,03456789012,other3"
        )
        f.name = "import.csv"
        return client.post(
            "/users/import",
            {
                "upload_file": f,
            },
            follow=follow,
        )

    def test_import_as_anonymous(self, client, helpers):
        response = self.post_csv(client, follow=False)
        helpers.assert_login_redirect(response)
        assert [u.username for u in User.objects.all()] == []

    def test_import_as_participant(self, as_project_participant):
        response = self.post_csv(as_project_participant)
        assert response.status_code == 403
        assert [u.username for u in User.objects.all()] == [
            "project_participant@example.com",
        ]

    def test_import_as_pm(self, as_programme_manager):
        response = self.post_csv(as_programme_manager)
        assert response.status_code == 200
        assert set([u.username for u in User.objects.all()]) == set([
            "coordinator@example.com",
            "fn1.ln1@example.com",
            "fn2.ln2@example.com",
            "fn3.ln3@example.com",
        ])

    def test_csv_users(self):
        users = csv_users(
            "Email,Last Name,First Name,Mobile Phone,Other field\nem1@email.com,ln1,fn1,01234567890,other1\nem2@email.com,ln2,fn2,02345678901,other2\nem3@email.com,ln3,fn3,03456789012,other3"
        )
        u1 = users.__next__()
        assert u1.first_name == "fn1"
        assert u1.last_name == "ln1"
        assert u1.email == "em1@email.com"
        assert u1.mobile.as_e164 == "+441234567890"

        u2 = users.__next__()
        assert u2.first_name == "fn2"
        assert u2.last_name == "ln2"
        assert u2.email == "em2@email.com"
        assert u2.mobile.as_e164 == "+442345678901"

        u3 = users.__next__()
        assert u3.first_name == "fn3"
        assert u3.last_name == "ln3"
        assert u3.email == "em3@email.com"
        assert u3.mobile.as_e164 == "+443456789012"
