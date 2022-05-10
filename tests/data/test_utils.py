import pytest

from haven.core import recipes
from haven.data.utils import get_accessible_datasets
from haven.projects.roles import ProjectRole


@pytest.mark.django_db
class TestGetAccessibleDatasets:
    def test_get_accessible_datasets(
        self,
        programme_manager,
        project_participant,
        classified_work_package,
    ):
        """
        Test that the `get_accessible_datasets` returns the correct accessible datasets for a given
        user.
        """
        num_accessible_datasets = 3
        # Create work packages and add api user
        accessible_work_packages = [
            classified_work_package(0) for _ in range(num_accessible_datasets)
        ]
        for work_package in accessible_work_packages:
            work_package.project.add_user(
                user=project_participant,
                role=ProjectRole.RESEARCHER.value,
                created_by=programme_manager,
            )
            work_package.add_user(
                project_participant,
                programme_manager,
            )

        # Create more work packages that are not associated with api user, and associated datasets
        # should not show up in dataset list view
        unaccessible_work_packages = [classified_work_package(0) for _ in range(3)]

        accessible_datasets = get_accessible_datasets(project_participant)

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

        accessible_datasets = get_accessible_datasets(project_participant)

        # No datasets returned because work package is not classified
        assert len(accessible_datasets) == 0

    def test_dataset_without_work_package(
        self,
        programme_manager,
        project_participant,
        data_provider_representative,
        investigator,
        classified_work_package,
    ):
        """Test that that a dataset without a workpackage is not accessible"""
        work_package = classified_work_package(0)
        work_package.project.add_user(
            user=project_participant,
            role=ProjectRole.RESEARCHER.value,
            created_by=programme_manager,
        )
        work_package.add_user(
            project_participant,
            programme_manager,
        )

        # Is not associated with work package
        dataset = recipes.dataset.make()

        work_package.project.add_dataset(
            dataset, data_provider_representative.user, investigator.user
        )

        accessible_datasets = get_accessible_datasets(project_participant)

        assert accessible_datasets.count() == 1

        assert work_package.datasets.last() in accessible_datasets
        # Since it is not associated with a work package
        assert dataset not in accessible_datasets

    def test_user_without_work_package(
        self,
        programme_manager,
        project_participant,
        classified_work_package,
    ):
        """
        Test that is user is not associated with classified work package that they cannot access the
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

        accessible_datasets = get_accessible_datasets(project_participant)

        assert accessible_datasets.count() == 0

    def test_dataset_without_project(
        self,
        programme_manager,
        project_participant,
        data_provider_representative,
        investigator,
        classified_work_package,
    ):
        """Test that that a dataset without a project is not accessible"""
        work_package = classified_work_package(0)
        work_package.project.add_user(
            user=project_participant,
            role=ProjectRole.RESEARCHER.value,
            created_by=programme_manager,
        )
        work_package.add_user(
            project_participant,
            programme_manager,
        )

        # Is not associated with project
        dataset = recipes.dataset.make()

        accessible_datasets = get_accessible_datasets(project_participant)

        assert accessible_datasets.count() == 1

        assert work_package.datasets.last() in accessible_datasets
        # Since it is not associated with a work package
        assert dataset not in accessible_datasets
