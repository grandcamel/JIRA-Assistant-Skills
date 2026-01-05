"""
Tests for rank_issue.py - Ranking issues in JIRA backlog.

Following TDD: These tests are written FIRST and should FAIL initially.
Implementation comes after tests are defined.
"""

import sys
from pathlib import Path

# Add paths BEFORE any other imports
test_dir = Path(__file__).parent  # tests
jira_agile_dir = test_dir.parent  # jira-agile
skills_dir = jira_agile_dir.parent  # skills
shared_lib_path = skills_dir / "shared" / "scripts" / "lib"
scripts_path = jira_agile_dir / "scripts"

sys.path.insert(0, str(shared_lib_path))
sys.path.insert(0, str(scripts_path))

from unittest.mock import patch

import pytest


@pytest.mark.agile
@pytest.mark.unit
class TestRankIssue:
    """Test suite for rank_issue.py functionality."""

    def test_rank_issue_before(self, mock_jira_client):
        """Test ranking issue before another issue."""
        # Arrange
        from rank_issue import rank_issue

        mock_jira_client.rank_issues.return_value = None

        # Act
        result = rank_issue(
            issue_keys=["PROJ-1"], before_key="PROJ-2", client=mock_jira_client
        )

        # Assert
        assert result is not None
        assert result["ranked"] == 1

        # Verify API call
        mock_jira_client.rank_issues.assert_called_once()
        call_args = mock_jira_client.rank_issues.call_args
        assert "PROJ-1" in call_args[0][0]  # Issues to rank (positional)
        assert call_args[1]["rank_before"] == "PROJ-2"  # Before key (kwargs)

    def test_rank_issue_after(self, mock_jira_client):
        """Test ranking issue after another issue."""
        # Arrange
        from rank_issue import rank_issue

        mock_jira_client.rank_issues.return_value = None

        # Act
        result = rank_issue(
            issue_keys=["PROJ-1"], after_key="PROJ-3", client=mock_jira_client
        )

        # Assert
        assert result is not None
        assert result["ranked"] == 1

        # Verify after positioning - check both possible parameter names
        call_args = mock_jira_client.rank_issues.call_args
        assert (
            call_args[1].get("rank_after") == "PROJ-3"
            or call_args[1].get("after") == "PROJ-3"
        )

    def test_rank_issue_top(self, mock_jira_client):
        """Test moving issue to top of backlog - requires board context."""
        # Arrange
        from assistant_skills_lib.error_handler import ValidationError
        from rank_issue import rank_issue

        mock_jira_client.rank_issues.return_value = None

        # Act & Assert - top ranking requires board context
        with pytest.raises(
            ValidationError, match="Top/bottom ranking requires implementation"
        ):
            rank_issue(issue_keys=["PROJ-1"], position="top", client=mock_jira_client)

    def test_rank_issue_bottom(self, mock_jira_client):
        """Test moving issue to bottom of backlog - requires board context."""
        # Arrange
        from assistant_skills_lib.error_handler import ValidationError
        from rank_issue import rank_issue

        mock_jira_client.rank_issues.return_value = None

        # Act & Assert - bottom ranking requires board context
        with pytest.raises(
            ValidationError, match="Top/bottom ranking requires implementation"
        ):
            rank_issue(
                issue_keys=["PROJ-1"], position="bottom", client=mock_jira_client
            )

    def test_rank_multiple_issues(self, mock_jira_client):
        """Test bulk ranking."""
        # Arrange
        from rank_issue import rank_issue

        mock_jira_client.rank_issues.return_value = None

        # Act
        result = rank_issue(
            issue_keys=["PROJ-1", "PROJ-2", "PROJ-3"],
            before_key="PROJ-10",
            client=mock_jira_client,
        )

        # Assert
        assert result is not None
        assert result["ranked"] == 3

    def test_rank_issue_invalid_position(self, mock_jira_client):
        """Test validation of rank position."""
        # Arrange
        from assistant_skills_lib.error_handler import ValidationError
        from rank_issue import rank_issue

        # Act & Assert - no position specified
        with pytest.raises(ValidationError) as exc_info:
            rank_issue(issue_keys=["PROJ-1"], client=mock_jira_client)

        assert (
            "position" in str(exc_info.value).lower()
            or "before" in str(exc_info.value).lower()
        )

    @pytest.mark.xfail(reason="dry_run parameter not yet implemented in rank_issue")
    def test_rank_dry_run(self, mock_jira_client):
        """Test dry-run mode for ranking."""
        from rank_issue import rank_issue

        result = rank_issue(
            issue_keys=["PROJ-1"],
            before_key="PROJ-2",
            dry_run=True,
            client=mock_jira_client,
        )

        # Verify dry-run response
        assert result.get("dry_run") is True or result.get("would_rank") == 1
        # Verify NO actual ranking was called
        mock_jira_client.rank_issues.assert_not_called()


