"""
Tests for bulk_assign.py - TDD approach.
"""

import sys
from pathlib import Path
import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


@pytest.mark.bulk
@pytest.mark.unit
class TestBulkAssignToUser:
    """Test assigning multiple issues to specific user."""

    def test_bulk_assign_to_user_by_account_id(self, mock_jira_client, sample_issues):
        """Test assigning multiple issues to specific user by account ID."""
        from bulk_assign import bulk_assign

        # Setup mock
        mock_jira_client.assign_issue.return_value = None

        # Execute
        result = bulk_assign(
            client=mock_jira_client,
            issue_keys=['PROJ-1', 'PROJ-2', 'PROJ-3'],
            assignee='user-123',
            dry_run=False
        )

        # Verify
        assert result['success'] == 3
        assert result['failed'] == 0
        assert mock_jira_client.assign_issue.call_count == 3


@pytest.mark.bulk
@pytest.mark.unit
class TestBulkAssignToSelf:
    """Test assigning to self."""

    def test_bulk_assign_to_self(self, mock_jira_client, sample_issues):
        """Test assigning to self using 'self' keyword."""
        from bulk_assign import bulk_assign

        # Setup mock
        mock_jira_client.get_current_user_id.return_value = 'current-user-id'
        mock_jira_client.assign_issue.return_value = None

        # Execute
        result = bulk_assign(
            client=mock_jira_client,
            issue_keys=['PROJ-1', 'PROJ-2'],
            assignee='self',
            dry_run=False
        )

        # Verify self was resolved to current user
        assert result['success'] == 2
        mock_jira_client.get_current_user_id.assert_called_once()


@pytest.mark.bulk
@pytest.mark.unit
class TestBulkAssignUnassign:
    """Test removing assignee (unassign)."""

    def test_bulk_unassign(self, mock_jira_client, sample_issues):
        """Test removing assignee (unassign)."""
        from bulk_assign import bulk_assign

        # Setup mock
        mock_jira_client.assign_issue.return_value = None

        # Execute
        result = bulk_assign(
            client=mock_jira_client,
            issue_keys=['PROJ-1', 'PROJ-2'],
            unassign=True,
            dry_run=False
        )

        # Verify unassign was called with None
        assert result['success'] == 2
        # Verify assign_issue was called with None for account_id
        for call in mock_jira_client.assign_issue.call_args_list:
            assert call[0][1] is None or call[1].get('account_id') is None


@pytest.mark.bulk
@pytest.mark.unit
class TestBulkAssignByJql:
    """Test assigning issues matching JQL."""

    def test_bulk_assign_by_jql(self, mock_jira_client, sample_issues):
        """Test assigning issues matching JQL."""
        from bulk_assign import bulk_assign

        # Setup mock
        mock_jira_client.search_issues.return_value = {
            'issues': sample_issues,
            'total': 3
        }
        mock_jira_client.assign_issue.return_value = None

        # Execute
        result = bulk_assign(
            client=mock_jira_client,
            jql="project=PROJ AND status=Open",
            assignee='user-123',
            dry_run=False
        )

        # Verify
        assert result['success'] == 3
        mock_jira_client.search_issues.assert_called_once()


@pytest.mark.bulk
@pytest.mark.unit
class TestBulkAssignWithEmail:
    """Test resolving user by email."""

    def test_bulk_assign_with_email_lookup(self, mock_jira_client):
        """Test resolving user by email."""
        from bulk_assign import bulk_assign

        # Setup mock - simulate user search
        mock_jira_client.get.return_value = [
            {'accountId': 'resolved-user-id', 'emailAddress': 'john@example.com'}
        ]
        mock_jira_client.assign_issue.return_value = None

        # Execute
        result = bulk_assign(
            client=mock_jira_client,
            issue_keys=['PROJ-1'],
            assignee='john@example.com',
            dry_run=False
        )

        # Verify email was resolved
        assert result['success'] == 1


@pytest.mark.bulk
@pytest.mark.unit
class TestBulkAssignDryRun:
    """Test dry-run preview."""

    def test_bulk_assign_dry_run(self, mock_jira_client, sample_issues):
        """Test dry-run preview doesn't make changes."""
        from bulk_assign import bulk_assign

        # Setup mock
        mock_jira_client.search_issues.return_value = {
            'issues': sample_issues,
            'total': 3
        }

        # Execute
        result = bulk_assign(
            client=mock_jira_client,
            jql="project=PROJ",
            assignee='user-123',
            dry_run=True
        )

        # Verify no actual assignments made
        assert result['would_process'] == 3
        mock_jira_client.assign_issue.assert_not_called()


