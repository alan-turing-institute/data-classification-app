import pytest

from core import recipes
from identity.models import User
from identity.views import csv_users
from projects.roles import ProjectRole


@pytest.mark.django_db
class TestCreateUser:
    def test_anonymous_cannot_access_page(self, client, helpers):
        response = client.get('/users/new')
        helpers.assert_login_redirect(response)

        response = client.post('/users/new', {})
        helpers.assert_login_redirect(response)
        assert not User.objects.filter(username='testuser@example.com').exists()

    def test_view_page(self, as_system_controller):
        response = as_system_controller.get('/users/new')

        assert response.status_code == 200
        assert response.context['form']
        assert response.context['formset']

    def test_create_user(self, as_system_controller):
        response = as_system_controller.post('/users/new', {
            'email': 'testuser@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'mobile': '+443338888888',
            'participant_set-TOTAL_FORMS': 1,
            'participant_set-MAX_NUM_FORMS': 1,
            'participant_set-MIN_NUM_FORMS': 0,
            'participant_set-INITIAL_FORMS': 0,
        }, follow=True)

        assert response.status_code == 200
        assert User.objects.filter(email='testuser@example.com').exists()

    def test_create_user_and_add_to_project(self, as_system_controller):
        project = recipes.project.make()
        response = as_system_controller.post('/users/new', {
            'email': 'testuser@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'mobile': '+443338888888',
            'participant_set-TOTAL_FORMS': 1,
            'participant_set-MAX_NUM_FORMS': 1,
            'participant_set-MIN_NUM_FORMS': 0,
            'participant_set-INITIAL_FORMS': 0,
            'participant_set-0-project': project.id,
            'participant_set-0-role': 'researcher',
        }, follow=True)

        assert response.status_code == 200
        user = User.objects.filter(email='testuser@example.com').first()
        assert user
        assert user.project_participation_role(project) == \
               ProjectRole.RESEARCHER

    def test_returns_403_if_cannot_create_users(self, as_project_participant):
        response = as_project_participant.get('/users/new')
        assert response.status_code == 403

        response = as_project_participant.post('/users/new', {})
        assert response.status_code == 403
        assert not User.objects.filter(email='testuser@example.com').exists()


@pytest.mark.django_db
class TestEditUser:
    def test_anonymous_cannot_access_page(self, client, helpers, project_participant):
        response = client.get('/users/%d/edit' % project_participant.id)
        helpers.assert_login_redirect(response)

        response = client.post('/users/%d/edit' % project_participant.id, {})
        helpers.assert_login_redirect(response)

    def test_view_page(self, as_system_controller, project_participant):
        response = as_system_controller.get(
            '/users/%d/edit' % project_participant.id)
        assert response.status_code == 200
        assert response.context['formset']

    def test_add_to_project(self, as_system_controller, project_participant):
        project = recipes.project.make()
        response = as_system_controller.post(
            '/users/%d/edit' % project_participant.id, {
                'participant_set-TOTAL_FORMS': 1,
                'participant_set-MAX_NUM_FORMS': 1,
                'participant_set-MIN_NUM_FORMS': 0,
                'participant_set-INITIAL_FORMS': 0,
                'participant_set-0-project': project.id,
                'participant_set-0-role': 'researcher',
            }, follow=True)
        assert response.status_code == 200
        assert project_participant.project_participation_role(project) == ProjectRole.RESEARCHER

    def test_remove_from_project(self, as_system_controller, researcher):
        project = researcher.project
        user = researcher.user
        response = as_system_controller.post(
            '/users/%d/edit' % user.id, {
                'participant_set-TOTAL_FORMS': 1,
                'participant_set-MAX_NUM_FORMS': 1,
                'participant_set-MIN_NUM_FORMS': 0,
                'participant_set-INITIAL_FORMS': 1,
                'participant_set-0-project': project.id,
                'participant_set-0-role': 'researcher',
                'participant_set-0-id': researcher.id,
                'participant_set-0-DELETE': 'on',
            }, follow=True)
        assert response.status_code == 200
        assert user.project_participation_role(project) is None

    def test_returns_403_for_unprivileged_user(self, as_project_participant, researcher):
        response = as_project_participant.get('/users/%d/edit' % researcher.id)
        assert response.status_code == 403

        response = as_project_participant.post('/users/%d/edit' % researcher.id, {})
        assert response.status_code == 403

class TestImportUsers:
    def test_csv_users(self):
        users = csv_users('Email,Last Name,First Name,Mobile Phone,Other field\nem1@email.com,ln1,fn1,01234567890,other1\nem2@email.com,ln2,fn2,02345678901,other2\nem3@email.com,ln3,fn3,03456789012,other3')
        u1 = users.__next__()
        assert u1.first_name == 'fn1'
        assert u1.last_name == 'ln1'
        assert u1.email == 'em1@email.com'
        assert u1.mobile == '+441234567890'

        u2 = users.__next__()
        assert u2.first_name == 'fn2'
        assert u2.last_name == 'ln2'
        assert u2.email == 'em2@email.com'
        assert u2.mobile == '+442345678901'

        u3 = users.__next__()
        assert u3.first_name == 'fn3'
        assert u3.last_name == 'ln3'
        assert u3.email == 'em3@email.com'
        assert u3.mobile == '++443456789012'
