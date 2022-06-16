import pytest

from haven.api.utils import (
    get_accessible_datasets,
    get_accessible_projects,
    get_accessible_work_packages,
    get_maximum_tier_filter,
    safe_filter_and_deduplicate,
)
from haven.core import recipes
from haven.data.models import Dataset
from haven.projects.models import Project, WorkPackage
from haven.projects.roles import ProjectRole


@pytest.mark.django_db
class TestSafeFilterAndDeduplicate:
    @pytest.mark.parametrize("model_class", [WorkPackage, Project, Dataset])
    def test_caught_validation_error(
        self,
        model_class,
        project_participant,
        make_accessible_work_package,
    ):
        """
        Test that the `safe_filter_and_deduplicate` returns an empty array if an invalid UUID is
        used in filters. This would usually raise a `ValidationError`.
        """
        make_accessible_work_package(project_participant)

        queryset = safe_filter_and_deduplicate(model_class, {"uuid": "invalid_uuid"})

        assert queryset.count() == 0


@pytest.mark.django_db
class TestGetAccessibleDatasets:
    def test_get_accessible_datasets(
        self,
        project_participant,
        classified_work_package,
        make_accessible_work_package,
        make_mock_request_with_oauth_application,
    ):
        """
        Test that the `get_accessible_datasets` returns the correct accessible datasets for a given
        user.
        """
        num_accessible_datasets = 3
        accessible_work_packages = [
            make_accessible_work_package(project_participant)
            for _ in range(num_accessible_datasets)
        ]

        # Create more work packages that are not associated with api user
        unaccessible_work_packages = [classified_work_package(0) for _ in range(3)]

        mock_request = make_mock_request_with_oauth_application()

        accessible_datasets = get_accessible_datasets(mock_request)

        # Assert datasets in `accessible_work_packages` are in returned datasets
        for work_package in accessible_work_packages:
            for dataset in work_package.datasets.all():
                assert dataset in accessible_datasets

        # Assert datasets in `unaccessible_work_packages` are not in returned datasets
        for work_package in unaccessible_work_packages:
            for dataset in work_package.datasets.all():
                assert dataset not in accessible_datasets

    def test_work_package_not_classified(
        self,
        programme_manager,
        project_participant,
        unclassified_work_package,
        make_mock_request_with_oauth_application,
    ):
        """
        Test that even though user is associated with project and work package, that dataset is not
        accessible because the work package is not classified
        """
        work_package = unclassified_work_package()
        work_package.project.add_user(
            user=project_participant,
            role=ProjectRole.RESEARCHER.value,
            created_by=programme_manager,
        )
        work_package.add_user(
            project_participant,
            programme_manager,
        )

        mock_request = make_mock_request_with_oauth_application()

        accessible_datasets = get_accessible_datasets(mock_request)

        # No datasets returned because work package is not classified
        assert len(accessible_datasets) == 0

    def test_dataset_without_work_package(
        self,
        project_participant,
        data_provider_representative,
        investigator,
        make_accessible_work_package,
        make_mock_request_with_oauth_application,
    ):
        """Test that a dataset without a work package is not accessible"""
        work_package = make_accessible_work_package(project_participant)

        # Create a dataset in the project but *not* the work package
        dataset = recipes.dataset.make()

        work_package.project.add_dataset(
            dataset, data_provider_representative.user, investigator.user
        )

        mock_request = make_mock_request_with_oauth_application()

        accessible_datasets = get_accessible_datasets(mock_request)

        assert accessible_datasets.count() == 1

        # The fixture adds a dataset to the work package automatically
        assert work_package.datasets.last() in accessible_datasets
        # Since it is not associated with a work package
        assert dataset not in accessible_datasets

    def test_user_without_work_package(
        self,
        programme_manager,
        project_participant,
        classified_work_package,
        make_mock_request_with_oauth_application,
    ):
        """
        Test that if user is not associated with classified work package that they cannot access the
        dataset
        """
        # None of these work packages are associated with user, even though they are associated with
        # project
        for work_package in [classified_work_package(0) for _ in range(3)]:
            work_package.project.add_user(
                user=project_participant,
                role=ProjectRole.RESEARCHER.value,
                created_by=programme_manager,
            )

        mock_request = make_mock_request_with_oauth_application()

        accessible_datasets = get_accessible_datasets(mock_request)

        assert accessible_datasets.count() == 0

    def test_dataset_without_project(
        self,
        project_participant,
        make_accessible_work_package,
        make_mock_request_with_oauth_application,
    ):
        """Test that a dataset without a project is not accessible"""
        work_package = make_accessible_work_package(project_participant)

        # Is not associated with project
        dataset = recipes.dataset.make()

        mock_request = make_mock_request_with_oauth_application()

        accessible_datasets = get_accessible_datasets(mock_request)

        assert accessible_datasets.count() == 1

        assert work_package.datasets.last() in accessible_datasets
        # Since it is not associated with a work package
        assert dataset not in accessible_datasets

    def test_filter_by_project(
        self,
        project_participant,
        classified_work_package,
        make_accessible_work_package,
        make_mock_request_with_oauth_application,
    ):
        """
        Test that the `get_accessible_datasets` returns the correct accessible datasets for a given
        user and filtered by a specific project.
        """
        accessible_work_package = make_accessible_work_package(project_participant)

        # Create work packages that are accessible but are associated to other projects which are
        # excluded by the project filter
        work_packages_for_other_projects = [
            make_accessible_work_package(project_participant) for _ in range(3)
        ]

        # Create more work packages that are not associated with api user
        unaccessible_work_packages = [classified_work_package(0) for _ in range(3)]

        mock_request = make_mock_request_with_oauth_application()

        accessible_datasets = get_accessible_datasets(
            mock_request,
            extra_filters={"projects__uuid": accessible_work_package.project.uuid},
        )

        for dataset in accessible_work_package.datasets.all():
            assert dataset in accessible_datasets

        # Assert datasets in `work_packages_for_other_projects` are not in returned datasets
        for work_package in work_packages_for_other_projects:
            for dataset in work_package.datasets.all():
                assert dataset not in accessible_datasets

        # Assert datasets in `unaccessible_work_packages` are not in returned datasets
        for work_package in unaccessible_work_packages:
            for dataset in work_package.datasets.all():
                assert dataset not in accessible_datasets

    def test_filter_by_work_package(
        self,
        project_participant,
        classified_work_package,
        make_accessible_work_package,
        make_mock_request_with_oauth_application,
    ):
        """
        Test that the `get_accessible_datasets` returns the correct accessible datasets for a given
        user and filtered by a specific work package.
        """
        accessible_work_package = make_accessible_work_package(project_participant)

        # Create work packages that are accessible but are excluded by the work package filter
        work_packages_for_other_projects = [
            make_accessible_work_package(project_participant) for _ in range(3)
        ]

        # Create more work packages that are not associated with api user
        unaccessible_work_packages = [classified_work_package(0) for _ in range(3)]

        mock_request = make_mock_request_with_oauth_application()

        accessible_datasets = get_accessible_datasets(
            mock_request,
            extra_filters={"work_packages__uuid": accessible_work_package.uuid},
        )

        for dataset in accessible_work_package.datasets.all():
            assert dataset in accessible_datasets

        # Assert datasets in `work_packages_for_other_projects` are not in returned datasets
        for work_package in work_packages_for_other_projects:
            for dataset in work_package.datasets.all():
                assert dataset not in accessible_datasets

        # Assert datasets in `unaccessible_work_packages` are not in returned datasets
        for work_package in unaccessible_work_packages:
            for dataset in work_package.datasets.all():
                assert dataset not in accessible_datasets

    def test_filter_by_project_and_work_package(
        self,
        project_participant,
        classified_work_package,
        make_accessible_work_package,
        make_mock_request_with_oauth_application,
    ):
        """
        Test that the `get_accessible_datasets` returns the correct accessible datasets for a given
        user and filtered by a specific project and work package.
        """
        accessible_work_package = make_accessible_work_package(project_participant)

        # Create a classified work package that is associated with the same project but will be
        # excluded due to the work package filter
        excluded_work_package = classified_work_package(0)
        excluded_work_package.project = accessible_work_package.project
        excluded_work_package.save()

        # Create more work packages that are not associated with api user
        unaccessible_work_packages = [classified_work_package(0) for _ in range(3)]

        mock_request = make_mock_request_with_oauth_application()

        accessible_datasets = get_accessible_datasets(
            mock_request,
            extra_filters={
                "projects__uuid": accessible_work_package.project.uuid,
                "work_packages__uuid": accessible_work_package.uuid,
            },
        )

        for dataset in accessible_work_package.datasets.all():
            assert dataset in accessible_datasets

        # Assert datasets in `excluded_work_package` are not in returned datasets
        for dataset in excluded_work_package.datasets.all():
            assert dataset not in accessible_datasets

        # Assert datasets in `unaccessible_work_packages` are not in returned datasets
        for work_package in unaccessible_work_packages:
            for dataset in work_package.datasets.all():
                assert dataset not in accessible_datasets


