"""
Tests for project configuration management - set_avatar.py, set_project_lead.py,
set_default_assignee.py, get_config.py.

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
class TestSetAvatar:
    """Test suite for set_avatar.py functionality."""

    def test_list_available_avatars(self, mock_jira_client, sample_avatars_response):
        """Test listing available avatars for a project."""
        from set_avatar import list_avatars

        mock_jira_client.get_project_avatars.return_value = sample_avatars_response

        result = list_avatars(
            project_key="PROJ",
            client=mock_jira_client
        )

        assert result is not None
        assert 'system' in result or 'custom' in result

        mock_jira_client.get_project_avatars.assert_called_once_with("PROJ")

    def test_select_system_avatar(self, mock_jira_client, sample_avatars_response):
        """Test selecting a system avatar."""
        from set_avatar import set_avatar

        mock_jira_client.set_project_avatar.return_value = None

        result = set_avatar(
            project_key="PROJ",
            avatar_id="10200",
            client=mock_jira_client
        )

        assert result is not None
        assert result.get('success') is True

        mock_jira_client.set_project_avatar.assert_called_once_with("PROJ", "10200")

    def test_upload_avatar_from_file(self, mock_jira_client):
        """Test uploading avatar from local file."""
        from set_avatar import upload_avatar
        import tempfile
        import os

        # Create a minimal PNG file (1x1 transparent pixel)
        png_header = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(png_header)
            temp_file = f.name

        try:
            mock_jira_client.upload_project_avatar.return_value = {
                'id': '10300',
                'owner': 'PROJ',
                'isSystemAvatar': False
            }

            result = upload_avatar(
                project_key="PROJ",
                file_path=temp_file,
                client=mock_jira_client
            )

            assert result is not None
            mock_jira_client.upload_project_avatar.assert_called_once()
        finally:
            os.unlink(temp_file)

    def test_upload_avatar_invalid_format(self, mock_jira_client):
        """Test error for unsupported file format."""
        from set_avatar import upload_avatar
        from error_handler import ValidationError
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b'not an image')
            temp_file = f.name

        try:
            with pytest.raises(ValidationError):
                upload_avatar(
                    project_key="PROJ",
                    file_path=temp_file,
                    client=mock_jira_client
                )
        finally:
            os.unlink(temp_file)

    def test_set_avatar_project_not_found(self, mock_jira_client):
        """Test error when project doesn't exist."""
        from set_avatar import set_avatar
        from error_handler import JiraError

        mock_jira_client.set_project_avatar.side_effect = JiraError(
            "Project not found",
            status_code=404
        )

        with pytest.raises(JiraError) as exc_info:
            set_avatar(
                project_key="NOTFOUND",
                avatar_id="10200",
                client=mock_jira_client
            )

        assert exc_info.value.status_code == 404

    def test_delete_custom_avatar(self, mock_jira_client):
        """Test deleting a custom avatar."""
        from set_avatar import delete_avatar

        mock_jira_client.delete_project_avatar.return_value = None

        result = delete_avatar(
            project_key="PROJ",
            avatar_id="10300",
            client=mock_jira_client
        )

        assert result is not None
        assert result.get('success') is True

        mock_jira_client.delete_project_avatar.assert_called_once_with("PROJ", "10300")


