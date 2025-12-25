"""
Tests for add_worklog.py script.

Tests adding worklogs to JIRA issues with various options.
"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add paths for imports
scripts_path = str(Path(__file__).parent.parent / 'scripts')
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


class TestAddWorklogTimeSpent:
    """Tests for basic time logging."""

    def test_add_worklog_time_spent(self, mock_jira_client, sample_worklog):
        """Test adding worklog with time spent (e.g., '2h')."""
        mock_jira_client.add_worklog.return_value = sample_worklog

        from add_worklog import add_worklog
        result = add_worklog(mock_jira_client, 'PROJ-123', '2h')

        mock_jira_client.add_worklog.assert_called_once()
        call_args = mock_jira_client.add_worklog.call_args
        assert call_args[1]['issue_key'] == 'PROJ-123'
        assert call_args[1]['time_spent'] == '2h'
        assert result['id'] == '10045'

    def test_add_worklog_various_time_formats(self, mock_jira_client, sample_worklog):
        """Test various time format strings."""
        mock_jira_client.add_worklog.return_value = sample_worklog

        from add_worklog import add_worklog

        # Test different formats
        for time_str in ['30m', '2h', '1d', '1w', '1d 4h', '2h 30m']:
            add_worklog(mock_jira_client, 'PROJ-123', time_str)
            call_args = mock_jira_client.add_worklog.call_args
            assert call_args[1]['time_spent'] == time_str


class TestAddWorklogWithStarted:
    """Tests for specifying when work was started."""

    def test_add_worklog_with_started_datetime(self, mock_jira_client, sample_worklog):
        """Test specifying when work was started."""
        mock_jira_client.add_worklog.return_value = sample_worklog

        from add_worklog import add_worklog
        result = add_worklog(
            mock_jira_client, 'PROJ-123', '2h',
            started='2025-01-15T09:00:00.000+0000'
        )

        call_args = mock_jira_client.add_worklog.call_args
        assert call_args[1]['started'] == '2025-01-15T09:00:00.000+0000'

    def test_add_worklog_with_relative_date(self, mock_jira_client, sample_worklog):
        """Test using relative date like 'yesterday'."""
        mock_jira_client.add_worklog.return_value = sample_worklog

        from add_worklog import add_worklog
        result = add_worklog(
            mock_jira_client, 'PROJ-123', '2h',
            started='yesterday'
        )

        call_args = mock_jira_client.add_worklog.call_args
        # Started should be converted to ISO format
        assert 'started' in call_args[1]
        assert call_args[1]['started'] is not None


class TestAddWorklogWithComment:
    """Tests for adding worklogs with comments."""

    def test_add_worklog_with_comment(self, mock_jira_client, sample_worklog):
        """Test adding worklog with ADF comment."""
        mock_jira_client.add_worklog.return_value = sample_worklog

        from add_worklog import add_worklog
        result = add_worklog(
            mock_jira_client, 'PROJ-123', '2h',
            comment='Debugging authentication issue'
        )

        call_args = mock_jira_client.add_worklog.call_args
        assert 'comment' in call_args[1]
        # Comment should be converted to ADF
        comment = call_args[1]['comment']
        assert comment['type'] == 'doc'
        assert comment['version'] == 1


class TestAddWorklogEstimateAdjustment:
    """Tests for estimate adjustment options."""

    def test_add_worklog_adjust_estimate_auto(self, mock_jira_client, sample_worklog):
        """Test automatic estimate adjustment."""
        mock_jira_client.add_worklog.return_value = sample_worklog

        from add_worklog import add_worklog
        result = add_worklog(mock_jira_client, 'PROJ-123', '2h')

        call_args = mock_jira_client.add_worklog.call_args
        # Default should be 'auto'
        assert call_args[1].get('adjust_estimate', 'auto') == 'auto'

    def test_add_worklog_adjust_estimate_leave(self, mock_jira_client, sample_worklog):
        """Test leaving estimate unchanged."""
        mock_jira_client.add_worklog.return_value = sample_worklog

        from add_worklog import add_worklog
        result = add_worklog(
            mock_jira_client, 'PROJ-123', '2h',
            adjust_estimate='leave'
        )

        call_args = mock_jira_client.add_worklog.call_args
        assert call_args[1]['adjust_estimate'] == 'leave'

    def test_add_worklog_adjust_estimate_new(self, mock_jira_client, sample_worklog):
        """Test setting new remaining estimate."""
        mock_jira_client.add_worklog.return_value = sample_worklog

        from add_worklog import add_worklog
        result = add_worklog(
            mock_jira_client, 'PROJ-123', '2h',
            adjust_estimate='new',
            new_estimate='6h'
        )

        call_args = mock_jira_client.add_worklog.call_args
        assert call_args[1]['adjust_estimate'] == 'new'
        assert call_args[1]['new_estimate'] == '6h'


class TestAddWorklogValidation:
    """Tests for input validation."""

    def test_add_worklog_invalid_time_format(self, mock_jira_client):
        """Test validation of time format."""
        from add_worklog import add_worklog
        from error_handler import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            add_worklog(mock_jira_client, 'PROJ-123', 'invalid')

        assert 'time format' in str(exc_info.value).lower()

    def test_add_worklog_empty_time(self, mock_jira_client):
        """Test validation rejects empty time."""
        from add_worklog import add_worklog
        from error_handler import ValidationError

        with pytest.raises(ValidationError):
            add_worklog(mock_jira_client, 'PROJ-123', '')


class TestAddWorklogErrors:
    """Tests for error handling."""

    def test_add_worklog_issue_not_found(self, mock_jira_client):
        """Test error when issue doesn't exist."""
        from error_handler import NotFoundError

        mock_jira_client.add_worklog.side_effect = NotFoundError(
            "Issue PROJ-999 not found"
        )

        from add_worklog import add_worklog

        with pytest.raises(NotFoundError):
            add_worklog(mock_jira_client, 'PROJ-999', '2h')

    def test_add_worklog_time_tracking_disabled(self, mock_jira_client):
        """Test error when time tracking is disabled."""
        from error_handler import JiraError

        mock_jira_client.add_worklog.side_effect = JiraError(
            "Time Tracking is not enabled for this issue"
        )

        from add_worklog import add_worklog

        with pytest.raises(JiraError) as exc_info:
            add_worklog(mock_jira_client, 'PROJ-123', '2h')

        assert 'time tracking' in str(exc_info.value).lower()
