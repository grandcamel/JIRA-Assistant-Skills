"""
Tests for get_estimates.py - Story point estimation summaries.

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
import copy

STORY_POINTS_FIELD = 'customfield_10016'


@pytest.mark.agile
@pytest.mark.unit
class TestGetEstimates:
    """Test suite for get_estimates.py functionality."""

    def test_get_estimates_for_sprint(self, mock_jira_client):
        """Test summing story points in sprint."""
        from get_estimates import get_estimates

        mock_jira_client.get_sprint_issues.return_value = {
            'issues': [
                {'key': 'PROJ-1', 'fields': {STORY_POINTS_FIELD: 5, 'status': {'name': 'Done'}}},
                {'key': 'PROJ-2', 'fields': {STORY_POINTS_FIELD: 8, 'status': {'name': 'In Progress'}}},
                {'key': 'PROJ-3', 'fields': {STORY_POINTS_FIELD: 3, 'status': {'name': 'To Do'}}},
            ]
        }

        result = get_estimates(
            sprint_id=456,
            client=mock_jira_client
        )

        assert result is not None
        assert result['total_points'] == 16
        assert 'by_status' in result or 'issues' in result

    def test_get_estimates_for_epic(self, mock_jira_client):
        """Test summing story points in epic."""
        from get_estimates import get_estimates

        mock_jira_client.search_issues.return_value = {
            'issues': [
                {'key': 'PROJ-1', 'fields': {STORY_POINTS_FIELD: 5, 'status': {'name': 'Done'}}},
                {'key': 'PROJ-2', 'fields': {STORY_POINTS_FIELD: 13, 'status': {'name': 'Done'}}},
                {'key': 'PROJ-3', 'fields': {STORY_POINTS_FIELD: 8, 'status': {'name': 'To Do'}}},
            ]
        }

        result = get_estimates(
            epic_key="PROJ-100",
            client=mock_jira_client
        )

        assert result is not None
        assert result['total_points'] == 26

    def test_get_estimates_by_assignee(self, mock_jira_client):
        """Test grouping estimates by assignee."""
        from get_estimates import get_estimates

        mock_jira_client.get_sprint_issues.return_value = {
            'issues': [
                {'key': 'PROJ-1', 'fields': {
                    STORY_POINTS_FIELD: 5,
                    'status': {'name': 'Done'},
                    'assignee': {'displayName': 'Alice', 'accountId': 'alice123'}
                }},
                {'key': 'PROJ-2', 'fields': {
                    STORY_POINTS_FIELD: 8,
                    'status': {'name': 'In Progress'},
                    'assignee': {'displayName': 'Bob', 'accountId': 'bob456'}
                }},
                {'key': 'PROJ-3', 'fields': {
                    STORY_POINTS_FIELD: 3,
                    'status': {'name': 'To Do'},
                    'assignee': {'displayName': 'Alice', 'accountId': 'alice123'}
                }},
            ]
        }

        result = get_estimates(
            sprint_id=456,
            group_by='assignee',
            client=mock_jira_client
        )

        assert result is not None
        assert 'by_assignee' in result
        # Alice: 5 + 3 = 8, Bob: 8
        assert result['by_assignee']['Alice'] == 8
        assert result['by_assignee']['Bob'] == 8

    def test_get_estimates_by_status(self, mock_jira_client):
        """Test grouping estimates by status (done vs todo)."""
        from get_estimates import get_estimates

        mock_jira_client.get_sprint_issues.return_value = {
            'issues': [
                {'key': 'PROJ-1', 'fields': {STORY_POINTS_FIELD: 5, 'status': {'name': 'Done'}}},
                {'key': 'PROJ-2', 'fields': {STORY_POINTS_FIELD: 8, 'status': {'name': 'In Progress'}}},
                {'key': 'PROJ-3', 'fields': {STORY_POINTS_FIELD: 3, 'status': {'name': 'To Do'}}},
                {'key': 'PROJ-4', 'fields': {STORY_POINTS_FIELD: 2, 'status': {'name': 'Done'}}},
            ]
        }

        result = get_estimates(
            sprint_id=456,
            group_by='status',
            client=mock_jira_client
        )

        assert result is not None
        assert 'by_status' in result
        # Done: 5 + 2 = 7
        assert result['by_status']['Done'] == 7
        # In Progress: 8
        assert result['by_status']['In Progress'] == 8
        # To Do: 3
        assert result['by_status']['To Do'] == 3


@pytest.mark.agile
@pytest.mark.unit
class TestGetEstimatesCLI:
    """Test command-line interface for get_estimates.py."""

    def test_cli_main_exists(self):
        """Test CLI main function exists and is callable."""
        from get_estimates import main
        assert callable(main)

    def test_cli_help_output(self, capsys):
        """Test that --help shows usage information."""
        with patch('sys.argv', ['get_estimates.py', '--help']):
            from get_estimates import main
            try:
                main()
            except SystemExit:
                pass  # --help causes SystemExit

        captured = capsys.readouterr()
        assert '--sprint' in captured.out or '--epic' in captured.out or 'usage' in captured.out.lower()


@pytest.mark.agile
@pytest.mark.unit
class TestGetEstimatesErrorHandling:
    """Test API error handling scenarios for get_estimates."""

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from jira_assistant_skills_lib import AuthenticationError
        from get_estimates import get_estimates

        mock_jira_client.get_sprint_issues.side_effect = AuthenticationError(
            "Invalid API token"
        )

        with pytest.raises(AuthenticationError):
            get_estimates(
                sprint_id=456,
                client=mock_jira_client
            )

    def test_forbidden_error(self, mock_jira_client):
        """Test handling of 403 forbidden."""
        from jira_assistant_skills_lib import PermissionError
        from get_estimates import get_estimates

        mock_jira_client.get_sprint_issues.side_effect = PermissionError(
            "Insufficient permissions"
        )

        with pytest.raises(PermissionError):
            get_estimates(
                sprint_id=456,
                client=mock_jira_client
            )

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from jira_assistant_skills_lib import JiraError
        from get_estimates import get_estimates

        mock_jira_client.get_sprint_issues.side_effect = JiraError(
            "Rate limit exceeded",
            status_code=429
        )

        with pytest.raises(JiraError) as exc_info:
            get_estimates(
                sprint_id=456,
                client=mock_jira_client
            )
        assert exc_info.value.status_code == 429

    def test_server_error(self, mock_jira_client):
        """Test handling of 500 server error."""
        from jira_assistant_skills_lib import JiraError
        from get_estimates import get_estimates

        mock_jira_client.get_sprint_issues.side_effect = JiraError(
            "Internal server error",
            status_code=500
        )

        with pytest.raises(JiraError) as exc_info:
            get_estimates(
                sprint_id=456,
                client=mock_jira_client
            )
        assert exc_info.value.status_code == 500

    def test_sprint_not_found(self, mock_jira_client):
        """Test error when sprint doesn't exist."""
        from jira_assistant_skills_lib import JiraError
        from get_estimates import get_estimates

        mock_jira_client.get_sprint_issues.side_effect = JiraError(
            "Sprint does not exist",
            status_code=404
        )

        with pytest.raises(JiraError) as exc_info:
            get_estimates(
                sprint_id=999,
                client=mock_jira_client
            )
        assert exc_info.value.status_code == 404
