"""
Tests for manage_watchers.py - Manage issue watchers.
"""

import pytest
from unittest.mock import patch
import sys
from pathlib import Path

# Add script path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


@pytest.fixture
def sample_watchers():
    """Sample watchers list."""
    return [
        {
            'accountId': '5b10a2844c20165700ede21g',
            'displayName': 'Alice Smith',
            'emailAddress': 'alice@company.com'
        },
        {
            'accountId': '5b10a2844c20165700ede22h',
            'displayName': 'Bob Jones',
            'emailAddress': 'bob@company.com'
        }
    ]


@pytest.mark.collaborate
@pytest.mark.unit
class TestListWatchers:
    """Tests for listing watchers."""

    @patch('manage_watchers.get_jira_client')
    def test_list_watchers_success(self, mock_get_client, mock_jira_client, sample_watchers):
        """Test listing watchers."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get.return_value = {'watchers': sample_watchers}

        from manage_watchers import list_watchers

        result = list_watchers('PROJ-123', profile=None)

        assert len(result) == 2
        assert result[0]['displayName'] == 'Alice Smith'
        mock_jira_client.get.assert_called_once()

    @patch('manage_watchers.get_jira_client')
    def test_list_watchers_empty(self, mock_get_client, mock_jira_client):
        """Test listing when no watchers."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get.return_value = {'watchers': []}

        from manage_watchers import list_watchers

        result = list_watchers('PROJ-123', profile=None)

        assert len(result) == 0

    def test_list_watchers_invalid_issue_key(self):
        """Test error for invalid issue key."""
        from jira_assistant_skills_lib import ValidationError

        from manage_watchers import list_watchers

        with pytest.raises(ValidationError):
            list_watchers('invalid', profile=None)


@pytest.mark.collaborate
@pytest.mark.unit
class TestAddWatcher:
    """Tests for adding watchers."""

    @patch('manage_watchers.get_jira_client')
    def test_add_watcher_by_account_id(self, mock_get_client, mock_jira_client):
        """Test adding watcher by account ID."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.post.return_value = None

        from manage_watchers import add_watcher

        add_watcher('PROJ-123', '5b10a2844c20165700ede21g', profile=None)

        mock_jira_client.post.assert_called_once()

    @patch('manage_watchers.get_jira_client')
    def test_add_watcher_by_email(self, mock_get_client, mock_jira_client):
        """Test adding watcher by email (lookup required)."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.search_users.return_value = [{'accountId': '5b10a2844c20165700ede21g'}]
        mock_jira_client.post.return_value = None

        from manage_watchers import add_watcher

        add_watcher('PROJ-123', 'alice@company.com', profile=None)

        mock_jira_client.search_users.assert_called_once()
        mock_jira_client.post.assert_called_once()

    @patch('manage_watchers.get_jira_client')
    def test_add_watcher_user_not_found(self, mock_get_client, mock_jira_client):
        """Test error when user not found."""
        from jira_assistant_skills_lib import ValidationError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.search_users.return_value = []

        from manage_watchers import add_watcher

        with pytest.raises(ValidationError):
            add_watcher('PROJ-123', 'nonexistent@company.com', profile=None)


@pytest.mark.collaborate
@pytest.mark.unit
class TestRemoveWatcher:
    """Tests for removing watchers."""

    @patch('manage_watchers.get_jira_client')
    def test_remove_watcher_by_account_id(self, mock_get_client, mock_jira_client):
        """Test removing watcher by account ID."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.delete.return_value = None

        from manage_watchers import remove_watcher

        remove_watcher('PROJ-123', '5b10a2844c20165700ede21g', profile=None)

        mock_jira_client.delete.assert_called_once()

    @patch('manage_watchers.get_jira_client')
    def test_remove_watcher_by_email(self, mock_get_client, mock_jira_client):
        """Test removing watcher by email (lookup required)."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.search_users.return_value = [{'accountId': '5b10a2844c20165700ede21g'}]
        mock_jira_client.delete.return_value = None

        from manage_watchers import remove_watcher

        remove_watcher('PROJ-123', 'alice@company.com', profile=None)

        mock_jira_client.search_users.assert_called_once()
        mock_jira_client.delete.assert_called_once()


@pytest.mark.collaborate
@pytest.mark.unit
class TestManageWatchersErrorHandling:
    """Test API error handling scenarios for manage_watchers."""

    @patch('manage_watchers.get_jira_client')
    def test_authentication_error(self, mock_get_client, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from jira_assistant_skills_lib import AuthenticationError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get.side_effect = AuthenticationError("Invalid API token")

        from manage_watchers import list_watchers

        with pytest.raises(AuthenticationError):
            list_watchers('PROJ-123', profile=None)

    @patch('manage_watchers.get_jira_client')
    def test_permission_error(self, mock_get_client, mock_jira_client):
        """Test handling of 403 forbidden."""
        from jira_assistant_skills_lib import PermissionError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.post.side_effect = PermissionError("No permission to manage watchers")

        from manage_watchers import add_watcher

        with pytest.raises(PermissionError):
            add_watcher('PROJ-123', '5b10a2844c20165700ede21g', profile=None)

    @patch('manage_watchers.get_jira_client')
    def test_not_found_error(self, mock_get_client, mock_jira_client):
        """Test handling of 404 not found."""
        from jira_assistant_skills_lib import NotFoundError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get.side_effect = NotFoundError("Issue PROJ-999 not found")

        from manage_watchers import list_watchers

        with pytest.raises(NotFoundError):
            list_watchers('PROJ-999', profile=None)

    @patch('manage_watchers.get_jira_client')
    def test_rate_limit_error(self, mock_get_client, mock_jira_client):
        """Test handling of 429 rate limit."""
        from jira_assistant_skills_lib import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get.side_effect = JiraError("Rate limit exceeded", status_code=429)

        from manage_watchers import list_watchers

        with pytest.raises(JiraError) as exc_info:
            list_watchers('PROJ-123', profile=None)
        assert exc_info.value.status_code == 429

    @patch('manage_watchers.get_jira_client')
    def test_server_error(self, mock_get_client, mock_jira_client):
        """Test handling of 500 server error."""
        from jira_assistant_skills_lib import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get.side_effect = JiraError("Internal server error", status_code=500)

        from manage_watchers import list_watchers

        with pytest.raises(JiraError) as exc_info:
            list_watchers('PROJ-123', profile=None)
        assert exc_info.value.status_code == 500
