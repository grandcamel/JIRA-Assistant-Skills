"""
Tests for favourite_filter.py - Manage filter favourites.
"""

import copy
import sys
from pathlib import Path

import pytest

# Add script path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


@pytest.mark.search
@pytest.mark.unit
class TestFavouriteFilter:
    """Tests for managing filter favourites."""

    def test_add_to_favourites(self, mock_jira_client, sample_filter):
        """Test adding filter to favourites."""
        expected = copy.deepcopy(sample_filter)
        expected["favourite"] = True
        mock_jira_client.add_filter_favourite.return_value = expected

        from favourite_filter import add_favourite

        result = add_favourite(mock_jira_client, "10042")

        assert result["favourite"] is True
        mock_jira_client.add_filter_favourite.assert_called_once_with("10042")

    def test_remove_from_favourites(self, mock_jira_client):
        """Test removing filter from favourites."""
        mock_jira_client.remove_filter_favourite.return_value = None

        from favourite_filter import remove_favourite

        remove_favourite(mock_jira_client, "10042")

        mock_jira_client.remove_filter_favourite.assert_called_once_with("10042")

    def test_already_favourite(self, mock_jira_client, sample_filter):
        """Test handling already favourited filter."""
        expected = copy.deepcopy(sample_filter)
        expected["favourite"] = True
        mock_jira_client.add_filter_favourite.return_value = expected

        from favourite_filter import add_favourite

        # Should still succeed (idempotent)
        result = add_favourite(mock_jira_client, "10042")
        assert result["favourite"] is True

    def test_not_favourite(self, mock_jira_client):
        """Test handling non-favourited filter removal."""
        # JIRA typically returns 204 even if not favourited
        mock_jira_client.remove_filter_favourite.return_value = None

        from favourite_filter import remove_favourite

        # Should not raise
        remove_favourite(mock_jira_client, "10042")

    def test_filter_not_found(self, mock_jira_client):
        """Test error when filter doesn't exist."""
        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.add_filter_favourite.side_effect = NotFoundError(
            "Filter 99999 not found"
        )

        from favourite_filter import add_favourite

        with pytest.raises(NotFoundError):
            add_favourite(mock_jira_client, "99999")


@pytest.mark.search
@pytest.mark.unit
class TestFavouriteFilterErrorHandling:
    """Test API error handling scenarios for favourite_filter."""

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from jira_assistant_skills_lib import AuthenticationError

        mock_jira_client.add_filter_favourite.side_effect = AuthenticationError(
            "Invalid API token"
        )

        from favourite_filter import add_favourite

        with pytest.raises(AuthenticationError):
            add_favourite(mock_jira_client, "10042")

    def test_forbidden_error(self, mock_jira_client):
        """Test handling of 403 forbidden."""
        from jira_assistant_skills_lib import PermissionError

        mock_jira_client.add_filter_favourite.side_effect = PermissionError(
            "You don't have permission to favourite this filter"
        )

        from favourite_filter import add_favourite

        with pytest.raises(PermissionError):
            add_favourite(mock_jira_client, "10042")

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.add_filter_favourite.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        from favourite_filter import add_favourite

        with pytest.raises(JiraError) as exc_info:
            add_favourite(mock_jira_client, "10042")
        assert exc_info.value.status_code == 429

    def test_server_error(self, mock_jira_client):
        """Test handling of 500 internal server error."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.add_filter_favourite.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        from favourite_filter import add_favourite

        with pytest.raises(JiraError) as exc_info:
            add_favourite(mock_jira_client, "10042")
        assert exc_info.value.status_code == 500
