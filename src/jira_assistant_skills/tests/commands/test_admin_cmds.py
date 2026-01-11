"""
Tests for jira-as admin commands.

Tests cover:
- Helper functions
- Implementation functions for all admin operations
- Formatting functions
- CLI commands
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from jira_assistant_skills.cli.commands.admin_cmds import (
    # Helper functions
    _parse_comma_list,
    _is_system_group,
    SYSTEM_GROUPS,
    # Project implementation functions
    _list_projects_impl,
    _list_trash_projects_impl,
    _get_project_impl,
    _create_project_impl,
    _update_project_impl,
    _delete_project_impl,
    _archive_project_impl,
    _restore_project_impl,
    _get_project_config_impl,
    # Category implementation functions
    _list_categories_impl,
    _create_category_impl,
    _assign_category_impl,
    # User implementation functions
    _search_users_impl,
    _get_user_impl,
    # Group implementation functions
    _list_groups_impl,
    _get_group_members_impl,
    _create_group_impl,
    _delete_group_impl,
    _add_user_to_group_impl,
    _remove_user_from_group_impl,
    # Automation implementation functions
    _list_automation_rules_impl,
    _get_automation_rule_impl,
    _search_automation_rules_impl,
    _enable_automation_rule_impl,
    _disable_automation_rule_impl,
    _toggle_automation_rule_impl,
    _invoke_manual_rule_impl,
    _list_automation_templates_impl,
    _get_automation_template_impl,
    # Permission scheme implementation functions
    _list_permission_schemes_impl,
    _get_permission_scheme_impl,
    _create_permission_scheme_impl,
    _assign_permission_scheme_impl,
    _list_permissions_impl,
    # Notification scheme implementation functions
    _list_notification_schemes_impl,
    _get_notification_scheme_impl,
    _create_notification_scheme_impl,
    _add_notification_impl,
    _remove_notification_impl,
    # Screen implementation functions
    _list_screens_impl,
    _get_screen_impl,
    _list_screen_tabs_impl,
    _get_screen_fields_impl,
    _add_field_to_screen_impl,
    _remove_field_from_screen_impl,
    _list_screen_schemes_impl,
    _get_screen_scheme_impl,
    # Issue type implementation functions
    _list_issue_types_impl,
    _get_issue_type_impl,
    _create_issue_type_impl,
    _update_issue_type_impl,
    _delete_issue_type_impl,
    _list_issue_type_schemes_impl,
    _get_issue_type_scheme_impl,
    _create_issue_type_scheme_impl,
    _assign_issue_type_scheme_impl,
    _get_project_issue_type_scheme_impl,
    # Workflow implementation functions
    _list_workflows_impl,
    _get_workflow_impl,
    _search_workflows_impl,
    _get_workflow_for_issue_impl,
    _list_workflow_schemes_impl,
    _get_workflow_scheme_impl,
    _assign_workflow_scheme_impl,
    _list_statuses_impl,
    # Formatting functions
    _format_projects,
    _format_trash_projects,
    _format_project,
    _format_categories,
    _format_users,
    _format_groups,
    _format_group_members,
    _format_automation_rules,
    _format_permission_schemes,
    _format_notification_schemes,
    _format_screens,
    _format_issue_types,
    _format_workflows,
    _format_statuses,
    # Click commands
    admin,
)
from jira_assistant_skills_lib import JiraError, ValidationError


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_client():
    """Create mock JIRA client."""
    client = MagicMock()
    client.close = MagicMock()
    return client


@pytest.fixture
def mock_automation_client():
    """Create mock automation client."""
    client = MagicMock()
    client.close = MagicMock()
    return client


@pytest.fixture
def sample_projects():
    """Sample projects for testing."""
    return {
        "values": [
            {
                "id": "10001",
                "key": "PROJ1",
                "name": "Project One",
                "projectTypeKey": "software",
                "lead": {"displayName": "John Doe"},
            },
            {
                "id": "10002",
                "key": "PROJ2",
                "name": "Project Two",
                "projectTypeKey": "business",
                "lead": {"displayName": "Jane Smith"},
            },
        ],
        "isLast": True,
        "total": 2,
    }


@pytest.fixture
def sample_project():
    """Sample project for testing."""
    return {
        "id": "10001",
        "key": "TEST",
        "name": "Test Project",
        "projectTypeKey": "software",
        "lead": {"displayName": "John Doe", "accountId": "user123"},
        "description": "A test project",
        "url": "https://jira.example.com/projects/TEST",
    }


@pytest.fixture
def sample_users():
    """Sample users for testing."""
    return [
        {
            "accountId": "user123",
            "displayName": "John Doe",
            "emailAddress": "john@example.com",
            "active": True,
        },
        {
            "accountId": "user456",
            "displayName": "Jane Smith",
            "emailAddress": "jane@example.com",
            "active": True,
        },
        {
            "accountId": "user789",
            "displayName": "Inactive User",
            "emailAddress": "inactive@example.com",
            "active": False,
        },
    ]


@pytest.fixture
def sample_groups():
    """Sample groups for testing."""
    return [
        {"name": "jira-administrators", "groupId": "group1"},
        {"name": "developers", "groupId": "group2"},
        {"name": "jira-users", "groupId": "group3"},
        {"name": "qa-team", "groupId": "group4"},
    ]


@pytest.fixture
def sample_automation_rules():
    """Sample automation rules for testing."""
    return [
        {
            "id": "1",
            "name": "Auto-assign bugs",
            "state": "ENABLED",
            "projects": [{"projectId": "10001", "projectName": "Test Project"}],
            "trigger": {"type": "issue.created"},
        },
        {
            "id": "2",
            "name": "Close stale issues",
            "state": "DISABLED",
            "projects": [],
            "trigger": {"type": "scheduled"},
        },
    ]


@pytest.fixture
def sample_permission_schemes():
    """Sample permission schemes for testing."""
    return [
        {
            "id": "10000",
            "name": "Default Permission Scheme",
            "description": "Default permissions",
        },
        {
            "id": "10001",
            "name": "Restricted Scheme",
            "description": "Restricted access",
        },
    ]


@pytest.fixture
def sample_screens():
    """Sample screens for testing."""
    return [
        {
            "id": "1",
            "name": "Default Screen",
            "description": "Default issue screen",
        },
        {
            "id": "2",
            "name": "Bug Screen",
            "description": "Screen for bugs",
        },
    ]


@pytest.fixture
def sample_issue_types():
    """Sample issue types for testing."""
    return [
        {
            "id": "10001",
            "name": "Bug",
            "description": "A bug",
            "subtask": False,
            "scope": {"type": "PROJECT"},
        },
        {
            "id": "10002",
            "name": "Task",
            "description": "A task",
            "subtask": False,
            "scope": {"type": "PROJECT"},
        },
        {
            "id": "10003",
            "name": "Sub-task",
            "description": "A sub-task",
            "subtask": True,
            "scope": {"type": "PROJECT"},
        },
    ]


@pytest.fixture
def sample_workflows():
    """Sample workflows for testing."""
    return [
        {
            "name": "Default Workflow",
            "description": "The default workflow",
            "scope": {"type": "GLOBAL"},
            "statuses": [
                {"id": "1", "name": "Open"},
                {"id": "2", "name": "In Progress"},
                {"id": "3", "name": "Done"},
            ],
        },
        {
            "name": "Bug Workflow",
            "description": "Workflow for bugs",
            "scope": {"type": "PROJECT"},
            "statuses": [
                {"id": "1", "name": "Open"},
                {"id": "4", "name": "Investigating"},
                {"id": "3", "name": "Done"},
            ],
        },
    ]


@pytest.fixture
def sample_statuses():
    """Sample statuses for testing."""
    return [
        {"id": "1", "name": "Open", "statusCategory": {"name": "To Do"}},
        {"id": "2", "name": "In Progress", "statusCategory": {"name": "In Progress"}},
        {"id": "3", "name": "Done", "statusCategory": {"name": "Done"}},
    ]


@pytest.fixture
def cli_runner():
    """Create CLI test runner."""
    return CliRunner()


# =============================================================================
# Test Helper Functions
# =============================================================================


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_parse_comma_list_basic(self):
        """Test parsing comma-separated values."""
        result = _parse_comma_list("a,b,c")
        assert result == ["a", "b", "c"]

    def test_parse_comma_list_with_spaces(self):
        """Test parsing with spaces around values."""
        result = _parse_comma_list(" a , b , c ")
        assert result == ["a", "b", "c"]

    def test_parse_comma_list_empty(self):
        """Test parsing empty string returns None."""
        result = _parse_comma_list("")
        assert result is None

    def test_parse_comma_list_none(self):
        """Test parsing None returns None."""
        result = _parse_comma_list(None)
        assert result is None

    def test_parse_comma_list_single(self):
        """Test parsing single value."""
        result = _parse_comma_list("single")
        assert result == ["single"]

    def test_is_system_group_true(self):
        """Test system group detection - true cases."""
        assert _is_system_group("jira-administrators") is True
        assert _is_system_group("jira-users") is True
        assert _is_system_group("site-admins") is True

    def test_is_system_group_false(self):
        """Test system group detection - false cases."""
        assert _is_system_group("developers") is False
        assert _is_system_group("qa-team") is False
        assert _is_system_group("my-custom-group") is False

    def test_system_groups_constant(self):
        """Test SYSTEM_GROUPS contains expected groups."""
        assert "jira-administrators" in SYSTEM_GROUPS
        assert "jira-users" in SYSTEM_GROUPS


# =============================================================================
# Test Project Implementation Functions
# =============================================================================


class TestProjectImplementation:
    """Tests for project implementation functions."""

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_list_projects_impl(self, mock_get_client, mock_client, sample_projects):
        """Test listing projects."""
        mock_get_client.return_value = mock_client
        mock_client.search_projects.return_value = sample_projects

        result = _list_projects_impl()

        assert result == sample_projects
        mock_client.close.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_list_projects_with_query(self, mock_get_client, mock_client, sample_projects):
        """Test listing projects with search query."""
        mock_get_client.return_value = mock_client
        mock_client.search_projects.return_value = sample_projects

        _list_projects_impl(query="test")

        mock_client.search_projects.assert_called_once()
        call_args = mock_client.search_projects.call_args
        assert call_args.kwargs["query"] == "test"

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_list_projects_include_archived(self, mock_get_client, mock_client, sample_projects):
        """Test listing projects including archived."""
        mock_get_client.return_value = mock_client
        mock_client.search_projects.return_value = sample_projects

        _list_projects_impl(include_archived=True)

        call_args = mock_client.search_projects.call_args
        assert "archived" in call_args.kwargs["status"]

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_list_trash_projects_impl(self, mock_get_client, mock_client):
        """Test listing trashed projects."""
        mock_get_client.return_value = mock_client
        mock_client.search_projects.return_value = {"values": [], "total": 0}

        result = _list_trash_projects_impl()

        # Should call search_projects with status=["deleted"]
        mock_client.search_projects.assert_called_once()
        call_args = mock_client.search_projects.call_args
        assert call_args.kwargs["status"] == ["deleted"]
        mock_client.close.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_get_project_impl(self, mock_get_client, mock_client, sample_project):
        """Test getting a project."""
        mock_get_client.return_value = mock_client
        mock_client.get_project.return_value = sample_project

        result = _get_project_impl("TEST")

        assert result == sample_project
        mock_client.get_project.assert_called_once_with("TEST", expand=None)
        mock_client.close.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.admin_cmds.validate_project_key")
    @patch("jira_assistant_skills.cli.commands.admin_cmds.validate_project_name")
    @patch("jira_assistant_skills.cli.commands.admin_cmds.validate_project_type")
    @patch("jira_assistant_skills.cli.commands.admin_cmds.validate_project_template")
    def test_create_project_impl(
        self,
        mock_validate_template,
        mock_validate_type,
        mock_validate_name,
        mock_validate_key,
        mock_get_client,
        mock_client,
        sample_project,
    ):
        """Test creating a project."""
        mock_get_client.return_value = mock_client
        mock_validate_key.return_value = "TEST"
        mock_validate_name.return_value = "Test Project"
        mock_validate_type.return_value = "software"
        mock_validate_template.return_value = "com.pyxis.greenhopper.jira:gh-scrum-template"
        mock_client.create_project.return_value = sample_project
        mock_client.search_users.return_value = [{"accountId": "user123"}]

        result = _create_project_impl(
            key="TEST",
            name="Test Project",
            project_type="software",
            template="scrum",
            lead="john",
        )

        assert result == sample_project
        mock_client.create_project.assert_called_once()
        mock_client.close.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_update_project_impl(self, mock_get_client, mock_client, sample_project):
        """Test updating a project."""
        mock_get_client.return_value = mock_client
        mock_client.update_project.return_value = sample_project

        result = _update_project_impl("TEST", name="New Name")

        mock_client.update_project.assert_called_once()
        mock_client.close.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_delete_project_impl_dry_run(self, mock_get_client, mock_client, sample_project):
        """Test deleting a project with dry run."""
        mock_get_client.return_value = mock_client
        mock_client.get_project.return_value = sample_project

        result = _delete_project_impl("TEST", dry_run=True)

        assert result["action"] == "dry_run"
        assert result["would_delete"] is True
        assert result["project"]["key"] == "TEST"
        mock_client.delete_project.assert_not_called()
        mock_client.close.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_delete_project_impl_actual(self, mock_get_client, mock_client, sample_project):
        """Test actually deleting a project."""
        mock_get_client.return_value = mock_client
        mock_client.get_project.return_value = sample_project
        mock_client.delete_project.return_value = None

        result = _delete_project_impl("TEST", dry_run=False)

        assert result["action"] == "deleted"
        mock_client.delete_project.assert_called_once_with("TEST")
        mock_client.close.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_archive_project_impl(self, mock_get_client, mock_client):
        """Test archiving a project."""
        mock_get_client.return_value = mock_client

        result = _archive_project_impl("TEST")

        mock_client.archive_project.assert_called_once_with("TEST")
        mock_client.close.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_restore_project_impl(self, mock_get_client, mock_client):
        """Test restoring a project."""
        mock_get_client.return_value = mock_client

        result = _restore_project_impl("TEST")

        mock_client.restore_project.assert_called_once_with("TEST")
        mock_client.close.assert_called_once()


# =============================================================================
# Test Category Implementation Functions
# =============================================================================


class TestCategoryImplementation:
    """Tests for category implementation functions."""

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_list_categories_impl(self, mock_get_client, mock_client):
        """Test listing categories."""
        mock_get_client.return_value = mock_client
        categories = [{"id": "1", "name": "Development"}]
        mock_client.get_project_categories.return_value = categories

        result = _list_categories_impl()

        assert result == categories
        mock_client.get_project_categories.assert_called_once()
        mock_client.close.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_create_category_impl(self, mock_get_client, mock_client):
        """Test creating a category."""
        mock_get_client.return_value = mock_client
        new_category = {"id": "2", "name": "Testing"}
        mock_client.create_project_category.return_value = new_category

        result = _create_category_impl("Testing", "Testing category")

        assert result == new_category
        mock_client.close.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_assign_category_impl(self, mock_get_client, mock_client, sample_project):
        """Test assigning category to project."""
        mock_get_client.return_value = mock_client
        mock_client.update_project.return_value = sample_project

        result = _assign_category_impl("TEST", 1)

        mock_client.update_project.assert_called_once()
        mock_client.close.assert_called_once()


# =============================================================================
# Test User Implementation Functions
# =============================================================================


class TestUserImplementation:
    """Tests for user implementation functions."""

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_search_users_impl(self, mock_get_client, mock_client, sample_users):
        """Test searching users - default filters inactive."""
        mock_get_client.return_value = mock_client
        mock_client.search_users.return_value = sample_users

        result = _search_users_impl("john")

        # Default active_only=True filters out inactive user
        assert len(result) == 2
        assert all(u["active"] for u in result)
        mock_client.close.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_search_users_impl_include_inactive(self, mock_get_client, mock_client, sample_users):
        """Test searching users including inactive."""
        mock_get_client.return_value = mock_client
        mock_client.search_users.return_value = sample_users

        result = _search_users_impl("john", active_only=False)

        # Should include all 3 users
        assert len(result) == 3
        mock_client.close.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_search_users_impl_with_groups(self, mock_get_client, mock_client, sample_users):
        """Test searching users with group information."""
        mock_get_client.return_value = mock_client
        mock_client.search_users.return_value = sample_users[:1]
        mock_client.get_user_groups.return_value = [{"name": "developers"}]

        result = _search_users_impl("john", include_groups=True, active_only=False)

        assert result[0]["groups"] == ["developers"]
        mock_client.close.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_search_users_impl_assignable(self, mock_get_client, mock_client, sample_users):
        """Test searching assignable users for a project."""
        mock_get_client.return_value = mock_client
        mock_client.find_assignable_users.return_value = sample_users[:2]

        result = _search_users_impl("john", project="TEST", assignable=True)

        mock_client.find_assignable_users.assert_called_once()
        assert len(result) == 2
        mock_client.close.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_get_user_impl(self, mock_get_client, mock_client, sample_users):
        """Test getting a user by account ID."""
        mock_get_client.return_value = mock_client
        mock_client.get_user.return_value = sample_users[0]

        result = _get_user_impl("user123")

        assert result["displayName"] == "John Doe"
        mock_client.close.assert_called_once()


# =============================================================================
# Test Group Implementation Functions
# =============================================================================


class TestGroupImplementation:
    """Tests for group implementation functions."""

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_list_groups_impl(self, mock_get_client, mock_client, sample_groups):
        """Test listing groups."""
        mock_get_client.return_value = mock_client
        mock_client.find_groups.return_value = {"groups": sample_groups}

        result = _list_groups_impl()

        assert len(result) == 4
        mock_client.find_groups.assert_called_once()
        mock_client.close.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_list_groups_impl_with_query(self, mock_get_client, mock_client, sample_groups):
        """Test listing groups with query."""
        mock_get_client.return_value = mock_client
        mock_client.find_groups.return_value = {"groups": sample_groups}

        result = _list_groups_impl(query="dev")

        mock_client.find_groups.assert_called_once()
        call_args = mock_client.find_groups.call_args
        assert call_args.kwargs["query"] == "dev"

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_get_group_members_impl(self, mock_get_client, mock_client, sample_users):
        """Test getting group members."""
        mock_get_client.return_value = mock_client
        mock_client.get_group_members.return_value = {
            "values": sample_users,
            "isLast": True,
        }

        result = _get_group_members_impl("developers")

        mock_client.get_group_members.assert_called_once()
        mock_client.close.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_create_group_impl(self, mock_get_client, mock_client):
        """Test creating a group."""
        mock_get_client.return_value = mock_client
        new_group = {"name": "new-team", "groupId": "group123"}
        mock_client.create_group.return_value = new_group

        result = _create_group_impl("new-team")

        assert result == new_group
        mock_client.close.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_delete_group_impl_dry_run(self, mock_get_client, mock_client):
        """Test deleting a group with dry run."""
        mock_get_client.return_value = mock_client

        result = _delete_group_impl("developers", dry_run=True)

        assert result["action"] == "dry_run"
        assert result["would_delete"] is True
        mock_client.delete_group.assert_not_called()
        mock_client.close.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_delete_group_impl_actual(self, mock_get_client, mock_client):
        """Test actually deleting a group."""
        mock_get_client.return_value = mock_client
        mock_client.delete_group.return_value = None

        result = _delete_group_impl("developers", dry_run=False)

        assert result["action"] == "deleted"
        mock_client.delete_group.assert_called_once()
        mock_client.close.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_add_user_to_group_impl(self, mock_get_client, mock_client):
        """Test adding user to group."""
        mock_get_client.return_value = mock_client
        mock_client.search_users.return_value = [{"accountId": "user123"}]
        mock_client.add_user_to_group.return_value = {"name": "developers"}

        result = _add_user_to_group_impl("developers", "john@example.com")

        mock_client.add_user_to_group.assert_called_once()
        mock_client.close.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_remove_user_from_group_impl(self, mock_get_client, mock_client):
        """Test removing user from group."""
        mock_get_client.return_value = mock_client
        mock_client.search_users.return_value = [{"accountId": "user123"}]
        mock_client.remove_user_from_group.return_value = None

        result = _remove_user_from_group_impl("developers", "john@example.com")

        mock_client.remove_user_from_group.assert_called_once()
        mock_client.close.assert_called_once()


# =============================================================================
# Test Automation Implementation Functions
# =============================================================================


class TestAutomationImplementation:
    """Tests for automation implementation functions."""

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_automation_client")
    def test_list_automation_rules_impl(
        self, mock_get_client, mock_automation_client, sample_automation_rules
    ):
        """Test listing automation rules."""
        mock_get_client.return_value = mock_automation_client
        mock_automation_client.get_rules.return_value = {
            "values": sample_automation_rules,
            "hasMore": False,
        }

        result = _list_automation_rules_impl()

        assert len(result) == 2
        # Note: automation client doesn't call close()

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_automation_client")
    def test_list_automation_rules_impl_with_project(
        self, mock_get_client, mock_automation_client, sample_automation_rules
    ):
        """Test listing automation rules for a project."""
        mock_get_client.return_value = mock_automation_client
        mock_automation_client.search_rules.return_value = {
            "values": sample_automation_rules,
            "hasMore": False,
        }

        result = _list_automation_rules_impl(project="TEST")

        mock_automation_client.search_rules.assert_called_once()
        assert len(result) == 2

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_automation_client")
    def test_get_automation_rule_impl(self, mock_get_client, mock_automation_client):
        """Test getting an automation rule."""
        mock_get_client.return_value = mock_automation_client
        rule = {"id": "1", "name": "Test Rule"}
        mock_automation_client.get_rule.return_value = rule

        result = _get_automation_rule_impl("1")

        assert result == rule

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_automation_client")
    def test_enable_automation_rule_impl(self, mock_get_client, mock_automation_client):
        """Test enabling an automation rule."""
        mock_get_client.return_value = mock_automation_client
        rule = {"id": "1", "state": "ENABLED"}
        mock_automation_client.enable_rule.return_value = rule

        result = _enable_automation_rule_impl("1")

        assert result == rule

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_automation_client")
    def test_disable_automation_rule_impl(self, mock_get_client, mock_automation_client):
        """Test disabling an automation rule."""
        mock_get_client.return_value = mock_automation_client
        rule = {"id": "1", "state": "DISABLED"}
        mock_automation_client.disable_rule.return_value = rule

        result = _disable_automation_rule_impl("1")

        assert result == rule

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_automation_client")
    def test_toggle_automation_rule_impl(self, mock_get_client, mock_automation_client):
        """Test toggling an automation rule."""
        mock_get_client.return_value = mock_automation_client
        mock_automation_client.get_rule.return_value = {"id": "1", "state": "ENABLED"}
        mock_automation_client.disable_rule.return_value = {"id": "1", "state": "DISABLED"}

        result = _toggle_automation_rule_impl("1")

        mock_automation_client.disable_rule.assert_called_once()


# =============================================================================
# Test Permission Scheme Implementation Functions
# =============================================================================


class TestPermissionSchemeImplementation:
    """Tests for permission scheme implementation functions."""

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_list_permission_schemes_impl(
        self, mock_get_client, mock_client, sample_permission_schemes
    ):
        """Test listing permission schemes."""
        mock_get_client.return_value = mock_client
        mock_client.get_permission_schemes.return_value = {
            "permissionSchemes": sample_permission_schemes
        }

        result = _list_permission_schemes_impl()

        # Returns a list of schemes, not the whole dict
        assert len(result) == 2
        mock_client.close.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_get_permission_scheme_impl(self, mock_get_client, mock_client):
        """Test getting a permission scheme."""
        mock_get_client.return_value = mock_client
        scheme = {"id": "10000", "name": "Default"}
        mock_client.get_permission_scheme.return_value = scheme

        result = _get_permission_scheme_impl("10000")

        # Returns {"scheme": scheme, ...}
        assert result["scheme"] == scheme
        mock_client.close.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_create_permission_scheme_impl(self, mock_get_client, mock_client):
        """Test creating a permission scheme."""
        mock_get_client.return_value = mock_client
        scheme = {"id": "10002", "name": "New Scheme"}
        mock_client.create_permission_scheme.return_value = scheme

        result = _create_permission_scheme_impl("New Scheme", "A new scheme")

        assert result == scheme
        mock_client.close.assert_called_once()


# =============================================================================
# Test Notification Scheme Implementation Functions
# =============================================================================


class TestNotificationSchemeImplementation:
    """Tests for notification scheme implementation functions."""

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_list_notification_schemes_impl(self, mock_get_client, mock_client):
        """Test listing notification schemes."""
        mock_get_client.return_value = mock_client
        schemes = [{"id": "1", "name": "Default Notifications"}]
        mock_client.get_notification_schemes.return_value = {"values": schemes}

        result = _list_notification_schemes_impl()

        assert len(result) == 1
        mock_client.close.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_get_notification_scheme_impl(self, mock_get_client, mock_client):
        """Test getting a notification scheme."""
        mock_get_client.return_value = mock_client
        scheme = {"id": "1", "name": "Default"}
        mock_client.get_notification_scheme.return_value = scheme

        result = _get_notification_scheme_impl("1")

        assert result == scheme
        mock_client.close.assert_called_once()


# =============================================================================
# Test Screen Implementation Functions
# =============================================================================


class TestScreenImplementation:
    """Tests for screen implementation functions."""

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_list_screens_impl(self, mock_get_client, mock_client, sample_screens):
        """Test listing screens."""
        mock_get_client.return_value = mock_client
        mock_client.get_screens.return_value = {"values": sample_screens}

        result = _list_screens_impl()

        assert len(result) == 2
        mock_client.close.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_get_screen_impl(self, mock_get_client, mock_client):
        """Test getting a screen."""
        mock_get_client.return_value = mock_client
        screen = {"id": "1", "name": "Default Screen"}
        mock_client.get_screen.return_value = screen

        result = _get_screen_impl("1")

        assert result == screen
        mock_client.close.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_list_screen_tabs_impl(self, mock_get_client, mock_client):
        """Test listing screen tabs."""
        mock_get_client.return_value = mock_client
        tabs = [{"id": "1", "name": "Field Tab"}]
        mock_client.get_screen_tabs.return_value = tabs

        result = _list_screen_tabs_impl("1")

        assert len(result) == 1
        mock_client.close.assert_called_once()


# =============================================================================
# Test Issue Type Implementation Functions
# =============================================================================


class TestIssueTypeImplementation:
    """Tests for issue type implementation functions."""

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_list_issue_types_impl(self, mock_get_client, mock_client, sample_issue_types):
        """Test listing issue types."""
        mock_get_client.return_value = mock_client
        mock_client.get_issue_types.return_value = sample_issue_types

        result = _list_issue_types_impl()

        assert len(result) == 3
        mock_client.close.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_list_issue_types_impl_subtask_only(
        self, mock_get_client, mock_client, sample_issue_types
    ):
        """Test listing only subtask issue types."""
        mock_get_client.return_value = mock_client
        mock_client.get_issue_types.return_value = sample_issue_types

        result = _list_issue_types_impl(subtask_only=True)

        assert len(result) == 1
        assert result[0]["name"] == "Sub-task"
        mock_client.close.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_get_issue_type_impl(self, mock_get_client, mock_client):
        """Test getting an issue type."""
        mock_get_client.return_value = mock_client
        issue_type = {"id": "10001", "name": "Bug"}
        mock_client.get_issue_type.return_value = issue_type

        result = _get_issue_type_impl("10001")

        assert result == issue_type
        mock_client.close.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_create_issue_type_impl(self, mock_get_client, mock_client):
        """Test creating an issue type."""
        mock_get_client.return_value = mock_client
        issue_type = {"id": "10004", "name": "Feature"}
        mock_client.create_issue_type.return_value = issue_type

        result = _create_issue_type_impl("Feature", "A new feature", issue_type="standard")

        assert result == issue_type
        mock_client.close.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_delete_issue_type_impl(self, mock_get_client, mock_client):
        """Test deleting an issue type."""
        mock_get_client.return_value = mock_client
        mock_client.delete_issue_type.return_value = None

        result = _delete_issue_type_impl("10004")

        mock_client.delete_issue_type.assert_called_once_with("10004")
        mock_client.close.assert_called_once()


# =============================================================================
# Test Workflow Implementation Functions
# =============================================================================


class TestWorkflowImplementation:
    """Tests for workflow implementation functions."""

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_list_workflows_impl(self, mock_get_client, mock_client, sample_workflows):
        """Test listing workflows."""
        mock_get_client.return_value = mock_client
        mock_client.get_workflows.return_value = sample_workflows

        result = _list_workflows_impl()

        # Returns a dict with "workflows" key
        assert "workflows" in result
        mock_client.close.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_get_workflow_impl(self, mock_get_client, mock_client, sample_workflows):
        """Test getting a workflow."""
        mock_get_client.return_value = mock_client
        # search_workflows returns {"values": [...]}
        mock_client.search_workflows.return_value = {"values": [sample_workflows[0]]}

        result = _get_workflow_impl("Default Workflow")

        assert result["name"] == "Default Workflow"
        mock_client.close.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_get_workflow_for_issue_impl(self, mock_get_client, mock_client, sample_workflows):
        """Test getting workflow for an issue."""
        mock_get_client.return_value = mock_client
        mock_client.get_issue.return_value = {
            "key": "TEST-1",
            "fields": {
                "project": {"key": "TEST"},
                "issuetype": {"id": "10001"},
                "status": {"name": "Open"},
            },
        }
        mock_client.get_project_workflow_scheme.return_value = {
            "defaultWorkflow": "Default Workflow",
            "issueTypeMappings": {},
        }
        mock_client.search_workflows.return_value = {"values": [sample_workflows[0]]}

        result = _get_workflow_for_issue_impl("TEST-1")

        assert result["name"] == "Default Workflow"
        mock_client.close.assert_called()

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_list_statuses_impl(self, mock_get_client, mock_client, sample_statuses):
        """Test listing statuses."""
        mock_get_client.return_value = mock_client
        mock_client.get_statuses.return_value = sample_statuses

        result = _list_statuses_impl()

        assert len(result) == 3
        mock_client.close.assert_called_once()


# =============================================================================
# Test Formatting Functions
# =============================================================================


class TestFormattingFunctions:
    """Tests for formatting functions."""

    def test_format_projects(self, sample_projects):
        """Test formatting projects list."""
        result = _format_projects(sample_projects)

        assert "PROJ1" in result
        assert "PROJ2" in result

    def test_format_projects_empty(self):
        """Test formatting empty projects list."""
        result = _format_projects({"values": [], "total": 0})
        assert "No projects found" in result

    def test_format_project(self, sample_project):
        """Test formatting single project."""
        result = _format_project(sample_project)

        assert "TEST" in result
        assert "Test Project" in result
        assert "John Doe" in result

    def test_format_categories(self):
        """Test formatting categories."""
        categories = [
            {"id": "1", "name": "Development", "description": "Dev projects"},
            {"id": "2", "name": "Support", "description": "Support projects"},
        ]
        result = _format_categories(categories)

        assert "Development" in result
        assert "Support" in result

    def test_format_users(self, sample_users):
        """Test formatting users."""
        result = _format_users(sample_users)

        assert "John Doe" in result
        assert "Jane Smith" in result

    def test_format_users_with_groups(self, sample_users):
        """Test formatting users with groups."""
        sample_users[0]["groups"] = ["developers", "qa-team"]
        result = _format_users(sample_users, show_groups=True)

        assert "developers" in result

    def test_format_groups(self, sample_groups):
        """Test formatting groups."""
        result = _format_groups(sample_groups)

        assert "developers" in result
        assert "jira-administrators" in result

    def test_format_groups_show_system(self, sample_groups):
        """Test formatting groups with system flag."""
        result = _format_groups(sample_groups, show_system=True)

        # System groups should be shown
        assert "jira-administrators" in result
        assert "jira-users" in result

    def test_format_automation_rules(self, sample_automation_rules):
        """Test formatting automation rules."""
        result = _format_automation_rules(sample_automation_rules)

        assert "Auto-assign bugs" in result
        assert "ENABLED" in result or "enabled" in result.lower()

    def test_format_permission_schemes(self, sample_permission_schemes):
        """Test formatting permission schemes."""
        result = _format_permission_schemes(sample_permission_schemes)

        assert "Default Permission Scheme" in result
        assert "Restricted Scheme" in result

    def test_format_screens(self, sample_screens):
        """Test formatting screens."""
        result = _format_screens(sample_screens)

        assert "Default Screen" in result
        assert "Bug Screen" in result

    def test_format_issue_types(self, sample_issue_types):
        """Test formatting issue types."""
        result = _format_issue_types(sample_issue_types)

        assert "Bug" in result
        assert "Task" in result
        assert "Sub-task" in result

    def test_format_workflows(self, sample_workflows):
        """Test formatting workflows."""
        result = _format_workflows(sample_workflows)

        assert "Default Workflow" in result
        assert "Bug Workflow" in result

    def test_format_statuses(self, sample_statuses):
        """Test formatting statuses."""
        result = _format_statuses(sample_statuses)

        assert "Open" in result
        assert "In Progress" in result
        assert "Done" in result


# =============================================================================
# Test CLI Commands - Project
# =============================================================================


class TestProjectCLI:
    """Tests for project CLI commands."""

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_project_list_command(self, mock_get_client, mock_client, sample_projects, cli_runner):
        """Test project list command."""
        mock_get_client.return_value = mock_client
        mock_client.search_projects.return_value = sample_projects

        result = cli_runner.invoke(admin, ["project", "list"])

        assert result.exit_code == 0
        assert "PROJ1" in result.output

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_project_list_json_output(
        self, mock_get_client, mock_client, sample_projects, cli_runner
    ):
        """Test project list with JSON output."""
        mock_get_client.return_value = mock_client
        mock_client.search_projects.return_value = sample_projects

        result = cli_runner.invoke(admin, ["project", "list", "--output", "json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "values" in data

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_project_get_command(self, mock_get_client, mock_client, sample_project, cli_runner):
        """Test project get command."""
        mock_get_client.return_value = mock_client
        mock_client.get_project.return_value = sample_project

        result = cli_runner.invoke(admin, ["project", "get", "TEST"])

        assert result.exit_code == 0
        assert "TEST" in result.output


# =============================================================================
# Test CLI Commands - User
# =============================================================================


class TestUserCLI:
    """Tests for user CLI commands."""

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_user_search_command(self, mock_get_client, mock_client, sample_users, cli_runner):
        """Test user search command."""
        mock_get_client.return_value = mock_client
        mock_client.search_users.return_value = sample_users

        result = cli_runner.invoke(admin, ["user", "search", "john"])

        assert result.exit_code == 0
        assert "John Doe" in result.output

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_user_get_command(self, mock_get_client, mock_client, sample_users, cli_runner):
        """Test user get command."""
        mock_get_client.return_value = mock_client
        mock_client.get_user.return_value = sample_users[0]

        result = cli_runner.invoke(admin, ["user", "get", "user123"])

        assert result.exit_code == 0
        assert "John Doe" in result.output


# =============================================================================
# Test CLI Commands - Group
# =============================================================================


class TestGroupCLI:
    """Tests for group CLI commands."""

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_group_list_command(self, mock_get_client, mock_client, sample_groups, cli_runner):
        """Test group list command."""
        mock_get_client.return_value = mock_client
        mock_client.find_groups.return_value = {"groups": sample_groups}

        result = cli_runner.invoke(admin, ["group", "list"])

        assert result.exit_code == 0
        assert "developers" in result.output

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_group_create_command(self, mock_get_client, mock_client, cli_runner):
        """Test group create command."""
        mock_get_client.return_value = mock_client
        mock_client.create_group.return_value = {"name": "new-team", "groupId": "123"}

        result = cli_runner.invoke(admin, ["group", "create", "new-team"])

        assert result.exit_code == 0
        assert "new-team" in result.output

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_group_delete_dry_run(self, mock_get_client, mock_client, cli_runner):
        """Test group delete with dry run."""
        mock_get_client.return_value = mock_client

        result = cli_runner.invoke(admin, ["group", "delete", "developers", "--dry-run"])

        assert result.exit_code == 0
        assert "dry" in result.output.lower() or "would" in result.output.lower()


# =============================================================================
# Test CLI Commands - Automation
# =============================================================================


class TestAutomationCLI:
    """Tests for automation CLI commands."""

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_automation_client")
    def test_automation_list_command(
        self, mock_get_client, mock_automation_client, sample_automation_rules, cli_runner
    ):
        """Test automation list command."""
        mock_get_client.return_value = mock_automation_client
        mock_automation_client.get_rules.return_value = {
            "values": sample_automation_rules,
            "hasMore": False,
        }

        result = cli_runner.invoke(admin, ["automation", "list"])

        assert result.exit_code == 0
        assert "Auto-assign bugs" in result.output

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_automation_client")
    def test_automation_enable_command(self, mock_get_client, mock_automation_client, cli_runner):
        """Test automation enable command."""
        mock_get_client.return_value = mock_automation_client
        mock_automation_client.enable_rule.return_value = {"id": "1", "state": "ENABLED"}

        result = cli_runner.invoke(admin, ["automation", "enable", "1"])

        assert result.exit_code == 0


# =============================================================================
# Test CLI Commands - Issue Type
# =============================================================================


class TestIssueTypeCLI:
    """Tests for issue type CLI commands."""

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_issue_type_list_command(
        self, mock_get_client, mock_client, sample_issue_types, cli_runner
    ):
        """Test issue type list command."""
        mock_get_client.return_value = mock_client
        mock_client.get_issue_types.return_value = sample_issue_types

        result = cli_runner.invoke(admin, ["issue-type", "list"])

        assert result.exit_code == 0
        assert "Bug" in result.output
        assert "Task" in result.output


# =============================================================================
# Test CLI Commands - Workflow
# =============================================================================


class TestWorkflowCLI:
    """Tests for workflow CLI commands."""

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_workflow_list_command(
        self, mock_get_client, mock_client, sample_workflows, cli_runner
    ):
        """Test workflow list command."""
        mock_get_client.return_value = mock_client
        mock_client.get_workflows.return_value = sample_workflows

        result = cli_runner.invoke(admin, ["workflow", "list"])

        assert result.exit_code == 0


# =============================================================================
# Test CLI Commands - Status
# =============================================================================


class TestStatusCLI:
    """Tests for status CLI commands."""

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_status_list_command(
        self, mock_get_client, mock_client, sample_statuses, cli_runner
    ):
        """Test status list command."""
        mock_get_client.return_value = mock_client
        mock_client.get_statuses.return_value = sample_statuses

        result = cli_runner.invoke(admin, ["status", "list"])

        assert result.exit_code == 0
        assert "Open" in result.output
        assert "Done" in result.output


# =============================================================================
# Test Error Handling
# =============================================================================


class TestErrorHandling:
    """Tests for error handling in CLI commands."""

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_jira_error_handling(self, mock_get_client, mock_client, cli_runner):
        """Test JiraError handling in CLI."""
        mock_get_client.return_value = mock_client
        mock_client.search_projects.side_effect = JiraError("API error")

        result = cli_runner.invoke(admin, ["project", "list"])

        assert result.exit_code != 0

    @patch("jira_assistant_skills.cli.commands.admin_cmds.get_jira_client")
    def test_validation_error_handling(self, mock_get_client, mock_client, cli_runner):
        """Test ValidationError handling in CLI."""
        mock_get_client.return_value = mock_client
        mock_client.get_project.side_effect = ValidationError("Invalid project key")

        result = cli_runner.invoke(admin, ["project", "get", "INVALID"])

        assert result.exit_code != 0
