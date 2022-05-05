import pytest
from django.db.models.deletion import ProtectedError

from haven.core import recipes
from haven.data.tiers import Tier
from haven.identity.models import User
from haven.identity.roles import UserRole
from haven.projects.roles import ProjectRole


DUMMY_PASSWORD = "password"


class Helpers:
    def assert_login_redirect(response):
        assert response.status_code == 302
        assert "/login/" in response.url


@pytest.fixture
def helpers():
    return Helpers


@pytest.fixture
def system_manager():
    return User.objects.create_user(
        first_name="System",
        last_name="Manager",
        username="controller@example.com",
        email="controller@example.com",
        role=UserRole.SYSTEM_MANAGER.value,
        password=DUMMY_PASSWORD,
        mobile="+441234567890",
    )


@pytest.fixture
def programme_manager():
    return User.objects.create_user(
        username="coordinator@example.com",
        email="coordinator@example.com",
        role=UserRole.PROGRAMME_MANAGER.value,
        password=DUMMY_PASSWORD,
    )


@pytest.fixture
def standard_user():
    return User.objects.create_user(
        username="user@example.com",
        email="user@example.com",
        role=UserRole.NONE.value,
        password=DUMMY_PASSWORD,
    )


@pytest.fixture
def project_participant():
    return User.objects.create_user(
        first_name="Angela",
        last_name="Zala",
        username="project_participant@example.com",
        email="project_participant@example.com",
        password=DUMMY_PASSWORD,
        role=UserRole.NONE.value,
        mobile="+441234567890",
    )


@pytest.fixture
def user1():
    return User.objects.create_user(
        username="user1@example.com",
        email="user@example.com",
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
def as_system_manager(client, system_manager):
    return client_login(client, system_manager)


@pytest.fixture
def as_programme_manager(client, programme_manager):
    return client_login(client, programme_manager)


@pytest.fixture
def as_standard_user(client, standard_user):
    return client_login(client, standard_user)


@pytest.fixture
def as_data_provider_representative(client, data_provider_representative):
    return client_login(client, data_provider_representative.user)


@pytest.fixture
def as_project_participant(client, project_participant):
    return client_login(client, project_participant)


@pytest.fixture
def as_investigator(client, investigator):
    return client_login(client, investigator.user)


@pytest.fixture
def classified_work_package(programme_manager, investigator, data_provider_representative, referee):
    def _classified_work_package(tier):
        project = recipes.project.make(created_by=programme_manager)
        work_package = recipes.work_package.make(project=project)
        dataset = recipes.dataset.make()

        project.add_user(
            user=investigator.user,
            role=ProjectRole.INVESTIGATOR.value,
            created_by=programme_manager,
        )
        project.add_user(
            user=data_provider_representative.user,
            role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value,
            created_by=programme_manager,
        )
        work_package.add_user(data_provider_representative.user, programme_manager)
        project.add_user(
            user=referee.user,
            role=ProjectRole.REFEREE.value,
            created_by=programme_manager,
        )
        work_package.add_user(referee.user, programme_manager)

        project.add_dataset(dataset, data_provider_representative.user, investigator.user)
        work_package.add_dataset(dataset, investigator.user)

        work_package.open_classification()
        if tier is not None:
            work_package.classify_as(tier, investigator.user)
            work_package.classify_as(tier, data_provider_representative.user)
            work_package.classify_as(tier, referee.user)
            if tier >= Tier.THREE:
                p = referee.user.get_participant(project)
                p = p.get_work_package_participant(work_package)
                p.approve(data_provider_representative.user)
                work_package = p.work_package

            assert [] == work_package.missing_classification_requirements
            work_package.close_classification()
            assert work_package.has_tier
            assert tier == work_package.tier
        return work_package

    return _classified_work_package


@pytest.fixture
def hide_audit_warnings(caplog):
    """
    Filters out most (but not all) warnings from easyaudit.

    No tests use this by default, it's mostly useful to temporarily add to a
    failing test to reduce the noise.
    """

    def filter(record):
        if record.name in ["easyaudit.signals.model_signals", "model_signals.py"]:
            return False
        return True

    caplog.handler.addFilter(filter)


@pytest.fixture
def remove_data_from_model_with_self_references():
    """
    Fixture to return a function which removes data from a model class that has protected
    self-references, for example `ClassificationQuestion` has the protected foreign keys
    `yes_question` and `no_question` pointing to itself, therefore need to be deleted in particular
    order. This brute force approach does not need to know the order ahead of time and keeps trying
    to delete rows of data until it can.
    """

    def remove_data(model_class):
        if model_class.objects.exists():
            i = 0
            original_count = model_class.objects.all().count()
            while model_class.objects.all().count() and i < original_count:
                for instance in model_class.objects.all():
                    try:
                        instance.delete()
                    except ProtectedError:
                        pass

    # Pass function into fixture output which can be called in test
    return remove_data
