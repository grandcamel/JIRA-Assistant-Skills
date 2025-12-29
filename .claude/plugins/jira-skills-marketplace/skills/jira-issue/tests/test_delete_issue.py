"""
Unit tests for delete_issue.py script.

Tests cover:
- Deleting an issue with force flag
- Deleting an issue with confirmation
- Confirmation prompts (cancelled, accepted)
- Validation errors (invalid issue key)
- Not found errors
- Permission errors
- Authentication errors
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch
from copy import deepcopy

# Add scripts path
scripts_path = str(Path(__file__).parent.parent / 'scripts')
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

# Import after path setup
import delete_issue as delete_issue_module


@pytest.mark.unit
class TestDeleteIssueForce:
    """Tests for deleting issues with force flag."""

    def test_delete_issue_force_success(self, mock_jira_client):
        """Test deleting an issue with force flag."""
        mock_jira_client.delete_issue.return_value = None

        with patch.object(delete_issue_module, 'get_jira_client', return_value=mock_jira_client):
            delete_issue_module.delete_issue(
                issue_key="PROJ-123",
                force=True
            )

        mock_jira_client.delete_issue.assert_called_once_with("PROJ-123")

    def test_delete_issue_force_normalizes_key(self, mock_jira_client):
        """Test that issue key is normalized to uppercase."""
        mock_jira_client.delete_issue.return_value = None

        with patch.object(delete_issue_module, 'get_jira_client', return_value=mock_jira_client):
            delete_issue_module.delete_issue(
                issue_key="proj-123",
                force=True
            )

        mock_jira_client.delete_issue.assert_called_once_with("PROJ-123")

    def test_delete_issue_force_no_confirmation(self, mock_jira_client):
        """Test that force flag skips confirmation prompt."""
        mock_jira_client.delete_issue.return_value = None

        with patch.object(delete_issue_module, 'get_jira_client', return_value=mock_jira_client):
            with patch('builtins.input') as mock_input:
                delete_issue_module.delete_issue(
                    issue_key="PROJ-123",
                    force=True
                )

        # input should not be called when force=True
        mock_input.assert_not_called()


@pytest.mark.unit
class TestDeleteIssueConfirmation:
    """Tests for deleting issues with confirmation."""

    def test_delete_issue_confirmation_yes(self, mock_jira_client, sample_issue):
        """Test deleting issue with 'yes' confirmation."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)
        mock_jira_client.delete_issue.return_value = None

        with patch.object(delete_issue_module, 'get_jira_client', return_value=mock_jira_client):
            with patch('builtins.input', return_value='yes'):
                delete_issue_module.delete_issue(
                    issue_key="PROJ-123",
                    force=False
                )

        mock_jira_client.delete_issue.assert_called_once_with("PROJ-123")

    def test_delete_issue_confirmation_y(self, mock_jira_client, sample_issue):
        """Test deleting issue with 'y' confirmation."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)
        mock_jira_client.delete_issue.return_value = None

        with patch.object(delete_issue_module, 'get_jira_client', return_value=mock_jira_client):
            with patch('builtins.input', return_value='y'):
                delete_issue_module.delete_issue(
                    issue_key="PROJ-123",
                    force=False
                )

        mock_jira_client.delete_issue.assert_called_once_with("PROJ-123")

    def test_delete_issue_confirmation_cancelled_no(self, mock_jira_client, sample_issue):
        """Test that 'no' cancels deletion."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)

        with patch.object(delete_issue_module, 'get_jira_client', return_value=mock_jira_client):
            with patch('builtins.input', return_value='no'):
                delete_issue_module.delete_issue(
                    issue_key="PROJ-123",
                    force=False
                )

        mock_jira_client.delete_issue.assert_not_called()

    def test_delete_issue_confirmation_cancelled_empty(self, mock_jira_client, sample_issue):
        """Test that empty input cancels deletion."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)

        with patch.object(delete_issue_module, 'get_jira_client', return_value=mock_jira_client):
            with patch('builtins.input', return_value=''):
                delete_issue_module.delete_issue(
                    issue_key="PROJ-123",
                    force=False
                )

        mock_jira_client.delete_issue.assert_not_called()

    def test_delete_issue_shows_issue_details(self, mock_jira_client, sample_issue, capsys):
        """Test that confirmation shows issue details."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)

        with patch.object(delete_issue_module, 'get_jira_client', return_value=mock_jira_client):
            with patch('builtins.input', return_value='no'):
                delete_issue_module.delete_issue(
                    issue_key="PROJ-123",
                    force=False
                )

        captured = capsys.readouterr()
        assert "PROJ-123" in captured.out
        assert "Bug" in captured.out
        assert "Test Issue Summary" in captured.out


