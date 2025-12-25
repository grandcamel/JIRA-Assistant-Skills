"""
Tests for update_component.py - Update a project component.
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add script path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


class TestUpdateComponent:
    """Tests for updating project components."""

    @patch('update_component.get_jira_client')
    def test_update_component_name(self, mock_get_client, mock_jira_client):
        """Test updating component name."""
        mock_get_client.return_value = mock_jira_client
        updated_component = {
            'id': '10000',
            'name': 'New Component Name',
            'description': 'Server-side API components',
            'project': 'PROJ'
        }
        mock_jira_client.update_component.return_value = updated_component

        from update_component import update_component

        result = update_component(
            component_id='10000',
            name='New Component Name',
            profile=None
        )

        assert result['name'] == 'New Component Name'
        mock_jira_client.update_component.assert_called_once()

    @patch('update_component.get_jira_client')
    def test_update_component_description(self, mock_get_client, mock_jira_client):
        """Test updating component description."""
        mock_get_client.return_value = mock_jira_client
        updated_component = {
            'id': '10000',
            'name': 'Backend API',
            'description': 'Updated description',
            'project': 'PROJ'
        }
        mock_jira_client.update_component.return_value = updated_component

        from update_component import update_component

        result = update_component(
            component_id='10000',
            description='Updated description',
            profile=None
        )

        assert result['description'] == 'Updated description'

    @patch('update_component.get_jira_client')
    def test_update_component_lead(self, mock_get_client, mock_jira_client):
        """Test updating component lead."""
        mock_get_client.return_value = mock_jira_client
        updated_component = {
            'id': '10000',
            'name': 'Backend API',
            'project': 'PROJ',
            'lead': {
                'accountId': '5b10a2844c20165700ede22h',
                'displayName': 'Bob Jones'
            }
        }
        mock_jira_client.update_component.return_value = updated_component

        from update_component import update_component

        result = update_component(
            component_id='10000',
            lead_account_id='5b10a2844c20165700ede22h',
            profile=None
        )

        assert result['lead']['accountId'] == '5b10a2844c20165700ede22h'

    @patch('update_component.get_jira_client')
    def test_update_component_assignee_type(self, mock_get_client, mock_jira_client):
        """Test updating component assignee type."""
        mock_get_client.return_value = mock_jira_client
        updated_component = {
            'id': '10000',
            'name': 'Backend API',
            'project': 'PROJ',
            'assigneeType': 'PROJECT_LEAD'
        }
        mock_jira_client.update_component.return_value = updated_component

        from update_component import update_component

        result = update_component(
            component_id='10000',
            assignee_type='PROJECT_LEAD',
            profile=None
        )

        assert result['assigneeType'] == 'PROJECT_LEAD'

    @patch('update_component.get_jira_client')
    def test_update_component_multiple_fields(self, mock_get_client, mock_jira_client):
        """Test updating multiple component fields at once."""
        mock_get_client.return_value = mock_jira_client
        updated_component = {
            'id': '10000',
            'name': 'Updated Name',
            'description': 'Updated description',
            'project': 'PROJ',
            'lead': {
                'accountId': '5b10a2844c20165700ede22h',
                'displayName': 'Bob Jones'
            },
            'assigneeType': 'COMPONENT_LEAD'
        }
        mock_jira_client.update_component.return_value = updated_component

        from update_component import update_component

        result = update_component(
            component_id='10000',
            name='Updated Name',
            description='Updated description',
            lead_account_id='5b10a2844c20165700ede22h',
            assignee_type='COMPONENT_LEAD',
            profile=None
        )

        assert result['name'] == 'Updated Name'
        assert result['description'] == 'Updated description'
        assert result['assigneeType'] == 'COMPONENT_LEAD'

    @patch('update_component.get_jira_client')
    def test_update_component_dry_run(self, mock_get_client, mock_jira_client):
        """Test dry-run mode shows what would be updated."""
        mock_get_client.return_value = mock_jira_client

        from update_component import update_component_dry_run

        result = update_component_dry_run(
            component_id='10000',
            name='New Name',
            description='New description'
        )

        # Dry run should return data without calling API
        assert result['component_id'] == '10000'
        assert result['name'] == 'New Name'
        assert result['description'] == 'New description'
        mock_jira_client.update_component.assert_not_called()
