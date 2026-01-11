"""Tests for agile_cmds.py - Agile/Scrum commands."""

import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from jira_assistant_skills.cli.commands.agile_cmds import (
    FIBONACCI_SEQUENCE,
    VALID_EPIC_COLORS,
    _add_to_epic_impl,
    _close_sprint_impl,
    _convert_description_to_adf,
    _create_epic_impl,
    _create_sprint_impl,
    _create_subtask_impl,
    _estimate_issue_impl,
    _format_epic_created,
    _format_epic_details,
    _format_sprint_details,
    _format_sprint_list,
    _format_velocity,
    _get_active_sprint_impl,
    _get_backlog_impl,
    _get_board_for_project,
    _get_board_id_for_project,
    _get_epic_impl,
    _get_estimates_impl,
    _get_sprint_impl,
    _get_velocity_impl,
    _list_sprints_impl,
    _move_to_backlog_impl,
    _move_to_sprint_impl,
    _parse_date_safe,
    _rank_issue_impl,
    _start_sprint_impl,
    _update_sprint_impl,
    agile,
)
from jira_assistant_skills_lib import JiraError, ValidationError

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_client():
    """Create a mock JIRA client."""
    client = MagicMock()
    client.close = MagicMock()
    return client


@pytest.fixture
def sample_epic():
    """Sample epic data."""
    return {
        "id": "10001",
        "key": "PROJ-100",
        "self": "https://test.atlassian.net/rest/api/3/issue/10001",
        "fields": {
            "summary": "Epic Summary",
            "status": {"name": "To Do"},
            "issuetype": {"name": "Epic"},
            "project": {"key": "PROJ"},
            "customfield_10011": "Epic Name Value",
        },
    }


@pytest.fixture
def sample_sprint():
    """Sample sprint data."""
    return {
        "id": 456,
        "name": "Sprint 1",
        "state": "active",
        "startDate": "2024-01-01T00:00:00.000Z",
        "endDate": "2024-01-14T00:00:00.000Z",
        "goal": "Complete feature X",
    }


@pytest.fixture
def sample_board():
    """Sample board data."""
    return {
        "id": 123,
        "name": "PROJ board",
        "type": "scrum",
        "location": {"projectKey": "PROJ"},
    }


@pytest.fixture
def sample_issues():
    """Sample issues for sprint/backlog."""
    return [
        {
            "key": "PROJ-1",
            "fields": {
                "summary": "Issue 1",
                "status": {"name": "To Do"},
                "customfield_10016": 5,
            },
        },
        {
            "key": "PROJ-2",
            "fields": {
                "summary": "Issue 2",
                "status": {"name": "Done"},
                "customfield_10016": 3,
            },
        },
        {
            "key": "PROJ-3",
            "fields": {
                "summary": "Issue 3",
                "status": {"name": "In Progress"},
                "customfield_10016": 8,
            },
        },
    ]


@pytest.fixture
def sample_velocity_sprints():
    """Sample closed sprints for velocity calculation."""
    return [
        {
            "id": 101,
            "name": "Sprint 1",
            "state": "closed",
            "startDate": "2024-01-01T00:00:00.000Z",
            "endDate": "2024-01-14T00:00:00.000Z",
        },
        {
            "id": 102,
            "name": "Sprint 2",
            "state": "closed",
            "startDate": "2024-01-15T00:00:00.000Z",
            "endDate": "2024-01-28T00:00:00.000Z",
        },
        {
            "id": 103,
            "name": "Sprint 3",
            "state": "closed",
            "startDate": "2024-01-29T00:00:00.000Z",
            "endDate": "2024-02-11T00:00:00.000Z",
        },
    ]


# =============================================================================
# Constants Tests
# =============================================================================


class TestConstants:
    """Tests for constants."""

    def test_valid_epic_colors(self):
        """Test valid epic colors."""
        assert "blue" in VALID_EPIC_COLORS
        assert "red" in VALID_EPIC_COLORS
        assert "green" in VALID_EPIC_COLORS
        assert len(VALID_EPIC_COLORS) == 11

    def test_fibonacci_sequence(self):
        """Test Fibonacci sequence."""
        assert FIBONACCI_SEQUENCE == [0, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]


