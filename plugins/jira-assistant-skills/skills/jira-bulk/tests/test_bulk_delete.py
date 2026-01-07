"""
Tests for bulk_delete.py - TDD approach.
"""

import sys
from pathlib import Path

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


@pytest.fixture
def sample_issues_for_delete():
    """Sample issue data for delete testing."""
    return [
        {
            "key": "PROJ-1",
            "id": "10001",
            "fields": {
                "summary": "First issue to delete",
                "status": {"name": "To Do", "id": "1"},
                "issuetype": {"name": "Task", "id": "10001"},
                "subtasks": [],
            },
        },
        {
            "key": "PROJ-2",
            "id": "10002",
            "fields": {
                "summary": "Second issue to delete",
                "status": {"name": "In Progress", "id": "2"},
                "issuetype": {"name": "Bug", "id": "10002"},
                "subtasks": [],
            },
        },
        {
            "key": "PROJ-3",
            "id": "10003",
            "fields": {
                "summary": "Third issue to delete",
                "status": {"name": "Done", "id": "3"},
                "issuetype": {"name": "Story", "id": "10003"},
                "subtasks": [
                    {"key": "PROJ-4", "fields": {"summary": "Subtask 1"}},
                    {"key": "PROJ-5", "fields": {"summary": "Subtask 2"}},
                ],
            },
        },
    ]


@pytest.mark.bulk
@pytest.mark.unit
class TestBulkDeleteBasic:
    """Test basic bulk delete operations."""

    def test_bulk_delete_by_keys(self, mock_jira_client):
        """Test deleting multiple issues by keys."""
        from bulk_delete import bulk_delete

        # Setup mock
        mock_jira_client.delete_issue.return_value = None

        # Execute
        result = bulk_delete(
            client=mock_jira_client,
            issue_keys=["PROJ-1", "PROJ-2", "PROJ-3"],
            dry_run=False,
            skip_confirmation=True,
        )

        # Verify
        assert result["success"] == 3
        assert result["failed"] == 0
        assert mock_jira_client.delete_issue.call_count == 3

    def test_bulk_delete_by_jql(self, mock_jira_client, sample_issues_for_delete):
        """Test deleting issues matching JQL."""
        from bulk_delete import bulk_delete

        # Setup mock
        mock_jira_client.search_issues.return_value = {
            "issues": sample_issues_for_delete,
            "total": 3,
        }
        mock_jira_client.delete_issue.return_value = None

        # Execute
        result = bulk_delete(
            client=mock_jira_client,
            jql="project=PROJ",
            dry_run=False,
            skip_confirmation=True,
        )

        # Verify
        assert result["success"] == 3
        mock_jira_client.search_issues.assert_called_once()


@pytest.mark.bulk
@pytest.mark.unit
class TestBulkDeleteDryRun:
    """Test dry-run preview."""

    def test_bulk_delete_dry_run_by_keys(self, mock_jira_client):
        """Test dry-run preview doesn't make changes."""
        from bulk_delete import bulk_delete

        # Execute
        result = bulk_delete(
            client=mock_jira_client,
            issue_keys=["PROJ-1", "PROJ-2", "PROJ-3"],
            dry_run=True,
        )

        # Verify no actual deletions made
        assert result["would_process"] == 3
        assert result.get("dry_run") is True
        mock_jira_client.delete_issue.assert_not_called()

    def test_bulk_delete_dry_run_by_jql(
        self, mock_jira_client, sample_issues_for_delete
    ):
        """Test dry-run preview with JQL."""
        from bulk_delete import bulk_delete

        # Setup mock
        mock_jira_client.search_issues.return_value = {
            "issues": sample_issues_for_delete,
            "total": 3,
        }

        # Execute
        result = bulk_delete(
            client=mock_jira_client,
            jql="project=PROJ",
            dry_run=True,
        )

        # Verify no actual deletions made
        assert result["would_process"] == 3
        assert result.get("dry_run") is True
        mock_jira_client.delete_issue.assert_not_called()


