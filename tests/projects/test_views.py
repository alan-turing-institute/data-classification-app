import json

import bleach
import pytest

from haven.core import recipes
from haven.data.classification import insert_initial_questions
from haven.data.models import ClassificationGuidance, ClassificationQuestion
from haven.identity.models import User
from haven.projects.models import (
    ClassificationOpinion,
    Policy,
    PolicyAssignment,
    PolicyGroup,
    Project,
    WorkPackageStatus,
)
from haven.projects.policies import insert_initial_policies
from haven.projects.roles import ProjectRole


@pytest.mark.django_db
class TestCreateProject:
    def test_anonymous_cannot_access_page(self, client, helpers):
        response = client.get('/projects/new')
        helpers.assert_login_redirect(response)

    def test_anonymous_cannot_post_form(self, client, helpers):
        response = client.post('/projects/new')
        helpers.assert_login_redirect(response)

    def test_unprivileged_user_cannot_access_page(self, as_project_participant):
        response = as_project_participant.get('/projects/new')
        assert response.status_code == 403

    def test_unprivileged_user_cannot_post_form(self, as_project_participant):
        response = as_project_participant.post('/projects/new')
        assert response.status_code == 403

    def test_create_project(self, as_programme_manager):
        response = as_programme_manager.post(
            '/projects/new',
            {
                'name': 'my project',
                'description': 'a new project',
                'programmes': 'prog1, prog2',
            },
        )

        assert response.status_code == 302
        assert response.url == '/projects/'

        project = Project.objects.get()
        assert project.name == 'my project'
        assert project.description == 'a new project'
        programmes = set(p.name for p in project.programmes.all())
        assert programmes == set(('prog1', 'prog2'))
        assert project.created_by == as_programme_manager._user

    def test_cannot_create_duplicate_project(self, as_programme_manager):
        recipes.project.make(name='my project')

        response = as_programme_manager.post(
            '/projects/new',
            {'name': 'my project', 'description': 'a duplicate project'},
        )

        assert response.status_code == 200
        assert response.context['form'].errors == {
            'name': ['Project with this Name already exists.']
        }

        assert Project.objects.count() == 1

    def test_create_project_for_programme(self, as_programme_manager):
        response = as_programme_manager.get('/projects/new')
        assert response.context['form'].initial == {}

        response = as_programme_manager.post(
            '/projects/new',
            {
                'name': 'my project',
                'description': 'a new project',
                'programmes': 'prog1',
            },
        )

        assert response.status_code == 302
        assert response.url == '/projects/'

        response = as_programme_manager.get('/projects/new?programme=prog1')
        assert response.context['form'].initial == {'programmes': ['prog1']}


@pytest.mark.django_db
class TestListProjects:
    def test_anonymous_cannot_access_page(self, client, helpers):
        response = client.get('/projects/')
        helpers.assert_login_redirect(response)

    def test_list_owned_projects(self, as_standard_user, system_manager):
        my_project = recipes.project.make(created_by=as_standard_user._user)
        recipes.project.make(created_by=system_manager)

        response = as_standard_user.get('/projects/')

        assert list(response.context['projects']) == [my_project]

    def test_list_involved_projects(self, as_project_participant):
        project1, project2 = recipes.project.make(_quantity=2)

        recipes.participant.make(project=project1, user=as_project_participant._user)

        response = as_project_participant.get('/projects/')

        assert list(response.context['projects']) == [project1]

    def test_list_all_projects(self, programme_manager, as_system_manager):
        my_project = recipes.project.make(created_by=as_system_manager._user)
        other_project = recipes.project.make(created_by=programme_manager)

        response = as_system_manager.get('/projects/')

        assert list(response.context['projects']) == [other_project, my_project]

    def test_list_archived_projects(self, programme_manager, as_system_manager):
        my_project = recipes.project.make(created_by=as_system_manager._user)
        my_project.archive()
        other_project = recipes.project.make(created_by=programme_manager)

        response = as_system_manager.get('/projects/')

        assert list(response.context['projects']) == [other_project]

    def test_list_projects_by_programme(self, as_system_manager):
        project1, project2 = recipes.project.make(_quantity=2)

        project1.programmes.add('prog1', 'prog2')
        project2.programmes.add('prog2', 'prog3')

        response = as_system_manager.get('/projects/?programme=prog1')
        assert list(response.context['projects']) == [project1]

        response = as_system_manager.get('/projects/?programme=prog2')
        assert list(response.context['projects']) == [project2, project1]

        response = as_system_manager.get('/projects/?programme=prog3')
        assert list(response.context['projects']) == [project2]

    def test_missing_programme(self, as_system_manager):
        response = as_system_manager.get('/projects/?programme=prog1')
        assert response.status_code == 404


@pytest.mark.django_db
class TestViewProject:
    def test_anonymous_cannot_access_page(self, client, helpers):
        response = client.get('/projects/1')
        helpers.assert_login_redirect(response)

    def test_view_owned_project(self, as_programme_manager):
        project = recipes.project.make(created_by=as_programme_manager._user)

        response = as_programme_manager.get('/projects/%d' % project.id)

        assert response.status_code == 200
        assert response.context['project'] == project

    def test_view_involved_project(self, as_project_participant):
        project1, project2 = recipes.project.make(_quantity=2)
        recipes.participant.make(project=project1, user=as_project_participant._user)

        response = as_project_participant.get('/projects/%d' % project1.id)

        assert response.status_code == 200
        assert response.context['project'] == project1

    def test_cannot_view_other_project(self, as_standard_user):
        project = recipes.project.make()

        response = as_standard_user.get('/projects/%d' % project.id)

        assert response.status_code == 404

    def test_view_as_system_manager(self, as_system_manager):
        project = recipes.project.make()

        response = as_system_manager.get('/projects/%d' % project.id)

        assert response.status_code == 200
        assert response.context['project'] == project

    def test_cannot_view_archived_project(self, as_programme_manager):
        project = recipes.project.make(created_by=as_programme_manager._user)
        project.archive()

        response = as_programme_manager.get('/projects/%d' % project.id)

        assert response.status_code == 404


@pytest.mark.django_db
class TestViewProjectHistory:
    def test_anonymous_cannot_access_page(self, client, helpers):
        response = client.get('/projects/1/history')
        helpers.assert_login_redirect(response)

    def test_view_owned_project(self, as_programme_manager):
        project = recipes.project.make(created_by=as_programme_manager._user)

        response = as_programme_manager.get('/projects/%d/history' % project.id)

        assert response.status_code == 200
        table = list(response.context['history_table'].as_values())
        assert len(table) >= 2
        assert table[0] == ['Timestamp', 'Type', 'User', 'Subject', 'Details', 'Changes']


@pytest.mark.django_db
class TestArchiveProject:
    def test_archive_project(self, programme_manager, as_standard_user):
        project = recipes.project.make(created_by=programme_manager)
        project.add_user(as_standard_user._user, ProjectRole.PROJECT_MANAGER.value,
                         programme_manager)

        response = as_standard_user.get(f"/projects/{project.pk}")
        assert b'Archive Project' in response.content

        url = f"/projects/{project.pk}/archive"
        response = as_standard_user.get(url)
        assert b'Archive Project' in response.content

        response = as_standard_user.post(url, {}, follow=True)
        assert response.status_code == 200

        response = as_standard_user.get(f"/projects/{project.pk}")
        assert response.status_code == 404


@pytest.mark.django_db
class TestViewWorkPackage:
    def test_view_work_package_policy_tier0(self, as_programme_manager, classified_work_package):
        insert_initial_policies(PolicyGroup, Policy, PolicyAssignment)
        work_package = classified_work_package(0)

        response = as_programme_manager.get('/projects/%d/work_packages/%d'
                                            % (work_package.project.id, work_package.id))

        assert response.status_code == 200
        table = list(response.context['policy_table'].as_values())
        assert len(table) == 16
        assert table[0] == ['Policy', 'Description']
        assert table[1] == ['Tier', '0']

    def test_cannot_view_for_wrong_project(self, as_programme_manager, classified_work_package):
        wp1 = classified_work_package(0)
        wp2 = classified_work_package(0)

        response = as_programme_manager.get('/projects/%d/work_packages/%d'
                                            % (wp1.project.id, wp2.id))

        assert response.status_code == 404

    def test_cannot_view_other_project(self, as_standard_user):
        project = recipes.project.make()
        work_package = recipes.work_package.make(project=project)

        response = as_standard_user.get('/projects/%d/work_packages/%d'
                                        % (project.id, work_package.id))

        assert response.status_code == 404

    def test_list_participants(self, as_programme_manager, user1):
        project = recipes.project.make(
            created_by=as_programme_manager._user,
        )
        user2, user3 = recipes.user.make(_quantity=2)
        project.add_user(user1, ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value,
                         as_programme_manager._user)
        project.add_user(user2, ProjectRole.RESEARCHER.value,
                         as_programme_manager._user)
        project.add_user(user3, ProjectRole.RESEARCHER.value,
                         as_programme_manager._user)

        work_package = recipes.work_package.make(project=project)
        work_package.add_user(user2, as_programme_manager._user)
        work_package.add_user(user3, as_programme_manager._user)

        response = as_programme_manager.get('/projects/%d/work_packages/%d'
                                            % (project.id, work_package.id))

        assert response.status_code == 200
        table = response.context['participants_table'].as_values()
        assert list(table) == [
            ['Username', 'Role', 'Approved'],
            [user2.display_name(), 'Researcher', 'False'],
            [user3.display_name(), 'Researcher', 'False'],
        ]


@pytest.mark.django_db
class TestEditProject:
    def test_anonymous_cannot_access_page(self, client, helpers):
        response = client.get('/projects/1/edit')
        helpers.assert_login_redirect(response)

    def test_edit(self, as_project_participant):
        project = recipes.project.make()
        recipes.participant.make(project=project, user=as_project_participant._user,
                                 role=ProjectRole.PROJECT_MANAGER.value)

        response = as_project_participant.get('/projects/%d/edit' % project.id)

        assert response.status_code == 200
        assert response.context['project'] == project

        response = as_project_participant.post('/projects/%d/edit' % project.id, {
            'name': 'my updated project',
            'description': 'a different project',
        })

        assert response.status_code == 302
        assert response.url == '/projects/%d' % project.id

        response = as_project_participant.get('/projects/%d' % project.id)

        assert response.status_code == 200
        assert response.context['project'].name == 'my updated project'
        assert response.context['project'].description == 'a different project'

    def test_view_as_manager(self, as_project_participant):
        project = recipes.project.make()
        recipes.participant.make(project=project, user=as_project_participant._user,
                                 role=ProjectRole.PROJECT_MANAGER.value)

        response = as_project_participant.get('/projects/%d/edit' % project.id)

        assert response.status_code == 200
        assert response.context['project'] == project

    def test_view_as_user(self, as_project_participant):
        project = recipes.project.make()
        recipes.participant.make(project=project, user=as_project_participant._user,
                                 role=ProjectRole.RESEARCHER.value)

        response = as_project_participant.get('/projects/%d/edit' % project.id)

        assert response.status_code == 403

    def test_view_as_system_manager(self, as_system_manager):
        project = recipes.project.make()

        response = as_system_manager.get('/projects/%d' % project.id)

        assert response.status_code == 200
        assert response.context['project'] == project


