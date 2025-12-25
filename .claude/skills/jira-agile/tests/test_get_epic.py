"""
Tests for get_epic.py - Retrieving epic details and progress.

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
class TestGetEpic:
    """Test suite for get_epic.py functionality."""

    def test_get_epic_basic_info(self, mock_jira_client, sample_epic_response):
        """Test retrieving epic details."""
        # Arrange
        from get_epic import get_epic

        mock_jira_client.get_issue.return_value = sample_epic_response

        # Act
        result = get_epic(
            epic_key="PROJ-100",
            client=mock_jira_client
        )

        # Assert
        assert result is not None
        assert result['key'] == "PROJ-100"
        assert result['fields']['summary'] == "Mobile App MVP"
        assert result['fields']['issuetype']['name'] == "Epic"

        # Verify API call
        mock_jira_client.get_issue.assert_called_once_with("PROJ-100")

    def test_get_epic_with_children(self, mock_jira_client, sample_epic_response, sample_issue_response):
        """Test fetching all issues in epic."""
        # Arrange
        from get_epic import get_epic

        # Mock epic and child issues
        mock_jira_client.get_issue.return_value = sample_epic_response
        mock_jira_client.search_issues.return_value = {
            'issues': [sample_issue_response],
            'total': 1
        }

        # Act
        result = get_epic(
            epic_key="PROJ-100",
            with_children=True,
            client=mock_jira_client
        )

        # Assert
        assert result is not None
        assert 'children' in result
        assert len(result['children']) == 1
        assert result['children'][0]['key'] == "PROJ-101"

        # Verify JQL search was called
        mock_jira_client.search_issues.assert_called_once()
        call_args = mock_jira_client.search_issues.call_args[0][0]
        assert 'Epic Link' in call_args or 'PROJ-100' in call_args

    def test_get_epic_progress_calculation(self, mock_jira_client, sample_epic_response):
        """Test calculating epic progress (done/total)."""
        # Arrange
        from get_epic import get_epic

        mock_jira_client.get_issue.return_value = sample_epic_response
        mock_jira_client.search_issues.return_value = {
            'issues': [
                {'key': 'PROJ-101', 'fields': {'status': {'name': 'Done'}}},
                {'key': 'PROJ-102', 'fields': {'status': {'name': 'Done'}}},
                {'key': 'PROJ-103', 'fields': {'status': {'name': 'In Progress'}}},
                {'key': 'PROJ-104', 'fields': {'status': {'name': 'To Do'}}},
            ],
            'total': 4
        }

        # Act
        result = get_epic(
            epic_key="PROJ-100",
            with_children=True,
            client=mock_jira_client
        )

        # Assert
        assert 'progress' in result
        assert result['progress']['total'] == 4
        assert result['progress']['done'] == 2
        assert result['progress']['percentage'] == 50  # 2/4 = 50%

    def test_get_epic_story_points_sum(self, mock_jira_client, sample_epic_response):
        """Test summing story points in epic."""
        # Arrange
        from get_epic import get_epic

        mock_jira_client.get_issue.return_value = sample_epic_response
        mock_jira_client.search_issues.return_value = {
            'issues': [
                {'key': 'PROJ-101', 'fields': {'customfield_10016': 5, 'status': {'name': 'Done'}}},
                {'key': 'PROJ-102', 'fields': {'customfield_10016': 8, 'status': {'name': 'Done'}}},
                {'key': 'PROJ-103', 'fields': {'customfield_10016': 3, 'status': {'name': 'In Progress'}}},
            ],
            'total': 3
        }

        # Act
        result = get_epic(
            epic_key="PROJ-100",
            with_children=True,
            client=mock_jira_client
        )

        # Assert
        assert 'story_points' in result
        assert result['story_points']['total'] == 16  # 5+8+3
        assert result['story_points']['done'] == 13   # 5+8
        assert result['story_points']['percentage'] == 81  # 13/16 = 81.25% -> 81

    def test_get_epic_format_text(self, mock_jira_client, sample_epic_response):
        """Test text output format."""
        # Arrange
        from get_epic import format_epic_output

        # Act
        output = format_epic_output(sample_epic_response, format='text')

        # Assert
        assert output is not None
        assert isinstance(output, str)
        assert "PROJ-100" in output
        assert "Mobile App MVP" in output

    def test_get_epic_format_json(self, mock_jira_client, sample_epic_response):
        """Test JSON output format."""
        # Arrange
        from get_epic import format_epic_output
        import json

        # Act
        output = format_epic_output(sample_epic_response, format='json')

        # Assert
        assert output is not None
        # Should be valid JSON
        parsed = json.loads(output)
        assert parsed['key'] == "PROJ-100"

    def test_get_epic_not_found(self, mock_jira_client):
        """Test error when epic doesn't exist."""
        # Arrange
        from get_epic import get_epic
        from error_handler import JiraError

        # Simulate 404
        mock_jira_client.get_issue.side_effect = JiraError(
            "Issue does not exist",
            status_code=404
        )

        # Act & Assert
        with pytest.raises(JiraError) as exc_info:
            get_epic(
                epic_key="PROJ-999",
                client=mock_jira_client
            )

        assert exc_info.value.status_code == 404


@pytest.mark.agile
@pytest.mark.unit
class TestGetEpicCLI:
    """Test command-line interface for get_epic.py."""

    @patch('sys.argv', ['get_epic.py', 'PROJ-100'])
    def test_cli_basic(self, mock_jira_client, sample_epic_response):
        """Test CLI with just epic key."""
        # This will fail initially - tests the CLI parsing
        mock_jira_client.get_issue.return_value = sample_epic_response

        # from get_epic import main
        # This is a placeholder - will implement when script exists
        pass

    @patch('sys.argv', ['get_epic.py', 'PROJ-100', '--with-children'])
    def test_cli_with_children(self, mock_jira_client, sample_epic_response):
        """Test CLI with --with-children flag."""
        # This will fail initially
        # from get_epic import main
        pass
