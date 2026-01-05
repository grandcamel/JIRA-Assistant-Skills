"""
Tests for get_sprint.py - Retrieving sprint details and progress.

Following TDD: These tests are written FIRST and should FAIL initially.
Implementation comes after tests are defined.
"""

import sys
from pathlib import Path

# Add paths BEFORE any other imports
test_dir = Path(__file__).parent  # tests
jira_agile_dir = test_dir.parent  # jira-agile
skills_dir = jira_agile_dir.parent  # skills
shared_lib_path = skills_dir / "shared" / "scripts" / "lib"
scripts_path = jira_agile_dir / "scripts"

sys.path.insert(0, str(shared_lib_path))
sys.path.insert(0, str(scripts_path))

from unittest.mock import patch

import pytest


@pytest.mark.agile
@pytest.mark.unit
class TestGetSprint:
    """Test suite for get_sprint.py functionality."""

    def test_get_sprint_basic(self, mock_jira_client, sample_sprint_response):
        """Test fetching sprint metadata."""
        # Arrange
        from get_sprint import get_sprint

        mock_jira_client.get_sprint.return_value = sample_sprint_response

        # Act
        result = get_sprint(sprint_id=456, client=mock_jira_client)

        # Assert
        assert result is not None
        assert result["id"] == 456
        assert result["name"] == "Sprint 42"
        assert result["state"] == "active"

        # Verify API call
        mock_jira_client.get_sprint.assert_called_once_with(456)

    def test_get_sprint_with_issues(
        self, mock_jira_client, sample_sprint_response, sample_issue_response
    ):
        """Test listing all issues in sprint."""
        # Arrange
        from get_sprint import get_sprint

        mock_jira_client.get_sprint.return_value = sample_sprint_response
        mock_jira_client.get_sprint_issues.return_value = {
            "issues": [sample_issue_response],
            "total": 1,
        }

        # Act
        result = get_sprint(sprint_id=456, with_issues=True, client=mock_jira_client)

        # Assert
        assert result is not None
        assert "issues" in result
        assert len(result["issues"]) == 1
        assert result["issues"][0]["key"] == "PROJ-101"

    def test_get_sprint_progress(self, mock_jira_client, sample_sprint_response):
        """Test calculating sprint progress (burndown data)."""
        # Arrange
        from get_sprint import get_sprint

        mock_jira_client.get_sprint.return_value = sample_sprint_response
        mock_jira_client.get_sprint_issues.return_value = {
            "issues": [
                {
                    "key": "PROJ-101",
                    "fields": {"status": {"name": "Done"}, "customfield_10016": 5},
                },
                {
                    "key": "PROJ-102",
                    "fields": {"status": {"name": "Done"}, "customfield_10016": 8},
                },
                {
                    "key": "PROJ-103",
                    "fields": {
                        "status": {"name": "In Progress"},
                        "customfield_10016": 3,
                    },
                },
                {
                    "key": "PROJ-104",
                    "fields": {"status": {"name": "To Do"}, "customfield_10016": 5},
                },
            ],
            "total": 4,
        }

        # Act
        result = get_sprint(sprint_id=456, with_issues=True, client=mock_jira_client)

        # Assert
        assert "progress" in result
        assert result["progress"]["total"] == 4
        assert result["progress"]["done"] == 2
        assert result["progress"]["percentage"] == 50  # 2/4 = 50%

        assert "story_points" in result
        assert result["story_points"]["total"] == 21  # 5+8+3+5
        assert result["story_points"]["done"] == 13  # 5+8
        assert result["story_points"]["percentage"] == 61  # 13/21 ≈ 61%

    def test_get_sprint_by_board_active(self, mock_jira_client, sample_sprint_response):
        """Test finding active sprint for board."""
        # Arrange
        from get_sprint import get_active_sprint_for_board

        mock_jira_client.get_board_sprints.return_value = {
            "values": [sample_sprint_response],
            "isLast": True,
        }

        # Act
        result = get_active_sprint_for_board(board_id=123, client=mock_jira_client)

        # Assert
        assert result is not None
        assert result["id"] == 456
        assert result["state"] == "active"

    def test_get_sprint_format_text(self, mock_jira_client, sample_sprint_response):
        """Test text output format."""
        # Arrange
        from get_sprint import format_sprint_output

        # Act
        output = format_sprint_output(sample_sprint_response, format="text")

        # Assert
        assert output is not None
        assert isinstance(output, str)
        assert "Sprint 42" in output
        assert "active" in output.lower()

    def test_get_sprint_format_json(self, mock_jira_client, sample_sprint_response):
        """Test JSON output format."""
        # Arrange
        import json

        from get_sprint import format_sprint_output

        # Act
        output = format_sprint_output(sample_sprint_response, format="json")

        # Assert
        assert output is not None
        # Should be valid JSON
        parsed = json.loads(output)
        assert parsed["id"] == 456
        assert parsed["name"] == "Sprint 42"


@pytest.mark.agile
@pytest.mark.unit
class TestGetSprintCLI:
    """Test command-line interface for get_sprint.py."""

    def test_cli_main_exists(self):
        """Test CLI main function exists and is callable."""
        from get_sprint import main

        assert callable(main)

    def test_cli_help_output(self, capsys):
        """Test that --help shows usage information."""
        with patch("sys.argv", ["get_sprint.py", "--help"]):
            from get_sprint import main

            try:
                main()
            except SystemExit:
                pass  # --help causes SystemExit

        captured = capsys.readouterr()
        assert "sprint" in captured.out.lower() or "usage" in captured.out.lower()


@pytest.mark.agile
@pytest.mark.unit
class TestGetSprintErrorHandling:
    """Test API error handling scenarios for get_sprint."""

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from get_sprint import get_sprint

        from jira_assistant_skills_lib import AuthenticationError

        mock_jira_client.get_sprint.side_effect = AuthenticationError(
            "Invalid API token"
        )

        with pytest.raises(AuthenticationError):
            get_sprint(sprint_id=456, client=mock_jira_client)

    def test_forbidden_error(self, mock_jira_client):
        """Test handling of 403 forbidden."""
        from get_sprint import get_sprint

        from jira_assistant_skills_lib import PermissionError

        mock_jira_client.get_sprint.side_effect = PermissionError(
            "Insufficient permissions"
        )

        with pytest.raises(PermissionError):
            get_sprint(sprint_id=456, client=mock_jira_client)

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from get_sprint import get_sprint

        from jira_assistant_skills_lib import JiraError

        mock_jira_client.get_sprint.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        with pytest.raises(JiraError) as exc_info:
            get_sprint(sprint_id=456, client=mock_jira_client)
        assert exc_info.value.status_code == 429

    def test_server_error(self, mock_jira_client):
        """Test handling of 500 server error."""
        from get_sprint import get_sprint

        from jira_assistant_skills_lib import JiraError

        mock_jira_client.get_sprint.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        with pytest.raises(JiraError) as exc_info:
            get_sprint(sprint_id=456, client=mock_jira_client)
        assert exc_info.value.status_code == 500

    def test_sprint_not_found(self, mock_jira_client):
        """Test error when sprint doesn't exist."""
        from get_sprint import get_sprint

        from jira_assistant_skills_lib import JiraError

        mock_jira_client.get_sprint.side_effect = JiraError(
            "Sprint does not exist", status_code=404
        )

        with pytest.raises(JiraError) as exc_info:
            get_sprint(sprint_id=999, client=mock_jira_client)
        assert exc_info.value.status_code == 404