@pytest.mark.django_db
class TestAddUserToProject:
    def test_anonymous_cannot_access_page(self, client, helpers):
        project = recipes.project.make()
        response = client.get('/projects/%d/participants/add' % project.id)
        helpers.assert_login_redirect(response)

        response = client.post('/projects/%d/participants/add' % project.id)
        helpers.assert_login_redirect(response)

    def test_view_page(self, as_programme_manager):
        project = recipes.project.make(created_by=as_programme_manager._user)

        response = as_programme_manager.get('/projects/%d/participants/add' % project.id)
        assert response.status_code == 200
        assert response.context['project'] == project

    def test_add_new_user_to_project(self, as_programme_manager, project_participant):

        project = recipes.project.make(created_by=as_programme_manager._user)
        response = as_programme_manager.post('/projects/%d/participants/add' % project.id, {
            'role': ProjectRole.RESEARCHER.value,
            'user': project_participant.pk,
        })

        assert response.status_code == 302
        assert response.url == '/projects/%d' % project.id

        assert project.participants.count() == 1
        assert project.participants.first().user.username == project_participant.username

    def test_add_new_user_to_project_and_work_packages(self, as_programme_manager,
                                                       project_participant):

        project = recipes.project.make(created_by=as_programme_manager._user)
        work_package = recipes.work_package.make(project=project,
                                                 created_by=as_programme_manager._user)
        work_package2 = recipes.work_package.make(project=project,
                                                  created_by=as_programme_manager._user)
        work_package3 = recipes.work_package.make(project=project,
                                                  created_by=as_programme_manager._user)
        response = as_programme_manager.post('/projects/%d/participants/add' % project.id, {
            'role': ProjectRole.RESEARCHER.value,
            'user': project_participant.pk,
            'work_packages': [work_package.id, work_package3.id],
        })

        assert response.status_code == 302
        assert response.url == '/projects/%d' % project.id

        participants = project.participants
        assert participants.count() == 1
        assert participants.first().user.username == project_participant.username

        participants = work_package.participants
        assert participants.count() == 1
        assert participants.first().user.username == project_participant.username

        participants = work_package2.participants
        assert participants.count() == 0

        participants = work_package3.participants
        assert participants.count() == 1
        assert participants.first().user.username == project_participant.username

    def test_cancel_add_new_user_to_project(self, as_programme_manager, project_participant):

        project = recipes.project.make(created_by=as_programme_manager._user)
        response = as_programme_manager.post('/projects/%d/participants/add' % project.id, {
            'role': ProjectRole.RESEARCHER.value,
            'user': project_participant.pk,
            'cancel': 'Cancel',
        })

        assert response.status_code == 302
        assert response.url == '/projects/%d' % project.id

        assert project.participants.count() == 0

    def test_add_user_without_domain_to_project(self, as_programme_manager):
        """Check that domain will not be added to entered username if the username exists as it is"""

        project = recipes.project.make(created_by=as_programme_manager._user)

        new_user = User.objects.create_user(username='newuser')
        response = as_programme_manager.post('/projects/%d/participants/add' % project.id, {
            'role': ProjectRole.RESEARCHER.value,
            'user': new_user.pk,
        })

        assert response.status_code == 302
        assert response.url == '/projects/%d' % project.id

        assert project.participants.count() == 1
        assert project.participants.first().user.username == 'newuser'

    def test_cannot_add_existing_user_to_project(self, as_programme_manager, project_participant):
        project = recipes.project.make(created_by=as_programme_manager._user)

        project.add_user(project_participant, ProjectRole.RESEARCHER, as_programme_manager._user)
        assert project.participants.count() == 1

        response = as_programme_manager.post('/projects/%d/participants/add' % project.id, {
            'role': ProjectRole.RESEARCHER.value,
            'user': project_participant.pk,
        })

        assert response.status_code == 200
        assert response.context['project'] == project
        assert project.participants.count() == 1

    def test_cannot_add_nonexisting_user_to_project(self, as_programme_manager):
        project = recipes.project.make(created_by=as_programme_manager._user)

        response = as_programme_manager.post('/projects/%d/participants/add' % project.id, {
            'role': ProjectRole.RESEARCHER.value,
            'user': 12345,
        })

        assert response.status_code == 200
        assert response.context['project'] == project

        assert project.participants.count() == 0

    def test_returns_404_for_invisible_project(self, as_standard_user):
        project = recipes.project.make()

        # Programme manager shouldn't have visibility of this other project at all
        # so pretend it doesn't exist and raise a 404
        response = as_standard_user.get('/projects/%d/participants/add' % project.id)
        assert response.status_code == 404

        response = as_standard_user.post('/projects/%d/participants/add' % project.id)
        assert response.status_code == 404

    def test_returns_403_if_no_add_permissions(self, client, researcher):
        # Researchers can't add participants, so do not display the page
        client.force_login(researcher.user)

        response = client.get('/projects/%d/participants/add' % researcher.project.id)
        assert response.status_code == 403

        response = client.post('/projects/%d/participants/add' % researcher.project.id)
        assert response.status_code == 403

    def test_restricts_creation_based_on_role(self, client, investigator, researcher):
        # An investigator cannot add a user because they cannot see a list of users outside their
        # project
        client.force_login(investigator.user)
        response = client.post(
            '/projects/%d/participants/add' % investigator.project.id,
            {
                'username': researcher.pk,
                'role': ProjectRole.INVESTIGATOR.value,
            })

        assert response.status_code == 403


@pytest.mark.django_db
class TestEditParticipant:
    def test_anonymous_cannot_access_page(self, client, helpers):
        project = recipes.project.make()
        investigator = recipes.investigator.make(project=project)
        response = client.get('/projects/%d/participants/%d/edit' % (project.id, investigator.id))
        helpers.assert_login_redirect(response)

        response = client.post('/projects/%d/participants/%d/edit' % (project.id, investigator.id))
        helpers.assert_login_redirect(response)

    def test_view_page(self, as_programme_manager):
        project = recipes.project.make(created_by=as_programme_manager._user)
        investigator = recipes.investigator.make(project=project)

        response = as_programme_manager.get(
            '/projects/%d/participants/%d/edit' % (project.id, investigator.id))
        assert response.status_code == 200
        assert response.context['project'] == project

    def test_edit_participant(self, as_programme_manager):

        project = recipes.project.make(created_by=as_programme_manager._user)
        investigator = recipes.investigator.make(project=project)
        response = as_programme_manager.post(
            '/projects/%d/participants/%d/edit' % (project.id, investigator.id),
            {
                'role': ProjectRole.RESEARCHER.value,
            }
        )

        assert response.status_code == 302
        assert response.url == '/projects/%d' % project.id

        assert project.participants.count() == 1
        assert project.participants.first().user.username == investigator.user.username
        assert project.participants.first().role == ProjectRole.RESEARCHER.value

    def test_edit_participant_and_work_packages(self, as_programme_manager):

        project = recipes.project.make(created_by=as_programme_manager._user)
        work_package = recipes.work_package.make(project=project,
                                                 created_by=as_programme_manager._user)
        work_package2 = recipes.work_package.make(project=project,
                                                  created_by=as_programme_manager._user)
        work_package3 = recipes.work_package.make(project=project,
                                                  created_by=as_programme_manager._user)

        investigator = recipes.investigator.make(project=project)
        work_package.add_user(investigator.user, creator=as_programme_manager._user)
        work_package2.add_user(investigator.user, creator=as_programme_manager._user)

        response = as_programme_manager.post(
            '/projects/%d/participants/%d/edit' % (project.id, investigator.id),
            {
                'role': ProjectRole.RESEARCHER.value,
                'work_packages': [work_package.id, work_package3.id],
            }
        )

        assert response.status_code == 302
        assert response.url == '/projects/%d' % project.id

        assert project.participants.count() == 1
        assert project.participants.first().user.username == investigator.user.username
        assert project.participants.first().role == ProjectRole.RESEARCHER.value

        participants = work_package.participants
        assert participants.count() == 1
        assert participants.first().user.username == investigator.user.username

        participants = work_package2.participants
        assert participants.count() == 0

        participants = work_package3.participants
        assert participants.count() == 1
        assert participants.first().user.username == investigator.user.username

    def test_edit_approved_participant(self, data_provider_representative, as_programme_manager):

        project = recipes.project.make(created_by=as_programme_manager._user)
        work_package = recipes.work_package.make(project=project,
                                                 created_by=as_programme_manager._user)

        investigator = recipes.investigator.make(project=project)
        dataset = recipes.dataset.make()
        project.add_dataset(dataset, data_provider_representative.user, as_programme_manager._user)
        work_package.add_dataset(dataset, as_programme_manager._user)

        p = work_package.add_user(investigator.user, creator=as_programme_manager._user)
        p.approve(data_provider_representative.user)
        assert p.approvals.count() == 1

        response = as_programme_manager.post(
            '/projects/%d/participants/%d/edit' % (project.id, investigator.id),
            {
                'role': ProjectRole.RESEARCHER.value,
                'work_packages': [work_package.id],
            }
        )

        assert response.status_code == 302
        assert response.url == '/projects/%d' % project.id

        assert project.participants.count() == 2
        assert project.participants.first().user.username == investigator.user.username
        assert project.participants.first().role == ProjectRole.RESEARCHER.value

        participants = work_package.participants
        assert participants.count() == 2
        assert participants.first().user.username == investigator.user.username
        wpp = participants.first().get_work_package_participant(work_package)
        assert wpp.approvals.count() == 1

    def test_returns_404_for_invisible_project(self, as_standard_user):
        project = recipes.project.make()
        investigator = recipes.investigator.make(project=project)

        # Programme manager shouldn't have visibility of this other project at all
        # so pretend it doesn't exist and raise a 404
        response = as_standard_user.get(
            '/projects/%d/participants/%d/edit' % (project.id, investigator.id))
        assert response.status_code == 404

        response = as_standard_user.post(
            '/projects/%d/participants/%d/edit' % (project.id, investigator.id))
        assert response.status_code == 404

    def test_returns_403_if_no_add_permissions(self, client, researcher):
        # Researchers can't add participants, so do not display the page
        client.force_login(researcher.user)

        response = client.get(
            '/projects/%d/participants/%d/edit' % (researcher.project.id, researcher.id))
        assert response.status_code == 403

        response = client.post(
            '/projects/%d/participants/%d/edit' % (researcher.project.id, researcher.id))
        assert response.status_code == 403

    def test_restricts_creation_based_on_role(self, client, referee, researcher):
        client.force_login(referee.user)
        response = client.post(
            '/projects/%d/participants/%d/edit' % (referee.project.id, researcher.id),
            {
                'role': ProjectRole.INVESTIGATOR.value,
            })

        assert response.status_code == 403


@pytest.mark.django_db
class TestEditParticipants:
    def test_anonymous_cannot_access_page(self, client, helpers):
        project = recipes.project.make()
        response = client.get('/projects/%d/participants/edit' % (project.id,))
        helpers.assert_login_redirect(response)

        response = client.post('/projects/%d/participants/edit' % (project.id,))
        helpers.assert_login_redirect(response)

    def test_view_page(self, as_programme_manager):
        project = recipes.project.make(created_by=as_programme_manager._user)

        response = as_programme_manager.get(
            '/projects/%d/participants/edit' % (project.id,))
        assert response.status_code == 200
        assert response.context['project'] == project

    def test_edit_participants(self, as_programme_manager):
        project = recipes.project.make(created_by=as_programme_manager._user)
        investigator = recipes.investigator.make(project=project)
        participant = recipes.participant.make(project=project)
        response = as_programme_manager.post(
            '/projects/%d/participants/edit' % (project.id,),
            {
                'participants-TOTAL_FORMS': 2,
                'participants-MAX_NUM_FORMS': 2,
                'participants-MIN_NUM_FORMS': 0,
                'participants-INITIAL_FORMS': 2,
                'participants-0-id': investigator.id,
                'participants-0-project': project.id,
                'participants-0-role': ProjectRole.RESEARCHER.value,
                'participants-1-id': participant.id,
                'participants-1-project': project.id,
                'participants-1-role': ProjectRole.RESEARCHER.value,
                'participants-1-DELETE': 'on',
            }
        )

        assert response.status_code == 302
        assert response.url == '/projects/%d' % project.id

        assert project.participants.count() == 1
        assert project.participants.first().user.username == investigator.user.username
        assert project.participants.first().role == ProjectRole.RESEARCHER.value

    def test_returns_404_for_invisible_project(self, as_standard_user):
        project = recipes.project.make()

        # Programme manager shouldn't have visibility of this other project at all
        # so pretend it doesn't exist and raise a 404
        response = as_standard_user.get(
            '/projects/%d/participants/edit' % (project.id,))
        assert response.status_code == 404

        response = as_standard_user.post(
            '/projects/%d/participants/edit' % (project.id,))
        assert response.status_code == 404

    def test_returns_403_if_no_add_permissions(self, client, researcher):
        # Researchers can't add participants, so do not display the page
        client.force_login(researcher.user)

        response = client.get(
            '/projects/%d/participants/edit' % (researcher.project.id,))
        assert response.status_code == 403

        response = client.post(
            '/projects/%d/participants/edit' % (researcher.project.id,))
        assert response.status_code == 403

    def test_restricts_creation_based_on_role(self, client, referee, researcher):
        client.force_login(referee.user)
        response = client.post(
            '/projects/%d/participants/edit' % (referee.project.id,),
            {
                'participants-TOTAL_FORMS': 1,
                'participants-MAX_NUM_FORMS': 1,
                'participants-MIN_NUM_FORMS': 0,
                'participants-INITIAL_FORMS': 1,
                'participants-0-id': researcher.id,
                'participants-0-project': referee.project.id,
                'participants-0-role': ProjectRole.INVESTIGATOR.value,
            })

        assert response.status_code == 403