@pytest.mark.django_db
class TestGetAccessibleProjects:
    def test_get_accessible_projects(
        self,
        project_participant,
        classified_work_package,
        make_accessible_work_package,
        make_mock_request_with_oauth_application,
    ):
        """
        Test that the `get_accessible_projects` returns the correct accessible projects for a given
        user.
        """
        num_accessible_datasets = 3
        accessible_work_packages = [
            make_accessible_work_package(project_participant)
            for _ in range(num_accessible_datasets)
        ]

        # Create more projects that are not associated with api user
        unaccessible_work_packages = [classified_work_package(0) for _ in range(3)]

        mock_request = make_mock_request_with_oauth_application()

        accessible_projects = get_accessible_projects(mock_request)

        # Assert projects in `accessible_work_packages` are in returned projects
        for work_package in accessible_work_packages:
            assert work_package.project in accessible_projects

        # Assert projects in `unaccessible_work_packages` are not in returned projects
        for work_package in unaccessible_work_packages:
            assert work_package.project not in accessible_projects

    def test_work_package_not_classified(
        self,
        programme_manager,
        project_participant,
        unclassified_work_package,
        make_mock_request_with_oauth_application,
    ):
        """
        Test that if project is associated with unclassified work package, that project is still
        accessible
        """
        work_package = unclassified_work_package()
        work_package.project.add_user(
            user=project_participant,
            role=ProjectRole.RESEARCHER.value,
            created_by=programme_manager,
        )
        work_package.add_user(
            project_participant,
            programme_manager,
        )

        mock_request = make_mock_request_with_oauth_application()

        accessible_projects = get_accessible_projects(mock_request)

        assert len(accessible_projects) == 1
        assert work_package.project in accessible_projects

    def test_project_without_work_package(
        self,
        project_participant,
        programme_manager,
        make_mock_request_with_oauth_application,
    ):
        """Test that a project without a work package is still accessible"""
        # Is not associated with work package
        project = recipes.project.make()
        project.add_user(
            user=project_participant,
            role=ProjectRole.RESEARCHER.value,
            created_by=programme_manager,
        )

        mock_request = make_mock_request_with_oauth_application()

        accessible_projects = get_accessible_projects(mock_request)

        assert accessible_projects.count() == 1

        assert project in accessible_projects

    def test_user_without_project(
        self,
        project_participant,
        make_mock_request_with_oauth_application,
    ):
        """
        Test that if user is not a participant in project that they cannot access the project
        """
        recipes.project.make()

        mock_request = make_mock_request_with_oauth_application()

        accessible_datasets = get_accessible_datasets(mock_request)

        assert accessible_datasets.count() == 0