@pytest.mark.agile
@pytest.mark.unit
class TestRankIssueCLI:
    """Test command-line interface for rank_issue.py."""

    def test_cli_main_exists(self):
        """Test CLI main function exists and is callable."""
        from rank_issue import main

        assert callable(main)

    def test_cli_help_output(self, capsys):
        """Test that --help shows usage information."""
        with patch("sys.argv", ["rank_issue.py", "--help"]):
            from rank_issue import main

            try:
                main()
            except SystemExit:
                pass  # --help causes SystemExit

        captured = capsys.readouterr()
        assert "--before" in captured.out or "usage" in captured.out.lower()


@pytest.mark.agile
@pytest.mark.unit
class TestRankIssueErrorHandling:
    """Test API error handling scenarios for rank_issue."""

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from rank_issue import rank_issue

        from jira_assistant_skills_lib import AuthenticationError

        mock_jira_client.rank_issues.side_effect = AuthenticationError(
            "Invalid API token"
        )

        with pytest.raises(AuthenticationError):
            rank_issue(
                issue_keys=["PROJ-1"], before_key="PROJ-2", client=mock_jira_client
            )

    def test_forbidden_error(self, mock_jira_client):
        """Test handling of 403 forbidden."""
        from rank_issue import rank_issue

        from jira_assistant_skills_lib import PermissionError

        mock_jira_client.rank_issues.side_effect = PermissionError(
            "Insufficient permissions"
        )

        with pytest.raises(PermissionError):
            rank_issue(
                issue_keys=["PROJ-1"], before_key="PROJ-2", client=mock_jira_client
            )

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from rank_issue import rank_issue

        from jira_assistant_skills_lib import JiraError

        mock_jira_client.rank_issues.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        with pytest.raises(JiraError) as exc_info:
            rank_issue(
                issue_keys=["PROJ-1"], before_key="PROJ-2", client=mock_jira_client
            )
        assert exc_info.value.status_code == 429

    def test_server_error(self, mock_jira_client):
        """Test handling of 500 server error."""
        from rank_issue import rank_issue

        from jira_assistant_skills_lib import JiraError

        mock_jira_client.rank_issues.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        with pytest.raises(JiraError) as exc_info:
            rank_issue(
                issue_keys=["PROJ-1"], before_key="PROJ-2", client=mock_jira_client
            )
        assert exc_info.value.status_code == 500

    def test_issue_not_found(self, mock_jira_client):
        """Test error when issue doesn't exist."""
        from rank_issue import rank_issue

        from jira_assistant_skills_lib import JiraError

        mock_jira_client.rank_issues.side_effect = JiraError(
            "Issue does not exist", status_code=404
        )

        with pytest.raises(JiraError) as exc_info:
            rank_issue(
                issue_keys=["PROJ-999"], before_key="PROJ-2", client=mock_jira_client
            )
        assert exc_info.value.status_code == 404