@pytest.mark.django_db
class TestProjectAddDataset:
    def test_anonymous_cannot_access_page(self, client, helpers):
        project = recipes.project.make()
        response = client.get('/projects/%d/datasets/new' % project.id)
        helpers.assert_login_redirect(response)

        response = client.post('/projects/%d/datasets/new' % project.id)
        helpers.assert_login_redirect(response)

    def test_view_page(self, as_programme_manager):
        project = recipes.project.make(created_by=as_programme_manager._user)

        response = as_programme_manager.get('/projects/%d/datasets/new' % project.id)
        assert response.status_code == 200
        assert response.context['project'] == project

    def test_add_new_dataset_to_project(self, as_programme_manager, user1):
        project = recipes.project.make(created_by=as_programme_manager._user)
        project.add_user(user1, ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value,
                         as_programme_manager._user)

        response = as_programme_manager.post('/projects/%d/datasets/new' % project.id, {
            'name': 'dataset 1',
            'description': 'Dataset One',
            'default_representative': user1.pk,
        })

        assert response.status_code == 302
        assert response.url == '/projects/%d' % project.id

        assert project.datasets.count() == 1
        dataset = project.datasets.first()
        assert dataset.name == 'dataset 1'
        assert dataset.description == 'Dataset One'
        assert dataset.default_representative == user1

        assert project.get_representative(dataset) == user1

    def test_add_new_dataset_with_work_packages(self, as_programme_manager,
                                                data_provider_representative):
        pm = as_programme_manager._user
        project = recipes.project.make(created_by=pm)
        project.add_user(data_provider_representative.user,
                         role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value, creator=pm)
        work_package1 = recipes.work_package.make(project=project, created_by=pm)
        recipes.work_package.make(project=project, created_by=pm)
        work_package3 = recipes.work_package.make(project=project, created_by=pm)

        response = as_programme_manager.post('/projects/%d/datasets/new' % project.id, {
            'name': 'dataset 1',
            'description': 'Dataset One',
            'default_representative': data_provider_representative.user.pk,
            'work_packages': [work_package1.id, work_package3.id],
        })

        assert response.status_code == 302
        assert response.url == '/projects/%d' % project.id

        assert project.datasets.count() == 1
        assert list(project.datasets.first().work_packages.all()) == [work_package1, work_package3]

    def test_add_new_dataset_with_new_dpr(self, as_programme_manager, user1):
        project = recipes.project.make(created_by=as_programme_manager._user)

        response = as_programme_manager.post('/projects/%d/datasets/new' % project.id, {
            'name': 'dataset 1',
            'description': 'Dataset One',
            'default_representative': user1.pk,
        })

        assert response.status_code == 302
        assert response.url == '/projects/%d' % project.id

        assert project.datasets.count() == 1
        dataset = project.datasets.first()
        assert dataset.name == 'dataset 1'
        assert dataset.description == 'Dataset One'
        assert dataset.default_representative == user1

        assert project.get_representative(dataset) == user1

        assert user1.get_participant(project).role == ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value

    def test_add_new_dataset_to_project_no_user(self, as_programme_manager, user1):
        project = recipes.project.make(created_by=as_programme_manager._user)

        response = as_programme_manager.post('/projects/%d/datasets/new' % project.id, {
            'name': 'dataset 1',
            'description': 'Dataset One',
        })

        assert response.status_code == 200
        assert project.datasets.count() == 0

    def test_returns_404_for_invisible_project(self, as_standard_user):
        project = recipes.project.make()

        # Programme manager shouldn't have visibility of this other project at all
        # so pretend it doesn't exist and raise a 404
        response = as_standard_user.get('/projects/%d/datasets/new' % project.id)
        assert response.status_code == 404

        response = as_standard_user.post('/projects/%d/datasets/new' % project.id)
        assert response.status_code == 404

    def test_returns_403_if_no_add_permissions(self, client, researcher):
        # Researchers can't add datasets, so do not display the page
        client.force_login(researcher.user)

        response = client.get('/projects/%d/datasets/new' % researcher.project.id)
        assert response.status_code == 403

        response = client.post('/projects/%d/datasets/new' % researcher.project.id)
        assert response.status_code == 403


@pytest.mark.django_db
class TestProjectViewDataset:
    def test_anonymous_cannot_access_page(self, client, helpers, data_provider_representative,
                                          programme_manager):
        project = recipes.project.make(created_by=programme_manager)
        dataset = recipes.dataset.make()
        pd = project.add_dataset(dataset, data_provider_representative.user, programme_manager)

        response = client.get('/projects/%d/datasets/%d' % (project.id, pd.id))
        helpers.assert_login_redirect(response)

    def test_view_page(self, as_programme_manager, data_provider_representative):
        project = recipes.project.make(created_by=as_programme_manager._user)
        dataset = recipes.dataset.make()
        pd = project.add_dataset(dataset, data_provider_representative.user,
                                 as_programme_manager._user)

        response = as_programme_manager.get('/projects/%d/datasets/%d' % (project.id, pd.id))
        assert response.status_code == 200
        assert response.context['project'] == project
        assert response.context['dataset'] == pd


@pytest.mark.django_db
class TestProjectEditDataset:
    def test_anonymous_cannot_access_page(self, client, helpers, data_provider_representative,
                                          programme_manager):
        project = recipes.project.make(created_by=programme_manager)
        dataset = recipes.dataset.make()
        pd = project.add_dataset(dataset, data_provider_representative.user, programme_manager)

        response = client.get('/projects/%d/datasets/%d/edit' % (project.id, pd.id))
        helpers.assert_login_redirect(response)

        response = client.post('/projects/%d/datasets/%d/edit' % (project.id, pd.id))
        helpers.assert_login_redirect(response)

    def test_investigator_cannot_access_page(self, data_provider_representative, programme_manager,
                                             as_investigator):
        project = recipes.project.make(created_by=programme_manager)
        project.add_user(as_investigator._user, ProjectRole.INVESTIGATOR.value, programme_manager)
        dataset = recipes.dataset.make()
        pd = project.add_dataset(dataset, data_provider_representative.user, programme_manager)

        response = as_investigator.get('/projects/%d/datasets/%d/edit' % (project.id, pd.id))
        assert response.status_code == 403

        response = as_investigator.post('/projects/%d/datasets/%d/edit' % (project.id, pd.id))
        assert response.status_code == 403

        response = as_investigator.get('/projects/%d/datasets/%d/edit_dpr' % (project.id, pd.id))
        assert response.status_code == 403

        response = as_investigator.post('/projects/%d/datasets/%d/edit_dpr' % (project.id, pd.id))
        assert response.status_code == 403

    def test_edit_dataset(self, as_programme_manager, data_provider_representative):
        project = recipes.project.make(created_by=as_programme_manager._user)
        dataset = recipes.dataset.make()
        pd = project.add_dataset(dataset, data_provider_representative.user,
                                 as_programme_manager._user)

        response = as_programme_manager.get('/projects/%d/datasets/%d/edit' % (project.id, pd.id))
        assert response.status_code == 200
        assert response.context['project'] == project
        assert response.context['dataset'] == pd

        response = as_programme_manager.post(
            '/projects/%d/datasets/%d/edit' % (project.id, pd.id),
            {
                'name': 'Edited Project',
                'description': 'Edited Description',
            }
        )
        assert response.status_code == 302
        assert response.url == '/projects/%d/datasets/%d' % (project.id, pd.id)

        dataset.refresh_from_db()
        assert dataset.name == 'Edited Project'
        assert dataset.description == 'Edited Description'

    def test_cannot_edit_used_dataset(self, as_programme_manager, data_provider_representative):
        project = recipes.project.make(created_by=as_programme_manager._user)
        work_package = recipes.work_package.make(
            project=project, created_by=as_programme_manager._user,
            status=WorkPackageStatus.CLASSIFIED.value)
        work_package2 = recipes.work_package.make(
            project=project, created_by=as_programme_manager._user,
            status=WorkPackageStatus.NEW.value)
        dataset = recipes.dataset.make()
        pd = project.add_dataset(dataset, data_provider_representative.user,
                                 as_programme_manager._user)
        work_package.add_dataset(dataset, as_programme_manager._user)
        work_package2.add_dataset(dataset, as_programme_manager._user)

        response = as_programme_manager.get(f"/projects/{project.id}/datasets/{pd.id}/edit")
        assert response.status_code == 403
        response = as_programme_manager.post(
            f"/projects/{project.id}/datasets/{pd.id}/edit",
            {
                'name': 'Edited Project',
                'description': 'Edited Description',
            }
        )
        assert response.status_code == 403

        dataset.refresh_from_db()
        assert dataset.name != 'Edited Project'
        assert dataset.description != 'Edited Description'

    def test_edit_dpr(self, as_programme_manager, data_provider_representative, user1):
        project = recipes.project.make(created_by=as_programme_manager._user)
        work_package = recipes.work_package.make(
            project=project, created_by=as_programme_manager._user)
        dataset = recipes.dataset.make()
        pd = project.add_dataset(dataset, data_provider_representative.user,
                                 as_programme_manager._user)
        work_package.add_dataset(dataset, as_programme_manager._user)

        response = as_programme_manager.get(f"/projects/{project.id}/datasets/{pd.id}/edit_dpr")
        assert response.status_code == 200
        assert response.context['project'] == project
        assert response.context['dataset'] == pd

        response = as_programme_manager.post(
            '/projects/%d/datasets/%d/edit_dpr' % (project.id, pd.id),
            {
                'default_representative': user1.pk,
            }
        )
        assert response.status_code == 302
        assert response.url == '/projects/%d/datasets/%d' % (project.id, pd.id)

        dataset.refresh_from_db()
        assert dataset.default_representative == user1
        assert project.get_representative(dataset) == user1
        participants = project.get_all_participants(ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value)
        assert [p.user for p in participants] == [data_provider_representative.user, user1]
        participants = work_package.participants.all()
        assert [p.user for p in participants] == [data_provider_representative.user, user1]


@pytest.mark.django_db
class TestProjectDeleteDataset:
    def test_anonymous_cannot_access_page(self, client, helpers, data_provider_representative,
                                          programme_manager):
        project = recipes.project.make(created_by=programme_manager)
        dataset = recipes.dataset.make()
        pd = project.add_dataset(dataset, data_provider_representative.user, programme_manager)

        response = client.get(f"/projects/{project.id}/datasets/{pd.id}/delete")
        helpers.assert_login_redirect(response)

        response = client.post(f"/projects/{project.id}/datasets/{pd.id}/delete")
        helpers.assert_login_redirect(response)

    def test_investigator_cannot_access_page(self, data_provider_representative, programme_manager,
                                             as_investigator):
        project = recipes.project.make(created_by=programme_manager)
        project.add_user(as_investigator._user, ProjectRole.INVESTIGATOR.value, programme_manager)
        dataset = recipes.dataset.make()
        pd = project.add_dataset(dataset, data_provider_representative.user, programme_manager)

        response = as_investigator.get(f"/projects/{project.id}/datasets/{pd.id}/delete")
        assert response.status_code == 403

        response = as_investigator.post(f"/projects/{project.id}/datasets/{pd.id}/delete")
        assert response.status_code == 403

    def test_delete_dataset(self, as_programme_manager, data_provider_representative):
        project = recipes.project.make(created_by=as_programme_manager._user)
        dataset = recipes.dataset.make()
        pd = project.add_dataset(dataset, data_provider_representative.user,
                                 as_programme_manager._user)

        response = as_programme_manager.get(f"/projects/{project.id}/datasets/{pd.id}/delete")
        assert response.status_code == 200
        assert response.context['project'] == project
        assert response.context['dataset'] == pd

        response = as_programme_manager.post(f"/projects/{project.id}/datasets/{pd.id}/delete")
        assert response.status_code == 302
        assert response.url == f"/projects/{project.id}"

        project.refresh_from_db()
        assert project.datasets.count() == 0

    def test_cannot_delete_used_dataset(self, as_programme_manager, data_provider_representative):
        project = recipes.project.make(created_by=as_programme_manager._user)
        work_package = recipes.work_package.make(
            project=project, created_by=as_programme_manager._user,
            status=WorkPackageStatus.CLASSIFIED.value)
        work_package2 = recipes.work_package.make(
            project=project, created_by=as_programme_manager._user,
            status=WorkPackageStatus.NEW.value)
        dataset = recipes.dataset.make()
        pd = project.add_dataset(dataset, data_provider_representative.user,
                                 as_programme_manager._user)
        work_package.add_dataset(dataset, as_programme_manager._user)
        work_package2.add_dataset(dataset, as_programme_manager._user)

        response = as_programme_manager.get(f"/projects/{project.id}/datasets/{pd.id}/delete")
        assert response.status_code == 403
        response = as_programme_manager.post(f"/projects/{project.id}/datasets/{pd.id}/delete")
        assert response.status_code == 403

        project.refresh_from_db()
        assert project.datasets.count() == 1
        assert work_package.datasets.count() == 1
        assert work_package2.datasets.count() == 1

    def test_delete_dataset_used_on_new(self, as_programme_manager, data_provider_representative):
        project = recipes.project.make(created_by=as_programme_manager._user)
        work_package = recipes.work_package.make(
            project=project, created_by=as_programme_manager._user,
            status=WorkPackageStatus.NEW.value)
        dataset = recipes.dataset.make()
        pd = project.add_dataset(dataset, data_provider_representative.user,
                                 as_programme_manager._user)
        work_package.add_dataset(dataset, as_programme_manager._user)

        response = as_programme_manager.get(f"/projects/{project.id}/datasets/{pd.id}/delete")
        assert response.status_code == 200
        assert response.context['project'] == project
        assert response.context['dataset'] == pd

        response = as_programme_manager.post(f"/projects/{project.id}/datasets/{pd.id}/delete")
        assert response.status_code == 302
        assert response.url == f"/projects/{project.id}"

        project.refresh_from_db()
        assert project.datasets.count() == 0
        assert work_package.datasets.count() == 0


