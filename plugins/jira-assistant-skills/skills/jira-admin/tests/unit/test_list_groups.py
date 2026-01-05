"""
Unit tests for list_groups.py script.

Tests cover:
- Listing all groups
- Filtering groups by query
- Including member counts
- Pagination handling
- Empty results handling
- Output formats (table, JSON, CSV)
- Error handling
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add scripts path
scripts_path = str(Path(__file__).parent.parent.parent / "scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


class TestListGroupsBasic:
    """Tests for basic group listing."""

    def test_list_groups_returns_all_groups(
        self, mock_jira_client, sample_groups_picker_response
    ):
        """Test listing all groups returns complete list."""
        mock_jira_client.find_groups.return_value = sample_groups_picker_response

        with patch("config_manager.get_jira_client", return_value=mock_jira_client):
            from list_groups import list_groups

            results = list_groups(mock_jira_client)

        mock_jira_client.find_groups.assert_called_once()
        assert len(results) == 4


class TestListGroupsQuery:
    """Tests for filtering groups by query."""

    def test_list_groups_filter_by_query(self, mock_jira_client, sample_groups):
        """Test filtering groups by name query."""
        filtered_response = {
            "header": "Showing 2 of 2 matching groups",
            "total": 2,
            "groups": [g for g in sample_groups if "jira-" in g["name"]][:2],
        }
        mock_jira_client.find_groups.return_value = filtered_response

        with patch("config_manager.get_jira_client", return_value=mock_jira_client):
            from list_groups import list_groups

            list_groups(mock_jira_client, query="jira-")

        call_args = mock_jira_client.find_groups.call_args
        assert call_args[1].get("query") == "jira-" or call_args[0][0] == "jira-"


class TestListGroupsWithMemberCounts:
    """Tests for including member counts."""

    def test_list_groups_with_member_counts(
        self, mock_jira_client, sample_groups_picker_response, sample_group_members
    ):
        """Test including member counts for each group."""
        mock_jira_client.find_groups.return_value = sample_groups_picker_response
        mock_jira_client.get_group_members.return_value = sample_group_members

        with patch("config_manager.get_jira_client", return_value=mock_jira_client):
            from list_groups import list_groups_with_member_counts

            list_groups_with_member_counts(mock_jira_client)

        # Verify get_group_members was called for each group
        assert mock_jira_client.get_group_members.call_count == 4


class TestListGroupsPagination:
    """Tests for pagination handling."""

    def test_list_groups_pagination_max_results(
        self, mock_jira_client, sample_groups_picker_response
    ):
        """Test pagination with max_results parameter."""
        mock_jira_client.find_groups.return_value = sample_groups_picker_response

        with patch("config_manager.get_jira_client", return_value=mock_jira_client):
            from list_groups import list_groups

            list_groups(mock_jira_client, max_results=10)

        call_args = mock_jira_client.find_groups.call_args
        assert call_args[1].get("max_results") == 10


class TestListGroupsEmpty:
    """Tests for empty results handling."""

    def test_list_groups_no_groups(self, mock_jira_client):
        """Test handling when no groups exist or match query."""
        empty_response = {
            "header": "Showing 0 of 0 matching groups",
            "total": 0,
            "groups": [],
        }
        mock_jira_client.find_groups.return_value = empty_response

        with patch("config_manager.get_jira_client", return_value=mock_jira_client):
            from list_groups import list_groups

            results = list_groups(mock_jira_client, query="nonexistent")

        assert results == []


class TestListGroupsOutputFormats:
    """Tests for different output formats."""

    def test_list_groups_table_output(self, mock_jira_client, sample_groups):
        """Test formatted table output."""
        with patch("config_manager.get_jira_client", return_value=mock_jira_client):
            from list_groups import format_groups_table

            output = format_groups_table(sample_groups)

        assert "jira-administrators" in output
        assert "jira-developers" in output

    def test_list_groups_json_output(self, mock_jira_client, sample_groups):
        """Test JSON output format."""
        with patch("config_manager.get_jira_client", return_value=mock_jira_client):
            from list_groups import format_groups_json

            output = format_groups_json(sample_groups)

        parsed = json.loads(output)
        assert len(parsed) == 4
        assert parsed[0]["name"] == "jira-administrators"

    def test_list_groups_csv_output(self, mock_jira_client, sample_groups):
        """Test CSV output format."""
        with patch("config_manager.get_jira_client", return_value=mock_jira_client):
            from list_groups import format_groups_csv

            output = format_groups_csv(sample_groups)

        lines = output.strip().split("\n")
        assert "name" in lines[0] or "Name" in lines[0]  # Header
        assert len(lines) >= 5  # Header + 4 data rows


class TestListGroupsPermissionError:
    """Tests for permission error handling."""

    def test_list_groups_permission_denied(self, mock_jira_client):
        """Test handling insufficient permissions error."""
        from jira_assistant_skills_lib import PermissionError

        mock_jira_client.find_groups.side_effect = PermissionError(
            "Browse users and groups permission required"
        )

        with patch("config_manager.get_jira_client", return_value=mock_jira_client):
            from list_groups import list_groups

            with pytest.raises(PermissionError) as exc_info:
                list_groups(mock_jira_client)

        assert "permission" in str(exc_info.value).lower()


class TestListGroupsCaseInsensitive:
    """Tests for case-insensitive search."""

    def test_list_groups_case_insensitive_default(
        self, mock_jira_client, sample_groups_picker_response
    ):
        """Test that search is case-insensitive by default."""
        mock_jira_client.find_groups.return_value = sample_groups_picker_response

        with patch("config_manager.get_jira_client", return_value=mock_jira_client):
            from list_groups import list_groups

            list_groups(mock_jira_client, query="JIRA")

        call_args = mock_jira_client.find_groups.call_args
        # Default caseInsensitive should be True
        assert call_args[1].get("caseInsensitive", True) is True


class TestListGroupsSystemGroups:
    """Tests for system group identification."""

    def test_list_groups_identifies_system_groups(
        self, mock_jira_client, sample_groups, system_groups
    ):
        """Test that system groups can be identified in output."""
        with patch("config_manager.get_jira_client", return_value=mock_jira_client):
            from list_groups import format_groups_table

            output = format_groups_table(sample_groups, highlight_system=True)

        # System groups should be marked or identified in some way
        assert "jira-administrators" in output
