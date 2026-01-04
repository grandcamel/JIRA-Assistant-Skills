"""
Unit tests for remove_user_from_group.py script.

Tests cover:
- Removing user by account ID
- Removing user by email (with lookup)
- Idempotent operation (removing non-member)
- Confirmation requirement
- Dry-run mode
- Permission error handling
"""

import pytest
import sys
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

# Add scripts path
scripts_path = str(Path(__file__).parent.parent.parent / 'scripts')
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


class TestRemoveUserByAccountId:
    """Tests for removing user by account ID."""

    def test_remove_user_by_account_id_success(self, mock_jira_client):
        """Test removing user from group by account ID."""
        mock_jira_client.remove_user_from_group.return_value = None

        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from remove_user_from_group import remove_user_from_group
            remove_user_from_group(
                mock_jira_client,
                account_id="5b10ac8d82e05b22cc7d4ef5",
                group_name="jira-developers",
                confirmed=True
            )

        mock_jira_client.remove_user_from_group.assert_called_once_with(
            account_id="5b10ac8d82e05b22cc7d4ef5",
            group_name="jira-developers",
            group_id=None
        )


class TestRemoveUserByEmail:
    """Tests for removing user by email with lookup."""

    def test_remove_user_by_email_success(self, mock_jira_client, sample_user):
        """Test removing user from group by email lookup."""
        mock_jira_client.search_users.return_value = [sample_user]
        mock_jira_client.remove_user_from_group.return_value = None

        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from remove_user_from_group import remove_user_by_email
            remove_user_by_email(
                mock_jira_client,
                email="john.doe@example.com",
                group_name="jira-developers",
                confirmed=True
            )

        # Should have looked up user first
        mock_jira_client.search_users.assert_called_once()
        mock_jira_client.remove_user_from_group.assert_called_once()

    def test_remove_user_by_email_not_found(self, mock_jira_client):
        """Test error when email lookup returns no results."""
        mock_jira_client.search_users.return_value = []

        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from remove_user_from_group import remove_user_by_email
            from jira_assistant_skills_lib import NotFoundError

            with pytest.raises(NotFoundError) as exc_info:
                remove_user_by_email(
                    mock_jira_client,
                    email="nonexistent@example.com",
                    group_name="jira-developers",
                    confirmed=True
                )

        assert "user" in str(exc_info.value).lower()


class TestRemoveUserIdempotent:
    """Tests for idempotent behavior."""

    def test_remove_user_not_member_succeeds(self, mock_jira_client):
        """Test that removing user not in group succeeds (idempotent)."""
        # JIRA API returns success even if user is not a member
        mock_jira_client.remove_user_from_group.return_value = None

        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from remove_user_from_group import remove_user_from_group
            # Should not raise
            remove_user_from_group(
                mock_jira_client,
                account_id="5b10ac8d82e05b22cc7d4ef5",
                group_name="jira-developers",
                confirmed=True
            )


class TestRemoveUserConfirmation:
    """Tests for confirmation requirement."""

    def test_remove_user_requires_confirmation(self, mock_jira_client):
        """Test that removal requires confirmation."""
        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from remove_user_from_group import remove_user_from_group
            from assistant_skills_lib.error_handler import ValidationError

            with pytest.raises(ValidationError) as exc_info:
                remove_user_from_group(
                    mock_jira_client,
                    account_id="5b10ac8d82e05b22cc7d4ef5",
                    group_name="jira-developers",
                    confirmed=False
                )

        assert "confirm" in str(exc_info.value).lower()

    def test_remove_user_confirmed_proceeds(self, mock_jira_client):
        """Test that confirmed removal proceeds."""
        mock_jira_client.remove_user_from_group.return_value = None

        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from remove_user_from_group import remove_user_from_group
            remove_user_from_group(
                mock_jira_client,
                account_id="5b10ac8d82e05b22cc7d4ef5",
                group_name="jira-developers",
                confirmed=True
            )

        mock_jira_client.remove_user_from_group.assert_called_once()


class TestRemoveUserDryRun:
    """Tests for dry-run mode."""

    def test_remove_user_dry_run_no_api_call(self, mock_jira_client):
        """Test that dry-run mode does not make API call."""
        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from remove_user_from_group import remove_user_from_group
            remove_user_from_group(
                mock_jira_client,
                account_id="5b10ac8d82e05b22cc7d4ef5",
                group_name="jira-developers",
                dry_run=True
            )

        mock_jira_client.remove_user_from_group.assert_not_called()

    def test_remove_user_dry_run_preview(self, mock_jira_client):
        """Test that dry-run shows preview message."""
        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from remove_user_from_group import format_dry_run_preview
            preview = format_dry_run_preview(
                account_id="5b10ac8d82e05b22cc7d4ef5",
                group_name="jira-developers"
            )

        assert "jira-developers" in preview
        assert "dry run" in preview.lower()


class TestRemoveUserPermissionError:
    """Tests for permission error handling."""

    def test_remove_user_permission_denied(self, mock_jira_client):
        """Test handling insufficient permissions error."""
        from jira_assistant_skills_lib import PermissionError
        mock_jira_client.remove_user_from_group.side_effect = PermissionError(
            "Site administration permission required"
        )

        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from remove_user_from_group import remove_user_from_group

            with pytest.raises(PermissionError) as exc_info:
                remove_user_from_group(
                    mock_jira_client,
                    account_id="5b10ac8d82e05b22cc7d4ef5",
                    group_name="jira-developers",
                    confirmed=True
                )

        assert "permission" in str(exc_info.value).lower()


class TestRemoveUserGroupById:
    """Tests for removing user from group by group ID."""

    def test_remove_user_by_group_id(self, mock_jira_client):
        """Test removing user from group by group ID."""
        mock_jira_client.remove_user_from_group.return_value = None

        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from remove_user_from_group import remove_user_from_group
            remove_user_from_group(
                mock_jira_client,
                account_id="5b10ac8d82e05b22cc7d4ef5",
                group_id="276f955c-63d7-42c8-9520-92d01dca0625",
                confirmed=True
            )

        call_args = mock_jira_client.remove_user_from_group.call_args
        assert call_args[1].get('group_id') == "276f955c-63d7-42c8-9520-92d01dca0625"
