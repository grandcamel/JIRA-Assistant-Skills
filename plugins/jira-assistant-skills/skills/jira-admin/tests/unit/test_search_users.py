"""
Unit tests for search_users.py script.

Tests cover:
- Searching users by name
- Searching users by email
- Filtering active/inactive users
- Finding assignable users for a project
- Pagination handling
- Privacy-restricted fields
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


class TestSearchUsersByName:
    """Tests for searching users by display name."""

    def test_search_users_by_name_returns_matches(self, mock_jira_client, sample_users):
        """Test searching users by display name returns matching users."""
        mock_jira_client.search_users.return_value = sample_users[:2]  # First two Johns

        with patch("jira_assistant_skills_lib.get_jira_client", return_value=mock_jira_client):
            from search_users import search_users

            results = search_users(mock_jira_client, query="john")

        mock_jira_client.search_users.assert_called_once()
        assert len(results) == 2
        assert all("John" in u["displayName"] for u in results)

    def test_search_users_partial_match(self, mock_jira_client, sample_users):
        """Test that partial name matching works."""
        mock_jira_client.search_users.return_value = sample_users[:1]

        with patch("jira_assistant_skills_lib.get_jira_client", return_value=mock_jira_client):
            from search_users import search_users

            results = search_users(mock_jira_client, query="doe")

        assert len(results) == 1
        assert results[0]["displayName"] == "John Doe"


class TestSearchUsersByEmail:
    """Tests for searching users by email address."""

    def test_search_users_by_email_returns_match(self, mock_jira_client, sample_user):
        """Test searching users by email address."""
        mock_jira_client.search_users.return_value = [sample_user]

        with patch("jira_assistant_skills_lib.get_jira_client", return_value=mock_jira_client):
            from search_users import search_users

            results = search_users(mock_jira_client, query="john.doe@example.com")

        assert len(results) == 1
        assert results[0]["emailAddress"] == "john.doe@example.com"


class TestSearchUsersActiveFilter:
    """Tests for active/inactive user filtering."""

    def test_search_users_active_only_default(self, mock_jira_client, sample_users):
        """Test that active-only is the default behavior."""
        # Return only active users
        active_users = [u for u in sample_users if u["active"]]
        mock_jira_client.search_users.return_value = active_users

        with patch("jira_assistant_skills_lib.get_jira_client", return_value=mock_jira_client):
            from search_users import search_users

            results = search_users(mock_jira_client, query="john", active_only=True)

        assert all(u["active"] for u in results)

    def test_search_users_include_inactive(self, mock_jira_client, sample_users):
        """Test including inactive users in search results."""
        mock_jira_client.search_users.return_value = sample_users

        with patch("jira_assistant_skills_lib.get_jira_client", return_value=mock_jira_client):
            from search_users import search_users

            results = search_users(mock_jira_client, query="john", active_only=False)

        assert len(results) == 3
        inactive_users = [u for u in results if not u["active"]]
        assert len(inactive_users) == 1


class TestSearchUsersAssignable:
    """Tests for finding assignable users for a project."""

    def test_search_assignable_users_for_project(self, mock_jira_client, sample_users):
        """Test finding assignable users for specific project."""
        mock_jira_client.find_assignable_users.return_value = sample_users[:2]

        with patch("jira_assistant_skills_lib.get_jira_client", return_value=mock_jira_client):
            from search_users import search_assignable_users

            results = search_assignable_users(
                mock_jira_client, query="john", project_key="PROJ"
            )

        mock_jira_client.find_assignable_users.assert_called_once_with(
            query="john", project_key="PROJ", start_at=0, max_results=50
        )
        assert len(results) == 2


class TestSearchUsersPagination:
    """Tests for pagination handling."""

    def test_search_users_pagination_start_at(self, mock_jira_client, sample_users):
        """Test pagination with start_at parameter."""
        mock_jira_client.search_users.return_value = sample_users[1:]

        with patch("jira_assistant_skills_lib.get_jira_client", return_value=mock_jira_client):
            from search_users import search_users

            search_users(mock_jira_client, query="john", start_at=1, max_results=10)

        call_args = mock_jira_client.search_users.call_args
        assert call_args[1].get("start_at") == 1 or call_args[0][1] == 1

    def test_search_users_pagination_max_results(self, mock_jira_client, sample_users):
        """Test pagination with max_results parameter."""
        mock_jira_client.search_users.return_value = sample_users[:2]

        with patch("jira_assistant_skills_lib.get_jira_client", return_value=mock_jira_client):
            from search_users import search_users

            results = search_users(
                mock_jira_client, query="john", start_at=0, max_results=2
            )

        assert len(results) == 2


class TestSearchUsersEmptyResults:
    """Tests for empty search results handling."""

    def test_search_users_no_matches(self, mock_jira_client):
        """Test handling when no users match the query."""
        mock_jira_client.search_users.return_value = []

        with patch("jira_assistant_skills_lib.get_jira_client", return_value=mock_jira_client):
            from search_users import search_users

            results = search_users(mock_jira_client, query="nonexistent")

        assert results == []


class TestSearchUsersOutputFormats:
    """Tests for different output formats."""

    def test_search_users_table_output(self, mock_jira_client, sample_users, capsys):
        """Test formatted table output."""
        mock_jira_client.search_users.return_value = sample_users[:2]

        with patch("jira_assistant_skills_lib.get_jira_client", return_value=mock_jira_client):
            from search_users import format_users_table

            output = format_users_table(sample_users[:2])

        assert "John Doe" in output
        assert "john.doe@example.com" in output

    def test_search_users_json_output(self, mock_jira_client, sample_users):
        """Test JSON output format."""
        with patch("jira_assistant_skills_lib.get_jira_client", return_value=mock_jira_client):
            from search_users import format_users_json

            output = format_users_json(sample_users[:2])

        parsed = json.loads(output)
        assert len(parsed) == 2
        assert parsed[0]["accountId"] == sample_users[0]["accountId"]

    def test_search_users_csv_output(self, mock_jira_client, sample_users):
        """Test CSV export format."""
        with patch("jira_assistant_skills_lib.get_jira_client", return_value=mock_jira_client):
            from search_users import format_users_csv

            output = format_users_csv(sample_users[:2])

        lines = output.strip().split("\n")
        assert "accountId" in lines[0] or "Account ID" in lines[0]  # Header
        assert len(lines) >= 3  # Header + 2 data rows


class TestSearchUsersPrivacyControls:
    """Tests for handling privacy-restricted fields."""

    def test_search_users_hidden_email(self, mock_jira_client, privacy_restricted_user):
        """Test handling users with hidden email addresses."""
        mock_jira_client.search_users.return_value = [privacy_restricted_user]

        with patch("jira_assistant_skills_lib.get_jira_client", return_value=mock_jira_client):
            from search_users import format_users_table

            output = format_users_table([privacy_restricted_user])

        # Should show something like [hidden] for missing email
        assert "Jane Smith" in output
        assert "[hidden]" in output or "-" in output or "N/A" in output


class TestSearchUsersWithGroups:
    """Tests for including group membership in output."""

    def test_search_users_include_groups(
        self, mock_jira_client, sample_user_with_groups
    ):
        """Test including group membership in search results."""
        mock_jira_client.search_users.return_value = [sample_user_with_groups]
        mock_jira_client.get_user_groups.return_value = [
            {"name": "jira-users", "groupId": "g1"},
            {"name": "jira-developers", "groupId": "g2"},
        ]

        with patch("jira_assistant_skills_lib.get_jira_client", return_value=mock_jira_client):
            from search_users import search_users_with_groups

            search_users_with_groups(mock_jira_client, query="john")

        # Verify groups were fetched for each user
        mock_jira_client.get_user_groups.assert_called()


class TestSearchUsersPermissionError:
    """Tests for permission error handling."""

    def test_search_users_permission_denied(self, mock_jira_client):
        """Test handling insufficient permissions error."""
        from jira_assistant_skills_lib import PermissionError

        mock_jira_client.search_users.side_effect = PermissionError(
            "Browse users and groups permission required"
        )

        with patch("jira_assistant_skills_lib.get_jira_client", return_value=mock_jira_client):
            from search_users import search_users

            with pytest.raises(PermissionError) as exc_info:
                search_users(mock_jira_client, query="john")

        assert "permission" in str(exc_info.value).lower()


class TestSearchUsersEmptyQuery:
    """Tests for empty query behavior."""

    def test_search_users_empty_query_returns_all(self, mock_jira_client, sample_users):
        """Test that empty query returns paginated users."""
        mock_jira_client.search_users.return_value = sample_users

        with patch("jira_assistant_skills_lib.get_jira_client", return_value=mock_jira_client):
            from search_users import search_users

            results = search_users(mock_jira_client, query="", active_only=False)

        assert len(results) == len(sample_users)
