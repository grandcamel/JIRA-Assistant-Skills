"""
Tests for create_sprint.py - Creating sprints in JIRA.

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
class TestCreateSprint:
    """Test suite for create_sprint.py functionality."""

    def test_create_sprint_minimal(self, mock_jira_client, sample_sprint_response):
        """Test creating sprint with board ID and name."""
        # Arrange
        from create_sprint import create_sprint

        mock_jira_client.create_sprint.return_value = sample_sprint_response

        # Act
        result = create_sprint(
            board_id=123,
            name="Sprint 42",
            client=mock_jira_client
        )

        # Assert
        assert result is not None
        assert result['id'] == 456
        assert result['name'] == "Sprint 42"

        # Verify API call
        mock_jira_client.create_sprint.assert_called_once()
        call_kwargs = mock_jira_client.create_sprint.call_args[1]
        assert call_kwargs['board_id'] == 123
        assert call_kwargs['name'] == "Sprint 42"

    def test_create_sprint_with_dates(self, mock_jira_client, sample_sprint_response):
        """Test setting start and end dates."""
        # Arrange
        from create_sprint import create_sprint

        mock_jira_client.create_sprint.return_value = sample_sprint_response

        # Act
        result = create_sprint(
            board_id=123,
            name="Sprint 42",
            start_date="2025-01-20",
            end_date="2025-02-03",
            client=mock_jira_client
        )

        # Assert
        assert result is not None

        # Verify dates were passed
        call_kwargs = mock_jira_client.create_sprint.call_args[1]
        assert call_kwargs.get('start_date') is not None
        assert call_kwargs.get('end_date') is not None
        assert '2025-01-20' in call_kwargs['start_date']
        assert '2025-02-03' in call_kwargs['end_date']

    def test_create_sprint_with_goal(self, mock_jira_client, sample_sprint_response):
        """Test setting sprint goal."""
        # Arrange
        from create_sprint import create_sprint

        mock_jira_client.create_sprint.return_value = sample_sprint_response

        # Act
        result = create_sprint(
            board_id=123,
            name="Sprint 42",
            goal="Launch MVP",
            client=mock_jira_client
        )

        # Assert
        assert result is not None

        # Verify goal was set
        call_kwargs = mock_jira_client.create_sprint.call_args[1]
        assert call_kwargs['goal'] == "Launch MVP"

    def test_create_sprint_invalid_board(self, mock_jira_client):
        """Test error when board doesn't exist."""
        # Arrange
        from create_sprint import create_sprint
        from error_handler import JiraError

        # Simulate 404 when board doesn't exist
        mock_jira_client.create_sprint.side_effect = JiraError(
            "Board does not exist",
            status_code=404
        )

        # Act & Assert
        with pytest.raises(JiraError) as exc_info:
            create_sprint(
                board_id=999,
                name="Sprint 42",
                client=mock_jira_client
            )

        assert exc_info.value.status_code == 404

    def test_create_sprint_invalid_dates(self, mock_jira_client):
        """Test validation of date ranges (end > start)."""
        # Arrange
        from create_sprint import create_sprint
        from error_handler import ValidationError

        # Act & Assert - end date before start date
        with pytest.raises(ValidationError) as exc_info:
            create_sprint(
                board_id=123,
                name="Sprint 42",
                start_date="2025-02-03",
                end_date="2025-01-20",  # End before start
                client=mock_jira_client
            )

        assert "date" in str(exc_info.value).lower()

    def test_create_sprint_date_format(self, mock_jira_client, sample_sprint_response):
        """Test various date input formats (ISO, relative)."""
        # Arrange
        from create_sprint import create_sprint

        mock_jira_client.create_sprint.return_value = sample_sprint_response

        # Act - test with ISO date format
        result = create_sprint(
            board_id=123,
            name="Sprint 42",
            start_date="2025-01-20T00:00:00.000Z",
            client=mock_jira_client
        )

        # Assert
        assert result is not None

        # Verify date was properly formatted for API
        call_kwargs = mock_jira_client.create_sprint.call_args[1]
        assert call_kwargs.get('start_date') is not None


@pytest.mark.agile
@pytest.mark.unit
class TestCreateSprintCLI:
    """Test command-line interface for create_sprint.py."""

    @patch('sys.argv', ['create_sprint.py', '--board', '123', '--name', 'Sprint 42'])
    def test_cli_minimal_args(self, mock_jira_client, sample_sprint_response):
        """Test CLI with minimal required arguments."""
        mock_jira_client.create_sprint.return_value = sample_sprint_response
        # from create_sprint import main
        pass

    @patch('sys.argv', ['create_sprint.py', '--board', '123', '--name', 'Sprint 42', '--goal', 'Launch'])
    def test_cli_with_goal(self, mock_jira_client, sample_sprint_response):
        """Test CLI with sprint goal."""
        mock_jira_client.create_sprint.return_value = sample_sprint_response
        # from create_sprint import main
        pass