@pytest.mark.django_db
class TestWorkPackageAddParticipant:
    def test_add_participant(self, as_programme_manager, user1):
        project = recipes.project.make(
            created_by=as_programme_manager._user,
        )
        p1 = project.add_user(user1, ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value,
                              as_programme_manager._user)
        work_package = recipes.work_package.make(project=project)

        response = as_programme_manager.get('/projects/%d/work_packages/%d/participants/new'
                                            % (project.id, work_package.id))

        assert response.status_code == 200

        response = as_programme_manager.post(
            '/projects/%d/work_packages/%d/participants/new' % (project.id, work_package.id),
            {
                'participant': p1.pk,
            }
        )

        assert response.status_code == 302
        assert response.url == '/projects/%d/work_packages/%d' % (project.id, work_package.id)

        assert work_package.participants.count() == 1
        assert p1 == work_package.participants.first()


@pytest.mark.django_db
class TestWorkPackageApproveParticipants:
    def test_anonymous_cannot_access_page(self, client, helpers, programme_manager):
        project = recipes.project.make(created_by=programme_manager)
        work_package = recipes.work_package.make(project=project)

        url = f"/projects/{project.id}/work_packages/{work_package.id}/participants/approve"
        response = client.get(url)
        helpers.assert_login_redirect(response)

    def test_unprivileged_user_cannot_access_page(self, as_investigator, programme_manager):
        project = recipes.project.make(created_by=programme_manager)
        work_package = recipes.work_package.make(project=project)

        url = f"/projects/{project.id}/work_packages/{work_package.id}/participants/approve"
        response = as_investigator.get(url)
        assert response.status_code == 404

    def test_approve_participants(self, as_data_provider_representative, referee,
                                  programme_manager):
        project = recipes.project.make(created_by=programme_manager)
        p1 = project.add_user(as_data_provider_representative._user,
                              ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value,
                              programme_manager)
        p2 = project.add_user(referee.user,
                              ProjectRole.REFEREE.value,
                              programme_manager)
        work_package = recipes.work_package.make(
            project=project, status=WorkPackageStatus.UNDERWAY.value)
        work_package.add_user(as_data_provider_representative._user, programme_manager)
        work_package.add_user(referee.user, programme_manager)
        dataset = recipes.dataset.make()
        project.add_dataset(dataset, as_data_provider_representative._user, programme_manager)
        work_package.add_dataset(dataset, programme_manager)

        url = f"/projects/{project.id}/work_packages/{work_package.id}"
        response = as_data_provider_representative.get(url)
        table = response.context['participants_table']

        assert response.status_code == 200
        assert list(table.as_values()) == [
            ['Username', 'Role', 'Approved', 'Approved by you'],
            [p1.user.display_name(), 'Data Provider Representative', 'True', 'True'],
            [p2.user.display_name(), 'Referee', 'False', 'False'],
        ]

        url = f"/projects/{project.id}/work_packages/{work_package.id}/participants/approve"
        response = as_data_provider_representative.get(url)
        assert response.status_code == 200

        response = as_data_provider_representative.post(url, {
            'participants-TOTAL_FORMS': 1,
            'participants-MAX_NUM_FORMS': 1,
            'participants-MIN_NUM_FORMS': 0,
            'participants-INITIAL_FORMS': 1,
            'participants-0-id': p2.get_work_package_participant(work_package).id,
            'participants-0-approved': 'on',
        })

        url = f"/projects/{project.id}/work_packages/{work_package.id}"
        response = as_data_provider_representative.get(url)
        table = response.context['participants_table']

        assert response.status_code == 200
        assert list(table.as_values()) == [
            ['Username', 'Role', 'Approved', 'Approved by you'],
            [p1.user.display_name(), 'Data Provider Representative', 'True', 'True'],
            [p2.user.display_name(), 'Referee', 'True', 'True'],
        ]


@pytest.mark.django_db
class TestWorkPackageEditParticipants:
    def test_anonymous_cannot_access_page(self, client, helpers):
        project = recipes.project.make()
        work_package = recipes.work_package.make(project=project)
        response = client.get(
            '/projects/%d/work_packages/%d/participants/edit' % (project.id, work_package.id))
        helpers.assert_login_redirect(response)

        response = client.post(
            '/projects/%d/work_packages/%d/participants/edit' % (project.id, work_package.id))
        helpers.assert_login_redirect(response)

    def test_view_page(self, as_programme_manager):
        project = recipes.project.make(created_by=as_programme_manager._user)
        work_package = recipes.work_package.make(project=project)

        response = as_programme_manager.get(
            '/projects/%d/work_packages/%d/participants/edit' % (project.id, work_package.id))
        assert response.status_code == 200
        assert response.context['project'] == project

    def test_edit_participants(self, as_programme_manager, referee, data_provider_representative):
        project = recipes.project.make(created_by=as_programme_manager._user)
        project.add_user(data_provider_representative.user,
                         ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value,
                         as_programme_manager._user)
        project.add_user(referee.user,
                         ProjectRole.REFEREE.value,
                         as_programme_manager._user)
        work_package = recipes.work_package.make(project=project)
        wpp1 = work_package.add_user(data_provider_representative.user, as_programme_manager._user)
        wpp2 = work_package.add_user(referee.user, as_programme_manager._user)
        dataset = recipes.dataset.make()
        project.add_dataset(dataset, data_provider_representative.user, as_programme_manager._user)
        work_package.add_dataset(dataset, as_programme_manager._user)

        response = as_programme_manager.post(
            '/projects/%d/work_packages/%d/participants/edit' % (project.id, work_package.id),
            {
                'participants-TOTAL_FORMS': 2,
                'participants-MAX_NUM_FORMS': 2,
                'participants-MIN_NUM_FORMS': 0,
                'participants-INITIAL_FORMS': 2,
                'participants-0-id': wpp1.id,
                'participants-0-work_package': work_package.id,
                'participants-0-DELETE': 'on',
                'participants-1-id': wpp2.id,
                'participants-1-work_package': work_package.id,
            }
        )

        assert response.status_code == 302
        assert response.url == '/projects/%d/work_packages/%d' % (project.id, work_package.id)

        assert work_package.participants.count() == 1
        assert work_package.participants.first().role == ProjectRole.REFEREE.value

    def test_returns_404_for_invisible_project(self, as_standard_user):
        project = recipes.project.make()
        work_package = recipes.work_package.make(project=project)

        # Programme manager shouldn't have visibility of this other project at all
        # so pretend it doesn't exist and raise a 404
        response = as_standard_user.get(
            '/projects/%d/work_packages/%d/participants/edit' % (project.id, work_package.id))
        assert response.status_code == 404

        response = as_standard_user.post(
            '/projects/%d/work_packages/%d/participants/edit' % (project.id, work_package.id))
        assert response.status_code == 404

    def test_returns_403_if_no_add_permissions(self, client, researcher):
        project = researcher.project
        work_package = recipes.work_package.make(project=project)
        # Researchers can't add participants, so do not display the page
        client.force_login(researcher.user)

        response = client.get(
            '/projects/%d/work_packages/%d/participants/edit' % (project.id, work_package.id))
        assert response.status_code == 403

        response = client.post(
            '/projects/%d/work_packages/%d/participants/edit' % (project.id, work_package.id))
        assert response.status_code == 403


@pytest.mark.django_db
class TestWorkPackageAddDataset:
    def test_add_dataset(self, as_programme_manager, user1):
        ds1, ds2 = recipes.dataset.make(_quantity=2)
        project = recipes.project.make(
            created_by=as_programme_manager._user,
        )
        project.add_user(user1, ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value,
                         as_programme_manager._user)
        work_package = recipes.work_package.make(project=project)
        project.add_dataset(ds1, user1, as_programme_manager._user)
        project.add_dataset(ds2, user1, as_programme_manager._user)

        response = as_programme_manager.get('/projects/%d/work_packages/%d/datasets/new'
                                            % (project.id, work_package.id))

        assert response.status_code == 200

        response = as_programme_manager.post(
            '/projects/%d/work_packages/%d/datasets/new' % (project.id, work_package.id),
            {
                'dataset': ds1.pk,
            }
        )

        assert response.status_code == 302
        assert response.url == '/projects/%d/work_packages/%d' % (project.id, work_package.id)

        assert work_package.datasets.count() == 1
        assert ds1 == work_package.datasets.first()

    def test_cannot_add_underway_work_package(self, as_programme_manager, user1):
        ds1, ds2 = recipes.dataset.make(_quantity=2)
        project = recipes.project.make(
            created_by=as_programme_manager._user,
        )
        project.add_user(user1, ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value,
                         as_programme_manager._user)
        work_package = recipes.work_package.make(
            project=project, status=WorkPackageStatus.UNDERWAY.value)
        project.add_dataset(ds1, user1, as_programme_manager._user)
        project.add_dataset(ds2, user1, as_programme_manager._user)

        url = f"/projects/{project.id}/work_packages/{work_package.id}/datasets/new"
        response = as_programme_manager.get(url)
        assert response.status_code == 403

        work_package.status = WorkPackageStatus.CLASSIFIED.value
        work_package.save()

        response = as_programme_manager.get(url)
        assert response.status_code == 403


@pytest.mark.django_db
class TestWorkPackageEditDatasets:
    def test_anonymous_cannot_access_page(self, client, helpers):
        project = recipes.project.make()
        work_package = recipes.work_package.make(project=project)
        response = client.get(
            '/projects/%d/work_packages/%d/datasets/edit' % (project.id, work_package.id))
        helpers.assert_login_redirect(response)

        response = client.post(
            '/projects/%d/work_packages/%d/datasets/edit' % (project.id, work_package.id))
        helpers.assert_login_redirect(response)

    def test_view_page(self, as_programme_manager):
        project = recipes.project.make(created_by=as_programme_manager._user)
        work_package = recipes.work_package.make(project=project)

        response = as_programme_manager.get(
            '/projects/%d/work_packages/%d/datasets/edit' % (project.id, work_package.id))
        assert response.status_code == 200
        assert response.context['project'] == project

    def test_edit_datasets(self, as_programme_manager, referee, data_provider_representative):
        project = recipes.project.make(created_by=as_programme_manager._user)
        work_package = recipes.work_package.make(project=project)
        dataset1 = recipes.dataset.make()
        project.add_dataset(dataset1, data_provider_representative.user, as_programme_manager._user)
        wpd1 = work_package.add_dataset(dataset1, as_programme_manager._user)
        dataset2 = recipes.dataset.make()
        project.add_dataset(dataset2, data_provider_representative.user, as_programme_manager._user)
        wpd2 = work_package.add_dataset(dataset2, as_programme_manager._user)

        response = as_programme_manager.post(
            '/projects/%d/work_packages/%d/datasets/edit' % (project.id, work_package.id),
            {
                'datasets-TOTAL_FORMS': 2,
                'datasets-MAX_NUM_FORMS': 2,
                'datasets-MIN_NUM_FORMS': 0,
                'datasets-INITIAL_FORMS': 2,
                'datasets-0-id': wpd1.id,
                'datasets-0-work_package': work_package.id,
                'datasets-0-DELETE': 'on',
                'datasets-1-id': wpd2.id,
                'datasets-1-work_package': work_package.id,
            }
        )

        assert response.status_code == 302
        assert response.url == '/projects/%d/work_packages/%d' % (project.id, work_package.id)

        assert work_package.datasets.count() == 1
        assert work_package.datasets.first() == dataset2

    def test_returns_404_for_invisible_project(self, as_standard_user):
        project = recipes.project.make()
        work_package = recipes.work_package.make(project=project)

        # Programme manager shouldn't have visibility of this other project at all
        # so pretend it doesn't exist and raise a 404
        response = as_standard_user.get(
            '/projects/%d/work_packages/%d/datasets/edit' % (project.id, work_package.id))
        assert response.status_code == 404

        response = as_standard_user.post(
            '/projects/%d/work_packages/%d/datasets/edit' % (project.id, work_package.id))
        assert response.status_code == 404

    def test_returns_403_if_no_add_permissions(self, client, researcher):
        project = researcher.project
        work_package = recipes.work_package.make(project=project)
        # Researchers can't add datasets, so do not display the page
        client.force_login(researcher.user)

        response = client.get(
            '/projects/%d/work_packages/%d/datasets/edit' % (project.id, work_package.id))
        assert response.status_code == 403

        response = client.post(
            '/projects/%d/work_packages/%d/datasets/edit' % (project.id, work_package.id))
        assert response.status_code == 403

    def test_cannot_edit_underway(self, classified_work_package, as_programme_manager):
        work_package = classified_work_package(None)
        work_package.status = WorkPackageStatus.UNDERWAY.value
        work_package.save()
        project = work_package.project

        response = as_programme_manager.get(
            '/projects/%d/work_packages/%d/datasets/edit' % (project.id, work_package.id))
        assert response.status_code == 403

        response = as_programme_manager.post(
            '/projects/%d/work_packages/%d/datasets/edit' % (project.id, work_package.id))
        assert response.status_code == 403


