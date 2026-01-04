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
from unittest.mock import Mock, patch


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
        from jira_assistant_skills_lib import JiraError

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
        from assistant_skills_lib.error_handler import ValidationError

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

    def test_cli_main_exists(self):
        """Test CLI main function exists and is callable."""
        from create_sprint import main
        assert callable(main)

    def test_cli_help_output(self, capsys):
        """Test that --help shows usage information."""
        with patch('sys.argv', ['create_sprint.py', '--help']):
            from create_sprint import main
            try:
                main()
            except SystemExit:
                pass  # --help causes SystemExit

        captured = capsys.readouterr()
        assert '--board' in captured.out or '--name' in captured.out or 'usage' in captured.out.lower()


@pytest.mark.agile
@pytest.mark.unit
class TestCreateSprintErrorHandling:
    """Test API error handling scenarios for create_sprint."""

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from jira_assistant_skills_lib import AuthenticationError
        from create_sprint import create_sprint

        mock_jira_client.create_sprint.side_effect = AuthenticationError(
            "Invalid API token"
        )

        with pytest.raises(AuthenticationError):
            create_sprint(
                board_id=123,
                name="Sprint 42",
                client=mock_jira_client
            )

    def test_forbidden_error(self, mock_jira_client):
        """Test handling of 403 forbidden."""
        from jira_assistant_skills_lib import PermissionError
        from create_sprint import create_sprint

        mock_jira_client.create_sprint.side_effect = PermissionError(
            "Insufficient permissions"
        )

        with pytest.raises(PermissionError):
            create_sprint(
                board_id=123,
                name="Sprint 42",
                client=mock_jira_client
            )

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from jira_assistant_skills_lib import JiraError
        from create_sprint import create_sprint

        mock_jira_client.create_sprint.side_effect = JiraError(
            "Rate limit exceeded",
            status_code=429
        )

        with pytest.raises(JiraError) as exc_info:
            create_sprint(
                board_id=123,
                name="Sprint 42",
                client=mock_jira_client
            )
        assert exc_info.value.status_code == 429

    def test_server_error(self, mock_jira_client):
        """Test handling of 500 server error."""
        from jira_assistant_skills_lib import JiraError
        from create_sprint import create_sprint

        mock_jira_client.create_sprint.side_effect = JiraError(
            "Internal server error",
            status_code=500
        )

        with pytest.raises(JiraError) as exc_info:
            create_sprint(
                board_id=123,
                name="Sprint 42",
                client=mock_jira_client
            )
        assert exc_info.value.status_code == 500