@pytest.mark.unit
class TestDeleteIssueConfirmationIssueNotFound:
    """Tests for confirmation when issue details cannot be retrieved."""

    def test_delete_issue_confirmation_issue_not_found_confirms(self, mock_jira_client):
        """Test deletion proceeds with confirmation even if issue details fail."""
        from error_handler import JiraError
        mock_jira_client.get_issue.side_effect = JiraError("Cannot get issue details")
        mock_jira_client.delete_issue.return_value = None

        with patch.object(delete_issue_module, 'get_jira_client', return_value=mock_jira_client):
            with patch('builtins.input', return_value='yes'):
                delete_issue_module.delete_issue(
                    issue_key="PROJ-999",
                    force=False
                )

        mock_jira_client.delete_issue.assert_called_once_with("PROJ-999")


@pytest.mark.unit
class TestDeleteIssueValidation:
    """Tests for input validation."""

    def test_delete_issue_invalid_key_raises_error(self, mock_jira_client):
        """Test that invalid issue key raises ValidationError."""
        from error_handler import ValidationError

        with patch.object(delete_issue_module, 'get_jira_client', return_value=mock_jira_client):
            with pytest.raises(ValidationError):
                delete_issue_module.delete_issue(
                    issue_key="invalid-key",
                    force=True
                )

    def test_delete_issue_empty_key_raises_error(self, mock_jira_client):
        """Test that empty issue key raises ValidationError."""
        from error_handler import ValidationError

        with patch.object(delete_issue_module, 'get_jira_client', return_value=mock_jira_client):
            with pytest.raises(ValidationError):
                delete_issue_module.delete_issue(
                    issue_key="",
                    force=True
                )

    def test_delete_issue_key_with_spaces_raises_error(self, mock_jira_client):
        """Test that issue key with spaces raises ValidationError."""
        from error_handler import ValidationError

        with patch.object(delete_issue_module, 'get_jira_client', return_value=mock_jira_client):
            with pytest.raises(ValidationError):
                delete_issue_module.delete_issue(
                    issue_key="PROJ 123",
                    force=True
                )


@pytest.mark.unit
class TestDeleteIssueErrors:
    """Tests for error handling."""

    def test_delete_issue_not_found(self, mock_jira_client):
        """Test handling issue not found error."""
        from error_handler import NotFoundError
        mock_jira_client.delete_issue.side_effect = NotFoundError(
            "Issue", "PROJ-999"
        )

        with patch.object(delete_issue_module, 'get_jira_client', return_value=mock_jira_client):
            with pytest.raises(NotFoundError) as exc_info:
                delete_issue_module.delete_issue(
                    issue_key="PROJ-999",
                    force=True
                )

        assert "not found" in str(exc_info.value).lower()

    def test_delete_issue_permission_denied(self, mock_jira_client):
        """Test handling permission denied error."""
        from error_handler import PermissionError
        mock_jira_client.delete_issue.side_effect = PermissionError(
            "You do not have permission to delete this issue"
        )

        with patch.object(delete_issue_module, 'get_jira_client', return_value=mock_jira_client):
            with pytest.raises(PermissionError) as exc_info:
                delete_issue_module.delete_issue(
                    issue_key="PROJ-123",
                    force=True
                )

        assert "permission" in str(exc_info.value).lower()

    def test_delete_issue_authentication_error(self, mock_jira_client):
        """Test handling authentication error."""
        from error_handler import AuthenticationError
        mock_jira_client.delete_issue.side_effect = AuthenticationError(
            "Authentication failed"
        )

        with patch.object(delete_issue_module, 'get_jira_client', return_value=mock_jira_client):
            with pytest.raises(AuthenticationError):
                delete_issue_module.delete_issue(
                    issue_key="PROJ-123",
                    force=True
                )


@pytest.mark.unit
class TestDeleteIssueProfile:
    """Tests for profile handling."""

    def test_delete_issue_with_profile(self, mock_jira_client):
        """Test deleting issue with specific profile."""
        mock_jira_client.delete_issue.return_value = None

        with patch.object(delete_issue_module, 'get_jira_client', return_value=mock_jira_client) as mock_get_client:
            delete_issue_module.delete_issue(
                issue_key="PROJ-123",
                force=True,
                profile="development"
            )

        mock_get_client.assert_called_with("development")


@pytest.mark.unit
class TestDeleteIssueCleanup:
    """Tests for client cleanup."""

    def test_delete_issue_closes_client_on_success(self, mock_jira_client):
        """Test that client is closed after successful deletion."""
        mock_jira_client.delete_issue.return_value = None

        with patch.object(delete_issue_module, 'get_jira_client', return_value=mock_jira_client):
            delete_issue_module.delete_issue(
                issue_key="PROJ-123",
                force=True
            )

        mock_jira_client.close.assert_called()

    def test_delete_issue_closes_client_on_cancellation(self, mock_jira_client, sample_issue):
        """Test that client is closed when deletion is cancelled."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)

        with patch.object(delete_issue_module, 'get_jira_client', return_value=mock_jira_client):
            with patch('builtins.input', return_value='no'):
                delete_issue_module.delete_issue(
                    issue_key="PROJ-123",
                    force=False
                )

        mock_jira_client.close.assert_called()