# =============================================================================
# Helper Function Tests
# =============================================================================


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_get_board_for_project_scrum_board(self, mock_client):
        """Test finding scrum board for project."""
        mock_client.get_all_boards.return_value = {
            "values": [
                {"id": 1, "name": "Board 1", "type": "scrum"},
                {"id": 2, "name": "Board 2", "type": "kanban"},
            ]
        }

        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            result = _get_board_for_project("PROJ")

        assert result["id"] == 1
        assert result["type"] == "scrum"
        mock_client.close.assert_called_once()

    def test_get_board_for_project_kanban_fallback(self, mock_client):
        """Test falling back to any board when no scrum board."""
        mock_client.get_all_boards.return_value = {
            "values": [{"id": 2, "name": "Board 2", "type": "kanban"}]
        }

        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            result = _get_board_for_project("PROJ")

        assert result["id"] == 2
        assert result["type"] == "kanban"

    def test_get_board_for_project_no_board(self, mock_client):
        """Test no board found."""
        mock_client.get_all_boards.return_value = {"values": []}

        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            result = _get_board_for_project("PROJ")

        assert result is None

    def test_get_board_for_project_with_client(self, mock_client):
        """Test with provided client."""
        mock_client.get_all_boards.return_value = {
            "values": [{"id": 1, "name": "Board", "type": "scrum"}]
        }

        result = _get_board_for_project("PROJ", client=mock_client)

        assert result["id"] == 1
        mock_client.close.assert_not_called()

    def test_get_board_id_for_project_success(self, mock_client):
        """Test getting board ID for project."""
        mock_client.get_all_boards.return_value = {
            "values": [{"id": 123, "name": "Board", "type": "scrum"}]
        }

        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            result = _get_board_id_for_project("PROJ")

        assert result == 123

    def test_get_board_id_for_project_no_board(self, mock_client):
        """Test error when no board found."""
        mock_client.get_all_boards.return_value = {"values": []}

        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            with pytest.raises(ValidationError, match="No board found"):
                _get_board_id_for_project("PROJ")

    def test_parse_date_safe_valid(self):
        """Test parsing valid date."""
        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.parse_date_to_iso",
            return_value="2024-01-15T00:00:00.000Z",
        ):
            result = _parse_date_safe("2024-01-15")
            assert result == "2024-01-15T00:00:00.000Z"

    def test_parse_date_safe_none(self):
        """Test parsing None date."""
        result = _parse_date_safe(None)
        assert result is None

    def test_parse_date_safe_empty(self):
        """Test parsing empty date."""
        result = _parse_date_safe("")
        assert result is None

    def test_parse_date_safe_invalid(self):
        """Test parsing invalid date."""
        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.parse_date_to_iso",
            side_effect=ValueError("Invalid date"),
        ):
            with pytest.raises(ValidationError, match="Invalid date"):
                _parse_date_safe("invalid")

    def test_convert_description_to_adf_json(self):
        """Test converting JSON description to ADF."""
        adf_json = '{"type": "doc", "version": 1, "content": []}'
        result = _convert_description_to_adf(adf_json)
        assert result == {"type": "doc", "version": 1, "content": []}

    def test_convert_description_to_adf_markdown(self):
        """Test converting markdown description to ADF."""
        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.markdown_to_adf",
            return_value={"type": "doc", "content": []},
        ):
            result = _convert_description_to_adf("# Heading\n\nText")
            assert result == {"type": "doc", "content": []}

    def test_convert_description_to_adf_plain_text(self):
        """Test converting plain text description to ADF."""
        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.text_to_adf",
            return_value={"type": "doc", "content": []},
        ):
            result = _convert_description_to_adf("Plain text")
            assert result == {"type": "doc", "content": []}


# =============================================================================
# Epic Implementation Tests
# =============================================================================


class TestEpicImplementation:
    """Tests for epic implementation functions."""

    def test_create_epic_impl_success(self, mock_client, sample_epic):
        """Test creating an epic."""
        mock_client.create_issue.return_value = sample_epic

        with (
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
                return_value=mock_client,
            ),
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_agile_fields",
                return_value={
                    "epic_name": "customfield_10011",
                    "epic_color": "customfield_10012",
                },
            ),
        ):
            result = _create_epic_impl(
                project="PROJ",
                summary="Epic Summary",
                epic_name="Epic Name Value",
                color="blue",
            )

        assert result["key"] == "PROJ-100"
        mock_client.create_issue.assert_called_once()
        mock_client.close.assert_called_once()

    def test_create_epic_impl_missing_project(self):
        """Test error when project missing."""
        with pytest.raises(ValidationError, match="Project key is required"):
            _create_epic_impl(project="", summary="Summary")

    def test_create_epic_impl_missing_summary(self):
        """Test error when summary missing."""
        with pytest.raises(ValidationError, match="Summary is required"):
            _create_epic_impl(project="PROJ", summary="")

    def test_create_epic_impl_invalid_color(self):
        """Test error when invalid color."""
        with pytest.raises(ValidationError, match="Invalid epic color"):
            _create_epic_impl(project="PROJ", summary="Summary", color="invalid")

    def test_create_epic_impl_with_assignee_self(self, mock_client, sample_epic):
        """Test creating epic with self assignee."""
        mock_client.create_issue.return_value = sample_epic
        mock_client.get_current_user_id.return_value = "account123"

        with (
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
                return_value=mock_client,
            ),
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_agile_fields",
                return_value={
                    "epic_name": "customfield_10011",
                    "epic_color": "customfield_10012",
                },
            ),
        ):
            _create_epic_impl(
                project="PROJ",
                summary="Epic Summary",
                assignee="self",
            )

        mock_client.get_current_user_id.assert_called_once()
        call_args = mock_client.create_issue.call_args[0][0]
        assert call_args["assignee"]["accountId"] == "account123"

    def test_get_epic_impl_basic(self, mock_client, sample_epic):
        """Test getting epic without children."""
        mock_client.get_issue.return_value = sample_epic

        with (
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
                return_value=mock_client,
            ),
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_agile_fields",
                return_value={"story_points": "customfield_10016"},
            ),
        ):
            result = _get_epic_impl("PROJ-100")

        assert result["key"] == "PROJ-100"
        assert "children" not in result
        mock_client.close.assert_called_once()

    def test_get_epic_impl_with_children(self, mock_client, sample_epic, sample_issues):
        """Test getting epic with children."""
        mock_client.get_issue.return_value = sample_epic
        mock_client.search_issues.return_value = {"issues": sample_issues}

        with (
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
                return_value=mock_client,
            ),
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_agile_fields",
                return_value={"story_points": "customfield_10016"},
            ),
        ):
            result = _get_epic_impl("PROJ-100", with_children=True)

        assert result["key"] == "PROJ-100"
        assert "children" in result
        assert len(result["children"]) == 3
        assert "progress" in result
        assert result["progress"]["total"] == 3
        assert result["progress"]["done"] == 1  # Only PROJ-2 is Done
        assert "story_points" in result
        assert result["story_points"]["total"] == 16  # 5 + 3 + 8
        assert result["story_points"]["done"] == 3  # Only PROJ-2

    def test_add_to_epic_impl_success(self, mock_client, sample_epic):
        """Test adding issues to epic."""
        mock_client.get_issue.return_value = sample_epic

        with (
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
                return_value=mock_client,
            ),
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_agile_field",
                return_value="customfield_10014",
            ),
        ):
            result = _add_to_epic_impl("PROJ-100", ["PROJ-1", "PROJ-2"])

        assert result["added"] == 2
        assert result["failed"] == 0
        assert mock_client.update_issue.call_count == 2
        mock_client.close.assert_called_once()

    def test_add_to_epic_impl_dry_run(self, mock_client, sample_epic):
        """Test dry run for adding issues to epic."""
        mock_client.get_issue.return_value = sample_epic

        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            result = _add_to_epic_impl("PROJ-100", ["PROJ-1", "PROJ-2"], dry_run=True)

        assert result["would_add"] == 2
        mock_client.update_issue.assert_not_called()

    def test_add_to_epic_impl_not_epic(self, mock_client):
        """Test error when target is not an epic."""
        mock_client.get_issue.return_value = {
            "key": "PROJ-100",
            "fields": {"issuetype": {"name": "Story"}},
        }

        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            with pytest.raises(ValidationError, match="not an Epic"):
                _add_to_epic_impl("PROJ-100", ["PROJ-1"])

    def test_add_to_epic_impl_missing_issues(self, mock_client):
        """Test error when no issues provided."""
        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            with pytest.raises(ValidationError, match="At least one issue key"):
                _add_to_epic_impl("PROJ-100", [])