@pytest.mark.admin
@pytest.mark.unit
class TestSetProjectLead:
    """Test suite for set_project_lead.py functionality."""

    def test_set_lead_by_email(self, mock_jira_client, sample_project_response):
        """Test setting project lead by email address."""
        from set_project_lead import set_project_lead

        mock_jira_client.search_users.return_value = [
            {'accountId': 'alice-account-id', 'emailAddress': 'alice@example.com', 'displayName': 'Alice'}
        ]
        mock_jira_client.update_project.return_value = sample_project_response

        result = set_project_lead(
            project_key="PROJ",
            lead_email="alice@example.com",
            client=mock_jira_client
        )

        assert result is not None

        # Verify update_project was called with lead
        mock_jira_client.update_project.assert_called_once()

    def test_set_lead_by_account_id(self, mock_jira_client, sample_project_response):
        """Test setting project lead by account ID."""
        from set_project_lead import set_project_lead

        mock_jira_client.update_project.return_value = sample_project_response

        result = set_project_lead(
            project_key="PROJ",
            lead_account_id="557058:test-user-id",
            client=mock_jira_client
        )

        assert result is not None

        mock_jira_client.update_project.assert_called_once()

    def test_set_lead_user_not_found(self, mock_jira_client):
        """Test error when user doesn't exist."""
        from set_project_lead import set_project_lead
        from error_handler import ValidationError

        mock_jira_client.search_users.return_value = []

        with pytest.raises(ValidationError) as exc_info:
            set_project_lead(
                project_key="PROJ",
                lead_email="nonexistent@example.com",
                client=mock_jira_client
            )

        assert "not found" in str(exc_info.value).lower()

    def test_set_lead_no_permission(self, mock_jira_client):
        """Test error when user lacks permission."""
        from set_project_lead import set_project_lead
        from error_handler import JiraError

        mock_jira_client.update_project.side_effect = JiraError(
            "You don't have permission to update project lead",
            status_code=403
        )

        with pytest.raises(JiraError) as exc_info:
            set_project_lead(
                project_key="PROJ",
                lead_account_id="some-account-id",
                client=mock_jira_client
            )

        assert exc_info.value.status_code == 403

    def test_set_lead_requires_email_or_account_id(self, mock_jira_client):
        """Test error when neither email nor account ID provided."""
        from set_project_lead import set_project_lead
        from error_handler import ValidationError

        with pytest.raises(ValidationError):
            set_project_lead(
                project_key="PROJ",
                client=mock_jira_client
                # No lead_email or lead_account_id
            )


@pytest.mark.admin
@pytest.mark.unit
class TestSetDefaultAssignee:
    """Test suite for set_default_assignee.py functionality."""

    def test_set_assignee_type_project_lead(self, mock_jira_client, sample_project_response):
        """Test setting default assignee to project lead."""
        from set_default_assignee import set_default_assignee

        mock_jira_client.update_project.return_value = sample_project_response

        result = set_default_assignee(
            project_key="PROJ",
            assignee_type="PROJECT_LEAD",
            client=mock_jira_client
        )

        assert result is not None

        mock_jira_client.update_project.assert_called_once()
        call_kwargs = mock_jira_client.update_project.call_args
        assert 'assignee_type' in str(call_kwargs) or 'PROJECT_LEAD' in str(call_kwargs)

    def test_set_assignee_type_unassigned(self, mock_jira_client, sample_project_response):
        """Test setting default assignee to unassigned."""
        from set_default_assignee import set_default_assignee

        mock_jira_client.update_project.return_value = sample_project_response

        result = set_default_assignee(
            project_key="PROJ",
            assignee_type="UNASSIGNED",
            client=mock_jira_client
        )

        assert result is not None

        mock_jira_client.update_project.assert_called_once()

    def test_set_assignee_type_component_lead(self, mock_jira_client, sample_project_response):
        """Test setting default assignee to component lead."""
        from set_default_assignee import set_default_assignee

        mock_jira_client.update_project.return_value = sample_project_response

        result = set_default_assignee(
            project_key="PROJ",
            assignee_type="COMPONENT_LEAD",
            client=mock_jira_client
        )

        assert result is not None

        mock_jira_client.update_project.assert_called_once()

    def test_invalid_assignee_type(self, mock_jira_client):
        """Test error for invalid assignee type."""
        from set_default_assignee import set_default_assignee
        from error_handler import ValidationError

        with pytest.raises(ValidationError):
            set_default_assignee(
                project_key="PROJ",
                assignee_type="INVALID",
                client=mock_jira_client
            )

    def test_set_assignee_no_permission(self, mock_jira_client):
        """Test error when user lacks permission."""
        from set_default_assignee import set_default_assignee
        from error_handler import JiraError

        mock_jira_client.update_project.side_effect = JiraError(
            "You don't have permission to update project",
            status_code=403
        )

        with pytest.raises(JiraError) as exc_info:
            set_default_assignee(
                project_key="PROJ",
                assignee_type="PROJECT_LEAD",
                client=mock_jira_client
            )

        assert exc_info.value.status_code == 403


