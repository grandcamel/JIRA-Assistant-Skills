"""
Tests for get_worklogs.py script.

Tests retrieving worklogs from JIRA issues with filtering options.
"""

import pytest
from unittest.mock import Mock
import sys
from pathlib import Path

# Add paths for imports
scripts_path = str(Path(__file__).parent.parent / 'scripts')
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


class TestGetWorklogs:
    """Tests for fetching worklogs."""

    def test_get_all_worklogs(self, mock_jira_client, sample_worklogs):
        """Test fetching all worklogs for an issue."""
        mock_jira_client.get_worklogs.return_value = sample_worklogs

        from get_worklogs import get_worklogs
        result = get_worklogs(mock_jira_client, 'PROJ-123')

        mock_jira_client.get_worklogs.assert_called_once_with('PROJ-123')
        assert result['total'] == 3
        assert len(result['worklogs']) == 3

    def test_get_worklogs_returns_list(self, mock_jira_client, sample_worklogs):
        """Test that worklogs are returned as a list."""
        mock_jira_client.get_worklogs.return_value = sample_worklogs

        from get_worklogs import get_worklogs
        result = get_worklogs(mock_jira_client, 'PROJ-123')

        assert 'worklogs' in result
        assert isinstance(result['worklogs'], list)


class TestGetWorklogsFiltering:
    """Tests for filtering worklogs."""

    def test_get_worklogs_filter_by_author(self, mock_jira_client, sample_worklogs):
        """Test filtering worklogs by author."""
        mock_jira_client.get_worklogs.return_value = sample_worklogs

        from get_worklogs import get_worklogs
        result = get_worklogs(mock_jira_client, 'PROJ-123',
                              author_filter='alice@company.com')

        # Should filter to only Alice's worklogs (2 out of 3)
        assert len(result['worklogs']) == 2
        for worklog in result['worklogs']:
            assert worklog['author']['emailAddress'] == 'alice@company.com'

    def test_get_worklogs_filter_by_date_range(self, mock_jira_client, sample_worklogs):
        """Test filtering by date range."""
        mock_jira_client.get_worklogs.return_value = sample_worklogs

        from get_worklogs import get_worklogs
        result = get_worklogs(
            mock_jira_client, 'PROJ-123',
            since='2025-01-16T00:00:00.000+0000',
            until='2025-01-17T00:00:00.000+0000'
        )

        # Should only include worklogs from Jan 16
        assert len(result['worklogs']) == 1
        assert '2025-01-16' in result['worklogs'][0]['started']


class TestGetWorklogsOutput:
    """Tests for output formatting."""

    def test_get_worklogs_calculates_total(self, mock_jira_client, sample_worklogs):
        """Test total time calculation."""
        mock_jira_client.get_worklogs.return_value = sample_worklogs

        from get_worklogs import get_worklogs
        result = get_worklogs(mock_jira_client, 'PROJ-123')

        # Calculate expected total: 7200 + 5400 + 14400 = 27000 seconds
        total_seconds = sum(w['timeSpentSeconds'] for w in result['worklogs'])
        assert total_seconds == 27000

    def test_get_worklogs_format_text(self, mock_jira_client, sample_worklogs, capsys):
        """Test human-readable output."""
        mock_jira_client.get_worklogs.return_value = sample_worklogs

        from get_worklogs import format_worklogs_text
        output = format_worklogs_text(sample_worklogs, 'PROJ-123')

        assert 'PROJ-123' in output
        assert 'Alice Smith' in output or 'alice@company.com' in output
        assert '2h' in output or '7200' in output

    def test_get_worklogs_format_json(self, mock_jira_client, sample_worklogs):
        """Test JSON output format."""
        mock_jira_client.get_worklogs.return_value = sample_worklogs

        from get_worklogs import get_worklogs
        result = get_worklogs(mock_jira_client, 'PROJ-123')

        # Should be JSON-serializable dict
        import json
        json_str = json.dumps(result)
        assert 'worklogs' in json_str


class TestGetWorklogsEmpty:
    """Tests for empty worklog handling."""

    def test_get_worklogs_empty(self, mock_jira_client, sample_empty_worklogs):
        """Test output when no worklogs exist."""
        mock_jira_client.get_worklogs.return_value = sample_empty_worklogs

        from get_worklogs import get_worklogs
        result = get_worklogs(mock_jira_client, 'PROJ-123')

        assert result['total'] == 0
        assert len(result['worklogs']) == 0


class TestGetWorklogsErrors:
    """Tests for error handling."""

    def test_get_worklogs_issue_not_found(self, mock_jira_client):
        """Test error when issue doesn't exist."""
        from error_handler import NotFoundError

        mock_jira_client.get_worklogs.side_effect = NotFoundError(
            "Issue PROJ-999 not found"
        )

        from get_worklogs import get_worklogs

        with pytest.raises(NotFoundError):
            get_worklogs(mock_jira_client, 'PROJ-999')
