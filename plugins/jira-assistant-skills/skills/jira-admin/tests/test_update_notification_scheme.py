"""
Tests for update_notification_scheme.py - TDD approach.

Test cases per implementation plan:
1. test_update_scheme_name - Test updating scheme name
2. test_update_scheme_description - Test updating scheme description
3. test_update_both_fields - Test updating both name and description
4. test_validate_scheme_exists - Test error when scheme doesn't exist
5. test_format_text_output - Test human-readable success output
6. test_format_json_output - Test JSON output with updated scheme details
7. test_dry_run_mode - Test dry-run shows changes without applying
8. test_no_changes_error - Test error when no changes provided
"""

import sys
import json
from pathlib import Path
from unittest.mock import patch
import pytest

# Add scripts and shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


class TestUpdateSchemeName:
    """Test updating scheme name."""

    def test_update_scheme_name(self, mock_jira_client, sample_notification_scheme_detail):
        """Test updating scheme name."""
        from update_notification_scheme import update_notification_scheme

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = sample_notification_scheme_detail
        mock_jira_client.update_notification_scheme.return_value = {}

        # Execute
        result = update_notification_scheme(
            client=mock_jira_client,
            scheme_id='10000',
            name='Updated Scheme Name'
        )

        # Verify
        assert result['success'] is True
        mock_jira_client.update_notification_scheme.assert_called_once()
        call_args = mock_jira_client.update_notification_scheme.call_args
        assert call_args[0][0] == '10000'
        assert call_args[0][1]['name'] == 'Updated Scheme Name'


class TestUpdateSchemeDescription:
    """Test updating scheme description."""

    def test_update_scheme_description(self, mock_jira_client, sample_notification_scheme_detail):
        """Test updating scheme description."""
        from update_notification_scheme import update_notification_scheme

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = sample_notification_scheme_detail
        mock_jira_client.update_notification_scheme.return_value = {}

        # Execute
        result = update_notification_scheme(
            client=mock_jira_client,
            scheme_id='10000',
            description='New description text'
        )

        # Verify
        assert result['success'] is True
        call_args = mock_jira_client.update_notification_scheme.call_args
        assert call_args[0][1]['description'] == 'New description text'


class TestUpdateBothFields:
    """Test updating both name and description."""

    def test_update_both_fields(self, mock_jira_client, sample_notification_scheme_detail):
        """Test updating both name and description."""
        from update_notification_scheme import update_notification_scheme

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = sample_notification_scheme_detail
        mock_jira_client.update_notification_scheme.return_value = {}

        # Execute
        result = update_notification_scheme(
            client=mock_jira_client,
            scheme_id='10000',
            name='New Name',
            description='New Description'
        )

        # Verify both fields were included
        assert result['success'] is True
        call_args = mock_jira_client.update_notification_scheme.call_args
        assert call_args[0][1]['name'] == 'New Name'
        assert call_args[0][1]['description'] == 'New Description'


class TestValidateSchemeExists:
    """Test error when scheme doesn't exist."""

    def test_validate_scheme_exists(self, mock_jira_client):
        """Test error when scheme doesn't exist."""
        from update_notification_scheme import update_notification_scheme
        from jira_assistant_skills_lib import NotFoundError

        # Setup mock to raise NotFoundError
        mock_jira_client.get_notification_scheme.side_effect = NotFoundError(
            resource_type="Notification scheme",
            resource_id="99999"
        )

        # Execute and verify exception
        with pytest.raises(NotFoundError):
            update_notification_scheme(
                client=mock_jira_client,
                scheme_id='99999',
                name='New Name'
            )


class TestFormatTextOutput:
    """Test human-readable success output."""

    def test_format_text_output(self, mock_jira_client, sample_notification_scheme_detail):
        """Test human-readable success output."""
        from update_notification_scheme import update_notification_scheme, format_text_output

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = sample_notification_scheme_detail
        mock_jira_client.update_notification_scheme.return_value = {}

        # Execute
        result = update_notification_scheme(
            client=mock_jira_client,
            scheme_id='10000',
            name='Production Notifications',
            description='Notifications for production projects'
        )
        output = format_text_output(result)

        # Verify output contains expected content
        assert '10000' in output
        assert 'Production Notifications' in output or 'updated' in output.lower()


class TestFormatJsonOutput:
    """Test JSON output with updated scheme details."""

    def test_format_json_output(self, mock_jira_client, sample_notification_scheme_detail):
        """Test JSON output with updated scheme details."""
        from update_notification_scheme import update_notification_scheme, format_json_output

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = sample_notification_scheme_detail
        mock_jira_client.update_notification_scheme.return_value = {}

        # Execute
        result = update_notification_scheme(
            client=mock_jira_client,
            scheme_id='10000',
            name='Updated Name'
        )
        output = format_json_output(result)

        # Verify valid JSON
        parsed = json.loads(output)
        assert parsed['success'] is True
        assert 'scheme_id' in parsed


class TestDryRunMode:
    """Test dry-run shows changes without applying."""

    def test_dry_run_mode(self, mock_jira_client, sample_notification_scheme_detail):
        """Test dry-run shows changes without applying."""
        from update_notification_scheme import update_notification_scheme

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = sample_notification_scheme_detail

        # Execute with dry_run=True
        result = update_notification_scheme(
            client=mock_jira_client,
            scheme_id='10000',
            name='New Name',
            dry_run=True
        )

        # Verify API was NOT called
        mock_jira_client.update_notification_scheme.assert_not_called()

        # Verify result shows what would change
        assert result['dry_run'] is True
        assert 'changes' in result
        assert 'name' in result['changes']

    def test_dry_run_shows_before_after(self, mock_jira_client, sample_notification_scheme_detail):
        """Test dry-run shows before and after values."""
        from update_notification_scheme import update_notification_scheme, format_text_output

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = sample_notification_scheme_detail

        # Execute with dry_run
        result = update_notification_scheme(
            client=mock_jira_client,
            scheme_id='10000',
            name='New Name',
            dry_run=True
        )
        output = format_text_output(result)

        # Verify before/after in output
        assert 'Default Notification Scheme' in output  # Before
        assert 'New Name' in output  # After


class TestNoChangesError:
    """Test error when no changes provided."""

    def test_no_changes_error(self, mock_jira_client, sample_notification_scheme_detail):
        """Test error when no changes provided."""
        from update_notification_scheme import update_notification_scheme
        from assistant_skills_lib.error_handler import ValidationError

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = sample_notification_scheme_detail

        # Execute without any changes
        with pytest.raises(ValidationError) as exc_info:
            update_notification_scheme(
                client=mock_jira_client,
                scheme_id='10000'
                # No name or description provided
            )

        assert 'change' in str(exc_info.value).lower()
