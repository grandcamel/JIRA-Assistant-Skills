"""
Tests for bulk_set_priority.py - TDD approach.
"""

import sys
from pathlib import Path
import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


@pytest.mark.bulk
@pytest.mark.unit
class TestBulkPriorityByKeys:
    """Test setting priority on multiple issues by keys."""

    def test_bulk_priority_by_keys(self, mock_jira_client):
        """Test setting priority on multiple issues by key list."""
        from bulk_set_priority import bulk_set_priority

        # Setup mock
        mock_jira_client.update_issue.return_value = None

        # Execute
        result = bulk_set_priority(
            client=mock_jira_client,
            issue_keys=['PROJ-1', 'PROJ-2', 'PROJ-3'],
            priority='High',
            dry_run=False
        )

        # Verify
        assert result['success'] == 3
        assert result['failed'] == 0
        assert mock_jira_client.update_issue.call_count == 3


@pytest.mark.bulk
@pytest.mark.unit
class TestBulkPriorityByJql:
    """Test setting priority via JQL filter."""

    def test_bulk_priority_by_jql(self, mock_jira_client, sample_issues):
        """Test setting priority via JQL filter."""
        from bulk_set_priority import bulk_set_priority

        # Setup mock
        mock_jira_client.search_issues.return_value = {
            'issues': sample_issues,
            'total': 3
        }
        mock_jira_client.update_issue.return_value = None

        # Execute
        result = bulk_set_priority(
            client=mock_jira_client,
            jql="project=PROJ AND type=Bug",
            priority='Blocker',
            dry_run=False
        )

        # Verify
        assert result['success'] == 3
        mock_jira_client.search_issues.assert_called_once()


@pytest.mark.bulk
@pytest.mark.unit
class TestBulkPriorityInvalid:
    """Test error for invalid priority name."""

    def test_bulk_priority_invalid_name(self, mock_jira_client):
        """Test error for invalid priority name."""
        from bulk_set_priority import bulk_set_priority
        from error_handler import ValidationError

        # Execute with invalid priority
        with pytest.raises(ValidationError):
            bulk_set_priority(
                client=mock_jira_client,
                issue_keys=['PROJ-1'],
                priority='InvalidPriority',
                dry_run=False
            )


@pytest.mark.bulk
@pytest.mark.unit
class TestBulkPriorityDryRun:
    """Test dry-run preview."""

    def test_bulk_priority_dry_run(self, mock_jira_client, sample_issues):
        """Test dry-run preview doesn't make changes."""
        from bulk_set_priority import bulk_set_priority

        # Setup mock
        mock_jira_client.search_issues.return_value = {
            'issues': sample_issues,
            'total': 3
        }

        # Execute
        result = bulk_set_priority(
            client=mock_jira_client,
            jql="project=PROJ",
            priority='High',
            dry_run=True
        )

        # Verify no actual updates made
        assert result['would_process'] == 3
        mock_jira_client.update_issue.assert_not_called()


@pytest.mark.bulk
@pytest.mark.unit
class TestBulkPriorityPartialFailure:
    """Test partial failure handling."""

    def test_bulk_priority_partial_failure(self, mock_jira_client):
        """Test partial failure handling."""
        from bulk_set_priority import bulk_set_priority
        from error_handler import JiraError

        # Setup mock - fail on second issue
        def update_side_effect(issue_key, fields, **kwargs):
            if issue_key == 'PROJ-2':
                raise JiraError("Update failed")
            return None

        mock_jira_client.update_issue.side_effect = update_side_effect

        # Execute
        result = bulk_set_priority(
            client=mock_jira_client,
            issue_keys=['PROJ-1', 'PROJ-2', 'PROJ-3'],
            priority='High',
            dry_run=False
        )

        # Verify partial success
        assert result['success'] == 2
        assert result['failed'] == 1


@pytest.mark.bulk
@pytest.mark.unit
class TestBulkPriorityAllStandard:
    """Test all standard priorities work."""

    @pytest.mark.parametrize("priority", ['Highest', 'High', 'Medium', 'Low', 'Lowest'])
    def test_bulk_priority_standard_values(self, mock_jira_client, priority):
        """Test all standard priority values work."""
        from bulk_set_priority import bulk_set_priority

        # Setup mock
        mock_jira_client.update_issue.return_value = None

        # Execute
        result = bulk_set_priority(
            client=mock_jira_client,
            issue_keys=['PROJ-1'],
            priority=priority,
            dry_run=False
        )

        # Verify
        assert result['success'] == 1


