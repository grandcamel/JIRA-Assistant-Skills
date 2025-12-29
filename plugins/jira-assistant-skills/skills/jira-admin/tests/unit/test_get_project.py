"""
Tests for get_project.py - Getting JIRA project details.

Following TDD: These tests are written FIRST and should FAIL initially.
Implementation comes after tests are defined.
"""

import sys
from pathlib import Path

# Add paths BEFORE any other imports
test_dir = Path(__file__).parent  # unit
tests_dir = test_dir.parent  # tests
jira_admin_dir = tests_dir.parent  # jira-admin
skills_dir = jira_admin_dir.parent  # skills
shared_lib_path = skills_dir / 'shared' / 'scripts' / 'lib'
scripts_path = jira_admin_dir / 'scripts'

sys.path.insert(0, str(shared_lib_path))
sys.path.insert(0, str(scripts_path))

import pytest
from unittest.mock import Mock, patch


@pytest.mark.admin
@pytest.mark.unit
class TestGetProject:
    """Test suite for get_project.py functionality."""

    def test_get_project_basic(self, mock_jira_client, sample_project_response):
        """Test getting basic project information."""
        from get_project import get_project

        mock_jira_client.get_project.return_value = sample_project_response

        result = get_project(
            project_key="PROJ",
            client=mock_jira_client
        )

        assert result is not None
        assert result['key'] == "PROJ"
        assert result['name'] == "Test Project"
        assert result['projectTypeKey'] == "software"

        # Verify API call
        mock_jira_client.get_project.assert_called_once()

    def test_get_project_with_expand(self, mock_jira_client, sample_project_response):
        """Test getting project with expanded fields."""
        from get_project import get_project

        mock_jira_client.get_project.return_value = sample_project_response

        result = get_project(
            project_key="PROJ",
            expand=['description', 'lead', 'issueTypes'],
            client=mock_jira_client
        )

        assert result is not None

        # Verify expand was passed
        call_kwargs = mock_jira_client.get_project.call_args
        assert 'expand' in str(call_kwargs) or call_kwargs[1].get('expand') is not None

    def test_get_project_with_components(self, mock_jira_client, sample_project_response):
        """Test getting project with components."""
        from get_project import get_project

        # Add components to response
        project_with_components = sample_project_response.copy()
        project_with_components['components'] = [
            {"id": "10001", "name": "Backend", "description": "Backend services"},
            {"id": "10002", "name": "Frontend", "description": "UI components"}
        ]
        mock_jira_client.get_project.return_value = project_with_components
        mock_jira_client.get_project_components.return_value = project_with_components['components']

        result = get_project(
            project_key="PROJ",
            show_components=True,
            client=mock_jira_client
        )

        assert result is not None

    def test_get_project_with_versions(self, mock_jira_client, sample_project_response):
        """Test getting project with versions."""
        from get_project import get_project

        project_with_versions = sample_project_response.copy()
        project_with_versions['versions'] = [
            {"id": "10001", "name": "1.0.0", "released": False},
            {"id": "10002", "name": "1.1.0", "released": False}
        ]
        mock_jira_client.get_project.return_value = project_with_versions
        mock_jira_client.get_project_versions.return_value = project_with_versions['versions']

        result = get_project(
            project_key="PROJ",
            show_versions=True,
            client=mock_jira_client
        )

        assert result is not None

    def test_get_project_not_found(self, mock_jira_client):
        """Test error when project doesn't exist."""
        from get_project import get_project
        from jira_assistant_skills_lib import NotFoundError, JiraError

        mock_jira_client.get_project.side_effect = JiraError(
            "Project NOTFOUND not found",
            status_code=404
        )

        with pytest.raises(JiraError) as exc_info:
            get_project(
                project_key="NOTFOUND",
                client=mock_jira_client
            )

        assert exc_info.value.status_code == 404

    def test_get_project_invalid_key(self, mock_jira_client):
        """Test validation of project key format."""
        from get_project import get_project
        from jira_assistant_skills_lib import ValidationError

        with pytest.raises(ValidationError):
            get_project(
                project_key="",  # Empty key
                client=mock_jira_client
            )

    def test_get_project_no_permission(self, mock_jira_client):
        """Test error when user lacks browse permission."""
        from get_project import get_project
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.get_project.side_effect = JiraError(
            "You don't have permission to browse this project",
            status_code=403
        )

        with pytest.raises(JiraError) as exc_info:
            get_project(
                project_key="SECRET",
                client=mock_jira_client
            )

        assert exc_info.value.status_code == 403

    def test_get_project_json_output(self, mock_jira_client, sample_project_response):
        """Test JSON output format."""
        from get_project import get_project

        mock_jira_client.get_project.return_value = sample_project_response

        result = get_project(
            project_key="PROJ",
            output_format="json",
            client=mock_jira_client
        )

        assert result is not None
        # Result should be suitable for JSON serialization
        import json
        json.dumps(result)  # Should not raise

    def test_get_project_extracts_lead_info(self, mock_jira_client, sample_project_response):
        """Test that lead information is properly extracted."""
        from get_project import get_project

        mock_jira_client.get_project.return_value = sample_project_response

        result = get_project(
            project_key="PROJ",
            client=mock_jira_client
        )

        assert 'lead' in result
        assert result['lead']['displayName'] == "Test User"

    def test_get_project_extracts_category(self, mock_jira_client, sample_project_response):
        """Test that category information is properly extracted."""
        from get_project import get_project

        mock_jira_client.get_project.return_value = sample_project_response

        result = get_project(
            project_key="PROJ",
            client=mock_jira_client
        )

        assert 'projectCategory' in result
        assert result['projectCategory']['name'] == "Development"


@pytest.mark.admin
@pytest.mark.unit
class TestGetProjectCLI:
    """Test command-line interface for get_project.py."""

    @patch('sys.argv', ['get_project.py', 'PROJ'])
    def test_cli_basic(self, mock_jira_client, sample_project_response):
        """Test CLI with basic project key argument."""
        mock_jira_client.get_project.return_value = sample_project_response
        pass

    @patch('sys.argv', ['get_project.py', 'PROJ', '--output', 'json'])
    def test_cli_json_output(self, mock_jira_client, sample_project_response):
        """Test CLI with JSON output format."""
        mock_jira_client.get_project.return_value = sample_project_response
        pass

    @patch('sys.argv', ['get_project.py', 'PROJ', '--show-components', '--show-versions'])
    def test_cli_with_details(self, mock_jira_client, sample_project_response):
        """Test CLI with component and version flags."""
        mock_jira_client.get_project.return_value = sample_project_response
        pass
