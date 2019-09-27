import json

import bleach
import pytest

from core import recipes
from data.classification import insert_initial_questions
from data.models import ClassificationGuidance, ClassificationQuestion
from identity.models import User
from projects.models import Policy, PolicyAssignment, PolicyGroup, Project
from projects.policies import insert_initial_policies
from projects.roles import ProjectRole


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
            {'name': 'my project', 'description': 'a new project'},
        )

        assert response.status_code == 302
        assert response.url == '/projects/'

        project = Project.objects.get()
        assert project.name == 'my project'
        assert project.description == 'a new project'
        assert project.created_by == as_programme_manager._user


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

    def test_view_owned_project(self, as_programme_manager):
        project = recipes.project.make(created_by=as_programme_manager._user)

        response = as_programme_manager.get('/projects/%d/edit' % project.id)

        assert response.status_code == 200
        assert response.context['project'] == project

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
            'work_packages-TOTAL_FORMS': 1,
            'work_packages-MAX_NUM_FORMS': 1,
            'work_packages-MIN_NUM_FORMS': 0,
            'work_packages-INITIAL_FORMS': 0,
        })

        assert response.status_code == 302
        assert response.url == '/projects/%d/participants/' % project.id

        assert project.participants.count() == 1
        assert project.participants.first().user.username == project_participant.username

    def test_add_new_user_to_project_and_work_package(self, as_programme_manager,
                                                      project_participant):

        project = recipes.project.make(created_by=as_programme_manager._user)
        work_package = recipes.work_package.make(project=project,
                                                 created_by=as_programme_manager._user)
        response = as_programme_manager.post('/projects/%d/participants/add' % project.id, {
            'role': ProjectRole.RESEARCHER.value,
            'user': project_participant.pk,
            'work_packages-TOTAL_FORMS': 1,
            'work_packages-MAX_NUM_FORMS': 1,
            'work_packages-MIN_NUM_FORMS': 0,
            'work_packages-INITIAL_FORMS': 0,
            'work_packages-0-work_package': work_package.id,
        })

        assert response.status_code == 302
        assert response.url == '/projects/%d/participants/' % project.id

        participants = project.participants
        assert participants.count() == 1
        assert participants.first().user.username == project_participant.username

        participants = work_package.participants
        assert participants.count() == 1
        assert participants.first().user.username == project_participant.username

    def test_cancel_add_new_user_to_project(self, as_programme_manager, project_participant):

        project = recipes.project.make(created_by=as_programme_manager._user)
        response = as_programme_manager.post('/projects/%d/participants/add' % project.id, {
            'role': ProjectRole.RESEARCHER.value,
            'user': project_participant.pk,
            'work_packages-TOTAL_FORMS': 1,
            'work_packages-MAX_NUM_FORMS': 1,
            'work_packages-MIN_NUM_FORMS': 0,
            'work_packages-INITIAL_FORMS': 0,
            'cancel': 'Cancel',
        })

        assert response.status_code == 302
        assert response.url == '/projects/%d/participants/' % project.id

        assert project.participants.count() == 0

    def test_add_user_without_domain_to_project(self, as_programme_manager):
        """Check that domain will not be added to entered username if the username exists as it is"""

        project = recipes.project.make(created_by=as_programme_manager._user)

        new_user = User.objects.create_user(username='newuser')
        response = as_programme_manager.post('/projects/%d/participants/add' % project.id, {
            'role': ProjectRole.RESEARCHER.value,
            'user': new_user.pk,
            'work_packages-TOTAL_FORMS': 1,
            'work_packages-MAX_NUM_FORMS': 1,
            'work_packages-MIN_NUM_FORMS': 0,
            'work_packages-INITIAL_FORMS': 0,
        })

        assert response.status_code == 302
        assert response.url == '/projects/%d/participants/' % project.id

        assert project.participants.count() == 1
        assert project.participants.first().user.username == 'newuser'

    def test_cannot_add_existing_user_to_project(self, as_programme_manager, project_participant):
        project = recipes.project.make(created_by=as_programme_manager._user)

        project.add_user(project_participant, ProjectRole.RESEARCHER, as_programme_manager._user)
        assert project.participants.count() == 1

        response = as_programme_manager.post('/projects/%d/participants/add' % project.id, {
            'role': ProjectRole.RESEARCHER.value,
            'user': project_participant.pk,
            'work_packages-TOTAL_FORMS': 1,
            'work_packages-MAX_NUM_FORMS': 1,
            'work_packages-MIN_NUM_FORMS': 0,
            'work_packages-INITIAL_FORMS': 0,
        })

        assert response.status_code == 200
        assert response.context['project'] == project
        assert project.participants.count() == 1

    def test_cannot_add_nonexisting_user_to_project(self, as_programme_manager):
        project = recipes.project.make(created_by=as_programme_manager._user)

        response = as_programme_manager.post('/projects/%d/participants/add' % project.id, {
            'role': ProjectRole.RESEARCHER.value,
            'user': 12345,
            'work_packages-TOTAL_FORMS': 1,
            'work_packages-MAX_NUM_FORMS': 1,
            'work_packages-MIN_NUM_FORMS': 0,
            'work_packages-INITIAL_FORMS': 0,
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
class TestListParticipants:
    def test_anonymous_cannot_access_page(self, client, helpers):
        project = recipes.project.make()
        response = client.get('/projects/%d/participants/' % project.id)
        helpers.assert_login_redirect(response)

    def test_view_page(self, as_programme_manager):
        project = recipes.project.make(created_by=as_programme_manager._user)
        researcher = recipes.researcher.make(project=project)
        investigator = recipes.investigator.make(project=project)

        response = as_programme_manager.get('/projects/%d/participants/' % project.id)

        assert response.status_code == 200
        assert list(response.context['ordered_participants']) == [investigator, researcher]

    def test_returns_404_for_invisible_project(self, as_standard_user):
        project = recipes.project.make()

        # Programme manager shouldn't have visibility of this other project at all
        # so pretend it doesn't exist and raise a 404
        response = as_standard_user.get('/projects/%d/participants/' % project.id)
        assert response.status_code == 404

    def test_returns_403_for_unauthorised_user(self, client, researcher):
        client.force_login(researcher.user)

        response = client.get('/projects/%d/participants/' % researcher.project.id)
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
        work_package = recipes.work_package.make(project=project,
                                                 created_by=as_programme_manager._user)
        investigator = recipes.investigator.make(project=project)
        response = as_programme_manager.post(
            '/projects/%d/participants/%d/edit' % (project.id, investigator.id),
            {
                'role': ProjectRole.RESEARCHER.value,
                'work_packages-TOTAL_FORMS': 1,
                'work_packages-MAX_NUM_FORMS': 1,
                'work_packages-MIN_NUM_FORMS': 0,
                'work_packages-INITIAL_FORMS': 0,
                'work_packages-0-work_package': work_package.id,
            }
        )

        assert response.status_code == 302
        assert response.url == '/projects/%d/participants/' % project.id

        assert project.participants.count() == 1
        assert project.participants.first().user.username == investigator.user.username
        assert project.participants.first().role == ProjectRole.RESEARCHER.value

        participants = work_package.participants
        assert participants.count() == 1
        assert participants.first().user.username == investigator.user.username

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
class TestListDatasets:
    def test_anonymous_cannot_access_page(self, client, helpers):
        project = recipes.project.make()
        response = client.get('/projects/%d/datasets/' % project.id)
        helpers.assert_login_redirect(response)

    def test_view_page(self, as_programme_manager, user1):
        ds1, ds2 = recipes.dataset.make(_quantity=2)
        project = recipes.project.make(
            created_by=as_programme_manager._user,
        )
        project.add_user(user1, ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value,
                         as_programme_manager._user)
        project.add_dataset(ds1, user1, as_programme_manager._user)
        project.add_dataset(ds2, user1, as_programme_manager._user)

        response = as_programme_manager.get('/projects/%d/datasets/' % project.id)

        assert response.status_code == 200
        assert list(response.context['datasets']) == [ds1, ds2]

    def test_returns_404_for_invisible_project(self, as_standard_user):
        project = recipes.project.make()

        # Regular user shouldn't have visibility of this other project at all
        # so pretend it doesn't exist and raise a 404
        response = as_standard_user.get('/projects/%d/datasets/' % project.id)
        assert response.status_code == 404


@pytest.mark.django_db
class TestWorkPackageListDatasets:
    def test_view_page(self, as_programme_manager, user1):
        ds1, ds2 = recipes.dataset.make(_quantity=2)
        project = recipes.project.make(
            created_by=as_programme_manager._user,
        )
        project.add_user(user1, ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value,
                         as_programme_manager._user)
        work_package = recipes.work_package.make(project=project)
        project.add_dataset(ds1, user1, as_programme_manager._user)
        project.add_dataset(ds2, user1, as_programme_manager._user)
        work_package.add_dataset(ds1, as_programme_manager._user)
        work_package.add_dataset(ds2, as_programme_manager._user)

        response = as_programme_manager.get('/projects/%d/work_packages/%d/datasets/'
                                            % (project.id, work_package.id))

        assert response.status_code == 200
        assert list(response.context['datasets']) == [ds1, ds2]


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

    def test_view_page(self, as_data_provider_representative, referee, programme_manager):
        project = recipes.project.make(created_by=programme_manager)
        p1 = project.add_user(as_data_provider_representative._user,
                              ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value,
                              programme_manager)
        p2 = project.add_user(referee.user,
                              ProjectRole.REFEREE.value,
                              programme_manager)
        work_package = recipes.work_package.make(project=project)
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
class TestListWorkPackages:
    def test_anonymous_cannot_access_page(self, client, helpers):
        project = recipes.project.make()
        response = client.get('/projects/%d/work_packages/' % project.id)
        helpers.assert_login_redirect(response)

    def test_view_page(self, as_programme_manager):
        wp1, wp2 = recipes.work_package.make(_quantity=2)
        project = recipes.project.make(
            created_by=as_programme_manager._user,
        )
        project.work_packages.add(wp1, wp2)

        response = as_programme_manager.get('/projects/%d/work_packages/' % project.id)

        assert response.status_code == 200
        assert list(response.context['work_packages']) == [wp1, wp2]

    def test_returns_404_for_invisible_project(self, as_standard_user):
        project = recipes.project.make()

        # Programme manager shouldn't have visibility of this other project at all
        # so pretend it doesn't exist and raise a 404
        response = as_standard_user.get('/projects/%d/work_packages/' % project.id)
        assert response.status_code == 404


@pytest.mark.django_db
class TestWorkPackageClassifyData:
    def url(self, work_package, page='classify'):
        return '/projects/%d/work_packages/%d/%s' % (work_package.project.id, work_package.id, page)

    def classify(self, client, work_package, response, current,
                 answer=None, back=None, start=None,
                 validate_goto=True, next=None, guidance=None):
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
            if response.context['modify']:
                url += '?modify=1'
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

    def test_view_page(self, as_project_participant, programme_manager):
        insert_initial_questions(ClassificationQuestion, ClassificationGuidance)
        project = recipes.project.make(created_by=programme_manager)
        work_package = recipes.work_package.make(project=project)
        project.add_user(user=as_project_participant._user,
                         role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value,
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

    def test_do_not_show_form_if_user_already_classified(
            self, classified_work_package, as_investigator):
        work_package = classified_work_package(None)

        work_package.classify_as(0, as_investigator._user)

        response = as_investigator.get(self.url(work_package), follow=True)

        assert 'question' not in response.context
        assert [m.message for m in response.context['messages']] == [
            'You have already completed classification. Please delete your classification if you '
            'wish to change any answers.'
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
                                 answer=False, next='closed_personal')
        response = self.classify(as_investigator, work_package, response, 'closed_personal',
                                 answer=True, next='public_and_open')
        response = self.classify(as_investigator, work_package, response, 'public_and_open',
                                 answer=False, next='no_reidentify')
        response = self.classify(as_investigator, work_package, response, 'no_reidentify',
                                 answer=True, next='no_reidentify_absolute')
        response = self.classify(as_investigator, work_package, response, 'no_reidentify_absolute',
                                 answer=False, next='no_reidentify_strong')
        response = self.classify(as_investigator, work_package, response, 'no_reidentify_strong',
                                 answer=True, next='include_commercial_personal')
        response = self.classify(as_investigator, work_package, response,
                                 'include_commercial_personal', answer=True,
                                 next='financial_low_personal')
        response = self.classify(as_investigator, work_package, response, 'financial_low_personal',
                                 answer=False, next='sophisticated_attack')
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
                                 answer=False, next='closed_personal')
        response = self.classify(as_investigator, work_package, response, 'closed_personal',
                                 answer=True, next='public_and_open')
        response = self.classify(as_investigator, work_package, response, 'public_and_open',
                                 start='open_generate_new', next='open_generate_new')
        response = self.classify(as_investigator, work_package, response, 'open_generate_new',
                                 answer=False, next='closed_personal')
        response = self.classify(as_investigator, work_package, response, 'closed_personal',
                                 answer=False, next='include_commercial')
        response = self.classify(as_investigator, work_package, response, 'include_commercial',
                                 answer=True, next='financial_low')
        response = self.classify(as_investigator, work_package, response, 'financial_low',
                                 back='include_commercial', next='include_commercial')
        response = self.classify(as_investigator, work_package, response, 'include_commercial',
                                 back='closed_personal', next='closed_personal')
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

    def test_classify_jump_back(self, classified_work_package, as_investigator):
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
                                 back='closed_personal', next='closed_personal',
                                 validate_goto=False)
        response = self.classify(as_investigator, work_package, response, 'closed_personal',
                                 answer=True, next='public_and_open')
        response = self.classify(as_investigator, work_package, response, 'public_and_open',
                                 answer=True, next='include_commercial')
        response = self.classify(as_investigator, work_package, response, 'include_commercial',
                                 answer=False, next='open_publication')
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

        response = self.classify(as_investigator, work_package, response, 'open_generate_new',
                                 answer=True, next='substantial_threat')
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

        response = self.classify(as_investigator, work_package, response, 'include_commercial',
                                 back='closed_personal', next='closed_personal')
        response = self.classify(as_investigator, work_package, response, 'closed_personal',
                                 answer=True, next='public_and_open')
        response = self.classify(as_investigator, work_package, response, 'public_and_open',
                                 start='open_generate_new', next='open_generate_new')
        response = self.classify(as_investigator, work_package, response, 'open_generate_new',
                                 answer=True, next='substantial_threat')
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

@pytest.mark.django_db
class TestNewParticipantAutocomplete:
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
                f'/projects/{project.id}/new_participant_autocomplete/?q={query_string}')
            assert response.status_code == 200
            output = json.loads(response.content.decode('UTF-8'))
            output_set = {d['text'] for d in output['results']}

            expected_set = {f'{u.first_name}{" " if u.first_name and u.last_name else ""}{u.last_name}{": " if u.first_name or u.last_name else ""}{u.username}' for u in expected_users}
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