@pytest.mark.bulk
@pytest.mark.unit
class TestBulkDeleteWithSubtasks:
    """Test subtask deletion control."""

    def test_bulk_delete_with_subtasks(self, mock_jira_client):
        """Test deleting issues including subtasks (default)."""
        from bulk_delete import bulk_delete

        # Setup mock
        mock_jira_client.delete_issue.return_value = None

        # Execute
        result = bulk_delete(
            client=mock_jira_client,
            issue_keys=["PROJ-1"],
            dry_run=False,
            delete_subtasks=True,
            skip_confirmation=True,
        )

        # Verify subtasks flag was passed
        assert result["success"] == 1
        mock_jira_client.delete_issue.assert_called_once_with(
            "PROJ-1", delete_subtasks=True
        )

    def test_bulk_delete_without_subtasks(self, mock_jira_client):
        """Test deleting issues without subtasks."""
        from bulk_delete import bulk_delete

        # Setup mock
        mock_jira_client.delete_issue.return_value = None

        # Execute
        result = bulk_delete(
            client=mock_jira_client,
            issue_keys=["PROJ-1"],
            dry_run=False,
            delete_subtasks=False,
            skip_confirmation=True,
        )

        # Verify subtasks flag was passed
        assert result["success"] == 1
        mock_jira_client.delete_issue.assert_called_once_with(
            "PROJ-1", delete_subtasks=False
        )


@pytest.mark.bulk
@pytest.mark.unit
class TestBulkDeletePartialFailure:
    """Test partial failure handling."""

    def test_bulk_delete_partial_failure(self, mock_jira_client):
        """Test partial failure handling."""
        from bulk_delete import bulk_delete

        from jira_assistant_skills_lib import JiraError

        # Setup mock - fail on second issue
        def delete_side_effect(issue_key, delete_subtasks=True):
            if issue_key == "PROJ-2":
                raise JiraError("Permission denied", status_code=403)
            return None

        mock_jira_client.delete_issue.side_effect = delete_side_effect

        # Execute
        result = bulk_delete(
            client=mock_jira_client,
            issue_keys=["PROJ-1", "PROJ-2", "PROJ-3"],
            dry_run=False,
            skip_confirmation=True,
        )

        # Verify partial success
        assert result["success"] == 2
        assert result["failed"] == 1
        assert "PROJ-2" in result.get("errors", {})


@pytest.mark.bulk
@pytest.mark.unit
class TestBulkDeleteProgressCallback:
    """Test progress reporting."""

    def test_bulk_delete_progress_callback(self, mock_jira_client):
        """Test progress reporting during operation."""
        from bulk_delete import bulk_delete

        # Setup mock
        mock_jira_client.delete_issue.return_value = None

        # Track progress calls
        progress_calls = []

        def progress_callback(current, total, issue_key, status):
            progress_calls.append(
                {
                    "current": current,
                    "total": total,
                    "issue_key": issue_key,
                    "status": status,
                }
            )

        # Execute
        bulk_delete(
            client=mock_jira_client,
            issue_keys=["PROJ-1", "PROJ-2"],
            dry_run=False,
            progress_callback=progress_callback,
            skip_confirmation=True,
        )

        # Verify progress was reported
        assert len(progress_calls) == 2


