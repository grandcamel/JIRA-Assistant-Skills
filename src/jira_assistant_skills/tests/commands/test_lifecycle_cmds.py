"""
Unit tests for lifecycle CLI commands.

Tests cover:
- transition: Transitioning issues to new status
- transitions: Getting available transitions
- assign: Assigning/unassigning issues
- resolve: Resolving issues
- reopen: Reopening issues
- version: Version management
- component: Component management
"""

import json
from copy import deepcopy
from unittest.mock import MagicMock, patch

import pytest

from jira_assistant_skills.cli.commands.lifecycle_cmds import (
    _assign_issue_impl,
    _create_component_impl,
    _create_version_impl,
    _get_components_impl,
    _get_transitions_impl,
    _get_versions_impl,
    _reopen_issue_impl,
    _resolve_issue_impl,
    _transition_issue_impl,
    lifecycle,
)


# =============================================================================
# Tests for _get_transitions_impl
# =============================================================================


@pytest.mark.unit
class TestGetTransitionsImpl:
    """Tests for the _get_transitions_impl implementation function."""

    def test_get_transitions_success(self, mock_jira_client, sample_transitions):
        """Test retrieving transitions successfully."""
        mock_jira_client.get_transitions.return_value = deepcopy(sample_transitions)

        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _get_transitions_impl(issue_key="PROJ-123")

        mock_jira_client.get_transitions.assert_called_once_with("PROJ-123")
        assert len(result) == 3
        assert result[0]["name"] == "In Progress"

    def test_get_transitions_normalizes_key(self, mock_jira_client, sample_transitions):
        """Test that issue key is normalized to uppercase."""
        mock_jira_client.get_transitions.return_value = deepcopy(sample_transitions)

        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            _get_transitions_impl(issue_key="proj-123")

        mock_jira_client.get_transitions.assert_called_once_with("PROJ-123")

    def test_get_transitions_empty(self, mock_jira_client):
        """Test handling no available transitions."""
        mock_jira_client.get_transitions.return_value = []

        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _get_transitions_impl(issue_key="PROJ-123")

        assert result == []

    def test_get_transitions_closes_client(self, mock_jira_client, sample_transitions):
        """Test that client is closed after operation."""
        mock_jira_client.get_transitions.return_value = deepcopy(sample_transitions)

        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            _get_transitions_impl(issue_key="PROJ-123")

        mock_jira_client.close.assert_called_once()


# =============================================================================
# Tests for _transition_issue_impl
# =============================================================================


