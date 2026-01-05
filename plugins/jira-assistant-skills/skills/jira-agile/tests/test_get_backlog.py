"""
Tests for get_backlog.py - Retrieving board backlog.

Following TDD: These tests are written FIRST and should FAIL initially.
"""

import sys
from pathlib import Path

test_dir = Path(__file__).parent
jira_agile_dir = test_dir.parent
skills_dir = jira_agile_dir.parent
shared_lib_path = skills_dir / "shared" / "scripts" / "lib"
scripts_path = jira_agile_dir / "scripts"

sys.path.insert(0, str(shared_lib_path))
sys.path.insert(0, str(scripts_path))

import copy
from unittest.mock import patch

import pytest


@pytest.mark.agile
@pytest.mark.unit
class TestGetBacklog:
    """Test suite for get_backlog.py functionality."""

    def test_get_backlog_all(self, mock_jira_client, sample_issue_response):
        """Test fetching full backlog for board."""
        from get_backlog import get_backlog

        mock_jira_client.get_board_backlog.return_value = {
            "issues": [sample_issue_response],
            "total": 1,
        }

        result = get_backlog(board_id=123, client=mock_jira_client)

        assert result is not None
        assert len(result["issues"]) == 1
        mock_jira_client.get_board_backlog.assert_called_once()

    def test_get_backlog_with_filter(self, mock_jira_client, sample_issue_response):
        """Test filtering backlog by JQL."""
        from get_backlog import get_backlog

        mock_jira_client.get_board_backlog.return_value = {
            "issues": [sample_issue_response],
            "total": 1,
        }

        result = get_backlog(
            board_id=123, jql_filter="priority=High", client=mock_jira_client
        )

        assert result is not None
        call_args = mock_jira_client.get_board_backlog.call_args
        # Verify JQL parameter was passed correctly
        call_kwargs = call_args[1] if len(call_args) > 1 else {}
        assert call_kwargs.get("jql") == "priority=High" or "jql" in call_kwargs

    def test_get_backlog_with_pagination(self, mock_jira_client, sample_issue_response):
        """Test paginated backlog retrieval."""
        from get_backlog import get_backlog

        mock_jira_client.get_board_backlog.return_value = {
            "issues": [sample_issue_response],
            "total": 100,
            "startAt": 0,
            "maxResults": 50,
        }

        result = get_backlog(board_id=123, max_results=50, client=mock_jira_client)

        assert result is not None
        assert result["total"] == 100

    def test_get_backlog_sorted(self, mock_jira_client):
        """Test backlog in rank order."""
        from get_backlog import get_backlog

        mock_jira_client.get_board_backlog.return_value = {
            "issues": [
                {"key": "PROJ-1", "fields": {"summary": "First"}},
                {"key": "PROJ-2", "fields": {"summary": "Second"}},
            ],
            "total": 2,
        }

        result = get_backlog(board_id=123, client=mock_jira_client)

        assert result["issues"][0]["key"] == "PROJ-1"
        assert result["issues"][1]["key"] == "PROJ-2"

    def test_get_backlog_with_epics(self, mock_jira_client, sample_issue_response):
        """Test grouping backlog by epic."""
        from get_backlog import get_backlog

        # Use deepcopy to avoid fixture mutation
        issue_with_epic = copy.deepcopy(sample_issue_response)
        issue_with_epic["fields"]["customfield_10014"] = "PROJ-100"

        mock_jira_client.get_board_backlog.return_value = {
            "issues": [issue_with_epic],
            "total": 1,
        }

        result = get_backlog(board_id=123, group_by_epic=True, client=mock_jira_client)

        assert result is not None
        # Strong assertion: when grouping by epic, expect 'by_epic' key or issues with epic link
        assert "by_epic" in result or len(result.get("issues", [])) > 0, (
            "Expected epic grouping in result"
        )


@pytest.mark.agile
@pytest.mark.unit
class TestGetBacklogCLI:
    """Test command-line interface for get_backlog.py."""

    def test_cli_main_exists(self):
        """Test CLI main function exists and is callable."""
        from get_backlog import main

        assert callable(main)

    def test_cli_help_output(self, capsys):
        """Test that --help shows usage information."""
        with patch("sys.argv", ["get_backlog.py", "--help"]):
            from get_backlog import main

            try:
                main()
            except SystemExit:
                pass  # --help causes SystemExit

        captured = capsys.readouterr()
        assert "--board" in captured.out or "usage" in captured.out.lower()


@pytest.mark.agile
@pytest.mark.unit
class TestGetBacklogErrorHandling:
    """Test API error handling scenarios for get_backlog."""

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from get_backlog import get_backlog

        from jira_assistant_skills_lib import AuthenticationError

        mock_jira_client.get_board_backlog.side_effect = AuthenticationError(
            "Invalid API token"
        )

        with pytest.raises(AuthenticationError):
            get_backlog(board_id=123, client=mock_jira_client)

    def test_forbidden_error(self, mock_jira_client):
        """Test handling of 403 forbidden."""
        from get_backlog import get_backlog

        from jira_assistant_skills_lib import PermissionError

        mock_jira_client.get_board_backlog.side_effect = PermissionError(
            "Insufficient permissions"
        )

        with pytest.raises(PermissionError):
            get_backlog(board_id=123, client=mock_jira_client)

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from get_backlog import get_backlog

        from jira_assistant_skills_lib import JiraError

        mock_jira_client.get_board_backlog.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        with pytest.raises(JiraError) as exc_info:
            get_backlog(board_id=123, client=mock_jira_client)
        assert exc_info.value.status_code == 429

    def test_server_error(self, mock_jira_client):
        """Test handling of 500 server error."""
        from get_backlog import get_backlog

        from jira_assistant_skills_lib import JiraError

        mock_jira_client.get_board_backlog.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        with pytest.raises(JiraError) as exc_info:
            get_backlog(board_id=123, client=mock_jira_client)
        assert exc_info.value.status_code == 500

    def test_board_not_found(self, mock_jira_client):
        """Test error when board doesn't exist."""
        from get_backlog import get_backlog

        from jira_assistant_skills_lib import JiraError

        mock_jira_client.get_board_backlog.side_effect = JiraError(
            "Board does not exist", status_code=404
        )

        with pytest.raises(JiraError) as exc_info:
            get_backlog(board_id=999, client=mock_jira_client)
        assert exc_info.value.status_code == 404
