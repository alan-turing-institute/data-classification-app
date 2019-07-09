import pytest

from core import recipes
from data.classification import insert_initial_questions
from data.models import ClassificationQuestion
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

    def test_list_owned_projects(self, as_programme_manager, system_manager):
        my_project = recipes.project.make(created_by=as_programme_manager._user)
        recipes.project.make(created_by=system_manager)

        response = as_programme_manager.get('/projects/')

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

        assert list(response.context['projects']) == [my_project, other_project]


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

    def test_cannot_view_other_project(self, as_programme_manager):
        project = recipes.project.make()

        response = as_programme_manager.get('/projects/%d' % project.id)

        assert response.status_code == 404

    def test_view_as_system_manager(self, as_system_manager):
        project = recipes.project.make()

        response = as_system_manager.get('/projects/%d' % project.id)

        assert response.status_code == 200
        assert response.context['project'] == project


@pytest.mark.django_db
class TestViewWorkPackage:
    def test_view_work_package_policy_tier0(self, as_programme_manager, classified_work_package):
        insert_initial_policies(PolicyGroup, Policy, PolicyAssignment)
        work_package = classified_work_package(0)

        response = as_programme_manager.get('/projects/%d/work_packages/%d'
                                            % (work_package.project.id, work_package.id))

        assert response.status_code == 200
        table = list(response.context['table'].as_values())
        assert len(table) == 16
        assert table[0] == ['Policy', 'Description']
        assert table[1] == ['Tier', '0']

    def test_cannot_view_for_wrong_project(self, as_programme_manager, classified_work_package):
        wp1 = classified_work_package(0)
        wp2 = classified_work_package(0)

        response = as_programme_manager.get('/projects/%d/work_packages/%d'
                                            % (wp1.project.id, wp2.id))

        assert response.status_code == 404

    def test_cannot_view_other_project(self, as_programme_manager):
        project = recipes.project.make()
        work_package = recipes.work_package.make(project=project)

        response = as_programme_manager.get('/projects/%d/work_packages/%d'
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
            'username': project_participant.pk,
        })

        assert response.status_code == 302
        assert response.url == '/projects/%d/participants/' % project.id

        assert project.participant_set.count() == 1
        assert project.participant_set.first().user.username == project_participant.username

    def test_cancel_add_new_user_to_project(self, as_programme_manager, project_participant):

        project = recipes.project.make(created_by=as_programme_manager._user)
        response = as_programme_manager.post('/projects/%d/participants/add' % project.id, {
            'role': ProjectRole.RESEARCHER.value,
            'username': project_participant.pk,
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
            'username': new_user.pk,
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
            'username': project_participant.pk,
        })

        assert response.status_code == 200
        assert response.context['project'] == project
        assert project.participant_set.count() == 1

    def test_cannot_add_nonexisting_user_to_project(self, as_programme_manager):
        project = recipes.project.make(created_by=as_programme_manager._user)

        response = as_programme_manager.post('/projects/%d/participants/add' % project.id, {
            'role': ProjectRole.RESEARCHER.value,
            'username': 12345,
        })

        assert response.status_code == 200
        assert response.context['project'] == project

        assert project.participant_set.count() == 0

    def test_returns_404_for_invisible_project(self, as_programme_manager):
        project = recipes.project.make()

        # Programme manager shouldn't have visibility of this other project at all
        # so pretend it doesn't exist and raise a 404
        response = as_programme_manager.get('/projects/%d/participants/add' % project.id)
        assert response.status_code == 404

        response = as_programme_manager.post('/projects/%d/participants/add' % project.id)
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

    def test_returns_404_for_invisible_project(self, as_programme_manager):
        project = recipes.project.make()

        # Programme manager shouldn't have visibility of this other project at all
        # so pretend it doesn't exist and raise a 404
        response = as_programme_manager.get('/projects/%d/participants/' % project.id)
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

    def test_add_new_dataset_to_project(self, as_programme_manager):
        project = recipes.project.make(created_by=as_programme_manager._user)

        response = as_programme_manager.post('/projects/%d/datasets/new' % project.id, {
            'role': ProjectRole.RESEARCHER.value,
            'name': 'dataset 1',
            'description': 'Dataset One',
        })

        assert response.status_code == 302
        assert response.url == '/projects/%d' % project.id

        assert project.datasets.count() == 1
        assert project.datasets.first().name == 'dataset 1'
        assert project.datasets.first().description == 'Dataset One'

    def test_returns_404_for_invisible_project(self, as_programme_manager):
        project = recipes.project.make()

        # Programme manager shouldn't have visibility of this other project at all
        # so pretend it doesn't exist and raise a 404
        response = as_programme_manager.get('/projects/%d/datasets/new' % project.id)
        assert response.status_code == 404

        response = as_programme_manager.post('/projects/%d/datasets/new' % project.id)
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

    def test_view_page(self, as_programme_manager):
        ds1, ds2 = recipes.dataset.make(_quantity=2)
        project = recipes.project.make(
            created_by=as_programme_manager._user,
        )
        project.add_dataset(ds1, as_programme_manager._user)
        project.add_dataset(ds2, as_programme_manager._user)

        response = as_programme_manager.get('/projects/%d/datasets/' % project.id)

        assert response.status_code == 200
        assert list(response.context['datasets']) == [ds1, ds2]

    def test_returns_404_for_invisible_project(self, as_programme_manager):
        project = recipes.project.make()

        # Programme manager shouldn't have visibility of this other project at all
        # so pretend it doesn't exist and raise a 404
        response = as_programme_manager.get('/projects/%d/datasets/' % project.id)
        assert response.status_code == 404


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

    def test_returns_404_for_invisible_project(self, as_programme_manager):
        project = recipes.project.make()

        # Programme manager shouldn't have visibility of this other project at all
        # so pretend it doesn't exist and raise a 404
        response = as_programme_manager.get('/projects/%d/work_packages/new' % project.id)
        assert response.status_code == 404

        response = as_programme_manager.post('/projects/%d/work_packages/new' % project.id)
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

    def test_returns_404_for_invisible_project(self, as_programme_manager):
        project = recipes.project.make()

        # Programme manager shouldn't have visibility of this other project at all
        # so pretend it doesn't exist and raise a 404
        response = as_programme_manager.get('/projects/%d/work_packages/' % project.id)
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
        insert_initial_questions(ClassificationQuestion)
        project = recipes.project.make(created_by=programme_manager)
        work_package = recipes.work_package.make(project=project)
        project.add_user(user=as_project_participant._user,
                         role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value,
                         creator=programme_manager)

        response = as_project_participant.get(self.url(work_package))
        assert response.status_code == 200
        assert response.context['work_package'] == work_package
        assert 'wizard' in response.context

    def test_returns_404_for_invisible_project(self, as_programme_manager):
        project = recipes.project.make()
        work_package = recipes.work_package.make(project=project)

        # Programme manager shouldn't have visibility of this other project at all
        # so pretend it doesn't exist and raise a 404
        response = as_programme_manager.get(self.url(work_package))
        assert response.status_code == 404

        response = as_programme_manager.post(self.url(work_package))
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

    def test_do_not_show_form_if_user_already_classified(self, client, as_project_participant,
                                                         programme_manager):
        project = recipes.project.make(created_by=programme_manager)
        work_package = recipes.work_package.make(project=project)
        project.add_user(user=as_project_participant._user,
                         role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value,
                         creator=programme_manager)
        work_package.classify_as(0, as_project_participant._user)

        response = as_project_participant.get(self.url(work_package))

        assert 'wizard' not in response.context

    def test_delete_classification(self, client, as_project_participant, programme_manager):
        insert_initial_questions(ClassificationQuestion)
        project = recipes.project.make(created_by=programme_manager)
        work_package = recipes.work_package.make(project=project)
        project.add_user(user=as_project_participant._user,
                         role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value,
                         creator=programme_manager)
        work_package.classify_as(0, as_project_participant._user)

        response = as_project_participant.get(self.url(work_package))
        assert b'Delete My Classification' in response.content

        response = as_project_participant.get(self.url(work_package, 'classify_delete'))
        assert b'Delete Classification' in response.content

        response = as_project_participant.post(self.url(work_package, 'classify_delete'))

        response = as_project_participant.get(self.url(work_package))
        assert 'wizard' in response.context
        assert b'Delete My Classification' not in response.content

    def test_classify_as_tier_0(self, as_project_participant, programme_manager):
        insert_initial_questions(ClassificationQuestion)
        project = recipes.project.make(created_by=programme_manager)
        work_package = recipes.work_package.make(project=project)
        project.add_user(user=as_project_participant._user,
                         role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value,
                         creator=programme_manager)

        response = as_project_participant.post(self.url(work_package), {
            'public_and_open-question': 'on',
            'work_package_classify_data-current_step': 'public_and_open',
        })
        assert 'wizard' in response.context
        assert response.context['wizard']['steps'].current == 'open_identify_living'

        response = as_project_participant.post(self.url(work_package), {
            'work_package_classify_data-current_step': 'open_identify_living',
        })
        assert 'wizard' in response.context
        assert response.context['wizard']['steps'].current == 'open_publication'

        response = as_project_participant.post(self.url(work_package), {
            'open_publication-question': 'on',
            'work_package_classify_data-current_step': 'open_publication',
        })

        assert response.status_code == 200
        assert response.context['classification'].tier == 0
        assert work_package.classifications.get().tier == 0

    def test_classify_as_tier_1(self, as_project_participant, programme_manager):
        insert_initial_questions(ClassificationQuestion)
        project = recipes.project.make(created_by=programme_manager)
        work_package = recipes.work_package.make(project=project)
        project.add_user(user=as_project_participant._user,
                         role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value,
                         creator=programme_manager)

        response = as_project_participant.post(self.url(work_package), {
            'work_package_classify_data-current_step': 'public_and_open',
        })
        assert 'wizard' in response.context
        assert response.context['wizard']['steps'].current == 'publishable'

        response = as_project_participant.post(self.url(work_package), {
            'work_package_classify_data-current_step': 'publishable',
        })
        assert 'wizard' in response.context
        assert response.context['wizard']['steps'].current == 'closed_personal'

        response = as_project_participant.post(self.url(work_package), {
            'work_package_classify_data-current_step': 'closed_personal',
        })
        assert 'wizard' in response.context
        assert response.context['wizard']['steps'].current == 'include_commercial'

        response = as_project_participant.post(self.url(work_package), {
            'work_package_classify_data-current_step': 'include_commercial',
        })

        assert response.status_code == 200
        assert response.context['classification'].tier == 1
        assert work_package.classifications.get().tier == 1

    def test_classify_as_tier_2(self, as_project_participant, programme_manager):
        insert_initial_questions(ClassificationQuestion)
        project = recipes.project.make(created_by=programme_manager)
        work_package = recipes.work_package.make(project=project)
        project.add_user(user=as_project_participant._user,
                         role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value,
                         creator=programme_manager)

        response = as_project_participant.post(self.url(work_package), {
            'work_package_classify_data-current_step': 'public_and_open',
        })
        assert 'wizard' in response.context
        assert response.context['wizard']['steps'].current == 'publishable'

        response = as_project_participant.post(self.url(work_package), {
            'work_package_classify_data-current_step': 'publishable',
        })
        assert 'wizard' in response.context
        assert response.context['wizard']['steps'].current == 'closed_personal'

        response = as_project_participant.post(self.url(work_package), {
            'closed_personal-question': 'on',
            'work_package_classify_data-current_step': 'closed_personal',
        })
        assert 'wizard' in response.context
        assert response.context['wizard']['steps'].current == 'closed_identify_living'

        response = as_project_participant.post(self.url(work_package), {
            'work_package_classify_data-current_step': 'closed_identify_living',
        })
        assert 'wizard' in response.context
        assert response.context['wizard']['steps'].current == 'no_reidentify_absolute'

        response = as_project_participant.post(self.url(work_package), {
            'no_reidentify_absolute-question': 'on',
            'work_package_classify_data-current_step': 'no_reidentify_absolute',
        })
        assert 'wizard' in response.context
        assert response.context['wizard']['steps'].current == 'include_commercial'

        response = as_project_participant.post(self.url(work_package), {
            'include_commercial-question': 'on',
            'work_package_classify_data-current_step': 'include_commercial',
        })
        assert 'wizard' in response.context
        assert response.context['wizard']['steps'].current == 'financial_low'

        response = as_project_participant.post(self.url(work_package), {
            'financial_low-question': 'on',
            'work_package_classify_data-current_step': 'financial_low',
        })

        assert response.status_code == 200
        assert response.context['classification'].tier == 2
        assert work_package.classifications.get().tier == 2

    def test_classify_as_tier_3(self, as_project_participant, programme_manager):
        insert_initial_questions(ClassificationQuestion)
        project = recipes.project.make(created_by=programme_manager)
        work_package = recipes.work_package.make(project=project)
        project.add_user(user=as_project_participant._user,
                         role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value,
                         creator=programme_manager)

        response = as_project_participant.post(self.url(work_package), {
            'public_and_open-question': 'on',
            'work_package_classify_data-current_step': 'public_and_open',
        })
        assert 'wizard' in response.context
        assert response.context['wizard']['steps'].current == 'open_identify_living'

        response = as_project_participant.post(self.url(work_package), {
            'open_identify_living-question': 'on',
            'work_package_classify_data-current_step': 'open_identify_living',
        })
        assert 'wizard' in response.context
        assert response.context['wizard']['steps'].current == 'open_generate_new'

        response = as_project_participant.post(self.url(work_package), {
            'open_generate_new-question': 'on',
            'work_package_classify_data-current_step': 'open_generate_new',
        })
        assert 'wizard' in response.context
        assert response.context['wizard']['steps'].current == 'substantial_threat'

        response = as_project_participant.post(self.url(work_package), {
            'work_package_classify_data-current_step': 'substantial_threat',
        })

        assert response.status_code == 200
        assert response.context['classification'].tier == 3
        assert work_package.classifications.get().tier == 3

    def test_classify_as_tier_4(self, as_project_participant, programme_manager):
        insert_initial_questions(ClassificationQuestion)
        project = recipes.project.make(created_by=programme_manager)
        work_package = recipes.work_package.make(project=project)
        project.add_user(user=as_project_participant._user,
                         role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value,
                         creator=programme_manager)

        response = as_project_participant.post(self.url(work_package), {
            'work_package_classify_data-current_step': 'public_and_open',
        })
        assert 'wizard' in response.context
        assert response.context['wizard']['steps'].current == 'publishable'

        response = as_project_participant.post(self.url(work_package), {
            'work_package_classify_data-current_step': 'publishable',
        })
        assert 'wizard' in response.context
        assert response.context['wizard']['steps'].current == 'closed_personal'

        response = as_project_participant.post(self.url(work_package), {
            'work_package_classify_data-current_step': 'closed_personal',
        })
        assert 'wizard' in response.context
        assert response.context['wizard']['steps'].current == 'include_commercial'

        response = as_project_participant.post(self.url(work_package), {
            'include_commercial-question': 'on',
            'work_package_classify_data-current_step': 'include_commercial',
        })
        assert 'wizard' in response.context
        assert response.context['wizard']['steps'].current == 'financial_low'

        response = as_project_participant.post(self.url(work_package), {
            'work_package_classify_data-current_step': 'financial_low',
        })
        assert 'wizard' in response.context
        assert response.context['wizard']['steps'].current == 'sophisticated_attack'

        response = as_project_participant.post(self.url(work_package), {
            'sophisticated_attack-question': 'on',
            'work_package_classify_data-current_step': 'sophisticated_attack',
        })

        assert response.status_code == 200
        assert response.context['classification'].tier == 4
        assert work_package.classifications.get().tier == 4

    def test_classify_backwards(self, as_project_participant, programme_manager):
        insert_initial_questions(ClassificationQuestion)
        project = recipes.project.make(created_by=programme_manager)
        work_package = recipes.work_package.make(project=project)
        project.add_user(user=as_project_participant._user,
                         role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value,
                         creator=programme_manager)

        response = as_project_participant.post(self.url(work_package), {
            'public_and_open-question': 'on',
            'work_package_classify_data-current_step': 'public_and_open',
        })
        assert 'wizard' in response.context
        assert response.context['wizard']['steps'].current == 'open_identify_living'

        response = as_project_participant.post(self.url(work_package), {
            'open_identify_living-question': 'on',
            'work_package_classify_data-current_step': 'open_identify_living',
        })
        assert 'wizard' in response.context
        assert response.context['wizard']['steps'].current == 'open_generate_new'

        response = as_project_participant.post(self.url(work_package), {
            'wizard_goto_step': 'public_and_open',
            'work_package_classify_data-current_step': 'open_generate_new',
        })
        assert 'wizard' in response.context
        assert response.context['wizard']['steps'].current == 'public_and_open'

        response = as_project_participant.post(self.url(work_package), {
            'work_package_classify_data-current_step': 'public_and_open',
        })
        assert 'wizard' in response.context
        assert response.context['wizard']['steps'].current == 'publishable'

        response = as_project_participant.post(self.url(work_package), {
            'work_package_classify_data-current_step': 'publishable',
        })
        assert 'wizard' in response.context
        assert response.context['wizard']['steps'].current == 'closed_personal'

        response = as_project_participant.post(self.url(work_package), {
            'wizard_goto_step': 'publishable',
            'work_package_classify_data-current_step': 'closed_personal',
        })
        assert 'wizard' in response.context
        assert response.context['wizard']['steps'].current == 'publishable'

        response = as_project_participant.post(self.url(work_package), {
            'publishable-question': 'on',
            'work_package_classify_data-current_step': 'publishable',
        })
        assert 'wizard' in response.context
        assert response.context['wizard']['steps'].current == 'open_publication'

        response = as_project_participant.post(self.url(work_package), {
            'open_publication-question': 'on',
            'work_package_classify_data-current_step': 'open_publication',
        })

        assert response.status_code == 200
        assert response.context['classification'].tier == 0
        assert work_package.classifications.get().tier == 0