@pytest.mark.unit
class TestTransitionIssueImpl:
    """Tests for the _transition_issue_impl implementation function."""

    def test_transition_by_name(self, mock_jira_client, sample_issue, sample_transitions):
        """Test transitioning an issue by status name."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)
        mock_jira_client.get_transitions.return_value = deepcopy(sample_transitions)

        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ), patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.has_project_context",
            return_value=False,
        ):
            result = _transition_issue_impl(
                issue_key="PROJ-123",
                transition_name="In Progress",
            )

        assert result["issue_key"] == "PROJ-123"
        assert result["transition"] == "In Progress"
        mock_jira_client.transition_issue.assert_called_once()

    def test_transition_by_id(self, mock_jira_client, sample_issue, sample_transitions):
        """Test transitioning an issue by transition ID."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)
        mock_jira_client.get_transitions.return_value = deepcopy(sample_transitions)

        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ), patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.has_project_context",
            return_value=False,
        ):
            result = _transition_issue_impl(
                issue_key="PROJ-123",
                transition_id="21",
            )

        assert result["issue_key"] == "PROJ-123"
        mock_jira_client.transition_issue.assert_called_once()

    def test_transition_with_resolution(
        self, mock_jira_client, sample_issue, sample_transitions
    ):
        """Test transitioning with a resolution."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)
        mock_jira_client.get_transitions.return_value = deepcopy(sample_transitions)

        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ), patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.has_project_context",
            return_value=False,
        ):
            result = _transition_issue_impl(
                issue_key="PROJ-123",
                transition_name="Done",
                resolution="Fixed",
            )

        assert result["resolution"] == "Fixed"
        call_args = mock_jira_client.transition_issue.call_args
        assert call_args[1]["fields"]["resolution"] == {"name": "Fixed"}

    def test_transition_dry_run(self, mock_jira_client, sample_issue, sample_transitions):
        """Test dry-run mode doesn't make changes."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)
        mock_jira_client.get_transitions.return_value = deepcopy(sample_transitions)

        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ), patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.has_project_context",
            return_value=False,
        ):
            result = _transition_issue_impl(
                issue_key="PROJ-123",
                transition_name="In Progress",
                dry_run=True,
            )

        assert result["dry_run"] is True
        mock_jira_client.transition_issue.assert_not_called()

    def test_transition_no_target_raises_error(self, mock_jira_client, sample_issue):
        """Test that not specifying transition raises error."""
        from jira_assistant_skills_lib import ValidationError

        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)

        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ), pytest.raises(ValidationError, match="Either --id or --to"):
            _transition_issue_impl(issue_key="PROJ-123")

    def test_transition_closes_client(
        self, mock_jira_client, sample_issue, sample_transitions
    ):
        """Test that client is closed after operation."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)
        mock_jira_client.get_transitions.return_value = deepcopy(sample_transitions)

        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ), patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.has_project_context",
            return_value=False,
        ):
            _transition_issue_impl(
                issue_key="PROJ-123",
                transition_name="In Progress",
            )

        mock_jira_client.close.assert_called_once()


# =============================================================================
# Tests for _assign_issue_impl
# =============================================================================


@pytest.mark.unit
class TestAssignIssueImpl:
    """Tests for the _assign_issue_impl implementation function."""

    def test_assign_to_user(self, mock_jira_client, sample_issue):
        """Test assigning an issue to a user."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)

        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _assign_issue_impl(
                issue_key="PROJ-123",
                user="user@example.com",
            )

        assert result["issue_key"] == "PROJ-123"
        assert result["target_assignee"] == "user@example.com"
        mock_jira_client.assign_issue.assert_called_once_with("PROJ-123", "user@example.com")

    def test_assign_to_self(self, mock_jira_client, sample_issue):
        """Test assigning an issue to self."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)

        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _assign_issue_impl(
                issue_key="PROJ-123",
                assign_to_self=True,
            )

        assert result["action"] == "assign to self"
        mock_jira_client.assign_issue.assert_called_once_with("PROJ-123", "-1")

    def test_unassign(self, mock_jira_client, sample_issue):
        """Test unassigning an issue."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)

        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _assign_issue_impl(
                issue_key="PROJ-123",
                unassign=True,
            )

        assert result["action"] == "unassign"
        mock_jira_client.assign_issue.assert_called_once_with("PROJ-123", None)

    def test_assign_dry_run(self, mock_jira_client, sample_issue):
        """Test dry-run mode doesn't make changes."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)

        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _assign_issue_impl(
                issue_key="PROJ-123",
                user="user@example.com",
                dry_run=True,
            )

        assert result["dry_run"] is True
        mock_jira_client.assign_issue.assert_not_called()

    def test_assign_multiple_options_raises_error(self, mock_jira_client):
        """Test that specifying multiple assignment options raises error."""
        from jira_assistant_skills_lib import ValidationError

        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ), pytest.raises(ValidationError, match="Specify exactly one"):
            _assign_issue_impl(
                issue_key="PROJ-123",
                user="user@example.com",
                assign_to_self=True,
            )

    def test_assign_closes_client(self, mock_jira_client, sample_issue):
        """Test that client is closed after operation."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)

        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            _assign_issue_impl(
                issue_key="PROJ-123",
                user="user@example.com",
            )

        mock_jira_client.close.assert_called_once()


# =============================================================================
# Tests for _resolve_issue_impl
# =============================================================================


