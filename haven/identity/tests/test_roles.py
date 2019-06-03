from identity.roles import UserRole


class TestUserRoleCreateUser:
    def test_superuser_can_create_users(self):
        assert UserRole.SUPERUSER.can_create_users

    def test_system_controller_can_create_users(self):
        assert UserRole.SYSTEM_CONTROLLER.can_create_users

    def test_research_coordinator_cannot_create_users(self):
        assert not UserRole.RESEARCH_COORDINATOR.can_create_users

    def test_unprivileged_user_cannot_create_users(self):
        assert not UserRole.NONE.can_create_users


class TestUserRoleCreatableRoles:
    def test_superuser_can_create_any_roles(self):
        assert UserRole.SUPERUSER.can_create(UserRole.SYSTEM_CONTROLLER)
        assert UserRole.SUPERUSER.can_create(UserRole.RESEARCH_COORDINATOR)

    def test_system_controller_creatable_roles(self):
        assert UserRole.SYSTEM_CONTROLLER.can_create(UserRole.RESEARCH_COORDINATOR)
        assert not UserRole.SYSTEM_CONTROLLER.can_create(UserRole.SYSTEM_CONTROLLER)

    def test_research_coordinator_creatable_roles(self):
        assert UserRole.RESEARCH_COORDINATOR.creatable_roles == []
        assert not UserRole.RESEARCH_COORDINATOR.can_create(UserRole.NONE)

    def test_unprivileged_user_has_no_creatable_roles(self):
        assert UserRole.NONE.creatable_roles == []
        assert not UserRole.NONE.can_create(UserRole.NONE)


class TestUserRoleCreateProject:
    def test_superuser_can_create_projects(self):
        assert UserRole.SUPERUSER.can_create_projects

    def test_system_controller_can_create_projects(self):
        assert UserRole.SYSTEM_CONTROLLER.can_create_projects

    def test_research_coordinator_can_create_projects(self):
        assert UserRole.RESEARCH_COORDINATOR.can_create_projects

    def test_unprivileged_user_cannot_create_projects(self):
        assert not UserRole.NONE.can_create_projects


class TestUserRoleViewAllProjects:
    def test_superuser_can_view_all_projects(self):
        assert UserRole.SUPERUSER.can_view_all_projects

    def test_system_controller_can_view_all_projects(self):
        assert UserRole.SYSTEM_CONTROLLER.can_view_all_projects

    def test_research_coordinator_cannot_view_all_projects(self):
        assert not UserRole.RESEARCH_COORDINATOR.can_view_all_projects

    def test_unprivileged_user_cannot_view_all_projects(self):
        assert not UserRole.NONE.can_view_all_projects


class TestUserRoleViewAllUsers:
    def test_superuser_can_view_all_users(self):
        assert UserRole.SUPERUSER.can_view_all_users

    def test_system_controller_can_view_all_users(self):
        assert UserRole.SYSTEM_CONTROLLER.can_view_all_users

    def test_research_coordinator_cannot_view_all_users(self):
        assert not UserRole.RESEARCH_COORDINATOR.can_view_all_users

    def test_unprivileged_user_cannot_view_all_users(self):
        assert not UserRole.NONE.can_view_all_users


class TestUserRoleImportUsers:
    def test_superuser_can_import_users(self):
        assert UserRole.SUPERUSER.can_import_users

    def test_system_controller_can_import_users(self):
        assert UserRole.SYSTEM_CONTROLLER.can_import_users

    def test_research_coordinator_cannot_import_users(self):
        assert not UserRole.RESEARCH_COORDINATOR.can_import_users

    def test_unprivileged_user_cannot_import_users(self):
        assert not UserRole.NONE.can_import_users


class TestUserRoleExportUsers:
    def test_superuser_can_export_users(self):
        assert UserRole.SUPERUSER.can_export_users

    def test_system_controller_can_export_users(self):
        assert UserRole.SYSTEM_CONTROLLER.can_export_users

    def test_research_coordinator_cannot_export_users(self):
        assert not UserRole.RESEARCH_COORDINATOR.can_export_users

    def test_unprivileged_user_cannot_export_users(self):
        assert not UserRole.NONE.can_export_users
