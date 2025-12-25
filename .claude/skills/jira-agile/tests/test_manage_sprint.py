"""
Tests for manage_sprint.py - Managing sprint lifecycle in JIRA.

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
class TestManageSprint:
    """Test suite for manage_sprint.py functionality."""

    def test_start_sprint(self, mock_jira_client, sample_sprint_response):
        """Test starting a sprint (moves from future to active)."""
        # Arrange
        from manage_sprint import start_sprint

        # Sprint starts as 'future', becomes 'active'
        started_sprint = sample_sprint_response.copy()
        started_sprint['state'] = 'active'
        mock_jira_client.update_sprint.return_value = started_sprint

        # Act
        result = start_sprint(
            sprint_id=456,
            client=mock_jira_client
        )

        # Assert
        assert result is not None
        assert result['state'] == 'active'

        # Verify API call
        mock_jira_client.update_sprint.assert_called_once()
        call_args = mock_jira_client.update_sprint.call_args
        assert call_args[0][0] == 456  # Sprint ID
        assert call_args[0][1]['state'] == 'active'

    def test_close_sprint(self, mock_jira_client, sample_sprint_response):
        """Test closing active sprint."""
        # Arrange
        from manage_sprint import close_sprint

        # Sprint becomes 'closed'
        closed_sprint = sample_sprint_response.copy()
        closed_sprint['state'] = 'closed'
        mock_jira_client.update_sprint.return_value = closed_sprint

        # Act
        result = close_sprint(
            sprint_id=456,
            client=mock_jira_client
        )

        # Assert
        assert result is not None
        assert result['state'] == 'closed'

        # Verify API call
        mock_jira_client.update_sprint.assert_called_once()
        call_args = mock_jira_client.update_sprint.call_args
        assert call_args[0][1]['state'] == 'closed'

    def test_close_sprint_with_incomplete_issues(self, mock_jira_client, sample_sprint_response):
        """Test moving incomplete issues to next sprint."""
        # Arrange
        from manage_sprint import close_sprint

        closed_sprint = sample_sprint_response.copy()
        closed_sprint['state'] = 'closed'
        mock_jira_client.update_sprint.return_value = closed_sprint
        mock_jira_client.move_issues_to_sprint.return_value = {'movedIssues': 3}

        # Act
        result = close_sprint(
            sprint_id=456,
            move_incomplete_to=457,
            client=mock_jira_client
        )

        # Assert
        assert result is not None
        assert result['state'] == 'closed'
        assert 'moved_issues' in result
        assert result['moved_issues'] == 3

    def test_update_sprint_dates(self, mock_jira_client, sample_sprint_response):
        """Test extending sprint end date."""
        # Arrange
        from manage_sprint import update_sprint

        updated_sprint = sample_sprint_response.copy()
        updated_sprint['endDate'] = '2025-02-10T00:00:00.000Z'
        mock_jira_client.update_sprint.return_value = updated_sprint

        # Act
        result = update_sprint(
            sprint_id=456,
            end_date='2025-02-10',
            client=mock_jira_client
        )

        # Assert
        assert result is not None
        assert '2025-02-10' in result['endDate']

    def test_update_sprint_goal(self, mock_jira_client, sample_sprint_response):
        """Test changing sprint goal mid-sprint."""
        # Arrange
        from manage_sprint import update_sprint

        updated_sprint = sample_sprint_response.copy()
        updated_sprint['goal'] = 'Updated goal: Ship v2.0'
        mock_jira_client.update_sprint.return_value = updated_sprint

        # Act
        result = update_sprint(
            sprint_id=456,
            goal='Updated goal: Ship v2.0',
            client=mock_jira_client
        )

        # Assert
        assert result is not None
        assert result['goal'] == 'Updated goal: Ship v2.0'

    def test_get_active_sprint(self, mock_jira_client, sample_sprint_response):
        """Test fetching current active sprint for board."""
        # Arrange
        from manage_sprint import get_active_sprint

        mock_jira_client.get_board_sprints.return_value = {
            'values': [sample_sprint_response],
            'isLast': True
        }

        # Act
        result = get_active_sprint(
            board_id=123,
            client=mock_jira_client
        )

        # Assert
        assert result is not None
        assert result['state'] == 'active'
        assert result['id'] == 456

        # Verify API call with state filter
        mock_jira_client.get_board_sprints.assert_called_once()


@pytest.mark.agile
@pytest.mark.unit
class TestManageSprintCLI:
    """Test command-line interface for manage_sprint.py."""

    @patch('sys.argv', ['manage_sprint.py', '--sprint', '456', '--start'])
    def test_cli_start_sprint(self, mock_jira_client, sample_sprint_response):
        """Test CLI to start a sprint."""
        # from manage_sprint import main
        pass

    @patch('sys.argv', ['manage_sprint.py', '--sprint', '456', '--close'])
    def test_cli_close_sprint(self, mock_jira_client, sample_sprint_response):
        """Test CLI to close a sprint."""
        # from manage_sprint import main
        pass
