"""
Unit tests for get_group_members.py script.

Tests cover:
- Getting members by group name
- Getting members by group ID
- Including inactive users
- Pagination handling
- Empty group handling
- Privacy-restricted user fields
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


class TestGetGroupMembersByName:
    """Tests for getting group members by group name."""

    def test_get_members_by_group_name(self, mock_jira_client, sample_group_members):
        """Test getting members by group name."""
        mock_jira_client.get_group_members.return_value = sample_group_members

        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from get_group_members import get_members
            results = get_members(mock_jira_client, group_name="jira-developers")

        mock_jira_client.get_group_members.assert_called_once()
        assert len(results) == 3


class TestGetGroupMembersById:
    """Tests for getting group members by group ID."""

    def test_get_members_by_group_id(self, mock_jira_client, sample_group_members):
        """Test getting members by group ID."""
        mock_jira_client.get_group_members.return_value = sample_group_members

        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from get_group_members import get_members
            results = get_members(mock_jira_client, group_id="276f955c-63d7-42c8-9520-92d01dca0625")

        call_args = mock_jira_client.get_group_members.call_args
        assert 'group_id' in call_args[1] or call_args[1].get('group_name') is None


class TestGetGroupMembersIncludeInactive:
    """Tests for including inactive users."""

    def test_get_members_include_inactive(self, mock_jira_client, sample_group_members):
        """Test including inactive users in results."""
        mock_jira_client.get_group_members.return_value = sample_group_members

        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from get_group_members import get_members
            results = get_members(mock_jira_client, group_name="jira-developers",
                                  include_inactive=True)

        call_args = mock_jira_client.get_group_members.call_args
        assert call_args[1].get('include_inactive') is True


class TestGetGroupMembersPagination:
    """Tests for pagination handling."""

    def test_get_members_pagination(self, mock_jira_client, sample_group_members):
        """Test pagination parameters."""
        mock_jira_client.get_group_members.return_value = sample_group_members

        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from get_group_members import get_members
            results = get_members(mock_jira_client, group_name="jira-developers",
                                  start_at=10, max_results=25)

        call_args = mock_jira_client.get_group_members.call_args
        assert call_args[1].get('start_at') == 10
        assert call_args[1].get('max_results') == 25


class TestGetGroupMembersEmpty:
    """Tests for empty group handling."""

    def test_get_members_empty_group(self, mock_jira_client, sample_empty_group_members):
        """Test handling group with no members."""
        mock_jira_client.get_group_members.return_value = sample_empty_group_members

        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from get_group_members import get_members
            results = get_members(mock_jira_client, group_name="empty-group")

        assert results == []


class TestGetGroupMembersPrivacy:
    """Tests for privacy-restricted user fields."""

    def test_format_members_privacy_hidden(self, mock_jira_client, sample_group_members):
        """Test handling privacy-restricted fields in output."""
        # Jane Smith in sample_group_members has no email
        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from get_group_members import format_members_table
            output = format_members_table(sample_group_members['values'])

        assert 'Jane Smith' in output
        # Should show hidden marker for missing email
        assert '[hidden]' in output or '-' in output or 'N/A' in output


class TestGetGroupMembersOutputFormats:
    """Tests for different output formats."""

    def test_format_members_table(self, mock_jira_client, sample_group_members):
        """Test table output format."""
        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from get_group_members import format_members_table
            output = format_members_table(sample_group_members['values'])

        assert 'John Doe' in output
        assert 'john.doe@example.com' in output

    def test_format_members_json(self, mock_jira_client, sample_group_members):
        """Test JSON output format."""
        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from get_group_members import format_members_json
            output = format_members_json(sample_group_members['values'])

        parsed = json.loads(output)
        assert len(parsed) == 3

    def test_format_members_csv(self, mock_jira_client, sample_group_members):
        """Test CSV output format."""
        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from get_group_members import format_members_csv
            output = format_members_csv(sample_group_members['values'])

        lines = output.strip().split('\n')
        assert 'accountId' in lines[0] or 'Account ID' in lines[0]
        assert len(lines) >= 4  # Header + 3 data rows


class TestGetGroupMembersNotFound:
    """Tests for group not found error."""

    def test_get_members_group_not_found(self, mock_jira_client):
        """Test handling group not found error."""
        from jira_assistant_skills_lib import NotFoundError
        mock_jira_client.get_group_members.side_effect = NotFoundError("Group", "nonexistent-group")

        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from get_group_members import get_members

            with pytest.raises(NotFoundError):
                get_members(mock_jira_client, group_name="nonexistent-group")


class TestGetGroupMembersPermissionError:
    """Tests for permission error handling."""

    def test_get_members_permission_denied(self, mock_jira_client):
        """Test handling insufficient permissions error."""
        from jira_assistant_skills_lib import PermissionError
        mock_jira_client.get_group_members.side_effect = PermissionError(
            "Browse users and groups permission required"
        )

        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from get_group_members import get_members

            with pytest.raises(PermissionError) as exc_info:
                get_members(mock_jira_client, group_name="jira-administrators")

        assert "permission" in str(exc_info.value).lower()
