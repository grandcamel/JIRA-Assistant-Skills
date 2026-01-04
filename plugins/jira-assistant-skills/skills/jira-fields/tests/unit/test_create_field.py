"""
Unit Tests: create_field.py

Tests for creating custom JIRA fields.
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Path setup
_this_dir = Path(__file__).parent
_tests_dir = _this_dir.parent
_jira_fields_dir = _tests_dir.parent
_scripts_dir = _jira_fields_dir / 'scripts'
_shared_lib_dir = _jira_fields_dir.parent / 'shared' / 'scripts' / 'lib'

for path in [str(_shared_lib_dir), str(_scripts_dir)]:
    if path not in sys.path:
        sys.path.insert(0, path)

from create_field import create_field, FIELD_TYPES
from jira_assistant_skills_lib import JiraError, AuthenticationError
from assistant_skills_lib.error_handler import ValidationError


@pytest.mark.fields
@pytest.mark.unit
class TestCreateFieldBasic:
    """Test basic create_field functionality."""

    def test_create_text_field(self, mock_jira_client, sample_created_field):
        """Test creating a text field."""
        mock_jira_client.post.return_value = sample_created_field

        result = create_field(
            name='Test Field',
            field_type='text',
            client=mock_jira_client
        )

        assert result is not None
        assert result['name'] == 'Test Field'
        mock_jira_client.post.assert_called_once()
        call_args = mock_jira_client.post.call_args
        assert call_args[0][0] == '/rest/api/3/field'
        assert call_args[1]['data']['name'] == 'Test Field'

    def test_create_number_field(self, mock_jira_client, sample_created_field):
        """Test creating a number field."""
        mock_jira_client.post.return_value = sample_created_field

        result = create_field(
            name='Story Points',
            field_type='number',
            client=mock_jira_client
        )

        assert result is not None
        call_args = mock_jira_client.post.call_args
        assert call_args[1]['data']['type'] == FIELD_TYPES['number']['type']

    def test_create_select_field(self, mock_jira_client, sample_created_field):
        """Test creating a select field."""
        mock_jira_client.post.return_value = sample_created_field

        result = create_field(
            name='Priority Level',
            field_type='select',
            client=mock_jira_client
        )

        assert result is not None
        call_args = mock_jira_client.post.call_args
        assert call_args[1]['data']['type'] == FIELD_TYPES['select']['type']

    def test_create_field_with_description(self, mock_jira_client, sample_created_field):
        """Test creating a field with description."""
        mock_jira_client.post.return_value = sample_created_field

        result = create_field(
            name='Test Field',
            field_type='text',
            description='A test description',
            client=mock_jira_client
        )

        assert result is not None
        call_args = mock_jira_client.post.call_args
        assert call_args[1]['data']['description'] == 'A test description'


@pytest.mark.fields
@pytest.mark.unit
class TestCreateFieldAllTypes:
    """Test creating all supported field types."""

    @pytest.mark.parametrize('field_type', list(FIELD_TYPES.keys()))
    def test_create_all_field_types(self, mock_jira_client, sample_created_field, field_type):
        """Test creating each supported field type."""
        mock_jira_client.post.return_value = sample_created_field

        result = create_field(
            name=f'Test {field_type}',
            field_type=field_type,
            client=mock_jira_client
        )

        assert result is not None
        call_args = mock_jira_client.post.call_args
        assert call_args[1]['data']['type'] == FIELD_TYPES[field_type]['type']
        assert call_args[1]['data']['searcherKey'] == FIELD_TYPES[field_type]['searcher']


@pytest.mark.fields
@pytest.mark.unit
class TestCreateFieldValidation:
    """Test validation in create_field."""

    def test_invalid_field_type(self, mock_jira_client):
        """Test error on invalid field type."""
        with pytest.raises(ValidationError) as exc_info:
            create_field(
                name='Test Field',
                field_type='invalid_type',
                client=mock_jira_client
            )

        assert 'invalid field type' in str(exc_info.value).lower()
        mock_jira_client.post.assert_not_called()

    def test_validation_error_lists_valid_types(self, mock_jira_client):
        """Test that validation error lists valid types."""
        with pytest.raises(ValidationError) as exc_info:
            create_field(
                name='Test Field',
                field_type='bogus',
                client=mock_jira_client
            )

        error_message = str(exc_info.value).lower()
        # Should list at least some valid types
        assert 'text' in error_message or 'valid types' in error_message


@pytest.mark.fields
@pytest.mark.unit
class TestCreateFieldErrorHandling:
    """Test error handling in create_field."""

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 authentication error."""
        mock_jira_client.post.side_effect = AuthenticationError("Invalid token")

        with pytest.raises(AuthenticationError):
            create_field(name='Test', field_type='text', client=mock_jira_client)

    def test_permission_denied_error(self, mock_jira_client):
        """Test handling of 403 permission denied (requires admin)."""
        mock_jira_client.post.side_effect = JiraError("Admin permission required", status_code=403)

        with pytest.raises(JiraError) as exc_info:
            create_field(name='Test', field_type='text', client=mock_jira_client)
        assert exc_info.value.status_code == 403

    def test_duplicate_field_error(self, mock_jira_client):
        """Test handling of duplicate field name."""
        mock_jira_client.post.side_effect = JiraError("Field with this name already exists", status_code=400)

        with pytest.raises(JiraError) as exc_info:
            create_field(name='Existing Field', field_type='text', client=mock_jira_client)
        assert exc_info.value.status_code == 400

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        mock_jira_client.post.side_effect = JiraError("Rate limit exceeded", status_code=429)

        with pytest.raises(JiraError) as exc_info:
            create_field(name='Test', field_type='text', client=mock_jira_client)
        assert exc_info.value.status_code == 429

    def test_server_error(self, mock_jira_client):
        """Test handling of 500 server error."""
        mock_jira_client.post.side_effect = JiraError("Server error", status_code=500)

        with pytest.raises(JiraError) as exc_info:
            create_field(name='Test', field_type='text', client=mock_jira_client)
        assert exc_info.value.status_code == 500


@pytest.mark.fields
@pytest.mark.unit
class TestCreateFieldClientManagement:
    """Test client lifecycle management."""

    def test_closes_client_on_success(self, sample_created_field):
        """Test that client is closed after successful operation."""
        mock_client = MagicMock()
        mock_client.post.return_value = sample_created_field

        with patch('create_field.get_jira_client', return_value=mock_client):
            create_field(name='Test', field_type='text')

        mock_client.close.assert_called_once()

    def test_closes_client_on_error(self):
        """Test that client is closed even when operation fails."""
        mock_client = MagicMock()
        mock_client.post.side_effect = JiraError("Test error")

        with patch('create_field.get_jira_client', return_value=mock_client):
            with pytest.raises(JiraError):
                create_field(name='Test', field_type='text')

        mock_client.close.assert_called_once()

    def test_does_not_close_provided_client(self, mock_jira_client, sample_created_field):
        """Test that provided client is not closed."""
        mock_jira_client.post.return_value = sample_created_field

        create_field(name='Test', field_type='text', client=mock_jira_client)

        mock_jira_client.close.assert_not_called()
