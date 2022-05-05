import uuid

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
