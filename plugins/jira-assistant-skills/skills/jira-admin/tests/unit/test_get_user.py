"""
Unit tests for get_user.py script.

Tests cover:
- Getting user by accountId
- Getting user by email
- Getting current user (/myself)
- Including groups and application roles
- Privacy-restricted fields handling
- Inactive user display
- Unknown/deleted user handling
- Output formats
- Error handling
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


class TestGetUserByAccountId:
    """Tests for getting user by accountId."""

    def test_get_user_by_account_id_returns_user(self, mock_jira_client, sample_user):
        """Test getting user details by accountId."""
        mock_jira_client.get_user.return_value = sample_user

        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from get_user import get_user_by_id
            result = get_user_by_id(mock_jira_client, account_id="5b10ac8d82e05b22cc7d4ef5")

        mock_jira_client.get_user.assert_called_once()
        assert result['accountId'] == "5b10ac8d82e05b22cc7d4ef5"
        assert result['displayName'] == "John Doe"


class TestGetUserByEmail:
    """Tests for getting user by email address."""

    def test_get_user_by_email_returns_user(self, mock_jira_client, sample_user):
        """Test getting user by email address."""
        mock_jira_client.get_user.return_value = sample_user

        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from get_user import get_user_by_email
            result = get_user_by_email(mock_jira_client, email="john.doe@example.com")

        assert result['emailAddress'] == "john.doe@example.com"


class TestGetCurrentUser:
    """Tests for getting current authenticated user."""

    def test_get_current_user_calls_myself(self, mock_jira_client, sample_user):
        """Test getting current user calls /myself endpoint."""
        mock_jira_client.get_current_user.return_value = sample_user

        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from get_user import get_current_user
            result = get_current_user(mock_jira_client)

        mock_jira_client.get_current_user.assert_called_once()
        assert result['accountId'] == sample_user['accountId']


class TestGetUserWithGroups:
    """Tests for including group membership."""

    def test_get_user_with_groups_includes_groups(self, mock_jira_client, sample_user_with_groups):
        """Test including group membership in user details."""
        mock_jira_client.get_user.return_value = sample_user_with_groups

        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from get_user import get_user_by_id
            result = get_user_by_id(mock_jira_client, account_id="5b10ac8d82e05b22cc7d4ef5",
                                    expand=['groups'])

        assert 'groups' in result
        assert result['groups']['size'] == 3


class TestGetUserWithApplicationRoles:
    """Tests for including application roles."""

    def test_get_user_with_roles_includes_roles(self, mock_jira_client, sample_user_with_groups):
        """Test including application roles in user details."""
        mock_jira_client.get_user.return_value = sample_user_with_groups

        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from get_user import get_user_by_id
            result = get_user_by_id(mock_jira_client, account_id="5b10ac8d82e05b22cc7d4ef5",
                                    expand=['applicationRoles'])

        assert 'applicationRoles' in result


class TestGetUserTextFormat:
    """Tests for formatted user details output."""

    def test_format_user_text_shows_details(self, mock_jira_client, sample_user):
        """Test formatted user profile output."""
        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from get_user import format_user_text
            output = format_user_text(sample_user)

        assert 'John Doe' in output
        assert 'john.doe@example.com' in output
        assert 'Active' in output


class TestGetUserJsonOutput:
    """Tests for JSON output format."""

    def test_format_user_json_complete(self, mock_jira_client, sample_user):
        """Test JSON output returns complete user object."""
        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from get_user import format_user_json
            output = format_user_json(sample_user)

        parsed = json.loads(output)
        assert parsed['accountId'] == sample_user['accountId']
        assert parsed['displayName'] == sample_user['displayName']


class TestGetUserNotFound:
    """Tests for user not found error handling."""

    def test_get_user_not_found_raises_error(self, mock_jira_client):
        """Test handling user not found error."""
        from error_handler import NotFoundError
        mock_jira_client.get_user.side_effect = NotFoundError("User", "unknown-id")

        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from get_user import get_user_by_id

            with pytest.raises(NotFoundError):
                get_user_by_id(mock_jira_client, account_id="unknown-id")


class TestGetUserPrivacyRestricted:
    """Tests for privacy-restricted profile handling."""

    def test_format_user_privacy_restricted(self, mock_jira_client, privacy_restricted_user):
        """Test handling privacy-restricted fields."""
        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from get_user import format_user_text
            output = format_user_text(privacy_restricted_user)

        assert 'Jane Smith' in output
        # Should show hidden marker for missing email
        assert '[hidden]' in output or '-' in output or 'N/A' in output


class TestGetUserInactive:
    """Tests for displaying inactive user."""

    def test_format_user_inactive_shows_status(self, mock_jira_client, sample_inactive_user):
        """Test that inactive status is clearly displayed."""
        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from get_user import format_user_text
            output = format_user_text(sample_inactive_user)

        assert 'Inactive' in output


class TestGetUserUnknownAccount:
    """Tests for handling 'unknown' special accountId."""

    def test_format_user_unknown_account(self, mock_jira_client, deleted_user):
        """Test handling 'unknown' accountId for deleted/anonymized users."""
        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from get_user import format_user_text
            output = format_user_text(deleted_user)

        # Should indicate this is a deleted/anonymized user
        assert 'unknown' in output.lower() or 'deleted' in output.lower()


class TestGetUserPermissionError:
    """Tests for permission error handling."""

    def test_get_user_permission_denied(self, mock_jira_client):
        """Test handling insufficient permissions error."""
        from error_handler import PermissionError
        mock_jira_client.get_user.side_effect = PermissionError(
            "Browse users and groups permission required"
        )

        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from get_user import get_user_by_id

            with pytest.raises(PermissionError) as exc_info:
                get_user_by_id(mock_jira_client, account_id="some-id")

        assert "permission" in str(exc_info.value).lower()
