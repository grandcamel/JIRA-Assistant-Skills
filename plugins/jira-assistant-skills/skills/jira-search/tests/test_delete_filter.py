"""
Tests for delete_filter.py - Delete saved filters.
"""

import sys
from pathlib import Path

import pytest

# Add script path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


@pytest.mark.search
@pytest.mark.unit
class TestDeleteFilter:
    """Tests for deleting filters."""

    def test_delete_filter(self, mock_jira_client):
        """Test deleting a filter."""
        mock_jira_client.delete_filter.return_value = None

        from delete_filter import delete_filter

        delete_filter(mock_jira_client, "10042")

        mock_jira_client.delete_filter.assert_called_once_with("10042")

    def test_delete_filter_not_owner(self, mock_jira_client):
        """Test error when not filter owner."""
        from jira_assistant_skills_lib import PermissionError

        mock_jira_client.delete_filter.side_effect = PermissionError(
            "You are not the owner of this filter"
        )

        from delete_filter import delete_filter

        with pytest.raises(PermissionError):
            delete_filter(mock_jira_client, "10042")

    def test_delete_filter_not_found(self, mock_jira_client):
        """Test error when filter doesn't exist."""
        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.delete_filter.side_effect = NotFoundError(
            "Filter 99999 not found"
        )

        from delete_filter import delete_filter

        with pytest.raises(NotFoundError):
            delete_filter(mock_jira_client, "99999")

    def test_delete_with_confirmation(self, mock_jira_client, sample_filter):
        """Test confirmation prompt."""
        mock_jira_client.get_filter.return_value = sample_filter

        from delete_filter import get_filter_info

        filter_info = get_filter_info(mock_jira_client, "10042")

        assert filter_info["name"] == "My Bugs"
        assert filter_info["jql"] is not None

    def test_delete_dry_run(self, mock_jira_client, sample_filter):
        """Test dry-run mode."""
        mock_jira_client.get_filter.return_value = sample_filter

        from delete_filter import dry_run_delete

        result = dry_run_delete(mock_jira_client, "10042")

        assert "Would delete filter" in result
        assert "10042" in result
        # delete_filter should NOT be called
        mock_jira_client.delete_filter.assert_not_called()


@pytest.mark.search
@pytest.mark.unit
class TestDeleteFilterErrorHandling:
    """Test API error handling scenarios for delete_filter."""

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from jira_assistant_skills_lib import AuthenticationError

        mock_jira_client.delete_filter.side_effect = AuthenticationError(
            "Invalid API token"
        )

        from delete_filter import delete_filter

        with pytest.raises(AuthenticationError):
            delete_filter(mock_jira_client, "10042")

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.delete_filter.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        from delete_filter import delete_filter

        with pytest.raises(JiraError) as exc_info:
            delete_filter(mock_jira_client, "10042")
        assert exc_info.value.status_code == 429

    def test_server_error(self, mock_jira_client):
        """Test handling of 500 internal server error."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.delete_filter.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        from delete_filter import delete_filter

        with pytest.raises(JiraError) as exc_info:
            delete_filter(mock_jira_client, "10042")
        assert exc_info.value.status_code == 500
