import pytest

from core import recipes
from data.tiers import Tier
from identity.models import User
from identity.roles import UserRole
from projects.roles import ProjectRole


DUMMY_PASSWORD = 'password'


class Helpers:
    def assert_login_redirect(response):
        assert response.status_code == 302
        assert '/login/' in response.url


@pytest.fixture
def helpers():
    return Helpers


@pytest.fixture
def superuser():
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password=DUMMY_PASSWORD,
    )


@pytest.fixture
def system_manager():
    return User.objects.create_user(
        username='controller@example.com',
        email='controller@example.com',
        role=UserRole.SYSTEM_MANAGER.value,
        password=DUMMY_PASSWORD,
    )


@pytest.fixture
def programme_manager():
    return User.objects.create_user(
        username='coordinator@example.com',
        email='coordinator@example.com',
        role=UserRole.PROGRAMME_MANAGER.value,
        password=DUMMY_PASSWORD,
    )


@pytest.fixture
def project_participant():
    return User.objects.create_user(
        first_name='Angela',
        last_name='Zala',
        username='project_participant@example.com',
        email='project_participant@example.com',
        password=DUMMY_PASSWORD,
        role=UserRole.NONE.value,
        mobile='+441234567890'
    )


@pytest.fixture
def user1():
    return User.objects.create_user(
        username='user1@example.com',
        email='user@example.com',
        password=DUMMY_PASSWORD,
    )


@pytest.fixture
def data_provider_representative():
    return recipes.participant.make(role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value)


@pytest.fixture
def investigator():
    return recipes.participant.make(role=ProjectRole.INVESTIGATOR.value)


@pytest.fixture
def researcher():
    return recipes.participant.make(role=ProjectRole.RESEARCHER.value)


@pytest.fixture
def referee():
    return recipes.participant.make(role=ProjectRole.REFEREE.value)


def client_login(client, user):
    client.force_login(user)
    client._user = user
    return client


@pytest.fixture
def as_superuser(client, superuser):
    return client_login(client, superuser)


@pytest.fixture
def as_system_manager(client, system_manager):
    return client_login(client, system_manager)


@pytest.fixture
def as_programme_manager(client, programme_manager):
    return client_login(client, programme_manager)


@pytest.fixture
def as_data_provider_representative(client, data_provider_representative):
    return client_login(client, data_provider_representative)


@pytest.fixture
def as_project_participant(client, project_participant):
    return client_login(client, project_participant)


@pytest.fixture
def classified_project(programme_manager, investigator, data_provider_representative, referee):
    def _classified_project(tier):
        project = recipes.project.make(created_by=programme_manager)
        project.add_user(user=investigator.user,
                         role=ProjectRole.INVESTIGATOR.value,
                         creator=programme_manager)
        project.add_user(user=data_provider_representative.user,
                         role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value,
                         creator=programme_manager)
        project.classify_as(tier, investigator.user)
        project.classify_as(tier, data_provider_representative.user)
        if tier >= Tier.TWO:
            project.add_user(user=referee.user,
                             role=ProjectRole.REFEREE.value,
                             creator=programme_manager)
            project.classify_as(tier, referee.user)
        return project
    return _classified_project