# =============================================================================
# Sprint Implementation Tests
# =============================================================================


class TestSprintImplementation:
    """Tests for sprint implementation functions."""

    def test_list_sprints_impl_by_board(self, mock_client, sample_sprint):
        """Test listing sprints by board."""
        mock_client.get_board_sprints.return_value = {"values": [sample_sprint]}

        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            result = _list_sprints_impl(board_id=123)

        assert len(result["sprints"]) == 1
        assert result["sprints"][0]["name"] == "Sprint 1"
        mock_client.close.assert_called_once()

    def test_list_sprints_impl_by_project(
        self, mock_client, sample_board, sample_sprint
    ):
        """Test listing sprints by project."""
        mock_client.get_all_boards.return_value = {"values": [sample_board]}
        mock_client.get_board_sprints.return_value = {"values": [sample_sprint]}

        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            result = _list_sprints_impl(project_key="PROJ")

        assert len(result["sprints"]) == 1
        assert result["board"]["id"] == 123

    def test_list_sprints_impl_no_params(self, mock_client):
        """Test error when no params."""
        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            with pytest.raises(ValidationError, match="Either board_id or project_key"):
                _list_sprints_impl()

    def test_create_sprint_impl_success(self, mock_client, sample_sprint):
        """Test creating sprint."""
        mock_client.create_sprint.return_value = sample_sprint

        with (
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
                return_value=mock_client,
            ),
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.parse_date_to_iso",
                side_effect=lambda x: f"{x}T00:00:00.000Z",
            ),
        ):
            result = _create_sprint_impl(
                board_id=123,
                name="Sprint 1",
                goal="Complete feature",
                start_date="2024-01-01",
                end_date="2024-01-14",
            )

        assert result["name"] == "Sprint 1"
        mock_client.create_sprint.assert_called_once()
        mock_client.close.assert_called_once()

    def test_create_sprint_impl_missing_board(self):
        """Test error when board missing."""
        with pytest.raises(ValidationError, match="Board ID is required"):
            _create_sprint_impl(board_id=None, name="Sprint 1")

    def test_create_sprint_impl_missing_name(self):
        """Test error when name missing."""
        with pytest.raises(ValidationError, match="Sprint name is required"):
            _create_sprint_impl(board_id=123, name="")

    def test_create_sprint_impl_invalid_dates(self):
        """Test error when end date before start date."""
        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.parse_date_to_iso",
            side_effect=lambda x: f"{x}T00:00:00.000Z",
        ):
            with pytest.raises(
                ValidationError, match="End date must be after start date"
            ):
                _create_sprint_impl(
                    board_id=123,
                    name="Sprint 1",
                    start_date="2024-01-14",
                    end_date="2024-01-01",
                )

    def test_get_sprint_impl_basic(self, mock_client, sample_sprint):
        """Test getting sprint without issues."""
        mock_client.get_sprint.return_value = sample_sprint

        with (
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
                return_value=mock_client,
            ),
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_agile_field",
                return_value="customfield_10016",
            ),
        ):
            result = _get_sprint_impl(456)

        assert result["name"] == "Sprint 1"
        assert "issues" not in result
        mock_client.close.assert_called_once()

    def test_get_sprint_impl_with_issues(
        self, mock_client, sample_sprint, sample_issues
    ):
        """Test getting sprint with issues."""
        mock_client.get_sprint.return_value = sample_sprint
        mock_client.get_sprint_issues.return_value = {"issues": sample_issues}

        with (
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
                return_value=mock_client,
            ),
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_agile_field",
                return_value="customfield_10016",
            ),
        ):
            result = _get_sprint_impl(456, with_issues=True)

        assert result["name"] == "Sprint 1"
        assert len(result["issues"]) == 3
        assert "progress" in result
        assert result["progress"]["total"] == 3
        assert result["progress"]["done"] == 1
        assert "story_points" in result

    def test_get_sprint_impl_missing_id(self, mock_client):
        """Test error when sprint ID missing."""
        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            with pytest.raises(ValidationError, match="Sprint ID is required"):
                _get_sprint_impl(None)

    def test_get_active_sprint_impl_found(self, mock_client, sample_sprint):
        """Test getting active sprint."""
        mock_client.get_board_sprints.return_value = {"values": [sample_sprint]}

        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            result = _get_active_sprint_impl(123)

        assert result["name"] == "Sprint 1"
        assert result["state"] == "active"

    def test_get_active_sprint_impl_not_found(self, mock_client):
        """Test no active sprint found."""
        mock_client.get_board_sprints.return_value = {"values": []}

        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            result = _get_active_sprint_impl(123)

        assert result is None

    def test_start_sprint_impl(self, mock_client, sample_sprint):
        """Test starting sprint."""
        mock_client.update_sprint.return_value = {**sample_sprint, "state": "active"}

        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            result = _start_sprint_impl(456)

        assert result["state"] == "active"
        mock_client.update_sprint.assert_called_once()
        call_kwargs = mock_client.update_sprint.call_args[1]
        assert call_kwargs["state"] == "active"

    def test_close_sprint_impl(self, mock_client, sample_sprint):
        """Test closing sprint."""
        mock_client.update_sprint.return_value = {**sample_sprint, "state": "closed"}

        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            result = _close_sprint_impl(456)

        assert result["state"] == "closed"
        mock_client.update_sprint.assert_called_once()

    def test_close_sprint_impl_with_move(self, mock_client, sample_sprint):
        """Test closing sprint with move incomplete."""
        mock_client.update_sprint.return_value = {**sample_sprint, "state": "closed"}
        mock_client.move_issues_to_sprint.return_value = {"movedIssues": 5}

        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            result = _close_sprint_impl(456, move_incomplete_to=457)

        assert result["moved_issues"] == 5
        mock_client.move_issues_to_sprint.assert_called_once()

    def test_update_sprint_impl(self, mock_client, sample_sprint):
        """Test updating sprint."""
        mock_client.update_sprint.return_value = {**sample_sprint, "name": "New Name"}

        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            result = _update_sprint_impl(456, name="New Name", goal="New goal")

        assert result["name"] == "New Name"
        call_kwargs = mock_client.update_sprint.call_args[1]
        assert call_kwargs["name"] == "New Name"
        assert call_kwargs["goal"] == "New goal"

    def test_update_sprint_impl_no_fields(self, mock_client):
        """Test error when no fields to update."""
        with pytest.raises(ValidationError, match="At least one field"):
            _update_sprint_impl(456)

    def test_move_to_sprint_impl_success(self, mock_client):
        """Test moving issues to sprint."""
        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            result = _move_to_sprint_impl(456, issue_keys=["PROJ-1", "PROJ-2"])

        assert result["moved"] == 2
        mock_client.move_issues_to_sprint.assert_called_once()

    def test_move_to_sprint_impl_with_jql(self, mock_client, sample_issues):
        """Test moving issues to sprint with JQL."""
        mock_client.search_issues.return_value = {"issues": sample_issues}

        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            result = _move_to_sprint_impl(456, jql="project = PROJ")

        assert result["moved"] == 3

    def test_move_to_sprint_impl_dry_run(self, mock_client):
        """Test dry run for moving issues."""
        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            result = _move_to_sprint_impl(456, issue_keys=["PROJ-1"], dry_run=True)

        assert result["would_move"] == 1
        mock_client.move_issues_to_sprint.assert_not_called()

    def test_move_to_backlog_impl_success(self, mock_client):
        """Test moving issues to backlog."""
        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            result = _move_to_backlog_impl(issue_keys=["PROJ-1", "PROJ-2"])

        assert result["moved_to_backlog"] == 2
        mock_client.move_issues_to_backlog.assert_called_once()

    def test_move_to_backlog_impl_dry_run(self, mock_client):
        """Test dry run for moving to backlog."""
        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            result = _move_to_backlog_impl(issue_keys=["PROJ-1"], dry_run=True)

        assert result["would_move_to_backlog"] == 1
        mock_client.move_issues_to_backlog.assert_not_called()


