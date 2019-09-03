import json

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
        })

        assert response.status_code == 302
        assert response.url == '/projects/%d/participants/' % project.id

        assert project.participant_set.count() == 1
        assert project.participant_set.first().user.username == project_participant.username

    def test_cancel_add_new_user_to_project(self, as_programme_manager, project_participant):

        project = recipes.project.make(created_by=as_programme_manager._user)
        response = as_programme_manager.post('/projects/%d/participants/add' % project.id, {
            'role': ProjectRole.RESEARCHER.value,
            'user': project_participant.pk,
            'cancel': 'Cancel',
        })

        assert response.status_code == 302
        assert response.url == '/projects/%d/participants/' % project.id

        assert project.participant_set.count() == 0

    def test_add_user_without_domain_to_project(self, as_programme_manager):
        """Check that domain will not be added to entered username if the username exists as it is"""

        project = recipes.project.make(created_by=as_programme_manager._user)

        new_user = User.objects.create_user(username='newuser')
        response = as_programme_manager.post('/projects/%d/participants/add' % project.id, {
            'role': ProjectRole.RESEARCHER.value,
            'user': new_user.pk,
        })

        assert response.status_code == 302
        assert response.url == '/projects/%d/participants/' % project.id

        assert project.participant_set.count() == 1
        assert project.participant_set.first().user.username == 'newuser'

    def test_cannot_add_existing_user_to_project(self, as_programme_manager, project_participant):
        project = recipes.project.make(created_by=as_programme_manager._user)

        project.add_user(project_participant, ProjectRole.RESEARCHER, as_programme_manager._user)
        assert project.participant_set.count() == 1

        response = as_programme_manager.post('/projects/%d/participants/add' % project.id, {
            'role': ProjectRole.RESEARCHER.value,
            'user': project_participant.pk,
        })

        assert response.status_code == 200
        assert response.context['project'] == project
        assert project.participant_set.count() == 1

    def test_cannot_add_nonexisting_user_to_project(self, as_programme_manager):
        project = recipes.project.make(created_by=as_programme_manager._user)

        response = as_programme_manager.post('/projects/%d/participants/add' % project.id, {
            'role': ProjectRole.RESEARCHER.value,
            'user': 12345,
        })

        assert response.status_code == 200
        assert response.context['project'] == project

        assert project.participant_set.count() == 0

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

        assert project.projectdataset_set.first().representative == user1

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

        response = as_project_participant.get(self.url(work_package))
        assert response.status_code == 200
        assert response.context['work_package'] == work_package
        assert 'wizard' in response.context

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

        response = as_investigator.get(self.url(work_package))

        assert 'wizard' not in response.context

    def test_delete_classification(self, classified_work_package, as_investigator):
        insert_initial_questions(ClassificationQuestion, ClassificationGuidance)
        work_package = classified_work_package(None)

        work_package.classify_as(0, as_investigator._user)

        response = as_investigator.get(self.url(work_package))
        assert b'Delete My Classification' in response.content

        response = as_investigator.get(self.url(work_package, 'classify_delete'))
        assert b'Delete Classification' in response.content

        response = as_investigator.post(self.url(work_package, 'classify_delete'))

        response = as_investigator.get(self.url(work_package))
        assert 'wizard' in response.context
        assert b'Delete My Classification' not in response.content

    def test_classify_as_tier(self, classified_work_package, as_investigator):
        insert_initial_questions(ClassificationQuestion, ClassificationGuidance)
        work_package = classified_work_package(None)

        def classify(current, answer, next):
            data = {}
            data['work_package_classify_data-current_step'] = current
            if answer:
                data[f"{current}-question"] = 'on'
            response = as_investigator.post(self.url(work_package), data)
            if next:
                assert 'wizard' in response.context
                assert response.context['wizard']['steps'].current == next
            return response

        response = classify('open_generate_new', False, 'closed_personal')
        response = classify('closed_personal', True, 'public_and_open')
        response = classify('public_and_open', False, 'no_reidentify')
        response = classify('no_reidentify', True, 'no_reidentify_absolute')
        response = classify('no_reidentify_absolute', False, 'no_reidentify_strong')
        response = classify('no_reidentify_strong', True, 'include_commercial_personal')
        response = classify('include_commercial_personal', True, 'financial_low_personal')
        response = classify('financial_low_personal', False, 'sophisticated_attack')
        response = classify('sophisticated_attack', False, None)

        assert response.status_code == 200
        assert response.context['classification'].tier == 3
        assert work_package.classifications.get().tier == 3

    def test_classify_backwards(self, classified_work_package, as_investigator):
        insert_initial_questions(ClassificationQuestion, ClassificationGuidance)
        work_package = classified_work_package(None)

        def classify(current, answer, goto, next):
            data = {}
            data['work_package_classify_data-current_step'] = current
            if answer:
                data[f"{current}-question"] = 'on'
            if goto:
                data['wizard_goto_step'] = goto,
            response = as_investigator.post(self.url(work_package), data)
            if next:
                assert 'wizard' in response.context
                assert response.context['wizard']['steps'].current == next
            return response

        response = classify('open_generate_new', False, None, 'closed_personal')
        response = classify('closed_personal', True, None, 'public_and_open')
        response = classify('public_and_open', False, 'open_generate_new', 'open_generate_new')
        response = classify('open_generate_new', False, None, 'closed_personal')
        response = classify('closed_personal', False, None, 'include_commercial')
        response = classify('include_commercial', True, None, 'financial_low')
        response = classify('financial_low', False, 'include_commercial', 'include_commercial')
        response = classify('include_commercial', False, None, 'open_publication')
        response = classify('open_publication', True, None, None)

        assert response.status_code == 200
        assert response.context['classification'].tier == 1
        assert work_package.classifications.get().tier == 1

    def test_classify_guidance(self, classified_work_package, as_investigator):
        insert_initial_questions(ClassificationQuestion, ClassificationGuidance)
        work_package = classified_work_package(None)

        response = as_investigator.get(self.url(work_package))
        assert 'wizard' in response.context
        assert response.context['wizard']['steps'].current == 'open_generate_new'
        guidance = ['personal_data', 'living_individual']
        assert [g.name for g in response.context['guidance']] == guidance

        def classify(current, answer, next, guidance=None):
            data = {}
            data['work_package_classify_data-current_step'] = current
            if answer:
                data[f"{current}-question"] = 'on'
            response = as_investigator.post(self.url(work_package), data)
            if next:
                assert 'wizard' in response.context
                assert response.context['wizard']['steps'].current == next
            if guidance:
                assert [g.name for g in response.context['guidance']] == guidance
            return response

        response = classify('open_generate_new', False, 'closed_personal',
                            guidance=['personal_data', 'living_individual'])
        response = classify('closed_personal', True, 'public_and_open',
                            guidance=['personal_data', 'living_individual'])
        response = classify('public_and_open', False, 'no_reidentify',
                            guidance=['personal_data', 'pseudonymized_data', 'living_individual'])
        response = classify('no_reidentify', False, 'substantial_threat')
        response = classify('substantial_threat', True, None)

        assert response.status_code == 200
        assert response.context['classification'].tier == 4
        assert work_package.classifications.get().tier == 4


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
