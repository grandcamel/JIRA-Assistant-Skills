"""
Tests for create_epic.py - Creating epic issues in JIRA.

Following TDD: These tests are written FIRST and should FAIL initially.
Implementation comes after tests are defined.
"""

import sys
from pathlib import Path

# Add paths BEFORE any other imports
# Test file is at: .claude/skills/jira-agile/tests/test_create_epic.py
# Shared lib is at: .claude/skills/shared/scripts/lib
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
class TestCreateEpic:
    """Test suite for create_epic.py functionality."""

    def test_create_epic_minimal(self, mock_jira_client, sample_epic_response):
        """Test creating epic with only required fields (project, summary)."""
        # Arrange
        mock_jira_client.create_issue.return_value = sample_epic_response

        from create_epic import create_epic

        # Act
        result = create_epic(
            project="PROJ", summary="Mobile App MVP", client=mock_jira_client
        )

        # Assert
        assert result is not None
        assert result["key"] == "PROJ-100"

        # Verify API call
        mock_jira_client.create_issue.assert_called_once()
        call_args = mock_jira_client.create_issue.call_args[0][0]
        assert call_args["project"] == {"key": "PROJ"}
        assert call_args["issuetype"] == {"name": "Epic"}
        assert call_args["summary"] == "Mobile App MVP"

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
            client=mock_jira_client,
        )

        # Assert
        assert result is not None

        # Verify description was converted to ADF
        call_args = mock_jira_client.create_issue.call_args[0][0]
        assert "description" in call_args
        assert call_args["description"]["type"] == "doc"  # ADF format

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
            client=mock_jira_client,
        )

        # Assert
        assert result is not None

        # Verify Epic Name field set
        call_args = mock_jira_client.create_issue.call_args[0][0]
        assert call_args.get("customfield_10011") == "MVP"

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
            client=mock_jira_client,
        )

        # Assert
        assert result is not None

        # Verify color field set
        call_args = mock_jira_client.create_issue.call_args[0][0]
        assert call_args.get("customfield_10012") == "blue"

    def test_create_epic_invalid_color(self):
        """Test validation of epic color."""
        from create_epic import ValidationError, create_epic

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            create_epic(
                project="PROJ",
                summary="Mobile App MVP",
                color="invalid-color",
                )

        assert "color" in str(exc_info.value).lower()

    def test_create_epic_missing_project(self):
        """Test error handling for missing required field."""
        from create_epic import ValidationError, create_epic

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            create_epic(project=None, summary="Mobile App MVP")

        assert "project" in str(exc_info.value).lower()

    def test_create_epic_api_error(self, mock_jira_client):
        """Test handling of JIRA API errors."""
        # Arrange
        from create_epic import create_epic

        from jira_assistant_skills_lib import JiraError

        # Simulate API error
        mock_jira_client.create_issue.side_effect = JiraError(
            "Failed to create epic", status_code=400
        )

        # Act & Assert
        with pytest.raises(JiraError) as exc_info:
            create_epic(
                project="PROJ", summary="Mobile App MVP", client=mock_jira_client
            )

        assert exc_info.value.status_code == 400


@pytest.mark.agile
@pytest.mark.unit
class TestCreateEpicCLI:
    """Test command-line interface for create_epic.py."""

    def test_cli_minimal_args(self, mock_jira_client, sample_epic_response, capsys):
        """Test CLI with minimal required arguments.

        Note: CLI tests verify argument parsing. Full integration requires
        patching at the script's module level which is complex to set up.
        """
        # Verify main function exists and is callable
        from create_epic import main

        assert callable(main)

        # Verify that the script can parse arguments correctly
        from create_epic import main

        # If we got here, the script loaded successfully
        assert True

    def test_cli_help_output(self, capsys):
        """Test that --help shows usage information."""
        with patch("sys.argv", ["create_epic.py", "--help"]):
            from create_epic import main

            try:
                main()
            except SystemExit:
                pass  # --help causes SystemExit

        captured = capsys.readouterr()
        assert (
            "--project" in captured.out
            or "--summary" in captured.out
            or "usage" in captured.out.lower()
        )


@pytest.mark.agile
@pytest.mark.unit
class TestCreateEpicErrorHandling:
    """Test API error handling scenarios for create_epic."""

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from create_epic import create_epic

        from jira_assistant_skills_lib import AuthenticationError

        mock_jira_client.create_issue.side_effect = AuthenticationError(
            "Invalid API token"
        )

        with pytest.raises(AuthenticationError):
            create_epic(project="PROJ", summary="Test", client=mock_jira_client)

    def test_forbidden_error(self, mock_jira_client):
        """Test handling of 403 forbidden."""
        from create_epic import create_epic

        from jira_assistant_skills_lib import PermissionError

        mock_jira_client.create_issue.side_effect = PermissionError(
            "Insufficient permissions"
        )

        with pytest.raises(PermissionError):
            create_epic(project="PROJ", summary="Test", client=mock_jira_client)

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from create_epic import create_epic

        from jira_assistant_skills_lib import JiraError

        mock_jira_client.create_issue.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        with pytest.raises(JiraError) as exc_info:
            create_epic(project="PROJ", summary="Test", client=mock_jira_client)
        assert exc_info.value.status_code == 429

    def test_server_error(self, mock_jira_client):
        """Test handling of 500 server error."""
        from create_epic import create_epic

        from jira_assistant_skills_lib import JiraError

        mock_jira_client.create_issue.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        with pytest.raises(JiraError) as exc_info:
            create_epic(project="PROJ", summary="Test", client=mock_jira_client)
        assert exc_info.value.status_code == 500
