"""
Tests for delete_worklog.py script.

Tests deleting worklogs from JIRA issues.
"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add paths for imports
scripts_path = str(Path(__file__).parent.parent / 'scripts')
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


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
