"""
Tests for share_filter.py - Manage filter sharing permissions.
"""

import sys
from pathlib import Path

import pytest

# Add script path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


@pytest.mark.search
@pytest.mark.unit
class TestShareFilter:
    """Tests for managing filter share permissions."""

    def test_share_with_project(self, mock_jira_client, sample_filter_permissions):
        """Test sharing filter with project members."""
        new_permission = {
            "id": 10003,
            "type": "project",
            "project": {"id": "10000", "key": "PROJ", "name": "Test Project"},
        }
        mock_jira_client.add_filter_permission.return_value = new_permission

        from share_filter import share_with_project

        result = share_with_project(mock_jira_client, "10042", "PROJ")

        assert result["type"] == "project"
        assert result["project"]["key"] == "PROJ"
        mock_jira_client.add_filter_permission.assert_called_once()

    def test_share_with_project_role(self, mock_jira_client):
        """Test sharing with specific project role."""
        # Mock the role lookup
        mock_jira_client.get.return_value = {
            "Developers": "https://test.atlassian.net/rest/api/3/project/PROJ/role/10001",
            "Administrators": "https://test.atlassian.net/rest/api/3/project/PROJ/role/10002",
        }
        new_permission = {
            "id": 10004,
            "type": "projectRole",
            "project": {"key": "PROJ"},
            "role": {"name": "Developers", "id": 10001},
        }
        mock_jira_client.add_filter_permission.return_value = new_permission

        from share_filter import share_with_project_role

        result = share_with_project_role(
            mock_jira_client, "10042", "PROJ", "Developers"
        )

        assert result["type"] == "projectRole"
        assert result["role"]["name"] == "Developers"

    def test_share_with_group(self, mock_jira_client):
        """Test sharing with group."""
        new_permission = {
            "id": 10005,
            "type": "group",
            "group": {"name": "developers", "groupId": "abc123"},
        }
        mock_jira_client.add_filter_permission.return_value = new_permission

        from share_filter import share_with_group

        result = share_with_group(mock_jira_client, "10042", "developers")

        assert result["type"] == "group"
        assert result["group"]["name"] == "developers"

    def test_share_globally(self, mock_jira_client):
        """Test sharing with all users."""
        new_permission = {"id": 10006, "type": "global"}
        mock_jira_client.add_filter_permission.return_value = new_permission

        from share_filter import share_globally

        result = share_globally(mock_jira_client, "10042")

        assert result["type"] == "global"

    def test_share_with_user(self, mock_jira_client):
        """Test sharing with specific user."""
        new_permission = {
            "id": 10007,
            "type": "user",
            "user": {"accountId": "5b10a2844c20165700ede21g", "displayName": "Alice"},
        }
        mock_jira_client.add_filter_permission.return_value = new_permission

        from share_filter import share_with_user

        result = share_with_user(mock_jira_client, "10042", "5b10a2844c20165700ede21g")

        assert result["type"] == "user"
        assert result["user"]["displayName"] == "Alice"

    def test_unshare(self, mock_jira_client):
        """Test removing share permission."""
        mock_jira_client.delete_filter_permission.return_value = None

        from share_filter import unshare

        unshare(mock_jira_client, "10042", "10001")

        mock_jira_client.delete_filter_permission.assert_called_once_with(
            "10042", "10001"
        )

    def test_list_permissions(self, mock_jira_client, sample_filter_permissions):
        """Test listing current share permissions."""
        mock_jira_client.get_filter_permissions.return_value = sample_filter_permissions

        from share_filter import list_permissions

        result = list_permissions(mock_jira_client, "10042")

        assert len(result) == 2
        assert result[0]["type"] == "project"
        assert result[1]["type"] == "group"
        mock_jira_client.get_filter_permissions.assert_called_once_with("10042")

    def test_share_not_owner(self, mock_jira_client):
        """Test error when not filter owner."""
        from jira_assistant_skills_lib import PermissionError

        mock_jira_client.add_filter_permission.side_effect = PermissionError(
            "You are not the owner of this filter"
        )

        from share_filter import share_with_project

        with pytest.raises(PermissionError):
            share_with_project(mock_jira_client, "10042", "PROJ")


@pytest.mark.search
@pytest.mark.unit
class TestShareFilterErrorHandling:
    """Test API error handling scenarios for share_filter."""

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from jira_assistant_skills_lib import AuthenticationError

        mock_jira_client.add_filter_permission.side_effect = AuthenticationError(
            "Invalid API token"
        )

        from share_filter import share_with_project

        with pytest.raises(AuthenticationError):
            share_with_project(mock_jira_client, "10042", "PROJ")

    def test_filter_not_found(self, mock_jira_client):
        """Test handling of 404 not found."""
        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.add_filter_permission.side_effect = NotFoundError(
            "Filter 99999 not found"
        )

        from share_filter import share_with_project

        with pytest.raises(NotFoundError):
            share_with_project(mock_jira_client, "99999", "PROJ")

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.add_filter_permission.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        from share_filter import share_with_project

        with pytest.raises(JiraError) as exc_info:
            share_with_project(mock_jira_client, "10042", "PROJ")
        assert exc_info.value.status_code == 429

    def test_server_error(self, mock_jira_client):
        """Test handling of 500 internal server error."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.add_filter_permission.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        from share_filter import share_with_project

        with pytest.raises(JiraError) as exc_info:
            share_with_project(mock_jira_client, "10042", "PROJ")
        assert exc_info.value.status_code == 500
