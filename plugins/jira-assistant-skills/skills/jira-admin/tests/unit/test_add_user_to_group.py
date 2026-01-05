"""
Unit tests for add_user_to_group.py script.

Tests cover:
- Adding user by account ID
- Adding user by email (with lookup)
- Idempotent operation (adding already member)
- Group not found error
- User not found error
- Permission error handling
- Dry-run mode
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add scripts path
scripts_path = str(Path(__file__).parent.parent.parent / "scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


class TestAddUserByAccountId:
    """Tests for adding user by account ID."""

    def test_add_user_by_account_id_success(self, mock_jira_client, sample_group):
        """Test adding user to group by account ID."""
        mock_jira_client.add_user_to_group.return_value = sample_group

        with patch("config_manager.get_jira_client", return_value=mock_jira_client):
            from add_user_to_group import add_user_to_group

            result = add_user_to_group(
                mock_jira_client,
                account_id="5b10ac8d82e05b22cc7d4ef5",
                group_name="jira-developers",
            )

        mock_jira_client.add_user_to_group.assert_called_once_with(
            account_id="5b10ac8d82e05b22cc7d4ef5",
            group_name="jira-developers",
            group_id=None,
        )
        assert result["name"] == "jira-developers"


class TestAddUserByEmail:
    """Tests for adding user by email with lookup."""

    def test_add_user_by_email_success(
        self, mock_jira_client, sample_user, sample_group
    ):
        """Test adding user to group by email lookup."""
        mock_jira_client.search_users.return_value = [sample_user]
        mock_jira_client.add_user_to_group.return_value = sample_group

        with patch("config_manager.get_jira_client", return_value=mock_jira_client):
            from add_user_to_group import add_user_by_email

            add_user_by_email(
                mock_jira_client,
                email="john.doe@example.com",
                group_name="jira-developers",
            )

        # Should have looked up user first
        mock_jira_client.search_users.assert_called_once()
        mock_jira_client.add_user_to_group.assert_called_once()

    def test_add_user_by_email_not_found(self, mock_jira_client):
        """Test error when email lookup returns no results."""
        mock_jira_client.search_users.return_value = []

        with patch("config_manager.get_jira_client", return_value=mock_jira_client):
            from add_user_to_group import add_user_by_email

            from jira_assistant_skills_lib import NotFoundError

            with pytest.raises(NotFoundError) as exc_info:
                add_user_by_email(
                    mock_jira_client,
                    email="nonexistent@example.com",
                    group_name="jira-developers",
                )

        assert "user" in str(exc_info.value).lower()


class TestAddUserIdempotent:
    """Tests for idempotent behavior."""

    def test_add_user_already_member_succeeds(self, mock_jira_client, sample_group):
        """Test that adding user already in group succeeds (idempotent)."""
        # JIRA API returns success even if user is already a member
        mock_jira_client.add_user_to_group.return_value = sample_group

        with patch("config_manager.get_jira_client", return_value=mock_jira_client):
            from add_user_to_group import add_user_to_group

            result = add_user_to_group(
                mock_jira_client,
                account_id="5b10ac8d82e05b22cc7d4ef5",
                group_name="jira-developers",
            )

        # Should succeed without error
        assert result is not None


class TestAddUserGroupNotFound:
    """Tests for group not found error."""

    def test_add_user_group_not_found(self, mock_jira_client):
        """Test error when group does not exist."""
        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.add_user_to_group.side_effect = NotFoundError(
            "Group", "nonexistent-group"
        )

        with patch("config_manager.get_jira_client", return_value=mock_jira_client):
            from add_user_to_group import add_user_to_group

            with pytest.raises(NotFoundError):
                add_user_to_group(
                    mock_jira_client,
                    account_id="5b10ac8d82e05b22cc7d4ef5",
                    group_name="nonexistent-group",
                )


class TestAddUserNotFound:
    """Tests for user not found error."""

    def test_add_user_account_not_found(self, mock_jira_client):
        """Test error when account ID does not exist."""
        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.add_user_to_group.side_effect = NotFoundError(
            "User", "invalid-account-id"
        )

        with patch("config_manager.get_jira_client", return_value=mock_jira_client):
            from add_user_to_group import add_user_to_group

            with pytest.raises(NotFoundError):
                add_user_to_group(
                    mock_jira_client,
                    account_id="invalid-account-id",
                    group_name="jira-developers",
                )


class TestAddUserPermissionError:
    """Tests for permission error handling."""

    def test_add_user_permission_denied(self, mock_jira_client):
        """Test handling insufficient permissions error."""
        from jira_assistant_skills_lib import PermissionError

        mock_jira_client.add_user_to_group.side_effect = PermissionError(
            "Site administration permission required"
        )

        with patch("config_manager.get_jira_client", return_value=mock_jira_client):
            from add_user_to_group import add_user_to_group

            with pytest.raises(PermissionError) as exc_info:
                add_user_to_group(
                    mock_jira_client,
                    account_id="5b10ac8d82e05b22cc7d4ef5",
                    group_name="jira-developers",
                )

        assert "permission" in str(exc_info.value).lower()


class TestAddUserDryRun:
    """Tests for dry-run mode."""

    def test_add_user_dry_run_no_api_call(self, mock_jira_client):
        """Test that dry-run mode does not make API call."""
        with patch("config_manager.get_jira_client", return_value=mock_jira_client):
            from add_user_to_group import add_user_to_group

            result = add_user_to_group(
                mock_jira_client,
                account_id="5b10ac8d82e05b22cc7d4ef5",
                group_name="jira-developers",
                dry_run=True,
            )

        mock_jira_client.add_user_to_group.assert_not_called()
        assert result is None

    def test_add_user_dry_run_preview(self, mock_jira_client):
        """Test that dry-run shows preview message."""
        with patch("config_manager.get_jira_client", return_value=mock_jira_client):
            from add_user_to_group import format_dry_run_preview

            preview = format_dry_run_preview(
                account_id="5b10ac8d82e05b22cc7d4ef5", group_name="jira-developers"
            )

        assert "jira-developers" in preview
        assert "dry run" in preview.lower()


class TestAddUserGroupById:
    """Tests for adding user to group by group ID."""

    def test_add_user_by_group_id(self, mock_jira_client, sample_group):
        """Test adding user to group by group ID."""
        mock_jira_client.add_user_to_group.return_value = sample_group

        with patch("config_manager.get_jira_client", return_value=mock_jira_client):
            from add_user_to_group import add_user_to_group

            add_user_to_group(
                mock_jira_client,
                account_id="5b10ac8d82e05b22cc7d4ef5",
                group_id="276f955c-63d7-42c8-9520-92d01dca0625",
            )

        call_args = mock_jira_client.add_user_to_group.call_args
        assert call_args[1].get("group_id") == "276f955c-63d7-42c8-9520-92d01dca0625"
