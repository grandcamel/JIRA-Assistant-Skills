"""
Tests for bulk_log_time.py script.

Tests logging time to multiple issues at once.
"""

import pytest
from unittest.mock import Mock, call
import sys
from pathlib import Path

# Add paths for imports
scripts_path = str(Path(__file__).parent.parent / 'scripts')
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


@pytest.mark.time
@pytest.mark.unit
class TestBulkLogTime:
    """Tests for bulk time logging."""

    def test_bulk_log_same_time(self, mock_jira_client, sample_worklog):
        """Test logging same time to multiple issues."""
        mock_jira_client.add_worklog.return_value = sample_worklog

        from bulk_log_time import bulk_log_time
        result = bulk_log_time(
            mock_jira_client,
            issues=['PROJ-1', 'PROJ-2', 'PROJ-3'],
            time_spent='30m'
        )

        assert mock_jira_client.add_worklog.call_count == 3
        assert result['success_count'] == 3
        assert result['total_seconds'] == 5400  # 30m * 3

    def test_bulk_log_with_comment(self, mock_jira_client, sample_worklog):
        """Test adding same comment to all."""
        mock_jira_client.add_worklog.return_value = sample_worklog

        from bulk_log_time import bulk_log_time
        result = bulk_log_time(
            mock_jira_client,
            issues=['PROJ-1', 'PROJ-2'],
            time_spent='15m',
            comment='Sprint planning'
        )

        # Verify comment was passed to all calls
        for call_args in mock_jira_client.add_worklog.call_args_list:
            assert call_args[1].get('comment') is not None


@pytest.mark.time
@pytest.mark.unit
class TestBulkLogTimeDryRun:
    """Tests for dry-run mode."""

    def test_bulk_log_dry_run(self, mock_jira_client):
        """Test preview without logging."""
        # Mock issue fetching for dry-run preview
        mock_jira_client.get_issue.side_effect = [
            {'key': 'PROJ-1', 'fields': {'summary': 'Task 1'}},
            {'key': 'PROJ-2', 'fields': {'summary': 'Task 2'}}
        ]

        from bulk_log_time import bulk_log_time
        result = bulk_log_time(
            mock_jira_client,
            issues=['PROJ-1', 'PROJ-2'],
            time_spent='1h',
            dry_run=True
        )

        # Should NOT call add_worklog
        mock_jira_client.add_worklog.assert_not_called()
        assert result['dry_run'] is True
        assert result['would_log_count'] == 2


@pytest.mark.time
@pytest.mark.unit
class TestBulkLogTimeJQL:
    """Tests for JQL-based bulk logging."""

    def test_bulk_log_from_jql(self, mock_jira_client, sample_worklog):
        """Test logging time to JQL results."""
        mock_jira_client.search_issues.return_value = {
            'issues': [
                {'key': 'PROJ-1', 'fields': {'summary': 'Task 1'}},
                {'key': 'PROJ-2', 'fields': {'summary': 'Task 2'}},
                {'key': 'PROJ-3', 'fields': {'summary': 'Task 3'}}
            ],
            'total': 3
        }
        mock_jira_client.add_worklog.return_value = sample_worklog

        from bulk_log_time import bulk_log_time
        result = bulk_log_time(
            mock_jira_client,
            jql='project=PROJ AND sprint=456',
            time_spent='15m'
        )

        mock_jira_client.search_issues.assert_called_once()
        assert mock_jira_client.add_worklog.call_count == 3
        assert result['success_count'] == 3


@pytest.mark.time
@pytest.mark.unit
class TestBulkLogTimeErrors:
    """Tests for error handling."""

    def test_bulk_log_partial_failure(self, mock_jira_client, sample_worklog):
        """Test handling when some logs fail."""
        from jira_assistant_skills_lib import JiraError

        # First call succeeds, second fails, third succeeds
        mock_jira_client.add_worklog.side_effect = [
            sample_worklog,
            JiraError("Permission denied"),
            sample_worklog
        ]

        from bulk_log_time import bulk_log_time
        result = bulk_log_time(
            mock_jira_client,
            issues=['PROJ-1', 'PROJ-2', 'PROJ-3'],
            time_spent='30m'
        )

        assert result['success_count'] == 2
        assert result['failure_count'] == 1
        assert len(result['failures']) == 1
        assert result['failures'][0]['issue'] == 'PROJ-2'

    def test_bulk_log_authentication_error_401(self, mock_jira_client):
        """Test handling of 401 unauthorized - captured in failures."""
        from jira_assistant_skills_lib import AuthenticationError

        mock_jira_client.add_worklog.side_effect = AuthenticationError("Invalid token")

        from bulk_log_time import bulk_log_time

        # Bulk log catches errors and records them as failures
        result = bulk_log_time(
            mock_jira_client,
            issues=['PROJ-1'],
            time_spent='30m'
        )
        assert result['success_count'] == 0
        assert result['failure_count'] == 1
        assert 'Invalid token' in result['failures'][0]['error']

    def test_bulk_log_rate_limit_error_429(self, mock_jira_client):
        """Test handling of 429 rate limit - captured in failures."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.add_worklog.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        from bulk_log_time import bulk_log_time

        # Bulk log catches errors and records them as failures
        result = bulk_log_time(
            mock_jira_client,
            issues=['PROJ-1'],
            time_spent='30m'
        )
        assert result['success_count'] == 0
        assert result['failure_count'] == 1
        assert 'Rate limit' in result['failures'][0]['error']

    def test_bulk_log_server_error_500(self, mock_jira_client):
        """Test handling of 500 server error - captured in failures."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.add_worklog.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        from bulk_log_time import bulk_log_time

        # Bulk log catches errors and records them as failures
        result = bulk_log_time(
            mock_jira_client,
            issues=['PROJ-1'],
            time_spent='30m'
        )
        assert result['success_count'] == 0
        assert result['failure_count'] == 1
        assert 'Internal server error' in result['failures'][0]['error']