@pytest.mark.unit
class TestResolveIssueImpl:
    """Tests for the _resolve_issue_impl implementation function."""

    def test_resolve_issue_default_resolution(
        self, mock_jira_client, sample_transitions_with_done
    ):
        """Test resolving an issue with default resolution."""
        mock_jira_client.get_transitions.return_value = deepcopy(
            sample_transitions_with_done
        )

        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            _resolve_issue_impl(issue_key="PROJ-123")

        mock_jira_client.transition_issue.assert_called_once()
        call_args = mock_jira_client.transition_issue.call_args
        assert call_args[1]["fields"]["resolution"] == {"name": "Fixed"}

    def test_resolve_issue_custom_resolution(
        self, mock_jira_client, sample_transitions_with_done
    ):
        """Test resolving with custom resolution."""
        mock_jira_client.get_transitions.return_value = deepcopy(
            sample_transitions_with_done
        )

        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            _resolve_issue_impl(issue_key="PROJ-123", resolution="Won't Fix")

        call_args = mock_jira_client.transition_issue.call_args
        assert call_args[1]["fields"]["resolution"] == {"name": "Won't Fix"}

    def test_resolve_issue_with_comment(
        self, mock_jira_client, sample_transitions_with_done
    ):
        """Test resolving with a comment."""
        mock_jira_client.get_transitions.return_value = deepcopy(
            sample_transitions_with_done
        )

        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            _resolve_issue_impl(
                issue_key="PROJ-123",
                comment="Fixed in version 1.0.0",
            )

        call_args = mock_jira_client.transition_issue.call_args
        assert "comment" in call_args[1]["fields"]

    def test_resolve_no_transition_available(self, mock_jira_client, sample_transitions):
        """Test resolving when no resolve transition is available."""
        from jira_assistant_skills_lib import ValidationError

        # sample_transitions doesn't have a "done" transition
        mock_jira_client.get_transitions.return_value = [
            {"id": "1", "name": "In Progress"}
        ]

        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ), pytest.raises(ValidationError, match="No resolution transition"):
            _resolve_issue_impl(issue_key="PROJ-123")


# =============================================================================
# Tests for _reopen_issue_impl
# =============================================================================


@pytest.mark.unit
class TestReopenIssueImpl:
    """Tests for the _reopen_issue_impl implementation function."""

    def test_reopen_issue(self, mock_jira_client):
        """Test reopening an issue."""
        mock_jira_client.get_transitions.return_value = [
            {"id": "11", "name": "Reopen"},
            {"id": "21", "name": "In Progress"},
        ]

        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            _reopen_issue_impl(issue_key="PROJ-123")

        mock_jira_client.transition_issue.assert_called_once()
        call_args = mock_jira_client.transition_issue.call_args
        assert call_args[0][1] == "11"  # Reopen transition ID

    def test_reopen_issue_with_comment(self, mock_jira_client):
        """Test reopening with a comment."""
        mock_jira_client.get_transitions.return_value = [
            {"id": "11", "name": "Reopen"},
        ]

        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            _reopen_issue_impl(
                issue_key="PROJ-123",
                comment="Regression found in testing",
            )

        call_args = mock_jira_client.transition_issue.call_args
        assert "comment" in call_args[1]["fields"]

    def test_reopen_no_transition_available(self, mock_jira_client):
        """Test reopening when no reopen transition is available."""
        from jira_assistant_skills_lib import ValidationError

        mock_jira_client.get_transitions.return_value = [
            {"id": "31", "name": "Done"}
        ]

        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ), pytest.raises(ValidationError, match="No reopen transition"):
            _reopen_issue_impl(issue_key="PROJ-123")


# =============================================================================
# Tests for Version Implementation Functions
# =============================================================================


@pytest.mark.unit
class TestGetVersionsImpl:
    """Tests for the _get_versions_impl implementation function."""

    def test_get_versions_success(self, mock_jira_client, sample_versions):
        """Test retrieving versions successfully."""
        mock_jira_client.get_versions.return_value = deepcopy(sample_versions)

        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _get_versions_impl(project="PROJ")

        assert len(result) == 3
        mock_jira_client.get_versions.assert_called_once_with("PROJ")

    def test_get_versions_unreleased_filter(self, mock_jira_client, sample_versions):
        """Test filtering for unreleased versions."""
        mock_jira_client.get_versions.return_value = deepcopy(sample_versions)

        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _get_versions_impl(project="PROJ", unreleased=True)

        assert all(not v.get("released") for v in result)

    def test_get_versions_closes_client(self, mock_jira_client, sample_versions):
        """Test that client is closed after operation."""
        mock_jira_client.get_versions.return_value = deepcopy(sample_versions)

        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            _get_versions_impl(project="PROJ")

        mock_jira_client.close.assert_called_once()


@pytest.mark.unit
class TestCreateVersionImpl:
    """Tests for the _create_version_impl implementation function."""

    def test_create_version_basic(self, mock_jira_client, sample_created_version):
        """Test creating a basic version."""
        mock_jira_client.create_version.return_value = deepcopy(sample_created_version)

        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _create_version_impl(project="PROJ", name="v1.0.0")

        assert result["name"] == "v1.0.0"
        mock_jira_client.create_version.assert_called_once()

    def test_create_version_dry_run(self, mock_jira_client):
        """Test dry-run mode doesn't create version."""
        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _create_version_impl(project="PROJ", name="v1.0.0", dry_run=True)

        assert result is None
        mock_jira_client.create_version.assert_not_called()