# =============================================================================
# Backlog/Rank Implementation Tests
# =============================================================================


class TestBacklogRankImplementation:
    """Tests for backlog and rank implementation functions."""

    def test_get_backlog_impl_by_board(self, mock_client, sample_issues):
        """Test getting backlog by board."""
        mock_client.get_board_backlog.return_value = {
            "issues": sample_issues,
            "total": 3,
        }

        with (
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
                return_value=mock_client,
            ),
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_agile_fields",
                return_value={
                    "epic_link": "customfield_10014",
                    "story_points": "customfield_10016",
                },
            ),
        ):
            result = _get_backlog_impl(board_id=123)

        assert len(result["issues"]) == 3
        mock_client.close.assert_called_once()

    def test_get_backlog_impl_group_by_epic(self, mock_client):
        """Test getting backlog grouped by epic."""
        issues = [
            {
                "key": "PROJ-1",
                "fields": {
                    "summary": "Issue 1",
                    "customfield_10014": "PROJ-100",
                    "status": {"name": "To Do"},
                },
            },
            {
                "key": "PROJ-2",
                "fields": {
                    "summary": "Issue 2",
                    "customfield_10014": "PROJ-100",
                    "status": {"name": "To Do"},
                },
            },
            {
                "key": "PROJ-3",
                "fields": {
                    "summary": "Issue 3",
                    "customfield_10014": None,
                    "status": {"name": "To Do"},
                },
            },
        ]
        mock_client.get_board_backlog.return_value = {"issues": issues}

        with (
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
                return_value=mock_client,
            ),
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_agile_fields",
                return_value={
                    "epic_link": "customfield_10014",
                    "story_points": "customfield_10016",
                },
            ),
        ):
            result = _get_backlog_impl(board_id=123, group_by_epic=True)

        assert "by_epic" in result
        assert "PROJ-100" in result["by_epic"]
        assert len(result["by_epic"]["PROJ-100"]) == 2
        assert len(result["no_epic"]) == 1

    def test_rank_issue_impl_before(self, mock_client):
        """Test ranking issue before another."""
        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            result = _rank_issue_impl(["PROJ-1"], before_key="PROJ-2")

        assert result["ranked"] == 1
        mock_client.rank_issues.assert_called_once_with(
            ["PROJ-1"], rank_before="PROJ-2"
        )

    def test_rank_issue_impl_after(self, mock_client):
        """Test ranking issue after another."""
        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            result = _rank_issue_impl(["PROJ-1"], after_key="PROJ-2")

        assert result["ranked"] == 1
        mock_client.rank_issues.assert_called_once_with(["PROJ-1"], rank_after="PROJ-2")

    def test_rank_issue_impl_no_position(self, mock_client):
        """Test error when no position specified."""
        with pytest.raises(ValidationError, match="Must specify"):
            _rank_issue_impl(["PROJ-1"])

    def test_rank_issue_impl_top_bottom_not_implemented(self, mock_client):
        """Test error for top/bottom (not implemented)."""
        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            with pytest.raises(ValidationError, match="requires implementation"):
                _rank_issue_impl(["PROJ-1"], position="top")