@pytest.mark.bulk
@pytest.mark.unit
class TestBulkDeleteApiErrors:
    """Test API error handling scenarios."""

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 unauthorized error."""
        from bulk_delete import bulk_delete

        from jira_assistant_skills_lib import AuthenticationError

        mock_jira_client.delete_issue.side_effect = AuthenticationError("Invalid token")

        result = bulk_delete(
            client=mock_jira_client,
            issue_keys=["PROJ-1"],
            dry_run=False,
            skip_confirmation=True,
        )

        assert result["failed"] == 1
        assert result["success"] == 0
        assert "PROJ-1" in result.get("errors", {})

    def test_permission_denied_error(self, mock_jira_client):
        """Test handling of 403 forbidden error."""
        from bulk_delete import bulk_delete

        from jira_assistant_skills_lib import JiraError

        mock_jira_client.delete_issue.side_effect = JiraError(
            "You do not have permission to delete this issue", status_code=403
        )

        result = bulk_delete(
            client=mock_jira_client,
            issue_keys=["PROJ-1"],
            dry_run=False,
            skip_confirmation=True,
        )

        assert result["failed"] == 1
        assert result["success"] == 0
        assert "PROJ-1" in result.get("errors", {})

    def test_not_found_error(self, mock_jira_client):
        """Test handling of 404 not found error."""
        from bulk_delete import bulk_delete

        from jira_assistant_skills_lib import JiraError

        mock_jira_client.delete_issue.side_effect = JiraError(
            "Issue not found", status_code=404
        )

        result = bulk_delete(
            client=mock_jira_client,
            issue_keys=["PROJ-999"],
            dry_run=False,
            skip_confirmation=True,
        )

        assert result["failed"] == 1
        assert result["success"] == 0

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit error."""
        from bulk_delete import bulk_delete

        from jira_assistant_skills_lib import JiraError

        mock_jira_client.delete_issue.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        result = bulk_delete(
            client=mock_jira_client,
            issue_keys=["PROJ-1"],
            dry_run=False,
            skip_confirmation=True,
        )

        assert result["failed"] == 1
        assert result["success"] == 0

    def test_server_error(self, mock_jira_client):
        """Test handling of 500 internal server error."""
        from bulk_delete import bulk_delete

        from jira_assistant_skills_lib import JiraError

        mock_jira_client.delete_issue.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        result = bulk_delete(
            client=mock_jira_client,
            issue_keys=["PROJ-1"],
            dry_run=False,
            skip_confirmation=True,
        )

        assert result["failed"] == 1
        assert result["success"] == 0


@pytest.mark.bulk
@pytest.mark.unit
class TestBulkDeleteMaxIssues:
    """Test max issues limit."""

    def test_bulk_delete_respects_max_issues(self, mock_jira_client):
        """Test that max_issues limit is respected."""
        from bulk_delete import bulk_delete

        # Setup mock
        mock_jira_client.delete_issue.return_value = None

        # Execute with 5 issues but max 3
        result = bulk_delete(
            client=mock_jira_client,
            issue_keys=["PROJ-1", "PROJ-2", "PROJ-3", "PROJ-4", "PROJ-5"],
            max_issues=3,
            dry_run=False,
            skip_confirmation=True,
        )

        # Verify only 3 were processed
        assert result["success"] == 3
        assert mock_jira_client.delete_issue.call_count == 3


@pytest.mark.bulk
@pytest.mark.unit
class TestBulkDeleteEmptyList:
    """Test handling of empty issue list."""

    def test_bulk_delete_empty_jql_result(self, mock_jira_client):
        """Test handling when JQL returns no issues."""
        from bulk_delete import bulk_delete

        # Setup mock - no issues found
        mock_jira_client.search_issues.return_value = {
            "issues": [],
            "total": 0,
        }

        # Execute
        result = bulk_delete(
            client=mock_jira_client,
            jql="project=NONEXISTENT",
            dry_run=False,
            skip_confirmation=True,
        )

        # Verify no operations performed
        assert result["success"] == 0
        assert result["failed"] == 0
        assert result["total"] == 0
        mock_jira_client.delete_issue.assert_not_called()


@pytest.mark.bulk
@pytest.mark.unit
class TestBulkDeleteConfirmation:
    """Test confirmation behavior."""

    def test_bulk_delete_low_threshold(self, mock_jira_client):
        """Test that confirmation threshold is lower (10) for delete."""
        from bulk_delete import bulk_delete

        # Setup mock
        mock_jira_client.delete_issue.return_value = None

        # Execute with skip_confirmation=True to bypass
        result = bulk_delete(
            client=mock_jira_client,
            issue_keys=["PROJ-1", "PROJ-2"],
            dry_run=False,
            skip_confirmation=True,
            confirm_threshold=10,  # Default for delete
        )

        # Verify deletion happened
        assert result["success"] == 2