@pytest.mark.bulk
@pytest.mark.unit
class TestBulkPriorityProgressCallback:
    """Test progress reporting."""

    def test_bulk_priority_progress_callback(self, mock_jira_client):
        """Test progress reporting during operation."""
        from bulk_set_priority import bulk_set_priority

        # Setup mock
        mock_jira_client.update_issue.return_value = None

        # Track progress calls
        progress_calls = []

        def progress_callback(current, total, issue_key, status):
            progress_calls.append({
                'current': current,
                'total': total,
                'issue_key': issue_key,
                'status': status
            })

        # Execute
        result = bulk_set_priority(
            client=mock_jira_client,
            issue_keys=['PROJ-1', 'PROJ-2', 'PROJ-3'],
            priority='High',
            dry_run=False,
            progress_callback=progress_callback
        )

        # Verify progress was reported
        assert len(progress_calls) == 3


@pytest.mark.bulk
@pytest.mark.unit
class TestBulkPriorityNoIssues:
    """Test when no issues found."""

    def test_bulk_priority_no_issues(self, mock_jira_client):
        """Test when no issues found."""
        from bulk_set_priority import bulk_set_priority

        # Setup mock
        mock_jira_client.search_issues.return_value = {
            'issues': [],
            'total': 0
        }

        # Execute
        result = bulk_set_priority(
            client=mock_jira_client,
            jql="project=NONEXISTENT",
            priority='High',
            dry_run=False
        )

        # Verify
        assert result['success'] == 0
        assert result['total'] == 0


@pytest.mark.bulk
@pytest.mark.unit
class TestBulkPriorityApiErrors:
    """Test API error handling scenarios."""

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 unauthorized error."""
        from bulk_set_priority import bulk_set_priority
        from error_handler import AuthenticationError

        mock_jira_client.update_issue.side_effect = AuthenticationError("Invalid token")

        result = bulk_set_priority(
            client=mock_jira_client,
            issue_keys=['PROJ-1'],
            priority='High',
            dry_run=False
        )

        assert result['failed'] == 1
        assert result['success'] == 0
        assert 'PROJ-1' in result.get('errors', {})

    def test_permission_denied_error(self, mock_jira_client):
        """Test handling of 403 forbidden error."""
        from bulk_set_priority import bulk_set_priority
        from error_handler import JiraError

        mock_jira_client.update_issue.side_effect = JiraError(
            "You do not have permission", status_code=403
        )

        result = bulk_set_priority(
            client=mock_jira_client,
            issue_keys=['PROJ-1'],
            priority='High',
            dry_run=False
        )

        assert result['failed'] == 1
        assert result['success'] == 0
        assert 'PROJ-1' in result.get('errors', {})

    def test_not_found_error(self, mock_jira_client):
        """Test handling of 404 not found error."""
        from bulk_set_priority import bulk_set_priority
        from error_handler import JiraError

        mock_jira_client.update_issue.side_effect = JiraError(
            "Issue not found", status_code=404
        )

        result = bulk_set_priority(
            client=mock_jira_client,
            issue_keys=['PROJ-999'],
            priority='High',
            dry_run=False
        )

        assert result['failed'] == 1
        assert result['success'] == 0

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit error."""
        from bulk_set_priority import bulk_set_priority
        from error_handler import JiraError

        mock_jira_client.update_issue.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        result = bulk_set_priority(
            client=mock_jira_client,
            issue_keys=['PROJ-1'],
            priority='High',
            dry_run=False
        )

        assert result['failed'] == 1
        assert result['success'] == 0

    def test_server_error(self, mock_jira_client):
        """Test handling of 500 internal server error."""
        from bulk_set_priority import bulk_set_priority
        from error_handler import JiraError

        mock_jira_client.update_issue.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        result = bulk_set_priority(
            client=mock_jira_client,
            issue_keys=['PROJ-1'],
            priority='High',
            dry_run=False
        )

        assert result['failed'] == 1
        assert result['success'] == 0