# =============================================================================
# Estimation Implementation Tests
# =============================================================================


class TestEstimationImplementation:
    """Tests for estimation implementation functions."""

    def test_estimate_issue_impl_success(self, mock_client):
        """Test setting story points."""
        with (
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
                return_value=mock_client,
            ),
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_agile_field",
                return_value="customfield_10016",
            ),
        ):
            result = _estimate_issue_impl(issue_keys=["PROJ-1"], points=5)

        assert result["updated"] == 1
        assert result["points"] == 5
        mock_client.update_issue.assert_called_once()

    def test_estimate_issue_impl_fibonacci_valid(self, mock_client):
        """Test valid Fibonacci value."""
        with (
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
                return_value=mock_client,
            ),
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_agile_field",
                return_value="customfield_10016",
            ),
        ):
            result = _estimate_issue_impl(
                issue_keys=["PROJ-1"], points=8, validate_fibonacci=True
            )

        assert result["updated"] == 1

    def test_estimate_issue_impl_fibonacci_invalid(self):
        """Test invalid Fibonacci value."""
        with pytest.raises(ValidationError, match="not a valid Fibonacci"):
            _estimate_issue_impl(
                issue_keys=["PROJ-1"], points=7, validate_fibonacci=True
            )

    def test_estimate_issue_impl_clear(self, mock_client):
        """Test clearing story points."""
        with (
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
                return_value=mock_client,
            ),
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_agile_field",
                return_value="customfield_10016",
            ),
        ):
            _estimate_issue_impl(issue_keys=["PROJ-1"], points=0)

        # Points 0 should set to None
        call_args = mock_client.update_issue.call_args[0]
        assert call_args[1]["customfield_10016"] is None

    def test_get_estimates_impl_by_sprint(self, mock_client, sample_issues):
        """Test getting estimates by sprint."""
        mock_client.get_sprint_issues.return_value = {"issues": sample_issues}

        with (
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
                return_value=mock_client,
            ),
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_agile_fields",
                return_value={"story_points": "customfield_10016"},
            ),
        ):
            result = _get_estimates_impl(sprint_id=456)

        assert result["total_points"] == 16
        assert result["issue_count"] == 3
        assert "by_status" in result
        assert "by_assignee" in result

    def test_get_estimates_impl_by_epic(self, mock_client, sample_issues):
        """Test getting estimates by epic."""
        mock_client.search_issues.return_value = {"issues": sample_issues}

        with (
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
                return_value=mock_client,
            ),
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_agile_fields",
                return_value={"story_points": "customfield_10016"},
            ),
        ):
            result = _get_estimates_impl(epic_key="PROJ-100")

        assert result["epic_key"] == "PROJ-100"
        assert result["total_points"] == 16

    def test_get_velocity_impl_success(
        self, mock_client, sample_board, sample_velocity_sprints
    ):
        """Test calculating velocity."""
        mock_client.get_all_boards.return_value = {"values": [sample_board]}
        mock_client.get_board_sprints.return_value = {"values": sample_velocity_sprints}

        # Different points for each sprint
        def mock_search(jql, **kwargs):
            if "sprint = 101" in jql:
                return {"issues": [{"fields": {"customfield_10016": 10}}]}
            elif "sprint = 102" in jql:
                return {"issues": [{"fields": {"customfield_10016": 15}}]}
            else:
                return {"issues": [{"fields": {"customfield_10016": 12}}]}

        mock_client.search_issues.side_effect = mock_search

        with (
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
                return_value=mock_client,
            ),
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_agile_fields",
                return_value={"story_points": "customfield_10016"},
            ),
        ):
            result = _get_velocity_impl(project_key="PROJ", num_sprints=3)

        assert result["sprints_analyzed"] == 3
        assert result["total_points"] == 37  # 10 + 15 + 12
        assert result["average_velocity"] == round((10 + 15 + 12) / 3, 1)

    def test_get_velocity_impl_no_closed_sprints(self, mock_client, sample_board):
        """Test error when no closed sprints."""
        mock_client.get_all_boards.return_value = {"values": [sample_board]}
        mock_client.get_board_sprints.return_value = {"values": []}

        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            with pytest.raises(ValidationError, match="No closed sprints"):
                _get_velocity_impl(project_key="PROJ")

    def test_create_subtask_impl_success(self, mock_client):
        """Test creating subtask."""
        mock_client.get_issue.return_value = {
            "key": "PROJ-1",
            "fields": {
                "project": {"key": "PROJ"},
                "issuetype": {"subtask": False},
            },
        }
        mock_client.get.return_value = [
            {"name": "Sub-task", "subtask": True},
            {"name": "Story", "subtask": False},
        ]
        mock_client.create_issue.return_value = {
            "key": "PROJ-10",
            "self": "https://test.atlassian.net/rest/api/3/issue/10",
        }

        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            result = _create_subtask_impl(parent_key="PROJ-1", summary="Subtask")

        assert result["key"] == "PROJ-10"
        mock_client.create_issue.assert_called_once()

    def test_create_subtask_impl_parent_is_subtask(self, mock_client):
        """Test error when parent is subtask."""
        mock_client.get_issue.return_value = {
            "key": "PROJ-1",
            "fields": {
                "project": {"key": "PROJ"},
                "issuetype": {"subtask": True},
            },
        }

        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            with pytest.raises(ValidationError, match="cannot have subtasks"):
                _create_subtask_impl(parent_key="PROJ-1", summary="Subtask")


