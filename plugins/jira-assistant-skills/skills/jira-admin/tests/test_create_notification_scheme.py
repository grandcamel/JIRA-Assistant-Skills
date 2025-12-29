"""
Tests for create_notification_scheme.py - TDD approach.

Test cases per implementation plan:
1. test_create_minimal_scheme - Test creating scheme with minimal required fields
2. test_create_scheme_with_events - Test creating scheme with event configurations
3. test_validate_required_fields - Test validation of required fields (name)
4. test_validate_event_ids - Test validation of event IDs
5. test_validate_recipient_types - Test validation of notification types
6. test_format_text_output - Test human-readable success output
7. test_format_json_output - Test JSON output with created scheme details
8. test_template_file_support - Test creating from JSON template file
9. test_dry_run_mode - Test dry-run shows what would be created without creating
10. test_duplicate_name_error - Test error when scheme name already exists
"""

import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest

# Add scripts and shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))


class TestCreateMinimalScheme:
    """Test creating scheme with minimal required fields."""

    def test_create_minimal_scheme(self, mock_jira_client, sample_created_notification_scheme):
        """Test creating scheme with minimal required fields."""
        from create_notification_scheme import create_notification_scheme

        # Setup mock
        mock_jira_client.create_notification_scheme.return_value = sample_created_notification_scheme

        # Execute
        result = create_notification_scheme(
            client=mock_jira_client,
            name='New Project Notifications',
            description='Custom notifications for new project'
        )

        # Verify
        assert result['id'] == '10100'
        assert result['name'] == 'New Project Notifications'
        mock_jira_client.create_notification_scheme.assert_called_once()


class TestCreateSchemeWithEvents:
    """Test creating scheme with event configurations."""

    def test_create_scheme_with_events(self, mock_jira_client, sample_created_notification_scheme):
        """Test creating scheme with event configurations."""
        from create_notification_scheme import create_notification_scheme

        # Setup mock
        mock_jira_client.create_notification_scheme.return_value = sample_created_notification_scheme

        # Execute with events
        result = create_notification_scheme(
            client=mock_jira_client,
            name='Dev Team Notifications',
            description='Notifications for development team',
            events=[
                {
                    'event_id': '1',
                    'recipients': ['CurrentAssignee', 'Reporter', 'Group:developers']
                }
            ]
        )

        # Verify scheme was created
        assert result['id'] == '10100'

        # Verify API was called with correct event structure
        call_args = mock_jira_client.create_notification_scheme.call_args[0][0]
        assert 'notificationSchemeEvents' in call_args
        assert len(call_args['notificationSchemeEvents']) == 1


class TestValidateRequiredFields:
    """Test validation of required fields (name)."""

    def test_validate_required_fields(self, mock_jira_client):
        """Test validation of required fields (name)."""
        from create_notification_scheme import create_notification_scheme
        from error_handler import ValidationError

        # Execute without name
        with pytest.raises(ValidationError) as exc_info:
            create_notification_scheme(
                client=mock_jira_client,
                name='',  # Empty name
                description='Some description'
            )

        assert 'name' in str(exc_info.value).lower()

    def test_validate_name_whitespace(self, mock_jira_client):
        """Test that whitespace-only name is rejected."""
        from create_notification_scheme import create_notification_scheme
        from error_handler import ValidationError

        with pytest.raises(ValidationError):
            create_notification_scheme(
                client=mock_jira_client,
                name='   ',  # Whitespace only
                description='Some description'
            )


class TestValidateEventIds:
    """Test validation of event IDs."""

    def test_validate_event_ids(self, mock_jira_client, sample_created_notification_scheme):
        """Test validation of event IDs."""
        from create_notification_scheme import create_notification_scheme

        # Setup mock
        mock_jira_client.create_notification_scheme.return_value = sample_created_notification_scheme

        # Execute with valid event ID
        result = create_notification_scheme(
            client=mock_jira_client,
            name='Test Scheme',
            events=[
                {
                    'event_id': '1',  # Issue created
                    'recipients': ['CurrentAssignee']
                }
            ]
        )

        # Verify success
        assert result['id'] == '10100'

    def test_event_by_name(self, mock_jira_client, sample_created_notification_scheme):
        """Test specifying event by name instead of ID."""
        from create_notification_scheme import create_notification_scheme

        # Setup mock
        mock_jira_client.create_notification_scheme.return_value = sample_created_notification_scheme

        # Execute with event name
        result = create_notification_scheme(
            client=mock_jira_client,
            name='Test Scheme',
            events=[
                {
                    'event_name': 'Issue created',
                    'recipients': ['CurrentAssignee']
                }
            ]
        )

        # Verify event ID was resolved
        call_args = mock_jira_client.create_notification_scheme.call_args[0][0]
        events = call_args.get('notificationSchemeEvents', [])
        assert events[0]['event']['id'] == '1'


