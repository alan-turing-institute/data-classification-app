from identity.roles import UserRole
from projects.roles import UserPermissions


def permissions_user(role):
    return UserPermissions(None, role)


class TestUserRoleCreateUser:
    def test_system_manager_can_create_users(self):
        assert permissions_user(UserRole.SYSTEM_MANAGER).can_create_users

    def test_programme_manager_can_create_users(self):
        assert permissions_user(UserRole.PROGRAMME_MANAGER).can_create_users

    def test_unprivileged_user_cannot_create_users(self):
        assert not permissions_user(UserRole.NONE).can_create_users


class TestUserRoleCreatableRoles:
    def test_system_manager_assignable_roles(self):
        assert permissions_user(UserRole.SYSTEM_MANAGER).can_assign_role(UserRole.PROGRAMME_MANAGER)
        assert permissions_user(UserRole.SYSTEM_MANAGER).can_assign_role(UserRole.NONE)
        assert not permissions_user(UserRole.SYSTEM_MANAGER).can_assign_role(UserRole.SYSTEM_MANAGER)

    def test_programme_manager_assignable_roles(self):
        assert permissions_user(UserRole.PROGRAMME_MANAGER).can_assign_role(UserRole.NONE)
        assert not permissions_user(UserRole.PROGRAMME_MANAGER).can_assign_role(UserRole.PROGRAMME_MANAGER)
        assert not permissions_user(UserRole.PROGRAMME_MANAGER).can_assign_role(UserRole.SYSTEM_MANAGER)

    def test_unprivileged_user_has_no_assignable_roles(self):
        assert permissions_user(UserRole.NONE).creatable_roles == []
        assert not permissions_user(UserRole.NONE).can_assign_role(UserRole.NONE)


class TestUserRoleCreateProject:
    def test_system_manager_can_create_projects(self):
        assert permissions_user(UserRole.SYSTEM_MANAGER).can_create_projects

    def test_programme_manager_can_create_projects(self):
        assert permissions_user(UserRole.PROGRAMME_MANAGER).can_create_projects

    def test_unprivileged_user_cannot_create_projects(self):
        assert not permissions_user(UserRole.NONE).can_create_projects


class TestUserRoleViewAllProjects:
    def test_system_manager_can_view_all_projects(self):
        assert permissions_user(UserRole.SYSTEM_MANAGER).can_view_all_projects

    def test_programme_manager_can_view_all_projects(self):
        assert permissions_user(UserRole.PROGRAMME_MANAGER).can_view_all_projects

    def test_unprivileged_user_cannot_view_all_projects(self):
        assert not permissions_user(UserRole.NONE).can_view_all_projects


class TestUserRoleViewAllUsers:
    def test_system_manager_can_view_all_users(self):
        assert permissions_user(UserRole.SYSTEM_MANAGER).can_view_all_users

    def test_programme_manager_can_view_all_users(self):
        assert permissions_user(UserRole.PROGRAMME_MANAGER).can_view_all_users

    def test_unprivileged_user_cannot_view_all_users(self):
        assert not permissions_user(UserRole.NONE).can_view_all_users


class TestUserRoleImportUsers:
    def test_system_manager_can_import_users(self):
        assert permissions_user(UserRole.SYSTEM_MANAGER).can_import_users

    def test_programme_manager_can_import_users(self):
        assert permissions_user(UserRole.PROGRAMME_MANAGER).can_import_users

    def test_unprivileged_user_cannot_import_users(self):
        assert not permissions_user(UserRole.NONE).can_import_users


class TestUserRoleExportUsers:
    def test_system_manager_can_export_users(self):
        assert permissions_user(UserRole.SYSTEM_MANAGER).can_export_users

    def test_programme_manager_can_export_users(self):
        assert permissions_user(UserRole.PROGRAMME_MANAGER).can_export_users

    def test_unprivileged_user_cannot_export_users(self):
        assert not permissions_user(UserRole.NONE).can_export_users