@pytest.mark.django_db
class TestProjectAddWorkPackage:
    def test_anonymous_cannot_access_page(self, client, helpers):
        project = recipes.project.make()
        response = client.get('/projects/%d/work_packages/new' % project.id)
        helpers.assert_login_redirect(response)

        response = client.post('/projects/%d/work_packages/new' % project.id)
        helpers.assert_login_redirect(response)

    def test_view_page(self, as_programme_manager):
        project = recipes.project.make(created_by=as_programme_manager._user)

        response = as_programme_manager.get('/projects/%d/work_packages/new' % project.id)
        assert response.status_code == 200
        assert response.context['project'] == project

    def test_add_new_work_package_to_project(self, as_programme_manager):
        project = recipes.project.make(created_by=as_programme_manager._user)

        response = as_programme_manager.post('/projects/%d/work_packages/new' % project.id, {
            'role': ProjectRole.RESEARCHER.value,
            'name': 'work package 1',
            'description': 'Work Package One',
        })

        assert response.status_code == 302
        assert response.url == '/projects/%d' % project.id

        assert project.work_packages.count() == 1
        assert project.work_packages.first().name == 'work package 1'
        assert project.work_packages.first().description == 'Work Package One'

    def test_add_new_work_package_with_datasets(self, as_programme_manager,
                                                data_provider_representative):
        pm = as_programme_manager._user
        project = recipes.project.make(created_by=pm)
        project.add_user(data_provider_representative.user,
                         role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value, creator=pm)
        dataset1 = recipes.dataset.make(created_by=pm)
        dataset2 = recipes.dataset.make(created_by=pm)
        dataset3 = recipes.dataset.make(created_by=pm)
        project.add_dataset(dataset1, representative=data_provider_representative.user, creator=pm)
        project.add_dataset(dataset2, representative=data_provider_representative.user, creator=pm)
        project.add_dataset(dataset3, representative=data_provider_representative.user, creator=pm)

        response = as_programme_manager.post('/projects/%d/work_packages/new' % project.id, {
            'role': ProjectRole.RESEARCHER.value,
            'name': 'work package 1',
            'description': 'Work Package One',
            'datasets': [dataset1.id, dataset3.id],
        })

        assert response.status_code == 302
        assert response.url == '/projects/%d' % project.id

        assert project.work_packages.count() == 1
        assert list(project.work_packages.first().datasets.all()) == [dataset1, dataset3]

    def test_returns_404_for_invisible_project(self, as_standard_user):
        project = recipes.project.make()

        # Programme manager shouldn't have visibility of this other project at all
        # so pretend it doesn't exist and raise a 404
        response = as_standard_user.get('/projects/%d/work_packages/new' % project.id)
        assert response.status_code == 404

        response = as_standard_user.post('/projects/%d/work_packages/new' % project.id)
        assert response.status_code == 404

    def test_returns_403_if_no_add_permissions(self, client, researcher):
        # Researchers can't add work packages, so do not display the page
        client.force_login(researcher.user)

        response = client.get('/projects/%d/work_packages/new' % researcher.project.id)
        assert response.status_code == 403

        response = client.post('/projects/%d/work_packages/new' % researcher.project.id)
        assert response.status_code == 403


@pytest.mark.django_db
class TestEditWorkPackage:
    def test_anonymous_cannot_access_page(self, client, helpers):
        response = client.get('/projects/1/work_packages/1/edit')
        helpers.assert_login_redirect(response)

    def test_investigator_cannot_access_page(self, as_investigator):
        project = recipes.project.make()
        work_package = recipes.work_package.make(project=project)
        recipes.participant.make(project=project, user=as_investigator._user,
                                 role=ProjectRole.INVESTIGATOR.value)

        url = f"/projects/{project.id}/work_packages/{work_package.id}"
        response = as_investigator.get(url + "/edit")

        assert response.status_code == 403

    def test_cannot_edit_classified(self, as_project_participant):
        project = recipes.project.make()
        work_package = recipes.work_package.make(
            project=project, status=WorkPackageStatus.CLASSIFIED.value)
        recipes.participant.make(project=project, user=as_project_participant._user,
                                 role=ProjectRole.PROJECT_MANAGER.value)

        url = f"/projects/{project.id}/work_packages/{work_package.id}"
        response = as_project_participant.get(url + "/edit")

        assert response.status_code == 403

    def test_edit(self, as_project_participant):
        project = recipes.project.make()
        work_package = recipes.work_package.make(project=project)
        recipes.participant.make(project=project, user=as_project_participant._user,
                                 role=ProjectRole.PROJECT_MANAGER.value)

        url = f"/projects/{project.id}/work_packages/{work_package.id}"
        response = as_project_participant.get(url + "/edit")

        assert response.status_code == 200
        assert response.context['work_package'] == work_package

        response = as_project_participant.post(url + "/edit", {
            'name': 'my updated work package',
            'description': 'a different work package',
        })

        assert response.status_code == 302
        assert response.url == url

        response = as_project_participant.get(url)

        assert response.status_code == 200
        assert response.context['work_package'].name == 'my updated work package'
        assert response.context['work_package'].description == 'a different work package'


@pytest.mark.django_db
class TestDeleteWorkPackage:
    def test_anonymous_cannot_access_page(self, client, helpers):
        response = client.get('/projects/1/work_packages/1/delete')
        helpers.assert_login_redirect(response)

    def test_investigator_cannot_access_page(self, as_investigator):
        project = recipes.project.make()
        work_package = recipes.work_package.make(project=project)
        recipes.participant.make(project=project, user=as_investigator._user,
                                 role=ProjectRole.INVESTIGATOR.value)

        url = f"/projects/{project.id}/work_packages/{work_package.id}"
        response = as_investigator.get(url + "/delete")

        assert response.status_code == 403

    def test_cannot_delete_classified(self, as_project_participant):
        project = recipes.project.make()
        work_package = recipes.work_package.make(
            project=project, status=WorkPackageStatus.CLASSIFIED.value)
        recipes.participant.make(project=project, user=as_project_participant._user,
                                 role=ProjectRole.PROJECT_MANAGER.value)

        url = f"/projects/{project.id}/work_packages/{work_package.id}"
        response = as_project_participant.get(url + "/delete")

        assert response.status_code == 403

    def test_delete(self, as_project_participant):
        project = recipes.project.make()
        work_package = recipes.work_package.make(project=project)
        recipes.participant.make(project=project, user=as_project_participant._user,
                                 role=ProjectRole.PROJECT_MANAGER.value)

        url = f"/projects/{project.id}/work_packages/{work_package.id}"
        response = as_project_participant.get(url + "/delete")

        assert response.status_code == 200
        assert response.context['work_package'] == work_package

        response = as_project_participant.post(url + "/delete")

        assert response.status_code == 302
        assert response.url == f"/projects/{project.id}"

        response = as_project_participant.get(url)

        assert response.status_code == 404


@pytest.mark.django_db
class TestWorkPackageOpenClassification:
    def test_open_classification(self, classified_work_package, programme_manager,
                                 as_standard_user):
        work_package = classified_work_package(None)
        work_package.status = WorkPackageStatus.NEW.value
        work_package.save()

        project = work_package.project
        project.add_user(as_standard_user._user, ProjectRole.PROJECT_MANAGER.value,
                         programme_manager)

        response = as_standard_user.get(f"/projects/{project.pk}/work_packages/{work_package.pk}")
        assert b'Open Classification' in response.content

        url = f"/projects/{project.pk}/work_packages/{work_package.pk}/classify_open"
        response = as_standard_user.get(url)
        assert b'Open Classification' in response.content

        response = as_standard_user.post(url, {}, follow=True)
        assert response.status_code == 200

        work_package.refresh_from_db()
        assert work_package.status == WorkPackageStatus.UNDERWAY.value

    def test_cannot_open_already_underway(self, classified_work_package, programme_manager,
                                          as_standard_user):
        work_package = classified_work_package(None)
        work_package.status = WorkPackageStatus.UNDERWAY.value
        work_package.save()

        project = work_package.project
        project.add_user(as_standard_user._user, ProjectRole.PROJECT_MANAGER.value,
                         programme_manager)

        response = as_standard_user.get(f"/projects/{project.pk}/work_packages/{work_package.pk}")
        assert b'Open Classification' not in response.content

        url = f"/projects/{project.pk}/work_packages/{work_package.pk}/classify_open"
        response = as_standard_user.get(url)
        assert response.status_code == 403

        response = as_standard_user.post(url, {}, follow=True)
        assert response.status_code == 403

    def test_cannot_open_no_datasets(self, classified_work_package, programme_manager,
                                     as_standard_user):
        project = recipes.project.make()
        work_package = recipes.work_package.make(project=project)
        project.add_user(as_standard_user._user, ProjectRole.PROJECT_MANAGER.value,
                         programme_manager)

        response = as_standard_user.get(f"/projects/{project.pk}/work_packages/{work_package.pk}")
        assert b'Open Classification' not in response.content

        url = f"/projects/{project.pk}/work_packages/{work_package.pk}/classify_open"
        response = as_standard_user.get(url)
        assert response.status_code == 403

        response = as_standard_user.post(url, {}, follow=True)
        assert response.status_code == 403

    def test_cannot_open_as_investigator(self, classified_work_package, as_investigator):
        work_package = classified_work_package(None)
        work_package.status = WorkPackageStatus.NEW.value
        work_package.save()

        project = work_package.project

        response = as_investigator.get(f"/projects/{project.pk}/work_packages/{work_package.pk}")
        assert b'Open Classification' not in response.content

        url = f"/projects/{project.pk}/work_packages/{work_package.pk}/classify_open"
        response = as_investigator.get(url)
        assert response.status_code == 403

        response = as_investigator.post(url, {}, follow=True)
        assert response.status_code == 403


@pytest.mark.django_db
class TestWorkPackageCloseClassification:
    def test_close_classification(self, classified_work_package, programme_manager,
                                  as_standard_user):
        work_package = classified_work_package(0)
        work_package.status = WorkPackageStatus.UNDERWAY.value
        work_package.tier = None
        work_package.save()

        project = work_package.project
        project.add_user(as_standard_user._user, ProjectRole.PROJECT_MANAGER.value,
                         programme_manager)

        response = as_standard_user.get(f"/projects/{project.pk}/work_packages/{work_package.pk}")
        assert b'Close Classification' in response.content

        url = f"/projects/{project.pk}/work_packages/{work_package.pk}/classify_close"
        response = as_standard_user.get(url)
        assert b'Close Classification' in response.content

        response = as_standard_user.post(url, {}, follow=True)
        assert response.status_code == 200

        work_package.refresh_from_db()
        assert work_package.status == WorkPackageStatus.CLASSIFIED.value

    def test_cannot_close_already_complete(self, classified_work_package, programme_manager,
                                           as_standard_user):
        work_package = classified_work_package(0)

        project = work_package.project
        project.add_user(as_standard_user._user, ProjectRole.PROJECT_MANAGER.value,
                         programme_manager)

        response = as_standard_user.get(f"/projects/{project.pk}/work_packages/{work_package.pk}")
        assert b'Close Classification' not in response.content

        url = f"/projects/{project.pk}/work_packages/{work_package.pk}/classify_close"
        response = as_standard_user.get(url)
        assert response.status_code == 403

        response = as_standard_user.post(url, {}, follow=True)
        assert response.status_code == 403

    def test_cannot_close_not_complete(self, classified_work_package, programme_manager,
                                       investigator, as_standard_user):
        work_package = classified_work_package(None)
        work_package.classify_as(0, investigator.user)
        project = work_package.project
        project.add_user(as_standard_user._user, ProjectRole.PROJECT_MANAGER.value,
                         programme_manager)

        response = as_standard_user.get(f"/projects/{project.pk}/work_packages/{work_package.pk}")
        assert b'Close Classification' not in response.content

        url = f"/projects/{project.pk}/work_packages/{work_package.pk}/classify_close"
        response = as_standard_user.get(url)
        assert response.status_code == 403

        response = as_standard_user.post(url, {}, follow=True)
        assert response.status_code == 403

    def test_cannot_close_no_agreement(self, classified_work_package, programme_manager,
                                       investigator, as_standard_user):
        work_package = classified_work_package(0)
        ClassificationOpinion.objects.filter(created_by=investigator.user).delete()
        work_package.classify_as(1, investigator.user)
        project = work_package.project
        project.add_user(as_standard_user._user, ProjectRole.PROJECT_MANAGER.value,
                         programme_manager)

        response = as_standard_user.get(f"/projects/{project.pk}/work_packages/{work_package.pk}")
        assert b'Close Classification' not in response.content

        url = f"/projects/{project.pk}/work_packages/{work_package.pk}/classify_close"
        response = as_standard_user.get(url)
        assert response.status_code == 403

        response = as_standard_user.post(url, {}, follow=True)
        assert response.status_code == 403

    def test_cannot_close_as_investigator(self, classified_work_package, as_investigator):
        work_package = classified_work_package(0)

        project = work_package.project

        response = as_investigator.get(f"/projects/{project.pk}/work_packages/{work_package.pk}")
        assert b'Close Classification' not in response.content

        url = f"/projects/{project.pk}/work_packages/{work_package.pk}/classify_close"
        response = as_investigator.get(url)
        assert response.status_code == 403

        response = as_investigator.post(url, {}, follow=True)
        assert response.status_code == 403


