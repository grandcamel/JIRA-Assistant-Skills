"""
Tests for delete_component.py - Delete a project component.
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
class TestDeleteComponent:
    """Tests for deleting project components."""

    @patch('delete_component.get_jira_client')
    def test_delete_component_by_id(self, mock_get_client, mock_jira_client):
        """Test deleting a component by ID."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.delete_component.return_value = None

        from delete_component import delete_component

        delete_component(component_id='10000', profile=None)

        mock_jira_client.delete_component.assert_called_once_with('10000')

    @patch('delete_component.get_jira_client')
    def test_delete_component_with_confirmation(self, mock_get_client, mock_jira_client, sample_component, monkeypatch):
        """Test deleting component with confirmation prompt."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_component.return_value = sample_component
        mock_jira_client.delete_component.return_value = None

        # Simulate user confirming with 'yes'
        monkeypatch.setattr('builtins.input', lambda _: 'yes')

        from delete_component import delete_component_with_confirmation

        result = delete_component_with_confirmation(
            component_id='10000',
            profile=None
        )

        assert result is True
        mock_jira_client.delete_component.assert_called_once()

    @patch('delete_component.get_jira_client')
    def test_delete_component_cancelled(self, mock_get_client, mock_jira_client, sample_component, monkeypatch):
        """Test cancelling component deletion."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_component.return_value = sample_component

        # Simulate user declining with 'no'
        monkeypatch.setattr('builtins.input', lambda _: 'no')

        from delete_component import delete_component_with_confirmation

        result = delete_component_with_confirmation(
            component_id='10000',
            profile=None
        )

        assert result is False
        mock_jira_client.delete_component.assert_not_called()

    @patch('delete_component.get_jira_client')
    def test_delete_component_move_issues(self, mock_get_client, mock_jira_client):
        """Test deleting component with move-to option."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.delete_component.return_value = None

        from delete_component import delete_component

        delete_component(
            component_id='10000',
            move_issues_to='10001',
            profile=None
        )

        call_args = mock_jira_client.delete_component.call_args
        assert call_args[0][0] == '10000'
        assert call_args[1].get('moveIssuesTo') == '10001'

    @patch('delete_component.get_jira_client')
    def test_delete_component_dry_run(self, mock_get_client, mock_jira_client, sample_component):
        """Test dry-run mode shows what would be deleted."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_component.return_value = sample_component

        from delete_component import delete_component_dry_run

        result = delete_component_dry_run(
            component_id='10000',
            profile=None
        )

        # Dry run should return component info without deleting
        assert result['id'] == '10000'
        assert result['name'] == 'Backend API'
        mock_jira_client.delete_component.assert_not_called()

    @patch('delete_component.get_jira_client')
    def test_delete_component_skip_confirmation(self, mock_get_client, mock_jira_client):
        """Test deleting component with --yes flag (skip confirmation)."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.delete_component.return_value = None

        from delete_component import delete_component

        # Should not prompt, should delete directly
        delete_component(component_id='10000', profile=None)

        mock_jira_client.delete_component.assert_called_once()


@pytest.mark.lifecycle
@pytest.mark.unit
class TestDeleteComponentErrorHandling:
    """Test API error handling for delete_component."""

    @patch('delete_component.get_jira_client')
    def test_authentication_error(self, mock_get_client, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from jira_assistant_skills_lib import AuthenticationError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.delete_component.side_effect = AuthenticationError("Invalid token")

        from delete_component import delete_component

        with pytest.raises(AuthenticationError):
            delete_component(component_id='10000', profile=None)

    @patch('delete_component.get_jira_client')
    def test_permission_error(self, mock_get_client, mock_jira_client):
        """Test handling of 403 forbidden."""
        from jira_assistant_skills_lib import PermissionError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.delete_component.side_effect = PermissionError("Cannot delete component")

        from delete_component import delete_component

        with pytest.raises(PermissionError):
            delete_component(component_id='10000', profile=None)

    @patch('delete_component.get_jira_client')
    def test_not_found_error(self, mock_get_client, mock_jira_client):
        """Test handling of 404 when component doesn't exist."""
        from jira_assistant_skills_lib import NotFoundError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.delete_component.side_effect = NotFoundError("Component", "99999")

        from delete_component import delete_component

        with pytest.raises(NotFoundError):
            delete_component(component_id='99999', profile=None)

    @patch('delete_component.get_jira_client')
    def test_rate_limit_error(self, mock_get_client, mock_jira_client):
        """Test handling of 429 rate limit."""
        from jira_assistant_skills_lib import JiraError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.delete_component.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        from delete_component import delete_component

        with pytest.raises(JiraError) as exc_info:
            delete_component(component_id='10000', profile=None)
        assert exc_info.value.status_code == 429

    @patch('delete_component.get_jira_client')
    def test_server_error(self, mock_get_client, mock_jira_client):
        """Test handling of 500 server error."""
        from jira_assistant_skills_lib import JiraError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.delete_component.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        from delete_component import delete_component

        with pytest.raises(JiraError) as exc_info:
            delete_component(component_id='10000', profile=None)
        assert exc_info.value.status_code == 500
