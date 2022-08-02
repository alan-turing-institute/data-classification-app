"""
Please Note! In order to run these unit tests locally without being skipped you must use the
`--migrations` flag when using pytest, currently the `pytest.ini` for this project uses
`--nomigrations` by default. GitHub actions will still run these unit tests in CI.
"""
import uuid

from django.contrib.auth import get_user_model
import pytest


@pytest.mark.django_db
class TestUserPopulateUUID:
    def test_user_populate_uuid(self, migrator):
        """
        Test that custom migration `0021_user_populate_uuid.py` correctly populates the UUID for any
        instances which existed before migrations introduced the new UUID field
        """
        # Revert to the state when the `uuid` field did not exist
        old_state = migrator.apply_initial_migration(("identity", "0019_name_for_standard_user"))
        User = old_state.apps.get_model("identity", "User")

        user_1 = User.objects.create(username="user_1")
        user_2 = User.objects.create(username="user_2")

        assert User.objects.count() == 2
        assert not hasattr(user_1, "uuid")
        assert not hasattr(user_2, "uuid")

        # Migrate to the state after the `uuid` field did not exists and after the migration to
        # populate with a unique uuid
        new_state = migrator.apply_tested_migration(("identity", "0022_user_uuid_unique_non_editable"))
        User = new_state.apps.get_model("identity", "User")

        assert User.objects.count() == 2

        user_1 = User.objects.get(username="user_1")
        user_2 = User.objects.get(username="user_2")

        assert hasattr(user_1, "uuid")
        assert len(str(user_1.uuid)) == len(str(uuid.uuid4()))
        assert hasattr(user_2, "uuid")
        assert len(str(user_2.uuid)) == len(str(uuid.uuid4()))
        assert str(user_1.uuid) != str(user_2.uuid)

    def test_dataset_populate_uuid(self, migrator):
        """
        Test that custom migration `0019_dataset_populate_uuid.py` correctly populates the UUID for
        any instances which existed before migrations introduced the new UUID field
        """
        # Revert to the state when the `uuid` field did not exist
        old_state = migrator.apply_initial_migration(("data", "0017_auto_20200115_1423"))

        User = old_state.apps.get_model("identity", "User")

        user_1 = User.objects.create(username="user_1")
        user_2 = User.objects.create(username="user_2")

        Dataset = old_state.apps.get_model("data", "Dataset")

        # `created_by` is an essential field
        dataset_1 = Dataset.objects.create(created_by_id=user_1.id)
        dataset_2 = Dataset.objects.create(created_by_id=user_2.id)

        assert Dataset.objects.count() == 2
        assert not hasattr(dataset_1, "uuid")
        assert not hasattr(dataset_2, "uuid")

        # Migrate to the state after the `uuid` field did not exists and after the migration to
        # populate with a unique uuid
        new_state = migrator.apply_tested_migration(("data", "0020_dataset_uuid_unique_non_editable"))
        Dataset = new_state.apps.get_model("data", "Dataset")

        assert Dataset.objects.count() == 2

        dataset_1 = Dataset.objects.get(created_by_id=user_1.id)
        dataset_2 = Dataset.objects.get(created_by_id=user_2.id)

        assert hasattr(dataset_1, "uuid")
        assert len(str(dataset_1.uuid)) == len(str(uuid.uuid4()))
        assert hasattr(dataset_2, "uuid")
        assert len(str(dataset_2.uuid)) == len(str(uuid.uuid4()))
        assert str(dataset_1.uuid) != str(dataset_2.uuid)

    def test_work_package_populate_uuid(self, migrator):
        """
        Test that custom migration `0038_workpackage_populate_uuid.py` correctly populates the UUID
        for any instances which existed before migrations introduced the new UUID field
        """
        # Revert to the state when the `uuid` field did not exist
        old_state = migrator.apply_initial_migration(("projects", "0036_project_programmes"))
        WorkPackage = old_state.apps.get_model("projects", "WorkPackage")

        User = old_state.apps.get_model("identity", "User")
        Project = old_state.apps.get_model("projects", "Project")

        user_1 = User.objects.create(username="user_1")
        user_2 = User.objects.create(username="user_2")
        
        project = Project.objects.create(created_by_id=user_1.id)

        # `created_by` is an essential field
        # `project` is an essential field
        work_package_1 = WorkPackage.objects.create(created_by_id=user_1.id, project_id=project.id)
        work_package_2 = WorkPackage.objects.create(created_by_id=user_2.id, project_id=project.id)

        assert WorkPackage.objects.count() == 2
        assert not hasattr(work_package_1, "uuid")
        assert not hasattr(work_package_2, "uuid")

        # Migrate to the state after the `uuid` field did not exists and after the migration to
        # populate with a unique uuid
        new_state = migrator.apply_tested_migration(("projects", "0039_workpackage_uuid_unique_non_editable"))
        WorkPackage = new_state.apps.get_model("projects", "WorkPackage")

        assert WorkPackage.objects.count() == 2

        work_package_1 = WorkPackage.objects.get(created_by_id=user_1.id)
        work_package_2 = WorkPackage.objects.get(created_by_id=user_2.id)

        assert hasattr(work_package_1, "uuid")
        assert len(str(work_package_1.uuid)) == len(str(uuid.uuid4()))
        assert hasattr(work_package_2, "uuid")
        assert len(str(work_package_2.uuid)) == len(str(uuid.uuid4()))
        assert str(work_package_1.uuid) != str(work_package_2.uuid)

    def test_project_populate_uuid(self, migrator):
        """
        Test that custom migration `0041_project_populate_uuid.py` correctly populates the UUID for
        any instances which existed before migrations introduced the new UUID field
        """
        # Revert to the state when the `uuid` field did not exist
        old_state = migrator.apply_initial_migration(("projects", "0039_workpackage_uuid_unique_non_editable"))

        User = old_state.apps.get_model("identity", "User")

        user_1 = User.objects.create(username="user_1")
        user_2 = User.objects.create(username="user_2")

        Project = old_state.apps.get_model("projects", "Project")

        # `created_by` is an essential field
        project_1 = Project.objects.create(name="project_1", created_by_id=user_1.id)
        project_2 = Project.objects.create(name="project_2", created_by_id=user_2.id)

        assert Project.objects.count() == 2
        assert not hasattr(project_1, "uuid")
        assert not hasattr(project_2, "uuid")

        # Migrate to the state after the `uuid` field did not exists and after the migration to
        # populate with a unique uuid
        new_state = migrator.apply_tested_migration(("projects", "0042_project_uuid_unique_non_editable"))
        Project = new_state.apps.get_model("projects", "Project")

        assert Project.objects.count() == 2

        project_1 = Project.objects.get(created_by_id=user_1.id)
        project_2 = Project.objects.get(created_by_id=user_2.id)

        assert hasattr(project_1, "uuid")
        assert len(str(project_1.uuid)) == len(str(uuid.uuid4()))
        assert hasattr(project_2, "uuid")
        assert len(str(project_2.uuid)) == len(str(uuid.uuid4()))
        assert str(project_1.uuid) != str(project_2.uuid)