@pytest.mark.django_db
class TestWorkPackageClassifyData:
    def url(self, work_package, page='classify'):
        return '/projects/%d/work_packages/%d/%s' % (work_package.project.id, work_package.id, page)

    def classify(self, client, work_package, response, current,
                 answer=None, back=None, start=None,
                 validate_goto=True, next=None, number=None, guidance=None):
        '''
        Posts data to answer a single classification question

        Parameters are divided into three stages.
        Defining the current page:
        client - Test client instance
        work_package - Work package to classify
        response - Response object for current page
        current - Name of the ClassificationQuestion being answered

        Actions to take (optional, normally you should supply exactly one):
        answer - boolean representing whether to answer Yes/No
        back - Name of previous step to go back to (simulating the Back button)
        start - Name of first step to go back to (simulating the Start Over button)

        Expected results (optional, will not be verified if not provided):
        validate_goto - Boolean indicating whether to check that back/start match what is
                        displayed on page. If false, essentially simulates the user manually
                        editing the URL
        next - Name of the ClassificationQuestion you expect to be asked next
        number - Number of the question you expect to be asked next
        guidance - List of names of ClassificationGuidance you expect to be on the next page
        '''
        url = response.request['PATH_INFO'] + '?' + response.request['QUERY_STRING']
        response = client.get(url)
        assert 'question' in response.context
        assert response.context['question'].name == current

        goto = back or start
        if goto:
            key = 'previous_question' if back else 'starting_question'
            if validate_goto:
                assert key in response.context
                assert response.context[key].name == goto
                pk = response.context[key].pk
            else:
                pk = ClassificationQuestion.objects.get(name=goto).pk
            url = self.url(work_package, f"classify/{pk}")
            response = client.get(url, follow=True)
            assert 'question' in response.context
            assert response.context['question'].name == goto
            return response

        data = {}
        if answer:
            data['submit_yes'] = 'Yes'
        else:
            data['submit_no'] = 'No'

        response = client.post(url, data, follow=True)
        if next:
            assert 'question' in response.context
            assert response.context['question'].name == next
            assert response.context['explanation'].name == next
        if number:
            assert response.context['question_number'] == number
        if guidance:
            assert [g.name for g in response.context['guidance']] == guidance

        return response

    def check_results_page(self, response, work_package, user, tier, questions):
        assert response.status_code == 200
        assert response.context['classification'].tier == tier
        assert work_package.classifications.get().tier == tier
        table = list(response.context['questions_table'].as_values())
        assert len(table) == len(questions) + 1

        def question(name):
            value = ClassificationQuestion.objects.get(name=name).question
            value = bleach.clean(value, tags=[], strip=True)
            return value

        assert table[0] == ['Question', user.username]
        assert table[1:] == [[question(q[0]), q[1]] for q in questions]

    def test_anonymous_cannot_access_page(self, client, helpers):
        project = recipes.project.make()
        work_package = recipes.work_package.make(project=project)
        response = client.get(self.url(work_package))
        helpers.assert_login_redirect(response)

        response = client.post(self.url(work_package), {})
        helpers.assert_login_redirect(response)

    def test_unassigned_cannot_view_page(self, as_project_participant, programme_manager):
        insert_initial_questions(ClassificationQuestion, ClassificationGuidance)
        project = recipes.project.make(created_by=programme_manager)
        work_package = recipes.work_package.make(project=project)
        project.add_user(user=as_project_participant._user,
                         role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value,
                         creator=programme_manager)

        response = as_project_participant.get(self.url(work_package), follow=True)
        assert response.status_code == 403

    def test_view_page(self, as_project_participant, programme_manager):
        insert_initial_questions(ClassificationQuestion, ClassificationGuidance)
        project = recipes.project.make(created_by=programme_manager)
        work_package = recipes.work_package.make(
            project=project, status=WorkPackageStatus.UNDERWAY.value)
        project.add_user(user=as_project_participant._user,
                         role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value,
                         creator=programme_manager)
        work_package.add_user(user=as_project_participant._user,
                              creator=programme_manager)

        response = as_project_participant.get(self.url(work_package), follow=True)
        assert response.status_code == 200
        assert response.context['work_package'] == work_package
        assert 'question' in response.context

    def test_returns_404_for_invisible_project(self, as_standard_user):
        project = recipes.project.make()
        work_package = recipes.work_package.make(project=project)

        # Programme manager shouldn't have visibility of this other project at all
        # so pretend it doesn't exist and raise a 404
        response = as_standard_user.get(self.url(work_package))
        assert response.status_code == 404

        response = as_standard_user.post(self.url(work_package))
        assert response.status_code == 404

    def test_returns_403_for_researcher(self, client, researcher):
        work_package = recipes.work_package.make(project=researcher.project)
        # Researchers can't classify, so do not display the page
        client.force_login(researcher.user)

        response = client.get(self.url(work_package))
        assert response.status_code == 403

        response = client.post(self.url(work_package))
        assert response.status_code == 403

    def test_returns_403_for_programme_manager(self, as_programme_manager):
        # Programme managers can't classify data
        project = recipes.project.make(created_by=as_programme_manager._user)
        work_package = recipes.work_package.make(project=project)

        response = as_programme_manager.get(self.url(work_package))
        assert response.status_code == 403

    def test_returns_403_for_project_manager(self, client, researcher, programme_manager):
        project = recipes.project.make(created_by=programme_manager)
        project.add_user(researcher.user, ProjectRole.PROJECT_MANAGER.value,
                         creator=programme_manager)
        work_package = recipes.work_package.make(project=project, created_by=programme_manager)

        client.force_login(researcher.user)

        response = client.get(self.url(work_package))
        assert response.status_code == 403

        response = client.post(self.url(work_package))
        assert response.status_code == 403

    def test_returns_403_when_not_open(self, classified_work_package, as_investigator):
        insert_initial_questions(ClassificationQuestion, ClassificationGuidance)
        work_package = classified_work_package(None)
        work_package.status = WorkPackageStatus.NEW.value
        work_package.save()

        response = as_investigator.get(self.url(work_package))
        assert response.status_code == 403

        work_package.status = WorkPackageStatus.CLASSIFIED.value
        work_package.save()

        response = as_investigator.get(self.url(work_package))
        assert response.status_code == 403

        work_package.status = WorkPackageStatus.UNDERWAY.value
        work_package.save()

        response = as_investigator.get(self.url(work_package))
        assert response.status_code == 302

    def test_do_not_show_form_if_user_already_classified(
            self, classified_work_package, as_investigator):
        work_package = classified_work_package(None)

        work_package.classify_as(0, as_investigator._user)

        response = as_investigator.get(self.url(work_package), follow=True)

        assert 'question' not in response.context
        assert [m.message for m in response.context['messages']] == [
            'You have already completed classification. Please delete your classification and '
            'start again if you wish to change any answers.'
        ]

    def test_delete_classification(self, classified_work_package, as_investigator):
        insert_initial_questions(ClassificationQuestion, ClassificationGuidance)
        work_package = classified_work_package(None)

        work_package.classify_as(0, as_investigator._user)

        response = as_investigator.get(self.url(work_package), follow=True)
        assert b'Delete My Classification' in response.content

        response = as_investigator.get(self.url(work_package, 'classify_delete'))
        assert b'Delete Classification' in response.content

        response = as_investigator.post(self.url(work_package, 'classify_delete'))

        response = as_investigator.get(self.url(work_package), follow=True)
        assert 'question' in response.context
        assert b'Delete My Classification' not in response.content

    def test_classify_as_tier(self, classified_work_package, as_investigator):
        insert_initial_questions(ClassificationQuestion, ClassificationGuidance)
        work_package = classified_work_package(None)

        response = as_investigator.get(self.url(work_package), follow=True)
        response = self.classify(as_investigator, work_package, response, 'open_generate_new',
                                 answer=False, next='closed_personal', number=2)
        response = self.classify(as_investigator, work_package, response, 'closed_personal',
                                 answer=True, next='public_and_open', number=3)
        response = self.classify(as_investigator, work_package, response, 'public_and_open',
                                 answer=False, next='no_reidentify', number=4)
        response = self.classify(as_investigator, work_package, response, 'no_reidentify',
                                 answer=True, next='no_reidentify_absolute', number=5)
        response = self.classify(as_investigator, work_package, response, 'no_reidentify_absolute',
                                 answer=False, next='no_reidentify_strong', number=6)
        response = self.classify(as_investigator, work_package, response, 'no_reidentify_strong',
                                 answer=True, next='include_commercial_personal', number=7)
        response = self.classify(as_investigator, work_package, response,
                                 'include_commercial_personal', answer=True,
                                 next='financial_low_personal', number=8)
        response = self.classify(as_investigator, work_package, response, 'financial_low_personal',
                                 answer=False, next='sophisticated_attack', number=9)
        response = self.classify(as_investigator, work_package, response, 'sophisticated_attack',
                                 answer=False)

        self.check_results_page(
            response, work_package, as_investigator._user, 3,
            [
                ['open_generate_new', 'False'],
                ['closed_personal', 'True'],
                ['public_and_open', 'False'],
                ['no_reidentify', 'True'],
                ['no_reidentify_absolute', 'False'],
                ['no_reidentify_strong', 'True'],
                ['include_commercial_personal', 'True'],
                ['financial_low_personal', 'False'],
                ['sophisticated_attack', 'False'],
            ]
        )

    def test_classify_backwards(self, classified_work_package, as_investigator):
        insert_initial_questions(ClassificationQuestion, ClassificationGuidance)
        work_package = classified_work_package(None)

        response = as_investigator.get(self.url(work_package), follow=True)
        response = self.classify(as_investigator, work_package, response, 'open_generate_new',
                                 answer=False, next='closed_personal', number=2)
        response = self.classify(as_investigator, work_package, response, 'closed_personal',
                                 answer=True, next='public_and_open', number=3)
        response = self.classify(as_investigator, work_package, response, 'public_and_open',
                                 start='open_generate_new', next='open_generate_new', number=1)
        response = self.classify(as_investigator, work_package, response, 'open_generate_new',
                                 answer=False, next='closed_personal', number=2)
        response = self.classify(as_investigator, work_package, response, 'closed_personal',
                                 answer=False, next='include_commercial', number=3)
        response = self.classify(as_investigator, work_package, response, 'include_commercial',
                                 answer=True, next='financial_low', number=4)
        response = self.classify(as_investigator, work_package, response, 'financial_low',
                                 back='include_commercial', next='include_commercial', number=3)
        response = self.classify(as_investigator, work_package, response, 'include_commercial',
                                 back='closed_personal', next='closed_personal', number=2)
        response = self.classify(as_investigator, work_package, response, 'closed_personal',
                                 answer=False, next='include_commercial', number=3)
        response = self.classify(as_investigator, work_package, response, 'include_commercial',
                                 answer=False, next='open_publication', number=4)
        response = self.classify(as_investigator, work_package, response, 'open_publication',
                                 answer=True)

        self.check_results_page(
            response, work_package, as_investigator._user, 1,
            [
                ['open_generate_new', 'False'],
                ['closed_personal', 'False'],
                ['include_commercial', 'False'],
                ['open_publication', 'True'],
            ]
        )

    def test_classify_jump_back(self, classified_work_package, as_investigator):
        insert_initial_questions(ClassificationQuestion, ClassificationGuidance)
        work_package = classified_work_package(None)

        response = as_investigator.get(self.url(work_package), follow=True)
        response = self.classify(as_investigator, work_package, response, 'open_generate_new',
                                 answer=False, next='closed_personal', number=2)
        response = self.classify(as_investigator, work_package, response, 'closed_personal',
                                 answer=False, next='include_commercial', number=3)
        response = self.classify(as_investigator, work_package, response, 'include_commercial',
                                 answer=False, next='open_publication', number=4)
        response = self.classify(as_investigator, work_package, response, 'open_publication',
                                 back='closed_personal', next='closed_personal', number=2,
                                 validate_goto=False)
        response = self.classify(as_investigator, work_package, response, 'closed_personal',
                                 answer=True, next='public_and_open', number=3)
        response = self.classify(as_investigator, work_package, response, 'public_and_open',
                                 answer=True, next='include_commercial', number=4)
        response = self.classify(as_investigator, work_package, response, 'include_commercial',
                                 answer=False, next='open_publication', number=5)
        response = self.classify(as_investigator, work_package, response, 'open_publication',
                                 answer=True)

        self.check_results_page(
            response, work_package, as_investigator._user, 1,
            [
                ['open_generate_new', 'False'],
                ['closed_personal', 'True'],
                ['public_and_open', 'True'],
                ['include_commercial', 'False'],
                ['open_publication', 'True'],
            ]
        )

    def test_classify_jump_illegal(self, classified_work_package, as_investigator):
        insert_initial_questions(ClassificationQuestion, ClassificationGuidance)
        work_package = classified_work_package(None)

        response = as_investigator.get(self.url(work_package), follow=True)
        response = self.classify(as_investigator, work_package, response, 'open_generate_new',
                                 answer=False, next='closed_personal')
        response = self.classify(as_investigator, work_package, response, 'closed_personal',
                                 back='open_publication', next='open_publication',
                                 validate_goto=False)
        response = self.classify(as_investigator, work_package, response, 'open_publication',
                                 answer=True)

        assert [m.message for m in response.context['messages']] == [
            'An error occurred storing the results of your classification.'
        ]

    def test_classify_guidance(self, classified_work_package, as_investigator):
        insert_initial_questions(ClassificationQuestion, ClassificationGuidance)
        work_package = classified_work_package(None)

        response = as_investigator.get(self.url(work_package), follow=True)
        assert 'question' in response.context
        assert response.context['question'].name == 'open_generate_new'
        assert response.context['explanation'].name == 'open_generate_new'
        guidance = ['personal_data', 'living_individual']
        assert [g.name for g in response.context['guidance']] == guidance

        response = self.classify(as_investigator, work_package, response, 'open_generate_new',
                                 answer=False, next='closed_personal',
                                 guidance=['personal_data', 'living_individual'])
        response = self.classify(as_investigator, work_package, response, 'closed_personal',
                                 answer=True, next='public_and_open',
                                 guidance=['personal_data', 'living_individual'])
        response = self.classify(as_investigator, work_package, response, 'public_and_open',
                                 answer=False, next='no_reidentify',
                                 guidance=['personal_data', 'pseudonymized_data',
                                           'living_individual'])
        response = self.classify(as_investigator, work_package, response, 'no_reidentify',
                                 answer=False, next='substantial_threat')
        response = self.classify(as_investigator, work_package, response, 'substantial_threat',
                                 answer=True)

        self.check_results_page(
            response, work_package, as_investigator._user, 4,
            [
                ['open_generate_new', 'False'],
                ['closed_personal', 'True'],
                ['public_and_open', 'False'],
                ['no_reidentify', 'False'],
                ['substantial_threat', 'True'],
            ]
        )

    def test_classify_simultaneous(self, classified_work_package, as_investigator):
        insert_initial_questions(ClassificationQuestion, ClassificationGuidance)
        work_package_1 = classified_work_package(None)
        work_package_2 = classified_work_package(None)

        response_1 = as_investigator.get(self.url(work_package_1), follow=True)
        response_2 = as_investigator.get(self.url(work_package_2), follow=True)

        response_1 = self.classify(as_investigator, work_package_1, response_1, 'open_generate_new',
                                   answer=True, next='substantial_threat')
        response_2 = self.classify(as_investigator, work_package_2, response_2, 'open_generate_new',
                                   answer=False, next='closed_personal')
        response_2 = self.classify(as_investigator, work_package_2, response_2, 'closed_personal',
                                   answer=True, next='public_and_open')
        response_2 = self.classify(as_investigator, work_package_2, response_2, 'public_and_open',
                                   answer=False, next='no_reidentify')
        response_1 = self.classify(as_investigator, work_package_1, response_1,
                                   'substantial_threat', answer=True)
        response_2 = self.classify(as_investigator, work_package_2, response_2, 'no_reidentify',
                                   answer=False, next='substantial_threat')
        response_2 = self.classify(as_investigator, work_package_2, response_2,
                                   'substantial_threat', answer=True)

        self.check_results_page(
            response_1, work_package_1, as_investigator._user, 4,
            [
                ['open_generate_new', 'True'],
                ['substantial_threat', 'True'],
            ]
        )

        self.check_results_page(
            response_2, work_package_2, as_investigator._user, 4,
            [
                ['open_generate_new', 'False'],
                ['closed_personal', 'True'],
                ['public_and_open', 'False'],
                ['no_reidentify', 'False'],
                ['substantial_threat', 'True'],
            ]
        )

    def test_modify_classification_from_start(self, classified_work_package, as_investigator):
        insert_initial_questions(ClassificationQuestion, ClassificationGuidance)
        work_package = classified_work_package(None)

        response = as_investigator.get(self.url(work_package), follow=True)
        response = self.classify(as_investigator, work_package, response, 'open_generate_new',
                                 answer=True, next='substantial_threat')
        response = self.classify(as_investigator, work_package, response, 'substantial_threat',
                                 answer=True)

        self.check_results_page(
            response, work_package, as_investigator._user, 4,
            [
                ['open_generate_new', 'True'],
                ['substantial_threat', 'True'],
            ]
        )

        response = as_investigator.get(self.url(work_package, page='classify?modify=1'),
                                       follow=True)

        assert 'question' in response.context
        assert [m.message for m in response.context['messages']] == []
        assert response.context['question_number'] == 1

        response = self.classify(as_investigator, work_package, response, 'open_generate_new',
                                 answer=True, next='substantial_threat', number=2)
        assert [m.message for m in response.context['messages']] == []
        response = self.classify(as_investigator, work_package, response, 'substantial_threat',
                                 answer=False)
        assert [m.message for m in response.context['messages']] == []

        self.check_results_page(
            response, work_package, as_investigator._user, 3,
            [
                ['open_generate_new', 'True'],
                ['substantial_threat', 'False'],
            ]
        )

    def test_modify_classification(self, classified_work_package, as_investigator):
        insert_initial_questions(ClassificationQuestion, ClassificationGuidance)
        work_package = classified_work_package(None)

        response = as_investigator.get(self.url(work_package), follow=True)
        response = self.classify(as_investigator, work_package, response, 'open_generate_new',
                                 answer=True, next='substantial_threat')
        response = self.classify(as_investigator, work_package, response, 'substantial_threat',
                                 answer=True)

        self.check_results_page(
            response, work_package, as_investigator._user, 4,
            [
                ['open_generate_new', 'True'],
                ['substantial_threat', 'True'],
            ]
        )

        pk = ClassificationQuestion.objects.get(name='substantial_threat').pk
        response = as_investigator.get(self.url(work_package, page=f"classify/{pk}?modify=1"),
                                       follow=True)

        assert 'question' in response.context
        assert [m.message for m in response.context['messages']] == []
        assert response.context['question_number'] == 2

        response = self.classify(as_investigator, work_package, response, 'substantial_threat',
                                 answer=False)
        assert [m.message for m in response.context['messages']] == []

        self.check_results_page(
            response, work_package, as_investigator._user, 3,
            [
                ['open_generate_new', 'True'],
                ['substantial_threat', 'False'],
            ]
        )

    def test_modify_classification_back(self, classified_work_package, as_investigator):
        insert_initial_questions(ClassificationQuestion, ClassificationGuidance)
        work_package = classified_work_package(None)

        response = as_investigator.get(self.url(work_package), follow=True)
        response = self.classify(as_investigator, work_package, response, 'open_generate_new',
                                 answer=False, next='closed_personal')
        response = self.classify(as_investigator, work_package, response, 'closed_personal',
                                 answer=False, next='include_commercial')
        response = self.classify(as_investigator, work_package, response, 'include_commercial',
                                 answer=False, next='open_publication')
        response = self.classify(as_investigator, work_package, response, 'open_publication',
                                 answer=True)

        self.check_results_page(
            response, work_package, as_investigator._user, 1,
            [
                ['open_generate_new', 'False'],
                ['closed_personal', 'False'],
                ['include_commercial', 'False'],
                ['open_publication', 'True'],
            ]
        )

        pk = ClassificationQuestion.objects.get(name='include_commercial').pk
        response = as_investigator.get(self.url(work_package, page=f"classify/{pk}?modify=1"),
                                       follow=True)

        assert 'question' in response.context
        assert [m.message for m in response.context['messages']] == []
        assert response.context['question_number'] == 3

        response = self.classify(as_investigator, work_package, response, 'include_commercial',
                                 back='closed_personal', next='closed_personal', number=2)
        response = self.classify(as_investigator, work_package, response, 'closed_personal',
                                 answer=True, next='public_and_open', number=3)
        response = self.classify(as_investigator, work_package, response, 'public_and_open',
                                 start='open_generate_new', next='open_generate_new', number=1)
        response = self.classify(as_investigator, work_package, response, 'open_generate_new',
                                 answer=True, next='substantial_threat', number=2)
        response = self.classify(as_investigator, work_package, response, 'substantial_threat',
                                 answer=True)
        assert [m.message for m in response.context['messages']] == []

        self.check_results_page(
            response, work_package, as_investigator._user, 4,
            [
                ['open_generate_new', 'True'],
                ['substantial_threat', 'True'],
            ]
        )

    def test_modify_classification_unanswered(self, classified_work_package, as_investigator):
        insert_initial_questions(ClassificationQuestion, ClassificationGuidance)
        work_package = classified_work_package(None)

        response = as_investigator.get(self.url(work_package), follow=True)
        response = self.classify(as_investigator, work_package, response, 'open_generate_new',
                                 answer=True, next='substantial_threat')
        response = self.classify(as_investigator, work_package, response, 'substantial_threat',
                                 answer=True)

        self.check_results_page(
            response, work_package, as_investigator._user, 4,
            [
                ['open_generate_new', 'True'],
                ['substantial_threat', 'True'],
            ]
        )

        pk = ClassificationQuestion.objects.get(name='closed_personal').pk
        response = as_investigator.get(self.url(work_package, page=f"classify/{pk}?modify=1"),
                                       follow=True)

        assert 'question' in response.context
        assert [m.message for m in response.context['messages']] == [
            'Recorded answers could not be retrieved. Please begin the classification process '
            'from the question below.'
        ]

        response = self.classify(as_investigator, work_package, response, 'open_generate_new',
                                 answer=False, next='closed_personal')
        response = self.classify(as_investigator, work_package, response, 'closed_personal',
                                 answer=True, next='public_and_open')
        response = self.classify(as_investigator, work_package, response, 'public_and_open',
                                 answer=False, next='no_reidentify')
        response = self.classify(as_investigator, work_package, response, 'no_reidentify',
                                 answer=False, next='substantial_threat')
        response = self.classify(as_investigator, work_package, response, 'substantial_threat',
                                 answer=False)
        assert [m.message for m in response.context['messages']] == []

        self.check_results_page(
            response, work_package, as_investigator._user, 3,
            [
                ['open_generate_new', 'False'],
                ['closed_personal', 'True'],
                ['public_and_open', 'False'],
                ['no_reidentify', 'False'],
                ['substantial_threat', 'False'],
            ]
        )

    def test_modify_classification_question_changed(self, classified_work_package, as_investigator):
        insert_initial_questions(ClassificationQuestion, ClassificationGuidance)
        work_package = classified_work_package(None)

        response = as_investigator.get(self.url(work_package), follow=True)
        response = self.classify(as_investigator, work_package, response, 'open_generate_new',
                                 answer=False, next='closed_personal')
        response = self.classify(as_investigator, work_package, response, 'closed_personal',
                                 answer=True, next='public_and_open')
        response = self.classify(as_investigator, work_package, response, 'public_and_open',
                                 answer=False, next='no_reidentify')
        response = self.classify(as_investigator, work_package, response, 'no_reidentify',
                                 answer=False, next='substantial_threat')
        response = self.classify(as_investigator, work_package, response, 'substantial_threat',
                                 answer=True)

        self.check_results_page(
            response, work_package, as_investigator._user, 4,
            [
                ['open_generate_new', 'False'],
                ['closed_personal', 'True'],
                ['public_and_open', 'False'],
                ['no_reidentify', 'False'],
                ['substantial_threat', 'True'],
            ]
        )

        q = ClassificationQuestion.objects.get(name='closed_personal')
        q.question = q.question + ' (Changed)'
        q.save()

        pk = ClassificationQuestion.objects.get(name='public_and_open').pk
        response = as_investigator.get(self.url(work_package, page=f"classify/{pk}?modify=1"),
                                       follow=True)

        assert 'question' in response.context
        assert [m.message for m in response.context['messages']] == [
            'Some recorded answers could not be retrieved. Please begin the classification '
            'process from the question below.'
        ]

        response = self.classify(as_investigator, work_package, response, 'closed_personal',
                                 answer=True, next='public_and_open')
        response = self.classify(as_investigator, work_package, response, 'public_and_open',
                                 answer=True, next='include_commercial')
        response = self.classify(as_investigator, work_package, response, 'include_commercial',
                                 answer=False, next='open_publication')
        response = self.classify(as_investigator, work_package, response, 'open_publication',
                                 answer=True)
        assert [m.message for m in response.context['messages']] == []

        self.check_results_page(
            response, work_package, as_investigator._user, 1,
            [
                ['open_generate_new', 'False'],
                ['closed_personal', 'True'],
                ['public_and_open', 'True'],
                ['include_commercial', 'False'],
                ['open_publication', 'True'],
            ]
        )

    def test_modify_classification_abandoned(self, classified_work_package, as_investigator):
        insert_initial_questions(ClassificationQuestion, ClassificationGuidance)
        work_package = classified_work_package(None)

        response = as_investigator.get(self.url(work_package), follow=True)
        response = self.classify(as_investigator, work_package, response, 'open_generate_new',
                                 answer=False, next='closed_personal')
        response = self.classify(as_investigator, work_package, response, 'closed_personal',
                                 answer=False, next='include_commercial')
        response = self.classify(as_investigator, work_package, response, 'include_commercial',
                                 answer=False, next='open_publication')
        response = self.classify(as_investigator, work_package, response, 'open_publication',
                                 answer=True)

        self.check_results_page(
            response, work_package, as_investigator._user, 1,
            [
                ['open_generate_new', 'False'],
                ['closed_personal', 'False'],
                ['include_commercial', 'False'],
                ['open_publication', 'True'],
            ]
        )

        pk = ClassificationQuestion.objects.get(name='open_generate_new').pk
        response = as_investigator.get(self.url(work_package, page=f"classify/{pk}?modify=1"),
                                       follow=True)

        assert 'question' in response.context
        assert [m.message for m in response.context['messages']] == []
        assert response.context['question_number'] == 1

        pk = ClassificationQuestion.objects.get(name='include_commercial').pk
        response = as_investigator.get(self.url(work_package, page=f"classify/{pk}?modify=1"),
                                       follow=True)

        assert 'question' in response.context
        assert [m.message for m in response.context['messages']] == []
        assert response.context['question_number'] == 3

        response = self.classify(as_investigator, work_package, response, 'include_commercial',
                                 answer=True, next='financial_low', number=4)
        response = self.classify(as_investigator, work_package, response, 'financial_low',
                                 answer=True, next='publishable', number=5)
        response = self.classify(as_investigator, work_package, response, 'publishable',
                                 answer=True)
        assert [m.message for m in response.context['messages']] == []

        self.check_results_page(
            response, work_package, as_investigator._user, 1,
            [
                ['open_generate_new', 'False'],
                ['closed_personal', 'False'],
                ['include_commercial', 'True'],
                ['financial_low', 'True'],
                ['publishable', 'True'],
            ]
        )


