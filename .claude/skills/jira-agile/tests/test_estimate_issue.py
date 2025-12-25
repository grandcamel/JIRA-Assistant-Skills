"""
Tests for estimate_issue.py - Setting story points on issues.

Following TDD: These tests are written FIRST and should FAIL initially.
"""

import sys
from pathlib import Path

test_dir = Path(__file__).parent
jira_agile_dir = test_dir.parent
skills_dir = jira_agile_dir.parent
shared_lib_path = skills_dir / 'shared' / 'scripts' / 'lib'
scripts_path = jira_agile_dir / 'scripts'

sys.path.insert(0, str(shared_lib_path))
sys.path.insert(0, str(scripts_path))

import pytest
from unittest.mock import Mock, patch


@pytest.mark.agile
@pytest.mark.unit
class TestEstimateIssue:
    """Test suite for estimate_issue.py functionality."""

    def test_set_story_points_single(self, mock_jira_client):
        """Test setting story points on one issue."""
        from estimate_issue import estimate_issue

        mock_jira_client.update_issue.return_value = None

        result = estimate_issue(
            issue_keys=["PROJ-1"],
            points=5,
            client=mock_jira_client
        )

        assert result is not None
        assert result['updated'] == 1
        mock_jira_client.update_issue.assert_called_once()

    def test_set_story_points_multiple(self, mock_jira_client):
        """Test bulk setting story points."""
        from estimate_issue import estimate_issue

        mock_jira_client.update_issue.return_value = None

        result = estimate_issue(
            issue_keys=["PROJ-1", "PROJ-2", "PROJ-3"],
            points=3,
            client=mock_jira_client
        )

        assert result is not None
        assert result['updated'] == 3
        assert mock_jira_client.update_issue.call_count == 3

    def test_set_story_points_fibonacci(self, mock_jira_client):
        """Test validation of Fibonacci sequence (1,2,3,5,8,13...)."""
        from estimate_issue import estimate_issue
        from error_handler import ValidationError

        # Valid Fibonacci values should work
        for points in [1, 2, 3, 5, 8, 13, 21]:
            mock_jira_client.reset_mock()
            mock_jira_client.update_issue.return_value = None
            result = estimate_issue(
                issue_keys=["PROJ-1"],
                points=points,
                validate_fibonacci=True,
                client=mock_jira_client
            )
            assert result['updated'] == 1

        # Invalid values should raise ValidationError when validation enabled
        with pytest.raises(ValidationError) as exc_info:
            estimate_issue(
                issue_keys=["PROJ-1"],
                points=4,  # Not in Fibonacci sequence
                validate_fibonacci=True,
                client=mock_jira_client
            )
        assert "fibonacci" in str(exc_info.value).lower()

    def test_set_story_points_custom_scale(self, mock_jira_client):
        """Test custom point scale (e.g., t-shirt sizes or custom values)."""
        from estimate_issue import estimate_issue

        mock_jira_client.update_issue.return_value = None

        # Custom scale allows any numeric value
        result = estimate_issue(
            issue_keys=["PROJ-1"],
            points=7,  # Not Fibonacci but valid for custom scale
            validate_fibonacci=False,
            client=mock_jira_client
        )

        assert result is not None
        assert result['updated'] == 1

    def test_clear_story_points(self, mock_jira_client):
        """Test removing story point estimate."""
        from estimate_issue import estimate_issue

        mock_jira_client.update_issue.return_value = None

        result = estimate_issue(
            issue_keys=["PROJ-1"],
            points=0,  # Zero clears the estimate
            client=mock_jira_client
        )

        assert result is not None
        assert result['updated'] == 1
        # Should call update with null/empty story points
        call_args = mock_jira_client.update_issue.call_args
        assert call_args is not None

    def test_estimate_by_jql(self, mock_jira_client):
        """Test bulk estimating from JQL query."""
        from estimate_issue import estimate_issue

        # Mock search returning issues
        mock_jira_client.search_issues.return_value = {
            'issues': [
                {'key': 'PROJ-1'},
                {'key': 'PROJ-2'},
                {'key': 'PROJ-3'}
            ]
        }
        mock_jira_client.update_issue.return_value = None

        result = estimate_issue(
            jql="sprint=456 AND type=Story",
            points=2,
            client=mock_jira_client
        )

        assert result is not None
        assert result['updated'] == 3
        mock_jira_client.search_issues.assert_called_once()


@pytest.mark.agile
@pytest.mark.unit
class TestEstimateIssueCLI:
    """Test command-line interface for estimate_issue.py."""

    def test_cli_single_issue(self, mock_jira_client):
        """Test CLI with single issue."""
        pass

    def test_cli_jql_query(self, mock_jira_client):
        """Test CLI with JQL query."""
        pass
