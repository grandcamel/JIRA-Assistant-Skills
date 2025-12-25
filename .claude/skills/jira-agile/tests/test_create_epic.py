"""
Tests for create_epic.py - Creating epic issues in JIRA.

Following TDD: These tests are written FIRST and should FAIL initially.
Implementation comes after tests are defined.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add scripts to path for importing
scripts_path = Path(__file__).parent.parent / 'scripts'
sys.path.insert(0, str(scripts_path))


@pytest.mark.agile
@pytest.mark.unit
class TestCreateEpic:
    """Test suite for create_epic.py functionality."""

    def test_create_epic_minimal(self, mock_jira_client, sample_epic_response):
        """Test creating epic with only required fields (project, summary)."""
        # Arrange
        mock_jira_client.create_issue.return_value = sample_epic_response

        # Import will fail initially - that's expected for TDD
        from create_epic import create_epic

        # Act
        result = create_epic(
            project="PROJ",
            summary="Mobile App MVP",
            profile=None
        )

        # Assert
        assert result is not None
        assert result['key'] == "PROJ-100"

        # Verify API call
        mock_jira_client.create_issue.assert_called_once()
        call_args = mock_jira_client.create_issue.call_args[0][0]
        assert call_args['project'] == {'key': 'PROJ'}
        assert call_args['issuetype'] == {'name': 'Epic'}
        assert call_args['summary'] == "Mobile App MVP"

    def test_create_epic_with_description(self, mock_jira_client, sample_epic_response):
        """Test creating epic with markdown description."""
        # Arrange
        mock_jira_client.create_issue.return_value = sample_epic_response
        from create_epic import create_epic

        # Act
        result = create_epic(
            project="PROJ",
            summary="Mobile App MVP",
            description="## Overview\nBuild mobile app with **React Native**",
            profile=None
        )

        # Assert
        assert result is not None

        # Verify description was converted to ADF
        call_args = mock_jira_client.create_issue.call_args[0][0]
        assert 'description' in call_args
        assert call_args['description']['type'] == 'doc'  # ADF format

    def test_create_epic_with_epic_name(self, mock_jira_client, sample_epic_response):
        """Test setting Epic Name field (customfield_10011)."""
        # Arrange
        mock_jira_client.create_issue.return_value = sample_epic_response
        from create_epic import create_epic

        # Act
        result = create_epic(
            project="PROJ",
            summary="Mobile App MVP",
            epic_name="MVP",
            profile=None
        )

        # Assert
        assert result is not None

        # Verify Epic Name field set
        call_args = mock_jira_client.create_issue.call_args[0][0]
        assert call_args.get('customfield_10011') == "MVP"

    def test_create_epic_with_color(self, mock_jira_client, sample_epic_response):
        """Test setting epic color (customfield_10012)."""
        # Arrange
        mock_jira_client.create_issue.return_value = sample_epic_response
        from create_epic import create_epic

        # Act
        result = create_epic(
            project="PROJ",
            summary="Mobile App MVP",
            color="blue",
            profile=None
        )

        # Assert
        assert result is not None

        # Verify color field set
        call_args = mock_jira_client.create_issue.call_args[0][0]
        assert call_args.get('customfield_10012') == "blue"

    def test_create_epic_invalid_color(self):
        """Test validation of epic color."""
        from create_epic import create_epic
        from error_handler import ValidationError

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            create_epic(
                project="PROJ",
                summary="Mobile App MVP",
                color="invalid-color",
                profile=None
            )

        assert "color" in str(exc_info.value).lower()

    def test_create_epic_missing_project(self):
        """Test error handling for missing required field."""
        from create_epic import create_epic
        from error_handler import ValidationError

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            create_epic(
                project=None,
                summary="Mobile App MVP",
                profile=None
            )

        assert "project" in str(exc_info.value).lower()

    def test_create_epic_api_error(self, mock_jira_client):
        """Test handling of JIRA API errors."""
        # Arrange
        from create_epic import create_epic
        from error_handler import JiraError

        # Simulate API error
        mock_jira_client.create_issue.side_effect = JiraError(
            "Failed to create epic",
            status_code=400
        )

        # Act & Assert
        with pytest.raises(JiraError) as exc_info:
            create_epic(
                project="PROJ",
                summary="Mobile App MVP",
                profile=None
            )

        assert exc_info.value.status_code == 400


@pytest.mark.agile
@pytest.mark.unit
class TestCreateEpicCLI:
    """Test command-line interface for create_epic.py."""

    @patch('sys.argv', ['create_epic.py', '--project', 'PROJ', '--summary', 'Test Epic'])
    def test_cli_minimal_args(self, mock_jira_client, sample_epic_response):
        """Test CLI with minimal required arguments."""
        # This will fail initially - tests the CLI parsing
        mock_jira_client.create_issue.return_value = sample_epic_response

        # Import and run main
        # from create_epic import main
        # This is a placeholder - will implement when script exists
        pass

    @patch('sys.argv', ['create_epic.py', '--help'])
    def test_cli_help_output(self, capsys):
        """Test that --help shows usage information."""
        # This will fail initially
        # from create_epic import main
        # Will test help output includes required flags
        pass