@pytest.mark.django_db
class TestWorkPackageClassifyResults:
    def url(self, work_package, page='classify_results'):
        return '/projects/%d/work_packages/%d/%s' % (work_package.project.id, work_package.id, page)

    def test_returns_403_for_researcher(self, client, researcher):
        work_package = recipes.work_package.make(project=researcher.project)
        client.force_login(researcher.user)

        response = client.get(self.url(work_package))
        assert response.status_code == 403

    def test_view_as_project_manager(self, client, classified_work_package, programme_manager):
        insert_initial_questions(ClassificationQuestion, ClassificationGuidance)
        project_manager = recipes.user.make()
        investigator = recipes.user.make()

        work_package = classified_work_package(None)
        work_package.project.add_user(project_manager, ProjectRole.PROJECT_MANAGER.value,
                                      creator=programme_manager)
        work_package.project.add_user(investigator, ProjectRole.INVESTIGATOR.value,
                                      creator=programme_manager)

        client.force_login(project_manager)

        response = client.get(self.url(work_package))
        assert response.status_code == 200
        assert response.context['classification'] is None
        assert 'questions_table' not in response.context

        questions = [
            [ClassificationQuestion.objects.get(name='open_generate_new'), 'False'],
            [ClassificationQuestion.objects.get(name='closed_personal'), 'False'],
            [ClassificationQuestion.objects.get(name='include_commercial'), 'False'],
            [ClassificationQuestion.objects.get(name='publishable'), 'True'],
        ]
        work_package.classify_as(0, investigator, questions)

        response = client.get(self.url(work_package))
        assert response.status_code == 200
        assert response.context['classification'] is None

        table = list(response.context['questions_table'].as_values())
        assert len(table) == len(questions) + 1

        def question(question):
            return bleach.clean(question.question, tags=[], strip=True)

        assert table[0] == ['Question', investigator.username]
        assert table[1:] == [[question(q[0]), q[1]] for q in questions]


