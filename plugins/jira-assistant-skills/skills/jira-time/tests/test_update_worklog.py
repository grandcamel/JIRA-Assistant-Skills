"""
Tests for update_worklog.py script.

Tests updating existing worklogs on JIRA issues.
"""

import sys
from pathlib import Path

import pytest

# Add paths for imports
scripts_path = str(Path(__file__).parent.parent / "scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


@pytest.mark.time
@pytest.mark.unit
class TestUpdateWorklog:
    """Tests for updating worklogs."""

    def test_update_worklog_time(self, mock_jira_client, sample_worklog):
        """Test updating time spent."""
        updated_worklog = {
            **sample_worklog,
            "timeSpent": "3h",
            "timeSpentSeconds": 10800,
        }
        mock_jira_client.update_worklog.return_value = updated_worklog

        from update_worklog import update_worklog

        result = update_worklog(mock_jira_client, "PROJ-123", "10045", time_spent="3h")

        mock_jira_client.update_worklog.assert_called_once()
        call_args = mock_jira_client.update_worklog.call_args
        assert call_args[1]["time_spent"] == "3h"
        assert result["timeSpent"] == "3h"

    def test_update_worklog_started(self, mock_jira_client, sample_worklog):
        """Test updating start time."""
        updated_worklog = {**sample_worklog, "started": "2025-01-15T10:00:00.000+0000"}
        mock_jira_client.update_worklog.return_value = updated_worklog

        from update_worklog import update_worklog

        update_worklog(
            mock_jira_client,
            "PROJ-123",
            "10045",
            started="2025-01-15T10:00:00.000+0000",
        )

        call_args = mock_jira_client.update_worklog.call_args
        assert call_args[1]["started"] == "2025-01-15T10:00:00.000+0000"

    def test_update_worklog_comment(self, mock_jira_client, sample_worklog):
        """Test updating comment."""
        mock_jira_client.update_worklog.return_value = sample_worklog

        from update_worklog import update_worklog

        update_worklog(
            mock_jira_client, "PROJ-123", "10045", comment="Updated description"
        )

        call_args = mock_jira_client.update_worklog.call_args
        assert "comment" in call_args[1]
        # Comment should be ADF
        assert call_args[1]["comment"]["type"] == "doc"

    def test_update_worklog_multiple_fields(self, mock_jira_client, sample_worklog):
        """Test updating multiple fields at once."""
        updated_worklog = {
            **sample_worklog,
            "timeSpent": "4h",
            "timeSpentSeconds": 14400,
        }
        mock_jira_client.update_worklog.return_value = updated_worklog

        from update_worklog import update_worklog

        update_worklog(
            mock_jira_client,
            "PROJ-123",
            "10045",
            time_spent="4h",
            comment="Updated work",
        )

        call_args = mock_jira_client.update_worklog.call_args
        assert call_args[1]["time_spent"] == "4h"
        assert "comment" in call_args[1]


@pytest.mark.time
@pytest.mark.unit
class TestUpdateWorklogErrors:
    """Tests for error handling."""

    def test_update_worklog_not_found(self, mock_jira_client):
        """Test error when worklog doesn't exist."""
        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.update_worklog.side_effect = NotFoundError(
            "Worklog 99999 not found"
        )

        from update_worklog import update_worklog

        with pytest.raises(NotFoundError):
            update_worklog(mock_jira_client, "PROJ-123", "99999", time_spent="2h")

    def test_update_worklog_not_author(self, mock_jira_client):
        """Test error when not the worklog author."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.update_worklog.side_effect = JiraError(
            "You do not have permission to edit this worklog"
        )

        from update_worklog import update_worklog

        with pytest.raises(JiraError):
            update_worklog(mock_jira_client, "PROJ-123", "10045", time_spent="2h")

    def test_update_worklog_authentication_error_401(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from jira_assistant_skills_lib import AuthenticationError

        mock_jira_client.update_worklog.side_effect = AuthenticationError(
            "Invalid token"
        )

        from update_worklog import update_worklog

        with pytest.raises(AuthenticationError):
            update_worklog(mock_jira_client, "PROJ-123", "10045", time_spent="2h")

    def test_update_worklog_rate_limit_error_429(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.update_worklog.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        from update_worklog import update_worklog

        with pytest.raises(JiraError) as exc_info:
            update_worklog(mock_jira_client, "PROJ-123", "10045", time_spent="2h")
        assert exc_info.value.status_code == 429

    def test_update_worklog_server_error_500(self, mock_jira_client):
        """Test handling of 500 server error."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.update_worklog.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        from update_worklog import update_worklog

        with pytest.raises(JiraError) as exc_info:
            update_worklog(mock_jira_client, "PROJ-123", "10045", time_spent="2h")
        assert exc_info.value.status_code == 500