@pytest.mark.admin
@pytest.mark.unit
class TestGetConfig:
    """Test suite for get_config.py functionality."""

    def test_get_full_configuration(self, mock_jira_client, sample_project_response):
        """Test fetching complete project configuration."""
        from get_config import get_project_config

        mock_jira_client.get_project.return_value = sample_project_response

        result = get_project_config(
            project_key="PROJ",
            client=mock_jira_client
        )

        assert result is not None
        assert result.get('key') == 'PROJ'

        mock_jira_client.get_project.assert_called_once()

    def test_get_config_with_schemes(self, mock_jira_client, sample_project_response):
        """Test fetching configuration with scheme details."""
        from get_config import get_project_config

        # Add scheme info to response
        project_with_schemes = sample_project_response.copy()
        project_with_schemes['issueTypeScreenScheme'] = {
            'id': '10000',
            'name': 'Default Issue Type Screen Scheme'
        }
        project_with_schemes['permissionScheme'] = {
            'id': '10000',
            'name': 'Default Permission Scheme'
        }
        project_with_schemes['notificationScheme'] = {
            'id': '10000',
            'name': 'Default Notification Scheme'
        }

        mock_jira_client.get_project.return_value = project_with_schemes

        result = get_project_config(
            project_key="PROJ",
            show_schemes=True,
            client=mock_jira_client
        )

        assert result is not None

    def test_get_config_project_not_found(self, mock_jira_client):
        """Test error when project doesn't exist."""
        from get_config import get_project_config
        from error_handler import JiraError

        mock_jira_client.get_project.side_effect = JiraError(
            "Project not found",
            status_code=404
        )

        with pytest.raises(JiraError) as exc_info:
            get_project_config(
                project_key="NOTFOUND",
                client=mock_jira_client
            )

        assert exc_info.value.status_code == 404

    def test_get_config_format_text(self, mock_jira_client, sample_project_response):
        """Test text output format."""
        from get_config import get_project_config, format_output

        mock_jira_client.get_project.return_value = sample_project_response

        result = get_project_config(
            project_key="PROJ",
            client=mock_jira_client
        )

        output = format_output(result, output_format="text")

        assert "PROJ" in output
        assert "Test Project" in output

    def test_get_config_format_json(self, mock_jira_client, sample_project_response):
        """Test JSON output format."""
        from get_config import get_project_config, format_output
        import json

        mock_jira_client.get_project.return_value = sample_project_response

        result = get_project_config(
            project_key="PROJ",
            client=mock_jira_client
        )

        output = format_output(result, output_format="json")

        # Should be valid JSON
        data = json.loads(output)
        assert data.get('key') == 'PROJ'


@pytest.mark.admin
@pytest.mark.unit
class TestProjectConfigCLI:
    """Test command-line interfaces for project configuration."""

    @patch('sys.argv', ['set_avatar.py', 'PROJ', '--list'])
    def test_cli_list_avatars(self, mock_jira_client, sample_avatars_response):
        """Test CLI for listing avatars."""
        mock_jira_client.get_project_avatars.return_value = sample_avatars_response
        # CLI test placeholder
        pass

    @patch('sys.argv', ['set_avatar.py', 'PROJ', '--avatar-id', '10200'])
    def test_cli_set_avatar(self, mock_jira_client):
        """Test CLI for setting avatar."""
        mock_jira_client.set_project_avatar.return_value = None
        # CLI test placeholder
        pass

    @patch('sys.argv', ['set_project_lead.py', 'PROJ', '--lead', 'alice@example.com'])
    def test_cli_set_project_lead(self, mock_jira_client, sample_project_response):
        """Test CLI for setting project lead."""
        mock_jira_client.search_users.return_value = [{'accountId': 'alice', 'emailAddress': 'alice@example.com'}]
        mock_jira_client.update_project.return_value = sample_project_response
        # CLI test placeholder
        pass

    @patch('sys.argv', ['set_default_assignee.py', 'PROJ', '--type', 'PROJECT_LEAD'])
    def test_cli_set_default_assignee(self, mock_jira_client, sample_project_response):
        """Test CLI for setting default assignee."""
        mock_jira_client.update_project.return_value = sample_project_response
        # CLI test placeholder
        pass

    @patch('sys.argv', ['get_config.py', 'PROJ'])
    def test_cli_get_config(self, mock_jira_client, sample_project_response):
        """Test CLI for getting project configuration."""
        mock_jira_client.get_project.return_value = sample_project_response
        # CLI test placeholder
        pass
