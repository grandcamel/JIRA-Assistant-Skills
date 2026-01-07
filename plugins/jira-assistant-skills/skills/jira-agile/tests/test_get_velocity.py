"""Unit tests for get_velocity.py."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add scripts directory to path
test_dir = Path(__file__).parent
jira_agile_dir = test_dir.parent
scripts_path = jira_agile_dir / "scripts"
sys.path.insert(0, str(scripts_path))

from get_velocity import (
    format_velocity,
    get_board_for_project,
    get_velocity,
    main,
)


@pytest.fixture
def mock_client():
    """Create a mock JIRA client."""
    return MagicMock()


@pytest.fixture
def mock_boards_response():
    """Sample boards response."""
    return {
        "values": [
            {"id": 1, "name": "DEMO Board", "type": "scrum"},
        ]
    }


@pytest.fixture
def mock_closed_sprints():
    """Sample closed sprints response."""
    return {
        "values": [
            {
                "id": 10,
                "name": "Sprint 3",
                "state": "closed",
                "startDate": "2024-01-15T00:00:00.000Z",
                "endDate": "2024-01-29T00:00:00.000Z",
            },
            {
                "id": 9,
                "name": "Sprint 2",
                "state": "closed",
                "startDate": "2024-01-01T00:00:00.000Z",
                "endDate": "2024-01-15T00:00:00.000Z",
            },
            {
                "id": 8,
                "name": "Sprint 1",
                "state": "closed",
                "startDate": "2023-12-18T00:00:00.000Z",
                "endDate": "2024-01-01T00:00:00.000Z",
            },
        ]
    }


@pytest.fixture
def mock_sprint_issues():
    """Sample completed issues for a sprint."""
    return {
        "issues": [
            {
                "key": "DEMO-1",
                "fields": {
                    "summary": "Issue 1",
                    "status": {"name": "Done"},
                    "customfield_10016": 5,
                },
            },
            {
                "key": "DEMO-2",
                "fields": {
                    "summary": "Issue 2",
                    "status": {"name": "Done"},
                    "customfield_10016": 3,
                },
            },
            {
                "key": "DEMO-3",
                "fields": {
                    "summary": "Issue 3",
                    "status": {"name": "Done"},
                    "customfield_10016": None,  # Unestimated
                },
            },
        ]
    }


class TestGetBoardForProject:
    """Tests for get_board_for_project function."""

    def test_finds_scrum_board(self, mock_client, mock_boards_response):
        """Test finding a scrum board for a project."""
        mock_client.get_all_boards.return_value = mock_boards_response

        result = get_board_for_project("DEMO", client=mock_client)

        assert result is not None
        assert result["id"] == 1
        assert result["type"] == "scrum"
        mock_client.get_all_boards.assert_called_once_with(project_key="DEMO")

    def test_returns_none_when_no_boards(self, mock_client):
        """Test when no boards exist."""
        mock_client.get_all_boards.return_value = {"values": []}

        result = get_board_for_project("DEMO", client=mock_client)

        assert result is None


class TestGetVelocity:
    """Tests for get_velocity function."""

    @patch("get_velocity.get_agile_fields")
    def test_calculates_velocity_by_project(
        self, mock_agile_fields, mock_client, mock_boards_response, mock_closed_sprints, mock_sprint_issues
    ):
        """Test calculating velocity for a project."""
        mock_agile_fields.return_value = {"story_points": "customfield_10016"}
        mock_client.get_all_boards.return_value = mock_boards_response
        mock_client.get_board_sprints.return_value = mock_closed_sprints
        mock_client.search_issues.return_value = mock_sprint_issues

        result = get_velocity(project_key="DEMO", num_sprints=3, client=mock_client)

        assert result["project_key"] == "DEMO"
        assert result["sprints_analyzed"] == 3
        assert result["average_velocity"] == 8.0  # 8 points per sprint (3 sprints, same issues)
        assert len(result["sprints"]) == 3

    @patch("get_velocity.get_agile_fields")
    def test_calculates_velocity_by_board_id(
        self, mock_agile_fields, mock_client, mock_closed_sprints, mock_sprint_issues
    ):
        """Test calculating velocity with board ID."""
        mock_agile_fields.return_value = {"story_points": "customfield_10016"}
        mock_client.get_board_sprints.return_value = mock_closed_sprints
        mock_client.search_issues.return_value = mock_sprint_issues

        result = get_velocity(board_id=1, num_sprints=3, client=mock_client)

        assert result["board_id"] == 1
        assert result["sprints_analyzed"] == 3
        mock_client.get_board_sprints.assert_called_once()

    def test_raises_error_when_no_board_or_project(self, mock_client):
        """Test error when neither board nor project specified."""
        from jira_assistant_skills_lib import ValidationError

        with pytest.raises(ValidationError, match="Either --board or --project is required"):
            get_velocity(client=mock_client)

    @patch("get_velocity.get_agile_fields")
    def test_raises_error_when_no_closed_sprints(self, mock_agile_fields, mock_client, mock_boards_response):
        """Test error when no closed sprints exist."""
        from jira_assistant_skills_lib import ValidationError

        mock_agile_fields.return_value = {"story_points": "customfield_10016"}
        mock_client.get_all_boards.return_value = mock_boards_response
        mock_client.get_board_sprints.return_value = {"values": []}

        with pytest.raises(ValidationError, match="No closed sprints found"):
            get_velocity(project_key="DEMO", client=mock_client)


class TestFormatVelocity:
    """Tests for format_velocity function."""

    def test_json_output(self):
        """Test JSON output format."""
        data = {
            "project_key": "DEMO",
            "board_id": 1,
            "board_name": "DEMO Board",
            "sprints_analyzed": 2,
            "average_velocity": 10.5,
            "velocity_stdev": 2.5,
            "min_velocity": 8,
            "max_velocity": 13,
            "total_points": 21,
            "sprints": [
                {
                    "sprint_id": 10,
                    "sprint_name": "Sprint 2",
                    "completed_points": 13,
                    "completed_issues": 5,
                    "start_date": "2024-01-15",
                    "end_date": "2024-01-29",
                },
                {
                    "sprint_id": 9,
                    "sprint_name": "Sprint 1",
                    "completed_points": 8,
                    "completed_issues": 3,
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-15",
                },
            ],
        }

        result = format_velocity(data, output_format="json")
        parsed = json.loads(result)

        assert parsed["average_velocity"] == 10.5
        assert parsed["sprints_analyzed"] == 2

    def test_text_output(self):
        """Test text output format."""
        data = {
            "project_key": "DEMO",
            "board_id": 1,
            "board_name": "DEMO Board",
            "sprints_analyzed": 2,
            "average_velocity": 10.5,
            "velocity_stdev": 2.5,
            "min_velocity": 8,
            "max_velocity": 13,
            "total_points": 21,
            "sprints": [
                {
                    "sprint_id": 10,
                    "sprint_name": "Sprint 2",
                    "completed_points": 13,
                    "completed_issues": 5,
                    "start_date": "2024-01-15",
                    "end_date": "2024-01-29",
                },
            ],
        }

        result = format_velocity(data, output_format="text")

        assert "Velocity Report: DEMO" in result
        assert "Average Velocity: 10.5 points/sprint" in result
        assert "Range: 8 - 13 points" in result
        assert "Sprint 2" in result


class TestMain:
    """Tests for main CLI function."""

    @patch("get_velocity.get_velocity")
    def test_main_with_project(self, mock_get_velocity, capsys):
        """Test CLI with project key."""
        mock_get_velocity.return_value = {
            "project_key": "DEMO",
            "board_id": 1,
            "board_name": "DEMO Board",
            "sprints_analyzed": 3,
            "average_velocity": 10.0,
            "velocity_stdev": 0,
            "min_velocity": 10,
            "max_velocity": 10,
            "total_points": 30,
            "sprints": [],
        }

        main(["--project", "DEMO"])

        mock_get_velocity.assert_called_once()
        captured = capsys.readouterr()
        assert "Velocity Report" in captured.out

    def test_main_requires_board_or_project(self, capsys):
        """Test CLI requires board or project."""
        with pytest.raises(SystemExit):
            main([])

    @patch("get_velocity.get_velocity")
    def test_main_json_output(self, mock_get_velocity, capsys):
        """Test CLI with JSON output."""
        mock_get_velocity.return_value = {
            "project_key": "DEMO",
            "board_id": 1,
            "board_name": None,
            "sprints_analyzed": 1,
            "average_velocity": 5.0,
            "velocity_stdev": 0,
            "min_velocity": 5,
            "max_velocity": 5,
            "total_points": 5,
            "sprints": [],
        }

        main(["--project", "DEMO", "--output", "json"])

        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert parsed["average_velocity"] == 5.0


class TestVelocityCLI:
    """Tests for CLI help and structure."""

    def test_cli_main_exists(self):
        """Test that main function exists."""
        from get_velocity import main as velocity_main
        assert callable(velocity_main)

    def test_cli_help_output(self, capsys):
        """Test help output."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "velocity" in captured.out.lower() or "sprint" in captured.out.lower()


class TestVelocityErrorHandling:
    """Tests for error handling."""

    @patch("get_velocity.get_velocity")
    def test_handles_jira_error(self, mock_get_velocity):
        """Test handling of JiraError."""
        from jira_assistant_skills_lib import JiraError

        mock_get_velocity.side_effect = JiraError("API error")

        with pytest.raises(SystemExit) as exc_info:
            main(["--project", "DEMO"])
        assert exc_info.value.code == 1

    @patch("get_velocity.get_velocity")
    def test_handles_validation_error(self, mock_get_velocity):
        """Test handling of ValidationError."""
        from jira_assistant_skills_lib import ValidationError

        mock_get_velocity.side_effect = ValidationError("No closed sprints")

        with pytest.raises(SystemExit) as exc_info:
            main(["--project", "DEMO"])
        assert exc_info.value.code == 1
