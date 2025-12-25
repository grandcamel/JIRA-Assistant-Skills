"""
Tests for get_components.py - Get project components.
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add script path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


class TestGetComponents:
    """Tests for getting project components."""

    @patch('get_components.get_jira_client')
    def test_get_all_components(self, mock_get_client, mock_jira_client, sample_components_list):
        """Test getting all components for a project."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_components.return_value = sample_components_list

        from get_components import get_components

        result = get_components('PROJ', profile=None)

        assert len(result) == 3
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

        # Alice Smith leads 2 components in sample data
        assert len(filtered) == 2
        assert all(c['lead']['displayName'] == 'Alice Smith' for c in filtered)

    @patch('get_components.get_jira_client')
    def test_get_component_issue_counts(self, mock_get_client, mock_jira_client, sample_component_issue_counts):
        """Test getting issue counts for a component."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_component_issue_counts.return_value = sample_component_issue_counts

        from get_components import get_component_issue_counts

        result = get_component_issue_counts('10000', profile=None)

        assert result['issueCount'] == 42
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
        assert 'Frontend UI' in captured.out
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

        # Should be valid JSON
        parsed_json = json.loads(json_output)
        assert len(parsed_json) == 3
        assert parsed_json[0]['name'] == 'Backend API'
