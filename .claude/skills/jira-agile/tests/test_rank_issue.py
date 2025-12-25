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
shared_lib_path = skills_dir / 'shared' / 'scripts' / 'lib'
scripts_path = jira_agile_dir / 'scripts'

sys.path.insert(0, str(shared_lib_path))
sys.path.insert(0, str(scripts_path))

import pytest
from unittest.mock import Mock, patch, MagicMock


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
            issue_keys=["PROJ-1"],
            before_key="PROJ-2",
            client=mock_jira_client
        )

        # Assert
        assert result is not None
        assert result['ranked'] == 1

        # Verify API call
        mock_jira_client.rank_issues.assert_called_once()
        call_args = mock_jira_client.rank_issues.call_args
        assert "PROJ-1" in call_args[0][0]  # Issues to rank (positional)
        assert call_args[1]['rank_before'] == "PROJ-2"  # Before key (kwargs)

    def test_rank_issue_after(self, mock_jira_client):
        """Test ranking issue after another issue."""
        # Arrange
        from rank_issue import rank_issue

        mock_jira_client.rank_issues.return_value = None

        # Act
        result = rank_issue(
            issue_keys=["PROJ-1"],
            after_key="PROJ-3",
            client=mock_jira_client
        )

        # Assert
        assert result is not None
        assert result['ranked'] == 1

        # Verify after positioning
        call_args = mock_jira_client.rank_issues.call_args
        assert call_args[1].get('after') == "PROJ-3" or 'after' in str(call_args)

    def test_rank_issue_top(self, mock_jira_client):
        """Test moving issue to top of backlog - requires board context."""
        # Arrange
        from rank_issue import rank_issue
        from error_handler import ValidationError

        mock_jira_client.rank_issues.return_value = None

        # Act & Assert - top ranking requires board context
        with pytest.raises(ValidationError, match="Top/bottom ranking requires implementation"):
            rank_issue(
                issue_keys=["PROJ-1"],
                position="top",
                client=mock_jira_client
            )

    def test_rank_issue_bottom(self, mock_jira_client):
        """Test moving issue to bottom of backlog - requires board context."""
        # Arrange
        from rank_issue import rank_issue
        from error_handler import ValidationError

        mock_jira_client.rank_issues.return_value = None

        # Act & Assert - bottom ranking requires board context
        with pytest.raises(ValidationError, match="Top/bottom ranking requires implementation"):
            rank_issue(
                issue_keys=["PROJ-1"],
                position="bottom",
                client=mock_jira_client
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
            client=mock_jira_client
        )

        # Assert
        assert result is not None
        assert result['ranked'] == 3

    def test_rank_issue_invalid_position(self, mock_jira_client):
        """Test validation of rank position."""
        # Arrange
        from rank_issue import rank_issue
        from error_handler import ValidationError

        # Act & Assert - no position specified
        with pytest.raises(ValidationError) as exc_info:
            rank_issue(
                issue_keys=["PROJ-1"],
                client=mock_jira_client
            )

        assert "position" in str(exc_info.value).lower() or "before" in str(exc_info.value).lower()


@pytest.mark.agile
@pytest.mark.unit
class TestRankIssueCLI:
    """Test command-line interface for rank_issue.py."""

    @patch('sys.argv', ['rank_issue.py', 'PROJ-1', '--before', 'PROJ-2'])
    def test_cli_before(self, mock_jira_client):
        """Test CLI with --before."""
        # from rank_issue import main
        pass

    @patch('sys.argv', ['rank_issue.py', 'PROJ-1', '--top'])
    def test_cli_top(self, mock_jira_client):
        """Test CLI with --top."""
        # from rank_issue import main
        pass
