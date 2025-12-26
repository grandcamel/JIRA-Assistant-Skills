"""
Tests for delete_worklog.py script.

Tests deleting worklogs from JIRA issues.
"""

import pytest
from unittest.mock import Mock
import sys
from pathlib import Path

# Add paths for imports
scripts_path = str(Path(__file__).parent.parent / 'scripts')
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


@pytest.mark.time
@pytest.mark.unit
class TestDeleteWorklog:
    """Tests for deleting worklogs."""

    def test_delete_worklog(self, mock_jira_client):
        """Test deleting a worklog."""
        mock_jira_client.delete_worklog.return_value = None

        from delete_worklog import delete_worklog
        delete_worklog(mock_jira_client, 'PROJ-123', '10045')

        mock_jira_client.delete_worklog.assert_called_once()
        call_args = mock_jira_client.delete_worklog.call_args
        assert call_args[1]['issue_key'] == 'PROJ-123'
        assert call_args[1]['worklog_id'] == '10045'

    def test_delete_worklog_adjust_estimate(self, mock_jira_client):
        """Test estimate adjustment on delete."""
        mock_jira_client.delete_worklog.return_value = None

        from delete_worklog import delete_worklog
        delete_worklog(
            mock_jira_client, 'PROJ-123', '10045',
            adjust_estimate='new',
            new_estimate='2d'
        )

        call_args = mock_jira_client.delete_worklog.call_args
        assert call_args[1]['adjust_estimate'] == 'new'
        assert call_args[1]['new_estimate'] == '2d'


@pytest.mark.time
@pytest.mark.unit
class TestDeleteWorklogDryRun:
    """Tests for dry-run mode."""

    def test_delete_worklog_dry_run(self, mock_jira_client, sample_worklog):
        """Test dry-run mode doesn't delete."""
        mock_jira_client.get_worklog.return_value = sample_worklog

        from delete_worklog import delete_worklog
        result = delete_worklog(
            mock_jira_client, 'PROJ-123', '10045',
            dry_run=True
        )

        # Should NOT call delete_worklog
        mock_jira_client.delete_worklog.assert_not_called()
        # Should return the worklog info for preview
        assert result is not None
        assert result.get('id') == '10045'


@pytest.mark.time
@pytest.mark.unit
class TestDeleteWorklogErrors:
    """Tests for error handling."""

    def test_delete_worklog_not_found(self, mock_jira_client):
        """Test error when worklog doesn't exist."""
        from error_handler import NotFoundError

        mock_jira_client.delete_worklog.side_effect = NotFoundError(
            "Worklog 99999 not found"
        )

        from delete_worklog import delete_worklog

        with pytest.raises(NotFoundError):
            delete_worklog(mock_jira_client, 'PROJ-123', '99999')

    def test_delete_worklog_issue_not_found(self, mock_jira_client):
        """Test error when issue doesn't exist."""
        from error_handler import NotFoundError

        mock_jira_client.delete_worklog.side_effect = NotFoundError(
            "Issue PROJ-999 not found"
        )

        from delete_worklog import delete_worklog

        with pytest.raises(NotFoundError):
            delete_worklog(mock_jira_client, 'PROJ-999', '10045')

    def test_delete_worklog_authentication_error_401(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from error_handler import AuthenticationError

        mock_jira_client.delete_worklog.side_effect = AuthenticationError("Invalid token")

        from delete_worklog import delete_worklog

        with pytest.raises(AuthenticationError):
            delete_worklog(mock_jira_client, 'PROJ-123', '10045')

    def test_delete_worklog_permission_denied_403(self, mock_jira_client):
        """Test handling of 403 forbidden."""
        from error_handler import PermissionError

        mock_jira_client.delete_worklog.side_effect = PermissionError(
            "You do not have permission to delete this worklog"
        )

        from delete_worklog import delete_worklog

        with pytest.raises(PermissionError):
            delete_worklog(mock_jira_client, 'PROJ-123', '10045')

    def test_delete_worklog_rate_limit_error_429(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from error_handler import JiraError

        mock_jira_client.delete_worklog.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        from delete_worklog import delete_worklog

        with pytest.raises(JiraError) as exc_info:
            delete_worklog(mock_jira_client, 'PROJ-123', '10045')
        assert exc_info.value.status_code == 429

    def test_delete_worklog_server_error_500(self, mock_jira_client):
        """Test handling of 500 server error."""
        from error_handler import JiraError

        mock_jira_client.delete_worklog.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        from delete_worklog import delete_worklog

        with pytest.raises(JiraError) as exc_info:
            delete_worklog(mock_jira_client, 'PROJ-123', '10045')
        assert exc_info.value.status_code == 500