# =============================================================================
# Formatting Function Tests
# =============================================================================


class TestFormattingFunctions:
    """Tests for formatting functions."""

    def test_format_epic_created(self):
        """Test formatting epic creation result."""
        result = {
            "key": "PROJ-100",
            "self": "https://test.atlassian.net/rest/api/3/issue/10001",
        }
        output = _format_epic_created(result, "Epic Name")

        assert "PROJ-100" in output
        assert "Epic Name" in output
        assert "https://test.atlassian.net/browse/PROJ-100" in output

    def test_format_epic_details(self, sample_epic):
        """Test formatting epic details."""
        epic_data = {
            "key": sample_epic["key"],
            "fields": sample_epic["fields"],
            "_agile_fields": {"epic_name": "customfield_10011"},
        }
        output = _format_epic_details(epic_data)

        assert "PROJ-100" in output
        assert "Epic Summary" in output
        assert "Epic Name Value" in output
        assert "To Do" in output

    def test_format_epic_details_with_progress(self, sample_epic):
        """Test formatting epic with progress."""
        epic_data = {
            "key": sample_epic["key"],
            "fields": sample_epic["fields"],
            "_agile_fields": {"epic_name": "customfield_10011"},
            "progress": {"total": 10, "done": 5, "percentage": 50},
            "story_points": {"total": 40, "done": 20, "percentage": 50},
            "children": [
                {
                    "key": "PROJ-1",
                    "fields": {"summary": "Child 1", "status": {"name": "Done"}},
                },
            ],
        }
        output = _format_epic_details(epic_data)

        assert "5/10 issues (50%)" in output
        assert "20/40 (50%)" in output
        assert "Children:" in output
        assert "PROJ-1" in output

    def test_format_sprint_list(self, sample_sprint, sample_board):
        """Test formatting sprint list."""
        data = {
            "board": sample_board,
            "sprints": [sample_sprint],
            "state_filter": "active",
            "total": 1,
        }
        output = _format_sprint_list(data)

        assert "PROJ board" in output
        assert "Sprint 1" in output
        assert "active" in output
        assert "2024-01-01" in output

    def test_format_sprint_list_empty(self, sample_board):
        """Test formatting empty sprint list."""
        data = {
            "board": sample_board,
            "sprints": [],
            "state_filter": None,
            "total": 0,
        }
        output = _format_sprint_list(data)

        assert "No sprints found" in output

    def test_format_sprint_details(self, sample_sprint):
        """Test formatting sprint details."""
        sprint_data = {
            **sample_sprint,
            "_story_points_field": "customfield_10016",
        }
        output = _format_sprint_details(sprint_data)

        assert "Sprint 1" in output
        assert "active" in output
        assert "Complete feature X" in output

    def test_format_sprint_details_with_issues(self, sample_sprint, sample_issues):
        """Test formatting sprint with issues."""
        sprint_data = {
            **sample_sprint,
            "_story_points_field": "customfield_10016",
            "issues": sample_issues,
            "progress": {"total": 3, "done": 1, "percentage": 33},
            "story_points": {"total": 16, "done": 3, "percentage": 19},
        }
        output = _format_sprint_details(sprint_data)

        assert "Issues:" in output
        assert "PROJ-1" in output
        assert "1/3 issues (33%)" in output

    def test_format_velocity(self):
        """Test formatting velocity report."""
        data = {
            "project_key": "PROJ",
            "board_id": 123,
            "sprints_analyzed": 3,
            "average_velocity": 12.3,
            "velocity_stdev": 2.5,
            "min_velocity": 10,
            "max_velocity": 15,
            "total_points": 37,
            "sprints": [
                {
                    "sprint_name": "Sprint 1",
                    "completed_points": 10,
                    "completed_issues": 5,
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-14",
                },
            ],
        }
        output = _format_velocity(data)

        assert "Velocity Report: PROJ" in output
        assert "12.3 points/sprint" in output
        assert "10 - 15 points" in output
        assert "Sprint 1" in output


