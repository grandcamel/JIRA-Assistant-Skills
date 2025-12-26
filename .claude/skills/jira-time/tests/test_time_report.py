"""
Tests for time_report.py script.

Tests generating time reports from JIRA worklogs.
"""

import pytest
from unittest.mock import Mock
import sys
from pathlib import Path

# Add paths for imports
scripts_path = str(Path(__file__).parent.parent / 'scripts')
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


@pytest.fixture
def sample_issues_with_worklogs():
    """Sample search results with issues that have worklogs."""
    return {
        'issues': [
            {
                'key': 'PROJ-123',
                'fields': {
                    'summary': 'Authentication refactor'
                }
            }
        ],
        'total': 1
    }


@pytest.fixture
def sample_worklogs_for_report():
    """Sample worklogs for report generation."""
    return [
        {
            'id': '10045',
            'author': {'accountId': 'user1', 'emailAddress': 'alice@company.com', 'displayName': 'Alice'},
            'started': '2025-01-15T09:00:00.000+0000',
            'timeSpent': '4h',
            'timeSpentSeconds': 14400
        },
        {
            'id': '10046',
            'author': {'accountId': 'user1', 'emailAddress': 'alice@company.com', 'displayName': 'Alice'},
            'started': '2025-01-15T14:00:00.000+0000',
            'timeSpent': '2h',
            'timeSpentSeconds': 7200
        },
        {
            'id': '10047',
            'author': {'accountId': 'user2', 'emailAddress': 'bob@company.com', 'displayName': 'Bob'},
            'started': '2025-01-16T10:00:00.000+0000',
            'timeSpent': '3h',
            'timeSpentSeconds': 10800
        }
    ]


@pytest.mark.time
@pytest.mark.unit
class TestTimeReportFiltering:
    """Tests for filtering worklogs."""

    def test_report_by_user(self, mock_jira_client, sample_issues_with_worklogs, sample_worklogs_for_report):
        """Test time report for specific user."""
        mock_jira_client.search_issues.return_value = sample_issues_with_worklogs
        mock_jira_client.get_worklogs.return_value = {
            'worklogs': sample_worklogs_for_report
        }

        from time_report import generate_report
        result = generate_report(
            mock_jira_client,
            project='PROJ',
            author='alice@company.com'
        )

        # Should only include Alice's worklogs (2 entries, 4h + 2h)
        assert result['total_seconds'] == 21600  # 6h
        assert len(result['entries']) == 2

    def test_report_by_project(self, mock_jira_client, sample_issues_with_worklogs, sample_worklogs_for_report):
        """Test time report for project."""
        mock_jira_client.search_issues.return_value = sample_issues_with_worklogs
        mock_jira_client.get_worklogs.return_value = {
            'worklogs': sample_worklogs_for_report
        }

        from time_report import generate_report
        result = generate_report(mock_jira_client, project='PROJ')

        # Should include all worklogs from one issue (4h + 2h + 3h = 9h)
        assert result['total_seconds'] == 32400

    def test_report_by_date_range(self, mock_jira_client, sample_issues_with_worklogs, sample_worklogs_for_report):
        """Test time report for date range."""
        mock_jira_client.search_issues.return_value = sample_issues_with_worklogs
        mock_jira_client.get_worklogs.return_value = {
            'worklogs': sample_worklogs_for_report
        }

        from time_report import generate_report
        result = generate_report(
            mock_jira_client,
            project='PROJ',
            since='2025-01-15',
            until='2025-01-15'
        )

        # Should only include worklogs from Jan 15 (first 2 entries)
        assert len(result['entries']) == 2