class TestValidateRecipientTypes:
    """Test validation of notification types."""

    def test_validate_recipient_types(self, mock_jira_client):
        """Test validation of notification types."""
        from create_notification_scheme import create_notification_scheme
        from error_handler import ValidationError

        # Execute with invalid recipient type
        with pytest.raises(ValidationError) as exc_info:
            create_notification_scheme(
                client=mock_jira_client,
                name='Test Scheme',
                events=[
                    {
                        'event_id': '1',
                        'recipients': ['InvalidType']
                    }
                ]
            )

        assert 'InvalidType' in str(exc_info.value)

    def test_validate_parameterized_recipients(self, mock_jira_client):
        """Test validation that Group/User/ProjectRole require parameters."""
        from create_notification_scheme import create_notification_scheme
        from error_handler import ValidationError

        # Execute with Group without parameter
        with pytest.raises(ValidationError) as exc_info:
            create_notification_scheme(
                client=mock_jira_client,
                name='Test Scheme',
                events=[
                    {
                        'event_id': '1',
                        'recipients': ['Group']  # Missing parameter
                    }
                ]
            )

        assert 'parameter' in str(exc_info.value).lower()


class TestFormatTextOutput:
    """Test human-readable success output."""

    def test_format_text_output(self, mock_jira_client, sample_created_notification_scheme):
        """Test human-readable success output."""
        from create_notification_scheme import create_notification_scheme, format_text_output

        # Setup mock
        mock_jira_client.create_notification_scheme.return_value = sample_created_notification_scheme

        # Execute
        result = create_notification_scheme(
            client=mock_jira_client,
            name='New Project Notifications'
        )
        output = format_text_output(result)

        # Verify output contains expected content
        assert '10100' in output
        assert 'New Project Notifications' in output
        assert 'Success' in output or 'Created' in output


class TestFormatJsonOutput:
    """Test JSON output with created scheme details."""

    def test_format_json_output(self, mock_jira_client, sample_created_notification_scheme):
        """Test JSON output with created scheme details."""
        from create_notification_scheme import create_notification_scheme, format_json_output

        # Setup mock
        mock_jira_client.create_notification_scheme.return_value = sample_created_notification_scheme

        # Execute
        result = create_notification_scheme(
            client=mock_jira_client,
            name='New Project Notifications'
        )
        output = format_json_output(result)

        # Verify valid JSON
        parsed = json.loads(output)
        assert parsed['id'] == '10100'


class TestTemplateFileSupport:
    """Test creating from JSON template file."""

    def test_template_file_support(self, mock_jira_client, sample_created_notification_scheme):
        """Test creating from JSON template file."""
        from create_notification_scheme import create_notification_scheme

        # Setup mock
        mock_jira_client.create_notification_scheme.return_value = sample_created_notification_scheme

        # Create temporary template file
        template_data = {
            'name': 'Template Scheme',
            'description': 'Created from template',
            'notificationSchemeEvents': [
                {
                    'event': {'id': '1'},
                    'notifications': [
                        {'notificationType': 'CurrentAssignee'},
                        {'notificationType': 'Reporter'}
                    ]
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(template_data, f)
            template_path = f.name

        try:
            # Execute with template
            result = create_notification_scheme(
                client=mock_jira_client,
                template_file=template_path
            )

            # Verify scheme was created
            assert result['id'] == '10100'

            # Verify API was called with template data
            call_args = mock_jira_client.create_notification_scheme.call_args[0][0]
            assert call_args['name'] == 'Template Scheme'
        finally:
            Path(template_path).unlink()


class TestDryRunMode:
    """Test dry-run shows what would be created without creating."""

    def test_dry_run_mode(self, mock_jira_client):
        """Test dry-run shows what would be created without creating."""
        from create_notification_scheme import create_notification_scheme

        # Execute with dry_run=True
        result = create_notification_scheme(
            client=mock_jira_client,
            name='Test Scheme',
            description='Test description',
            dry_run=True
        )

        # Verify API was NOT called
        mock_jira_client.create_notification_scheme.assert_not_called()

        # Verify result indicates dry run
        assert result['dry_run'] is True
        assert result['would_create']['name'] == 'Test Scheme'


class TestDuplicateNameError:
    """Test error when scheme name already exists."""

    def test_duplicate_name_error(self, mock_jira_client, sample_notification_schemes):
        """Test error when scheme name already exists."""
        from create_notification_scheme import create_notification_scheme
        from error_handler import ConflictError

        # Setup mock to indicate scheme already exists
        mock_jira_client.lookup_notification_scheme_by_name.return_value = {
            'id': '10000',
            'name': 'Default Notification Scheme'
        }

        # Execute
        with pytest.raises(ConflictError) as exc_info:
            create_notification_scheme(
                client=mock_jira_client,
                name='Default Notification Scheme',
                check_duplicate=True
            )

        assert 'already exists' in str(exc_info.value).lower()