# =============================================================================
# CLI Command Tests
# =============================================================================


class TestEpicCommands:
    """Tests for epic CLI commands."""

    def test_epic_create_text(self, mock_client, sample_epic):
        """Test epic create with text output."""
        mock_client.create_issue.return_value = sample_epic

        with (
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
                return_value=mock_client,
            ),
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_agile_fields",
                return_value={
                    "epic_name": "customfield_10011",
                    "epic_color": "customfield_10012",
                },
            ),
        ):
            runner = CliRunner()
            result = runner.invoke(
                agile,
                [
                    "epic",
                    "create",
                    "-p",
                    "PROJ",
                    "-s",
                    "Epic Summary",
                    "-n",
                    "Epic Name",
                ],
            )

        assert result.exit_code == 0
        assert "PROJ-100" in result.output

    def test_epic_create_json(self, mock_client, sample_epic):
        """Test epic create with JSON output."""
        mock_client.create_issue.return_value = sample_epic

        with (
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
                return_value=mock_client,
            ),
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_agile_fields",
                return_value={
                    "epic_name": "customfield_10011",
                    "epic_color": "customfield_10012",
                },
            ),
        ):
            runner = CliRunner()
            result = runner.invoke(
                agile,
                ["epic", "create", "-p", "PROJ", "-s", "Summary", "-o", "json"],
            )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["key"] == "PROJ-100"

    def test_epic_get_text(self, mock_client, sample_epic):
        """Test epic get with text output."""
        mock_client.get_issue.return_value = sample_epic

        with (
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
                return_value=mock_client,
            ),
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_agile_fields",
                return_value={"story_points": "customfield_10016"},
            ),
        ):
            runner = CliRunner()
            result = runner.invoke(agile, ["epic", "get", "PROJ-100"])

        assert result.exit_code == 0
        assert "PROJ-100" in result.output
        assert "Epic Summary" in result.output

    def test_epic_add_issues_text(self, mock_client, sample_epic):
        """Test adding issues to epic."""
        mock_client.get_issue.return_value = sample_epic

        with (
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
                return_value=mock_client,
            ),
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_agile_field",
                return_value="customfield_10014",
            ),
        ):
            runner = CliRunner()
            result = runner.invoke(
                agile,
                ["epic", "add-issues", "-e", "PROJ-100", "-i", "PROJ-1,PROJ-2"],
            )

        assert result.exit_code == 0
        assert "Added 2 issues" in result.output


class TestSprintCommands:
    """Tests for sprint CLI commands."""

    def test_sprint_list_text(self, mock_client, sample_board, sample_sprint):
        """Test sprint list with text output."""
        mock_client.get_board_sprints.return_value = {"values": [sample_sprint]}

        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            runner = CliRunner()
            result = runner.invoke(agile, ["sprint", "list", "-b", "123"])

        assert result.exit_code == 0
        assert "Sprint 1" in result.output

    def test_sprint_list_no_params(self):
        """Test sprint list without required params."""
        runner = CliRunner()
        result = runner.invoke(agile, ["sprint", "list"])

        assert result.exit_code != 0
        assert "Either --board or --project is required" in result.output

    def test_sprint_create_text(self, mock_client, sample_sprint):
        """Test sprint create with text output."""
        mock_client.create_sprint.return_value = sample_sprint

        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            runner = CliRunner()
            result = runner.invoke(
                agile,
                ["sprint", "create", "-b", "123", "-n", "Sprint 1", "-g", "Goal"],
            )

        assert result.exit_code == 0
        assert "Created sprint: Sprint 1" in result.output

    def test_sprint_get_by_id(self, mock_client, sample_sprint):
        """Test sprint get by ID."""
        mock_client.get_sprint.return_value = sample_sprint

        with (
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
                return_value=mock_client,
            ),
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_agile_field",
                return_value="customfield_10016",
            ),
        ):
            runner = CliRunner()
            result = runner.invoke(agile, ["sprint", "get", "456"])

        assert result.exit_code == 0
        assert "Sprint 1" in result.output

    def test_sprint_get_active(self, mock_client, sample_sprint):
        """Test getting active sprint."""
        mock_client.get_board_sprints.return_value = {"values": [sample_sprint]}

        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            runner = CliRunner()
            result = runner.invoke(agile, ["sprint", "get", "-b", "123", "--active"])

        assert result.exit_code == 0
        assert "Sprint 1" in result.output

    def test_sprint_manage_start(self, mock_client, sample_sprint):
        """Test starting sprint."""
        mock_client.update_sprint.return_value = {**sample_sprint, "state": "active"}

        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            runner = CliRunner()
            result = runner.invoke(
                agile,
                ["sprint", "manage", "-s", "456", "--start"],
            )

        assert result.exit_code == 0
        assert "Started sprint" in result.output

    def test_sprint_manage_close(self, mock_client, sample_sprint):
        """Test closing sprint."""
        mock_client.update_sprint.return_value = {**sample_sprint, "state": "closed"}

        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            runner = CliRunner()
            result = runner.invoke(
                agile,
                ["sprint", "manage", "-s", "456", "--close"],
            )

        assert result.exit_code == 0
        assert "Closed sprint" in result.output

    def test_sprint_move_issues_to_sprint(self, mock_client):
        """Test moving issues to sprint."""
        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            runner = CliRunner()
            result = runner.invoke(
                agile,
                ["sprint", "move-issues", "-s", "456", "-i", "PROJ-1,PROJ-2"],
            )

        assert result.exit_code == 0
        assert "Moved 2 issues" in result.output

    def test_sprint_move_issues_to_backlog(self, mock_client):
        """Test moving issues to backlog."""
        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            runner = CliRunner()
            result = runner.invoke(
                agile,
                ["sprint", "move-issues", "-b", "-i", "PROJ-1"],
            )

        assert result.exit_code == 0
        assert "Moved 1 issues to backlog" in result.output


