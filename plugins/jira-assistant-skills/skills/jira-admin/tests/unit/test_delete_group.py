"""
Unit tests for delete_group.py script.

Tests cover:
- Deleting a group by name
- Deleting a group by ID
- Confirmation requirement
- Dry-run mode
- System group protection
- Swap group option
- Permission error handling
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add scripts path
scripts_path = str(Path(__file__).parent.parent.parent / "scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


class TestDeleteGroupByName:
    """Tests for deleting group by name."""

    def test_delete_group_by_name_success(self, mock_jira_client, sample_group):
        """Test deleting a group by name."""
        mock_jira_client.delete_group.return_value = None

        with patch("jira_assistant_skills_lib.get_jira_client", return_value=mock_jira_client):
            from delete_group import delete_group

            delete_group(mock_jira_client, group_name="old-team", confirmed=True)

        mock_jira_client.delete_group.assert_called_once()
        call_args = mock_jira_client.delete_group.call_args
        assert call_args[1].get("group_name") == "old-team"


class TestDeleteGroupById:
    """Tests for deleting group by ID."""

    def test_delete_group_by_id_success(self, mock_jira_client):
        """Test deleting a group by group ID."""
        mock_jira_client.delete_group.return_value = None

        with patch("jira_assistant_skills_lib.get_jira_client", return_value=mock_jira_client):
            from delete_group import delete_group

            delete_group(mock_jira_client, group_id="abc-123-def", confirmed=True)

        call_args = mock_jira_client.delete_group.call_args
        assert call_args[1].get("group_id") == "abc-123-def"


class TestDeleteGroupConfirmation:
    """Tests for confirmation requirement."""

    def test_delete_group_requires_confirmation(self, mock_jira_client):
        """Test that deletion requires confirmation."""
        with patch("jira_assistant_skills_lib.get_jira_client", return_value=mock_jira_client):
            from assistant_skills_lib.error_handler import ValidationError
            from delete_group import delete_group

            with pytest.raises(ValidationError) as exc_info:
                delete_group(mock_jira_client, group_name="my-group", confirmed=False)

        assert "confirm" in str(exc_info.value).lower()

    def test_delete_group_confirmed_proceeds(self, mock_jira_client):
        """Test that confirmed deletion proceeds."""
        mock_jira_client.delete_group.return_value = None

        with patch("jira_assistant_skills_lib.get_jira_client", return_value=mock_jira_client):
            from delete_group import delete_group

            delete_group(mock_jira_client, group_name="my-group", confirmed=True)

        mock_jira_client.delete_group.assert_called_once()


class TestDeleteGroupDryRun:
    """Tests for dry-run mode."""

    def test_delete_group_dry_run_no_api_call(self, mock_jira_client):
        """Test that dry-run mode does not make API call."""
        with patch("jira_assistant_skills_lib.get_jira_client", return_value=mock_jira_client):
            from delete_group import delete_group

            delete_group(mock_jira_client, group_name="my-group", dry_run=True)

        mock_jira_client.delete_group.assert_not_called()

    def test_delete_group_dry_run_shows_preview(self, mock_jira_client):
        """Test that dry-run shows preview message."""
        with patch("jira_assistant_skills_lib.get_jira_client", return_value=mock_jira_client):
            from delete_group import format_dry_run_preview

            preview = format_dry_run_preview("my-group")

        assert "my-group" in preview
        assert "dry run" in preview.lower()


class TestDeleteGroupSystemProtection:
    """Tests for system group protection."""

    def test_delete_system_group_fails(self, mock_jira_client, system_groups):
        """Test that system groups cannot be deleted."""
        with patch("jira_assistant_skills_lib.get_jira_client", return_value=mock_jira_client):
            from assistant_skills_lib.error_handler import ValidationError
            from delete_group import check_system_group_protection

            for group_name in system_groups:
                with pytest.raises(ValidationError) as exc_info:
                    check_system_group_protection(group_name)

                assert (
                    "system" in str(exc_info.value).lower()
                    or "protected" in str(exc_info.value).lower()
                )

    def test_delete_custom_group_allowed(self, mock_jira_client):
        """Test that custom groups can be deleted."""
        with patch("jira_assistant_skills_lib.get_jira_client", return_value=mock_jira_client):
            from delete_group import check_system_group_protection

            # Should not raise for custom groups
            check_system_group_protection("my-custom-team")
            check_system_group_protection("project-admins")


class TestDeleteGroupSwap:
    """Tests for swap group option."""

    def test_delete_group_with_swap_group(self, mock_jira_client):
        """Test deleting group and moving members to swap group."""
        mock_jira_client.delete_group.return_value = None

        with patch("jira_assistant_skills_lib.get_jira_client", return_value=mock_jira_client):
            from delete_group import delete_group

            delete_group(
                mock_jira_client,
                group_name="old-team",
                swap_group="new-team",
                confirmed=True,
            )

        call_args = mock_jira_client.delete_group.call_args
        assert call_args[1].get("swap_group") == "new-team"


class TestDeleteGroupNotFound:
    """Tests for group not found error."""

    def test_delete_group_not_found(self, mock_jira_client):
        """Test handling group not found error."""
        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.delete_group.side_effect = NotFoundError(
            "Group", "nonexistent-group"
        )

        with patch("jira_assistant_skills_lib.get_jira_client", return_value=mock_jira_client):
            from delete_group import delete_group

            with pytest.raises(NotFoundError):
                delete_group(
                    mock_jira_client, group_name="nonexistent-group", confirmed=True
                )


class TestDeleteGroupPermissionError:
    """Tests for permission error handling."""

    def test_delete_group_permission_denied(self, mock_jira_client):
        """Test handling insufficient permissions error."""
        from jira_assistant_skills_lib import PermissionError

        mock_jira_client.delete_group.side_effect = PermissionError(
            "Site administration permission required"
        )

        with patch("jira_assistant_skills_lib.get_jira_client", return_value=mock_jira_client):
            from delete_group import delete_group

            with pytest.raises(PermissionError) as exc_info:
                delete_group(mock_jira_client, group_name="my-group", confirmed=True)

        assert "permission" in str(exc_info.value).lower()
