"""
Tests for move_issues_version.py - Move issues between versions.
"""

import copy
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add script path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


@pytest.mark.lifecycle
@pytest.mark.unit
class TestMoveIssuesVersion:
    """Tests for moving issues between versions."""

    @patch("move_issues_version.get_jira_client")
    def test_move_issues_by_jql(
        self, mock_get_client, mock_jira_client, sample_issue_list
    ):
        """Test moving issues found by JQL to a version."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.search_issues.return_value = sample_issue_list
        mock_jira_client.update_issue.return_value = None

        from move_issues_version import move_issues_to_version

        result = move_issues_to_version(
            jql='fixVersion = "v1.0.0"', target_version="v2.0.0", profile=None
        )

        # Should have updated both issues
        assert result["moved"] == 2
        assert mock_jira_client.update_issue.call_count == 2

    @patch("move_issues_version.get_jira_client")
    def test_move_issues_by_version_name(
        self, mock_get_client, mock_jira_client, sample_issue_list
    ):
        """Test moving issues from one version to another."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.search_issues.return_value = sample_issue_list
        mock_jira_client.update_issue.return_value = None

        from move_issues_version import move_issues_between_versions

        result = move_issues_between_versions(
            project="PROJ",
            source_version="v1.0.0",
            target_version="v1.2.0",
            profile=None,
        )

        # Should have moved the issues found by JQL
        assert result["moved"] == 2
        assert mock_jira_client.update_issue.call_count == 2

    @patch("move_issues_version.get_jira_client")
    def test_move_specific_issues(self, mock_get_client, mock_jira_client):
        """Test moving specific issues by key."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.update_issue.return_value = None

        from move_issues_version import move_specific_issues

        result = move_specific_issues(
            issue_keys=["PROJ-1", "PROJ-2"], target_version="v2.0.0", profile=None
        )

        assert result["moved"] == 2
        assert mock_jira_client.update_issue.call_count == 2

    @patch("move_issues_version.get_jira_client")
    def test_move_issues_field_type(self, mock_get_client, mock_jira_client):
        """Test moving issues with different version field types (fixVersions vs versions)."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.update_issue.return_value = None

        from move_issues_version import move_specific_issues

        # Test with fixVersions field
        result = move_specific_issues(
            issue_keys=["PROJ-1"],
            target_version="v2.0.0",
            field="fixVersions",
            profile=None,
        )

        assert result["moved"] == 1
        call_args = mock_jira_client.update_issue.call_args
        assert "fixVersions" in call_args[1]["fields"]

    @patch("move_issues_version.get_jira_client")
    def test_move_issues_dry_run(
        self, mock_get_client, mock_jira_client, sample_issue_list
    ):
        """Test dry-run mode shows what would be moved."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.search_issues.return_value = sample_issue_list

        from move_issues_version import move_issues_dry_run

        result = move_issues_dry_run(
            jql="project = PROJ", target_version="v2.0.0", profile=None
        )

        # Should return issue count without updating
        assert result["would_move"] == 2
        assert "issues" in result
        mock_jira_client.update_issue.assert_not_called()

    @patch("move_issues_version.get_jira_client")
    def test_move_issues_with_confirmation(
        self, mock_get_client, mock_jira_client, sample_issue_list, monkeypatch
    ):
        """Test confirmation prompt before moving."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.search_issues.return_value = sample_issue_list
        mock_jira_client.update_issue.return_value = None

        # Simulate user confirming with 'yes'
        monkeypatch.setattr("builtins.input", lambda _: "yes")

        from move_issues_version import move_issues_with_confirmation

        result = move_issues_with_confirmation(
            jql="project = PROJ", target_version="v2.0.0", profile=None
        )

        # Should have moved issues after confirmation
        assert result["moved"] == 2


@pytest.mark.lifecycle
@pytest.mark.unit
class TestMoveIssuesVersionErrorHandling:
    """Test API error handling for move_issues_version."""

    @patch("move_issues_version.get_jira_client")
    def test_authentication_error(self, mock_get_client, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from jira_assistant_skills_lib import AuthenticationError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.search_issues.side_effect = AuthenticationError(
            "Invalid token"
        )

        from move_issues_version import move_issues_to_version

        with pytest.raises(AuthenticationError):
            move_issues_to_version(
                jql="project = PROJ", target_version="v2.0.0", profile=None
            )

    @patch("move_issues_version.get_jira_client")
    def test_permission_error(
        self, mock_get_client, mock_jira_client, sample_issue_list
    ):
        """Test handling of 403 forbidden during bulk update."""
        from jira_assistant_skills_lib import PermissionError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.search_issues.return_value = copy.deepcopy(sample_issue_list)
        mock_jira_client.update_issue.side_effect = PermissionError(
            "Cannot update issue"
        )

        from move_issues_version import move_issues_to_version

        # Bulk operations capture errors per-issue rather than raising
        result = move_issues_to_version(
            jql="project = PROJ",
            target_version="v2.0.0",
            profile=None,
            show_progress=False,
        )

        assert result["moved"] == 0
        assert result["failed"] == 2
        assert "PROJ-123" in result["errors"]
        assert "PROJ-124" in result["errors"]
        assert "Cannot update issue" in result["errors"]["PROJ-123"]

    @patch("move_issues_version.get_jira_client")
    def test_not_found_error(self, mock_get_client, mock_jira_client):
        """Test handling of 404 when issues not found."""
        from jira_assistant_skills_lib import NotFoundError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.search_issues.side_effect = NotFoundError("Issue", "PROJ-999")

        from move_issues_version import move_issues_to_version

        with pytest.raises(NotFoundError):
            move_issues_to_version(
                jql="issue = PROJ-999", target_version="v2.0.0", profile=None
            )

    @patch("move_issues_version.get_jira_client")
    def test_rate_limit_error(self, mock_get_client, mock_jira_client):
        """Test handling of 429 rate limit."""
        from jira_assistant_skills_lib import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.search_issues.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        from move_issues_version import move_issues_to_version

        with pytest.raises(JiraError) as exc_info:
            move_issues_to_version(
                jql="project = PROJ", target_version="v2.0.0", profile=None
            )
        assert exc_info.value.status_code == 429

    @patch("move_issues_version.get_jira_client")
    def test_server_error(self, mock_get_client, mock_jira_client):
        """Test handling of 500 server error."""
        from jira_assistant_skills_lib import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.search_issues.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        from move_issues_version import move_issues_to_version

        with pytest.raises(JiraError) as exc_info:
            move_issues_to_version(
                jql="project = PROJ", target_version="v2.0.0", profile=None
            )
        assert exc_info.value.status_code == 500