@pytest.mark.django_db
class TestGetAccessibleWorkPackages:
    def test_get_accessible_work_packages(
        self,
        project_participant,
        classified_work_package,
        make_accessible_work_package,
        make_mock_request_with_oauth_application,
    ):
        """
        Test that the `get_accessible_work_packages` returns the correct accessible work packages
        for a given user
        """
        num_accessible_datasets = 3
        accessible_work_packages = [
            make_accessible_work_package(project_participant)
            for _ in range(num_accessible_datasets)
        ]

        # Create more work packages that are not associated with api user
        unaccessible_work_packages = [classified_work_package(0) for _ in range(3)]

        mock_request = make_mock_request_with_oauth_application()

        accessible_datasets = get_accessible_work_packages(mock_request)

        # Assert work packages in `accessible_work_packages` are in returned work packages
        for work_package in accessible_work_packages:
            assert work_package in accessible_work_packages

        # Assert work packages in `unaccessible_work_packages` are not in returned work packages
        for work_package in unaccessible_work_packages:
            assert work_package not in accessible_datasets

    def test_work_package_not_classified(
        self,
        programme_manager,
        project_participant,
        unclassified_work_package,
        make_mock_request_with_oauth_application,
    ):
        """
        Test that even though user is associated with project and work package, that work package
        is not accessible because the work package is not classified
        """
        work_package = unclassified_work_package()
        work_package.project.add_user(
            user=project_participant,
            role=ProjectRole.RESEARCHER.value,
            created_by=programme_manager,
        )
        work_package.add_user(
            project_participant,
            programme_manager,
        )

        mock_request = make_mock_request_with_oauth_application()

        accessible_work_packages = get_accessible_work_packages(mock_request)

        # No work packages returned because work package is not classified
        assert len(accessible_work_packages) == 0

    def test_user_without_work_package(
        self,
        programme_manager,
        project_participant,
        classified_work_package,
        make_mock_request_with_oauth_application,
    ):
        """
        Test that if user is not associated with classified work package that they cannot access it
        """
        # None of these work packages are associated with user, even though they are associated with
        # project
        for work_package in [classified_work_package(0) for _ in range(3)]:
            work_package.project.add_user(
                user=project_participant,
                role=ProjectRole.RESEARCHER.value,
                created_by=programme_manager,
            )

        mock_request = make_mock_request_with_oauth_application()

        accessible_datasets = get_accessible_datasets(mock_request)

        assert accessible_datasets.count() == 0

    def test_filter_by_project(
        self,
        project_participant,
        classified_work_package,
        make_accessible_work_package,
        make_mock_request_with_oauth_application,
    ):
        """
        Test that the `get_accessible_work_packages` returns the correct accessible work packages
        for a given user and filtered by a specific project.
        """
        accessible_work_package = make_accessible_work_package(project_participant)

        # Create work packages that are accessible but are associated to other projects which are
        # excluded by the project filter
        work_packages_for_other_projects = [
            make_accessible_work_package(project_participant) for _ in range(3)
        ]

        # Create more work packages that are not associated with api user
        unaccessible_work_packages = [classified_work_package(0) for _ in range(3)]

        mock_request = make_mock_request_with_oauth_application()

        accessible_work_packages = get_accessible_work_packages(
            mock_request,
            extra_filters={"project__uuid": accessible_work_package.project.uuid},
        )

        assert accessible_work_packages.count() == 1
        assert accessible_work_package in accessible_work_packages

        # Assert work packages in `work_packages_for_other_projects` are not in returned work
        # packages
        for work_package in work_packages_for_other_projects:
            assert work_package not in accessible_work_packages

        # Assert work packages in `unaccessible_work_packages` are not in returned work packages
        for work_package in unaccessible_work_packages:
            assert work_package not in accessible_work_packages


