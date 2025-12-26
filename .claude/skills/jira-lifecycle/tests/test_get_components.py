"""
Tests for get_components.py - Get project components.
"""

import copy
import pytest
from unittest.mock import patch
import sys
from pathlib import Path

# Add script path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


@pytest.mark.lifecycle
@pytest.mark.unit
class TestGetComponents:
    """Tests for getting project components."""

    @patch('get_components.get_jira_client')
    def test_get_all_components(self, mock_get_client, mock_jira_client, sample_components_list):
        """Test getting all components for a project."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_components.return_value = sample_components_list

        from get_components import get_components

        result = get_components('PROJ', profile=None)

        assert len(result) == 4
        mock_jira_client.get_components.assert_called_once_with('PROJ')

    @patch('get_components.get_jira_client')
    def test_get_component_by_id(self, mock_get_client, mock_jira_client, sample_component):
        """Test getting a specific component by ID."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_component.return_value = sample_component

        from get_components import get_component_by_id

        result = get_component_by_id('10000', profile=None)

        assert result['id'] == '10000'
        assert result['name'] == 'Backend API'
        mock_jira_client.get_component.assert_called_once_with('10000')

    @patch('get_components.get_jira_client')
    def test_filter_components_by_lead(self, mock_get_client, mock_jira_client, sample_components_list):
        """Test filtering components by lead."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_components.return_value = sample_components_list

        from get_components import get_components, filter_by_lead

        components = get_components('PROJ', profile=None)
        filtered = filter_by_lead(components, 'Alice Smith')

        # Alice Smith leads 1 component in sample data (Backend API)
        assert len(filtered) == 1
        assert all(c['lead']['displayName'] == 'Alice Smith' for c in filtered)

    @patch('get_components.get_jira_client')
    def test_get_component_issue_counts(self, mock_get_client, mock_jira_client, sample_component_issue_counts):
        """Test getting issue counts for a component."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_component_issue_counts.return_value = sample_component_issue_counts

        from get_components import get_component_issue_counts

        result = get_component_issue_counts('10000', profile=None)

        assert result['issueCount'] == 78
        mock_jira_client.get_component_issue_counts.assert_called_once()

    @patch('get_components.get_jira_client')
    def test_components_table_output(self, mock_get_client, mock_jira_client, sample_components_list, capsys):
        """Test table output format for components."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_components.return_value = sample_components_list

        from get_components import display_components_table

        display_components_table(sample_components_list)

        captured = capsys.readouterr()
        assert 'Backend API' in captured.out
        assert 'UI/Frontend' in captured.out
        assert 'Database' in captured.out

    @patch('get_components.get_jira_client')
    def test_components_json_output(self, mock_get_client, mock_jira_client, sample_components_list):
        """Test JSON output format for components."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_components.return_value = sample_components_list

        from get_components import get_components
        import json

        components = get_components('PROJ', profile=None)
        json_output = json.dumps(components, indent=2)

        # Should be valid JSON with 4 components
        parsed_json = json.loads(json_output)
        assert len(parsed_json) == 4
        # Components are ordered: UI/Frontend, Backend API, Database, Infrastructure
        assert parsed_json[0]['name'] == 'UI/Frontend'


@pytest.mark.lifecycle
@pytest.mark.unit
class TestGetComponentsErrorHandling:
    """Test API error handling for get_components."""

    @patch('get_components.get_jira_client')
    def test_authentication_error(self, mock_get_client, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from error_handler import AuthenticationError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_components.side_effect = AuthenticationError("Invalid token")

        from get_components import get_components

        with pytest.raises(AuthenticationError):
            get_components('PROJ', profile=None)

    @patch('get_components.get_jira_client')
    def test_permission_error(self, mock_get_client, mock_jira_client):
        """Test handling of 403 forbidden."""
        from error_handler import PermissionError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_components.side_effect = PermissionError("Cannot view components")

        from get_components import get_components

        with pytest.raises(PermissionError):
            get_components('PROJ', profile=None)

    @patch('get_components.get_jira_client')
    def test_not_found_error(self, mock_get_client, mock_jira_client):
        """Test handling of 404 when project doesn't exist."""
        from error_handler import NotFoundError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_components.side_effect = NotFoundError("Project", "INVALID")

        from get_components import get_components

        with pytest.raises(NotFoundError):
            get_components('INVALID', profile=None)

    @patch('get_components.get_jira_client')
    def test_rate_limit_error(self, mock_get_client, mock_jira_client):
        """Test handling of 429 rate limit."""
        from error_handler import JiraError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_components.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        from get_components import get_components

        with pytest.raises(JiraError) as exc_info:
            get_components('PROJ', profile=None)
        assert exc_info.value.status_code == 429

    @patch('get_components.get_jira_client')
    def test_server_error(self, mock_get_client, mock_jira_client):
        """Test handling of 500 server error."""
        from error_handler import JiraError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_components.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        from get_components import get_components

        with pytest.raises(JiraError) as exc_info:
            get_components('PROJ', profile=None)
        assert exc_info.value.status_code == 500