@pytest.mark.time
@pytest.mark.unit
class TestTimeReportGrouping:
    """Tests for grouping worklogs."""

    def test_report_group_by_issue(self, mock_jira_client, sample_issues_with_worklogs, sample_worklogs_for_report):
        """Test grouping by issue."""
        mock_jira_client.search_issues.return_value = sample_issues_with_worklogs
        mock_jira_client.get_worklogs.return_value = {
            'worklogs': sample_worklogs_for_report
        }

        from time_report import generate_report
        result = generate_report(
            mock_jira_client,
            project='PROJ',
            group_by='issue'
        )

        assert 'grouped' in result
        assert result['group_by'] == 'issue'

    def test_report_group_by_day(self, mock_jira_client, sample_issues_with_worklogs, sample_worklogs_for_report):
        """Test grouping by day."""
        mock_jira_client.search_issues.return_value = sample_issues_with_worklogs
        mock_jira_client.get_worklogs.return_value = {
            'worklogs': sample_worklogs_for_report
        }

        from time_report import generate_report
        result = generate_report(
            mock_jira_client,
            project='PROJ',
            group_by='day'
        )

        assert result['group_by'] == 'day'

    def test_report_group_by_user(self, mock_jira_client, sample_issues_with_worklogs, sample_worklogs_for_report):
        """Test grouping by user."""
        mock_jira_client.search_issues.return_value = sample_issues_with_worklogs
        mock_jira_client.get_worklogs.return_value = {
            'worklogs': sample_worklogs_for_report
        }

        from time_report import generate_report
        result = generate_report(
            mock_jira_client,
            project='PROJ',
            group_by='user'
        )

        assert result['group_by'] == 'user'


@pytest.mark.time
@pytest.mark.unit
class TestTimeReportOutput:
    """Tests for output formatting."""

    def test_report_format_json(self, mock_jira_client, sample_issues_with_worklogs, sample_worklogs_for_report):
        """Test JSON output."""
        mock_jira_client.search_issues.return_value = sample_issues_with_worklogs
        mock_jira_client.get_worklogs.return_value = {
            'worklogs': sample_worklogs_for_report
        }

        from time_report import generate_report
        result = generate_report(mock_jira_client, project='PROJ')

        # Result should be serializable
        import json
        json_str = json.dumps(result)
        assert 'total_seconds' in json_str

    def test_report_calculate_totals(self, mock_jira_client, sample_issues_with_worklogs, sample_worklogs_for_report):
        """Test total calculations."""
        mock_jira_client.search_issues.return_value = sample_issues_with_worklogs
        mock_jira_client.get_worklogs.return_value = {
            'worklogs': sample_worklogs_for_report
        }

        from time_report import generate_report
        result = generate_report(mock_jira_client, project='PROJ')

        # 4h + 2h + 3h = 9h = 32400 seconds
        assert result['total_seconds'] == 32400
        assert result['entry_count'] == 3


@pytest.mark.time
@pytest.mark.unit
class TestTimeReportEmpty:
    """Tests for empty results."""

    def test_report_no_worklogs(self, mock_jira_client):
        """Test report with no worklogs."""
        mock_jira_client.search_issues.return_value = {'issues': [], 'total': 0}

        from time_report import generate_report
        result = generate_report(mock_jira_client, project='PROJ')

        assert result['total_seconds'] == 0
        assert result['entry_count'] == 0
        assert result['entries'] == []


@pytest.mark.time
@pytest.mark.unit
class TestTimeReportErrors:
    """Tests for error handling."""

    def test_report_authentication_error_401(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from error_handler import AuthenticationError

        mock_jira_client.search_issues.side_effect = AuthenticationError("Invalid token")

        from time_report import generate_report

        with pytest.raises(AuthenticationError):
            generate_report(mock_jira_client, project='PROJ')

    def test_report_permission_denied_403(self, mock_jira_client):
        """Test handling of 403 forbidden."""
        from error_handler import PermissionError

        mock_jira_client.search_issues.side_effect = PermissionError(
            "You do not have permission to search issues"
        )

        from time_report import generate_report

        with pytest.raises(PermissionError):
            generate_report(mock_jira_client, project='PROJ')

    def test_report_rate_limit_error_429(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from error_handler import JiraError

        mock_jira_client.search_issues.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        from time_report import generate_report

        with pytest.raises(JiraError) as exc_info:
            generate_report(mock_jira_client, project='PROJ')
        assert exc_info.value.status_code == 429

    def test_report_server_error_500(self, mock_jira_client):
        """Test handling of 500 server error."""
        from error_handler import JiraError

        mock_jira_client.search_issues.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        from time_report import generate_report

        with pytest.raises(JiraError) as exc_info:
            generate_report(mock_jira_client, project='PROJ')
        assert exc_info.value.status_code == 500