@pytest.mark.django_db
class TestGetMaximumFilterTier:
    def test_get_accessible_work_packages(
        self, make_mock_request_with_oauth_application, application_profile
    ):
        """Test that the `get_maximum_tier_filter` returns the filter dictionary"""
        mock_request = make_mock_request_with_oauth_application()

        filter_key = "test"

        maximum_tier_filter = get_maximum_tier_filter(mock_request, filter_key=filter_key)

        assert maximum_tier_filter == {filter_key: application_profile.maximum_tier}

    def test_no_application(
        self,
        make_mock_request_with_oauth_application,
        oauth_application,
    ):
        """
        Test that the `get_maximum_tier_filter` returns an empty dictionary if a matching
        application does not exist
        """
        mock_request = make_mock_request_with_oauth_application()

        # Delete the application that is associated with the request
        oauth_application.delete()

        maximum_tier_filter = get_maximum_tier_filter(mock_request, filter_key="test")

        assert maximum_tier_filter == {}

    def test_no_application_profile(
        self,
        make_mock_request_with_oauth_application,
    ):
        """
        Test that the `get_maximum_tier_filter` returns an empty dictionary if a matching
        application profile does not exist
        """
        mock_request = make_mock_request_with_oauth_application()

        maximum_tier_filter = get_maximum_tier_filter(mock_request, filter_key="test")

        assert maximum_tier_filter == {}