@pytest.mark.bulk
@pytest.mark.unit
class TestBulkAssignInvalidUser:
    """Test error handling for invalid user."""

    def test_bulk_assign_invalid_user(self, mock_jira_client):
        """Test error handling when assignee cannot be found."""
        from bulk_assign import bulk_assign
        from error_handler import JiraError

        # Setup mock - user lookup returns empty, script treats email as account ID
        mock_jira_client.get.return_value = []  # No user found

        # The actual API call will fail when trying to assign with invalid account ID
        mock_jira_client.assign_issue.side_effect = JiraError(
            "User not found", status_code=404
        )

        # Execute - the assign operation should fail
        result = bulk_assign(
            client=mock_jira_client,
            issue_keys=['PROJ-1'],
            assignee='nonexistent@example.com',
            dry_run=False
        )

        # Verify the operation failed
        assert result['failed'] == 1
        assert result['success'] == 0


@pytest.mark.bulk
@pytest.mark.unit
class TestBulkAssignPartialFailure:
    """Test partial failure handling."""

    def test_bulk_assign_partial_failure(self, mock_jira_client):
        """Test partial failure handling."""
        from bulk_assign import bulk_assign
        from error_handler import JiraError

        # Setup mock - fail on second issue
        def assign_side_effect(issue_key, account_id):
            if issue_key == 'PROJ-2':
                raise JiraError("Permission denied")
            return None

        mock_jira_client.assign_issue.side_effect = assign_side_effect

        # Execute
        result = bulk_assign(
            client=mock_jira_client,
            issue_keys=['PROJ-1', 'PROJ-2', 'PROJ-3'],
            assignee='user-123',
            dry_run=False
        )

        # Verify partial success
        assert result['success'] == 2
        assert result['failed'] == 1


@pytest.mark.bulk
@pytest.mark.unit
class TestBulkAssignProgressCallback:
    """Test progress reporting."""

    def test_bulk_assign_progress_callback(self, mock_jira_client):
        """Test progress reporting during operation."""
        from bulk_assign import bulk_assign

        # Setup mock
        mock_jira_client.assign_issue.return_value = None

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
        result = bulk_assign(
            client=mock_jira_client,
            issue_keys=['PROJ-1', 'PROJ-2'],
            assignee='user-123',
            dry_run=False,
            progress_callback=progress_callback
        )

        # Verify progress was reported
        assert len(progress_calls) == 2


@pytest.mark.bulk
@pytest.mark.unit
class TestBulkAssignApiErrors:
    """Test API error handling scenarios."""

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 unauthorized error."""
        from bulk_assign import bulk_assign
        from error_handler import AuthenticationError

        mock_jira_client.assign_issue.side_effect = AuthenticationError("Invalid token")

        result = bulk_assign(
            client=mock_jira_client,
            issue_keys=['PROJ-1'],
            assignee='user-123',
            dry_run=False
        )

        assert result['failed'] == 1
        assert result['success'] == 0
        assert 'PROJ-1' in result.get('errors', {})

    def test_permission_denied_error(self, mock_jira_client):
        """Test handling of 403 forbidden error."""
        from bulk_assign import bulk_assign
        from error_handler import JiraError

        mock_jira_client.assign_issue.side_effect = JiraError(
            "You do not have permission", status_code=403
        )

        result = bulk_assign(
            client=mock_jira_client,
            issue_keys=['PROJ-1'],
            assignee='user-123',
            dry_run=False
        )

        assert result['failed'] == 1
        assert result['success'] == 0
        assert 'PROJ-1' in result.get('errors', {})

    def test_not_found_error(self, mock_jira_client):
        """Test handling of 404 not found error."""
        from bulk_assign import bulk_assign
        from error_handler import JiraError

        mock_jira_client.assign_issue.side_effect = JiraError(
            "Issue not found", status_code=404
        )

        result = bulk_assign(
            client=mock_jira_client,
            issue_keys=['PROJ-999'],
            assignee='user-123',
            dry_run=False
        )

        assert result['failed'] == 1
        assert result['success'] == 0

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit error."""
        from bulk_assign import bulk_assign
        from error_handler import JiraError

        mock_jira_client.assign_issue.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        result = bulk_assign(
            client=mock_jira_client,
            issue_keys=['PROJ-1'],
            assignee='user-123',
            dry_run=False
        )

        assert result['failed'] == 1
        assert result['success'] == 0

    def test_server_error(self, mock_jira_client):
        """Test handling of 500 internal server error."""
        from bulk_assign import bulk_assign
        from error_handler import JiraError

        mock_jira_client.assign_issue.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        result = bulk_assign(
            client=mock_jira_client,
            issue_keys=['PROJ-1'],
            assignee='user-123',
            dry_run=False
        )

        assert result['failed'] == 1
        assert result['success'] == 0