@pytest.mark.django_db
class TestAutocompleteNewParticipant:
    def test_visit(self, as_programme_manager):

        user0 = as_programme_manager._user
        project = recipes.project.make(created_by=user0)

        # Create some test users
        user1 = User.objects.create_user(
            first_name='Katherine',
            last_name='Johnson',
            username='kathyjohnson@example.com',
        )
        user2 = User.objects.create_user(
            first_name='Dorothy',
            last_name='Vaughan',
            username='dorothyvaughan@example.com',
        )
        user3 = User.objects.create_user(
            first_name='Mary',
            last_name='Jackson',
            username='mj@example.com',
        )
        user4 = User.objects.create_user(
            first_name='Margaret',
            last_name='Hamilton',
            username='mham@example.com',
        )
        user5 = User.objects.create_user(
            first_name='Judith',
            last_name='Cohen',
            username='jcohen@example.com',
        )

        def assert_autocomplete_result(query_string, expected_users):
            response = as_programme_manager.get(
                f'/projects/{project.id}/autocomplete_new_participant/?q={query_string}')
            assert response.status_code == 200
            output = json.loads(response.content.decode('UTF-8'))
            output_set = {d['text'] for d in output['results']}

            expected_set = {u.display_name() for u in expected_users}
            assert expected_set == output_set

        # Test all users returned with no query string
        assert_autocomplete_result('', {user0, user1, user2, user3, user4, user5})

        # Test various combinations
        assert_autocomplete_result('d', {user0, user2, user5})
        assert_autocomplete_result('Mar', {user3, user4})
        assert_autocomplete_result('Mart', {})
        assert_autocomplete_result('Cohen', {user5})
        assert_autocomplete_result('mj@exampl', {user3})
        assert_autocomplete_result('j@example.', {user3})
        assert_autocomplete_result('example.com', {user0, user1, user2, user3, user4, user5})
        assert_autocomplete_result('Dor Va', {user2})
        assert_autocomplete_result('Dor Va example', {user2})
        assert_autocomplete_result('Dott Va', {})
        assert_autocomplete_result('K Johnson', {user1})
        assert_autocomplete_result('D Vaughan', {user2})
        assert_autocomplete_result('M Jackson', {user3})
        assert_autocomplete_result('M Hamilton', {user4})
        assert_autocomplete_result('J Cohen', {user5})
        assert_autocomplete_result('son', {user1, user3})

        # Test last names
        assert_autocomplete_result('Johnson', {user1})
        assert_autocomplete_result('Vaughan', {user2})
        assert_autocomplete_result('Jackson', {user3})
        assert_autocomplete_result('Hamilton', {user4})
        assert_autocomplete_result('Cohen', {user5})

        # Test first names
        assert_autocomplete_result('Katherine', {user1})
        assert_autocomplete_result('Dorothy', {user2})
        assert_autocomplete_result('Mary', {user3})
        assert_autocomplete_result('Margaret', {user4})
        assert_autocomplete_result('Judith', {user5})

        # Test full names
        assert_autocomplete_result('Katherine Johnson', {user1})
        assert_autocomplete_result('Dorothy Vaughan', {user2})
        assert_autocomplete_result('Mary Jackson', {user3})
        assert_autocomplete_result('Margaret Hamilton', {user4})
        assert_autocomplete_result('Judith Cohen', {user5})

        # Test emails
        assert_autocomplete_result('coordinator@example.com', {user0})
        assert_autocomplete_result('kathyjohnson@example.com', {user1})
        assert_autocomplete_result('dorothyvaughan@example.com', {user2})
        assert_autocomplete_result('mj@example.com', {user3})
        assert_autocomplete_result('mham@example.com', {user4})
        assert_autocomplete_result('jcohen@example.com', {user5})

        # Check autocomplete does not return users who are already in a project
        project.add_user(user=user1,
                         role=ProjectRole.RESEARCHER.value,
                         creator=user0)
        assert_autocomplete_result('', {user0, user2, user3, user4, user5})
        assert_autocomplete_result('K Johnson', {})
        assert_autocomplete_result('son', {user3})


@pytest.mark.django_db
class TestAutocompleteDPR:
    def assert_autocomplete_result(self, as_user, project, query_string,
                                   expected_dprs, expected_users):
        response = as_user.get(
            f'/projects/{project.id}/autocomplete_dpr/?q={query_string}')
        assert response.status_code == 200
        output = json.loads(response.content.decode('UTF-8'))

        if expected_dprs:
            group = output['results'][0]
            assert group['text'] == 'Data Provider Representatives'
            output_set = {d['text'] for d in group['children']}

            expected_set = {u.display_name() for u in expected_dprs}
            assert expected_set == output_set
        else:
            assert len(output['results']) == 0 or output['results'][0]['text'] == 'Other users'

        if expected_users:
            group = output['results'][-1]
            assert group['text'] == 'Other users'
            output_set = {d['text'] for d in group['children']}

            expected_set = {u.display_name() for u in expected_users}
            assert expected_set == output_set
        else:
            assert (len(output['results']) == 0
                    or output['results'][-1]['text'] == 'Data Provider Representatives')

    def test_visit(self, as_programme_manager):

        user0 = as_programme_manager._user
        project = recipes.project.make(created_by=user0)

        # Create some test users
        user1 = User.objects.create_user(
            first_name='Katherine',
            last_name='Johnson',
            username='kathyjohnson@example.com',
        )
        user2 = User.objects.create_user(
            first_name='Dorothy',
            last_name='Vaughan',
            username='dorothyvaughan@example.com',
        )
        user3 = User.objects.create_user(
            first_name='Mary',
            last_name='Jackson',
            username='mj@example.com',
        )
        user4 = User.objects.create_user(
            first_name='Margaret',
            last_name='Hamilton',
            username='mham@example.com',
        )
        user5 = User.objects.create_user(
            first_name='Judith',
            last_name='Cohen',
            username='jcohen@example.com',
        )

        # Test all users returned with no query string
        self.assert_autocomplete_result(
            as_programme_manager, project, '', {},
            {user0, user1, user2, user3, user4, user5})
        self.assert_autocomplete_result(as_programme_manager, project, 'K Johnson', {}, {user1})
        self.assert_autocomplete_result(as_programme_manager, project, 'son', {}, {user1, user3})

        # Check autocomplete does not return users who are already in a project
        project.add_user(user=user1,
                         role=ProjectRole.RESEARCHER.value,
                         creator=user0)
        project.add_user(user=user3,
                         role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value,
                         creator=user0)
        self.assert_autocomplete_result(
            as_programme_manager, project, '', {user3},
            {user0, user2, user4, user5})
        self.assert_autocomplete_result(as_programme_manager, project, 'K Johnson', {}, {})
        self.assert_autocomplete_result(as_programme_manager, project, 'son', {user3}, {})

    def test_visit_as_pm(self, as_project_participant):

        user0 = as_project_participant._user
        project = recipes.project.make(created_by=user0)

        # Create some test users
        user1 = User.objects.create_user(
            first_name='Katherine',
            last_name='Johnson',
            username='kathyjohnson@example.com',
        )
        User.objects.create_user(
            first_name='Dorothy',
            last_name='Vaughan',
            username='dorothyvaughan@example.com',
        )
        user3 = User.objects.create_user(
            first_name='Mary',
            last_name='Jackson',
            username='mj@example.com',
        )
        User.objects.create_user(
            first_name='Margaret',
            last_name='Hamilton',
            username='mham@example.com',
        )
        User.objects.create_user(
            first_name='Judith',
            last_name='Cohen',
            username='jcohen@example.com',
        )

        # Test all users returned with no query string
        self.assert_autocomplete_result(as_project_participant, project, '', {}, {})
        self.assert_autocomplete_result(as_project_participant, project, 'K Johnson', {}, {})
        self.assert_autocomplete_result(as_project_participant, project, 'son', {}, {})

        # Check autocomplete does not return users who are already in a project
        project.add_user(user=user1,
                         role=ProjectRole.RESEARCHER.value,
                         creator=user0)
        project.add_user(user=user3,
                         role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value,
                         creator=user0)
        self.assert_autocomplete_result(as_project_participant, project, '', {user3}, {})
        self.assert_autocomplete_result(as_project_participant, project, 'K Johnson', {}, {})
        self.assert_autocomplete_result(as_project_participant, project, 'son', {user3}, {})