# =============================================================================
# Tests for Component Implementation Functions
# =============================================================================


@pytest.mark.unit
class TestGetComponentsImpl:
    """Tests for the _get_components_impl implementation function."""

    def test_get_components_success(self, mock_jira_client, sample_components):
        """Test retrieving components successfully."""
        mock_jira_client.get_components.return_value = deepcopy(sample_components)

        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _get_components_impl(project="PROJ")

        assert len(result) == 2
        mock_jira_client.get_components.assert_called_once_with("PROJ")

    def test_get_components_closes_client(self, mock_jira_client, sample_components):
        """Test that client is closed after operation."""
        mock_jira_client.get_components.return_value = deepcopy(sample_components)

        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            _get_components_impl(project="PROJ")

        mock_jira_client.close.assert_called_once()


@pytest.mark.unit
class TestCreateComponentImpl:
    """Tests for the _create_component_impl implementation function."""

    def test_create_component_basic(self, mock_jira_client, sample_created_component):
        """Test creating a basic component."""
        mock_jira_client.create_component.return_value = deepcopy(sample_created_component)

        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _create_component_impl(project="PROJ", name="Backend")

        assert result["name"] == "Backend"
        mock_jira_client.create_component.assert_called_once()

    def test_create_component_dry_run(self, mock_jira_client):
        """Test dry-run mode doesn't create component."""
        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _create_component_impl(project="PROJ", name="Backend", dry_run=True)

        assert result is None
        mock_jira_client.create_component.assert_not_called()


# =============================================================================
# Tests for CLI Commands
# =============================================================================


@pytest.mark.unit
class TestTransitionCommand:
    """Tests for the transition Click command."""

    def test_transition_cli_success(
        self, cli_runner, mock_jira_client, sample_issue, sample_transitions
    ):
        """Test CLI transition command success."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)
        mock_jira_client.get_transitions.return_value = deepcopy(sample_transitions)

        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ), patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.has_project_context",
            return_value=False,
        ):
            result = cli_runner.invoke(
                lifecycle, ["transition", "PROJ-123", "--to", "In Progress"]
            )

        assert result.exit_code == 0
        assert "Transitioned" in result.output


@pytest.mark.unit
class TestTransitionsCommand:
    """Tests for the transitions Click command."""

    def test_transitions_cli_success(
        self, cli_runner, mock_jira_client, sample_transitions
    ):
        """Test CLI transitions command success."""
        mock_jira_client.get_transitions.return_value = deepcopy(sample_transitions)

        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = cli_runner.invoke(lifecycle, ["transitions", "PROJ-123"])

        assert result.exit_code == 0
        assert "Available transitions" in result.output

    def test_transitions_cli_json_output(
        self, cli_runner, mock_jira_client, sample_transitions
    ):
        """Test CLI transitions command with JSON output."""
        mock_jira_client.get_transitions.return_value = deepcopy(sample_transitions)

        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = cli_runner.invoke(
                lifecycle, ["transitions", "PROJ-123", "--output", "json"]
            )

        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert len(parsed) == 3


@pytest.mark.unit
class TestAssignCommand:
    """Tests for the assign Click command."""

    def test_assign_cli_self(self, cli_runner, mock_jira_client, sample_issue):
        """Test CLI assign command with --self."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)

        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = cli_runner.invoke(lifecycle, ["assign", "PROJ-123", "--self"])

        assert result.exit_code == 0
        assert "Assigned" in result.output


@pytest.mark.unit
class TestVersionCommands:
    """Tests for version subcommands."""

    def test_version_list_cli_success(
        self, cli_runner, mock_jira_client, sample_versions
    ):
        """Test CLI version list command success."""
        mock_jira_client.get_versions.return_value = deepcopy(sample_versions)

        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = cli_runner.invoke(lifecycle, ["version", "list", "PROJ"])

        assert result.exit_code == 0
        assert "Versions for project" in result.output


@pytest.mark.unit
class TestComponentCommands:
    """Tests for component subcommands."""

    def test_component_list_cli_success(
        self, cli_runner, mock_jira_client, sample_components
    ):
        """Test CLI component list command success."""
        mock_jira_client.get_components.return_value = deepcopy(sample_components)

        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = cli_runner.invoke(lifecycle, ["component", "list", "PROJ"])

        assert result.exit_code == 0
        assert "Components for project" in result.output