class TestOtherAgileCommands:
    """Tests for other agile CLI commands."""

    def test_backlog_text(self, mock_client, sample_issues):
        """Test backlog command."""
        mock_client.get_board_backlog.return_value = {
            "issues": sample_issues,
            "total": 3,
        }

        with (
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
                return_value=mock_client,
            ),
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_agile_fields",
                return_value={
                    "epic_link": "customfield_10014",
                    "story_points": "customfield_10016",
                },
            ),
        ):
            runner = CliRunner()
            result = runner.invoke(agile, ["backlog", "-b", "123"])

        assert result.exit_code == 0
        assert "3/3 issues" in result.output

    def test_rank_before(self, mock_client):
        """Test ranking issue before another."""
        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            runner = CliRunner()
            result = runner.invoke(agile, ["rank", "PROJ-1", "--before", "PROJ-2"])

        assert result.exit_code == 0
        assert "Ranked 1 issue" in result.output
        assert "before PROJ-2" in result.output

    def test_rank_no_position(self):
        """Test ranking without position."""
        runner = CliRunner()
        result = runner.invoke(agile, ["rank", "PROJ-1"])

        assert result.exit_code != 0
        assert "Must specify one of" in result.output

    def test_estimate_text(self, mock_client):
        """Test estimate command."""
        with (
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
                return_value=mock_client,
            ),
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_agile_field",
                return_value="customfield_10016",
            ),
        ):
            runner = CliRunner()
            result = runner.invoke(agile, ["estimate", "PROJ-1", "-p", "5"])

        assert result.exit_code == 0
        assert "Updated 1 issue" in result.output
        assert "set to 5" in result.output

    def test_estimates_by_sprint(self, mock_client, sample_issues):
        """Test estimates by sprint."""
        mock_client.get_sprint_issues.return_value = {"issues": sample_issues}

        with (
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
                return_value=mock_client,
            ),
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_agile_fields",
                return_value={"story_points": "customfield_10016"},
            ),
        ):
            runner = CliRunner()
            result = runner.invoke(agile, ["estimates", "-s", "456"])

        assert result.exit_code == 0
        assert "Sprint 456 Estimates" in result.output
        assert "16 points" in result.output

    def test_estimates_no_params(self):
        """Test estimates without params."""
        runner = CliRunner()
        result = runner.invoke(agile, ["estimates"])

        assert result.exit_code != 0
        assert "One of --sprint, --project, or --epic is required" in result.output

    def test_velocity_text(self, mock_client, sample_board, sample_velocity_sprints):
        """Test velocity command."""
        mock_client.get_all_boards.return_value = {"values": [sample_board]}
        mock_client.get_board_sprints.return_value = {"values": sample_velocity_sprints}
        mock_client.search_issues.return_value = {
            "issues": [{"fields": {"customfield_10016": 10}}]
        }

        with (
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
                return_value=mock_client,
            ),
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_agile_fields",
                return_value={"story_points": "customfield_10016"},
            ),
        ):
            runner = CliRunner()
            result = runner.invoke(agile, ["velocity", "-p", "PROJ"])

        assert result.exit_code == 0
        assert "Velocity Report" in result.output

    def test_subtask_text(self, mock_client):
        """Test subtask create."""
        mock_client.get_issue.return_value = {
            "key": "PROJ-1",
            "fields": {
                "project": {"key": "PROJ"},
                "issuetype": {"subtask": False},
            },
        }
        mock_client.get.return_value = [
            {"name": "Sub-task", "subtask": True},
        ]
        mock_client.create_issue.return_value = {
            "key": "PROJ-10",
            "self": "https://test.atlassian.net/rest/api/3/issue/10",
        }

        with patch(
            "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
            return_value=mock_client,
        ):
            runner = CliRunner()
            result = runner.invoke(
                agile,
                ["subtask", "-p", "PROJ-1", "-s", "Subtask Summary"],
            )

        assert result.exit_code == 0
        assert "Created subtask: PROJ-10" in result.output
        assert "Parent: PROJ-1" in result.output


class TestErrorHandling:
    """Tests for error handling in CLI commands."""

    def test_jira_error_handled(self, mock_client):
        """Test JIRA error is handled gracefully."""
        mock_client.get_issue.side_effect = JiraError("API Error")

        with (
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_jira_client",
                return_value=mock_client,
            ),
            patch(
                "jira_assistant_skills.cli.commands.agile_cmds.get_agile_fields",
                return_value={"story_points": "customfield_10016"},
            ),
        ):
            runner = CliRunner()
            result = runner.invoke(agile, ["epic", "get", "PROJ-100"])

        assert result.exit_code == 1
        assert "Error" in result.output or "error" in result.output.lower()

    def test_validation_error_handled(self):
        """Test validation error is handled gracefully."""
        runner = CliRunner()
        result = runner.invoke(
            agile,
            ["epic", "create", "-p", "PROJ", "-s", "Summary", "-c", "invalid_color"],
        )

        assert result.exit_code != 0
