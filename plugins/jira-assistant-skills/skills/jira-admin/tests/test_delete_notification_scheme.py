"""
Tests for delete_notification_scheme.py - TDD approach.

Test cases per implementation plan:
1. test_delete_scheme - Test deleting notification scheme
2. test_confirm_before_delete - Test confirmation prompt before deletion
3. test_force_delete_no_confirm - Test --force flag bypasses confirmation
4. test_validate_scheme_exists - Test error when scheme doesn't exist
5. test_prevent_delete_in_use - Test preventing deletion of schemes in use by projects
6. test_format_text_output - Test human-readable success output
7. test_dry_run_mode - Test dry-run shows what would be deleted
"""

import sys
from pathlib import Path
from unittest.mock import patch
import pytest

# Add scripts and shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


class TestDeleteScheme:
    """Test deleting notification scheme."""

    def test_delete_scheme(self, mock_jira_client, sample_notification_scheme_detail):
        """Test deleting notification scheme."""
        from delete_notification_scheme import delete_notification_scheme

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = sample_notification_scheme_detail
        mock_jira_client.get_notification_scheme_projects.return_value = {
            'values': [],
            'total': 0
        }
        mock_jira_client.delete_notification_scheme.return_value = None

        # Execute with force=True to bypass confirmation
        result = delete_notification_scheme(
            client=mock_jira_client,
            scheme_id='10000',
            force=True
        )

        # Verify
        assert result['success'] is True
        mock_jira_client.delete_notification_scheme.assert_called_once_with('10000')


class TestConfirmBeforeDelete:
    """Test confirmation prompt before deletion."""

    def test_confirm_before_delete(self, mock_jira_client, sample_notification_scheme_detail):
        """Test confirmation prompt before deletion."""
        from delete_notification_scheme import delete_notification_scheme
        from error_handler import ValidationError

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = sample_notification_scheme_detail
        mock_jira_client.get_notification_scheme_projects.return_value = {
            'values': [],
            'total': 0
        }

        # Execute without force should raise if not confirmed
        with pytest.raises(ValidationError) as exc_info:
            delete_notification_scheme(
                client=mock_jira_client,
                scheme_id='10000',
                force=False,
                confirmed=False
            )

        assert 'confirm' in str(exc_info.value).lower()


class TestForceDeleteNoConfirm:
    """Test --force flag bypasses confirmation."""

    def test_force_delete_no_confirm(self, mock_jira_client, sample_notification_scheme_detail):
        """Test --force flag bypasses confirmation."""
        from delete_notification_scheme import delete_notification_scheme

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = sample_notification_scheme_detail
        mock_jira_client.get_notification_scheme_projects.return_value = {
            'values': [],
            'total': 0
        }
        mock_jira_client.delete_notification_scheme.return_value = None

        # Execute with force=True
        result = delete_notification_scheme(
            client=mock_jira_client,
            scheme_id='10000',
            force=True
        )

        # Verify deletion proceeded
        assert result['success'] is True
        mock_jira_client.delete_notification_scheme.assert_called_once()


class TestValidateSchemeExists:
    """Test error when scheme doesn't exist."""

    def test_validate_scheme_exists(self, mock_jira_client):
        """Test error when scheme doesn't exist."""
        from delete_notification_scheme import delete_notification_scheme
        from error_handler import NotFoundError

        # Setup mock to raise NotFoundError
        mock_jira_client.get_notification_scheme.side_effect = NotFoundError(
            resource_type="Notification scheme",
            resource_id="99999"
        )

        # Execute and verify exception
        with pytest.raises(NotFoundError):
            delete_notification_scheme(
                client=mock_jira_client,
                scheme_id='99999',
                force=True
            )


class TestPreventDeleteInUse:
    """Test preventing deletion of schemes in use by projects."""

    def test_prevent_delete_in_use(self, mock_jira_client, sample_notification_scheme_detail, sample_project_mappings):
        """Test preventing deletion of schemes in use by projects."""
        from delete_notification_scheme import delete_notification_scheme
        from error_handler import ValidationError

        # Setup mock - scheme is in use by projects
        mock_jira_client.get_notification_scheme.return_value = sample_notification_scheme_detail
        mock_jira_client.get_notification_scheme_projects.return_value = sample_project_mappings

        # Execute - should fail because scheme is in use
        with pytest.raises(ValidationError) as exc_info:
            delete_notification_scheme(
                client=mock_jira_client,
                scheme_id='10000',
                force=True
            )

        assert 'in use' in str(exc_info.value).lower()


class TestFormatTextOutput:
    """Test human-readable success output."""

    def test_format_text_output(self, mock_jira_client, sample_notification_scheme_detail):
        """Test human-readable success output."""
        from delete_notification_scheme import delete_notification_scheme, format_text_output

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = sample_notification_scheme_detail
        mock_jira_client.get_notification_scheme_projects.return_value = {
            'values': [],
            'total': 0
        }
        mock_jira_client.delete_notification_scheme.return_value = None

        # Execute
        result = delete_notification_scheme(
            client=mock_jira_client,
            scheme_id='10000',
            force=True
        )
        output = format_text_output(result)

        # Verify output contains expected content
        assert '10000' in output
        assert 'deleted' in output.lower() or 'success' in output.lower()


class TestDryRunMode:
    """Test dry-run shows what would be deleted."""

    def test_dry_run_mode(self, mock_jira_client, sample_notification_scheme_detail):
        """Test dry-run shows what would be deleted."""
        from delete_notification_scheme import delete_notification_scheme

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = sample_notification_scheme_detail
        mock_jira_client.get_notification_scheme_projects.return_value = {
            'values': [],
            'total': 0
        }

        # Execute with dry_run=True
        result = delete_notification_scheme(
            client=mock_jira_client,
            scheme_id='10000',
            dry_run=True
        )

        # Verify API was NOT called
        mock_jira_client.delete_notification_scheme.assert_not_called()

        # Verify result indicates dry run
        assert result['dry_run'] is True
        assert 'scheme_name' in result


class TestFormatJsonOutput:
    """Test JSON output formatting."""

    def test_format_json_output(self, mock_jira_client, sample_notification_scheme_detail):
        """Test JSON output is valid and contains expected fields."""
        import json
        from delete_notification_scheme import delete_notification_scheme, format_json_output

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = sample_notification_scheme_detail
        mock_jira_client.get_notification_scheme_projects.return_value = {
            'values': [],
            'total': 0
        }
        mock_jira_client.delete_notification_scheme.return_value = None

        # Execute
        result = delete_notification_scheme(
            client=mock_jira_client,
            scheme_id='10000',
            force=True
        )
        output = format_json_output(result)

        # Verify output is valid JSON with expected fields
        parsed = json.loads(output)
        assert parsed['success'] is True
        assert parsed['scheme_id'] == '10000'

    def test_format_json_output_dry_run(self, mock_jira_client, sample_notification_scheme_detail):
        """Test JSON output for dry-run mode."""
        import json
        from delete_notification_scheme import delete_notification_scheme, format_json_output

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = sample_notification_scheme_detail
        mock_jira_client.get_notification_scheme_projects.return_value = {
            'values': [],
            'total': 0
        }

        # Execute with dry_run=True
        result = delete_notification_scheme(
            client=mock_jira_client,
            scheme_id='10000',
            dry_run=True
        )
        output = format_json_output(result)

        # Verify output is valid JSON with dry_run indicator
        parsed = json.loads(output)
        assert parsed['dry_run'] is True
        assert parsed['scheme_id'] == '10000'
        assert 'scheme_name' in parsed
