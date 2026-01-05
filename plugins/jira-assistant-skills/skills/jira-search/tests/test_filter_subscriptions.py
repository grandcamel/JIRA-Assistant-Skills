"""
Tests for filter_subscriptions.py - View filter subscriptions.
"""

import sys
from pathlib import Path

import pytest

# Add script path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


@pytest.mark.search
@pytest.mark.unit
class TestFilterSubscriptions:
    """Tests for viewing filter subscriptions."""

    def test_get_subscriptions(
        self, mock_jira_client, sample_filter_with_subscriptions
    ):
        """Test fetching filter subscriptions."""
        mock_jira_client.get_filter.return_value = sample_filter_with_subscriptions

        from filter_subscriptions import get_subscriptions

        result = get_subscriptions(mock_jira_client, "10042")

        assert len(result["subscriptions"]["items"]) == 2
        assert result["subscriptions"]["items"][0]["user"]["displayName"] == "Alice"
        mock_jira_client.get_filter.assert_called_once()

    def test_subscriptions_empty(self, mock_jira_client, sample_filter):
        """Test handling filter with no subscriptions."""
        # sample_filter has empty subscriptions
        mock_jira_client.get_filter.return_value = sample_filter

        from filter_subscriptions import get_subscriptions

        result = get_subscriptions(mock_jira_client, "10042")

        assert result["subscriptions"]["size"] == 0
        assert len(result["subscriptions"]["items"]) == 0

    def test_subscription_details(self, mock_jira_client):
        """Test showing subscription schedule details."""
        filter_with_schedule = {
            "id": "10042",
            "name": "My Bugs",
            "jql": "project = PROJ AND type = Bug",
            "viewUrl": "https://test.atlassian.net/issues/?filter=10042",
            "subscriptions": {
                "size": 1,
                "items": [
                    {
                        "id": 789,
                        "user": {
                            "displayName": "Alice",
                            "emailAddress": "alice@company.com",
                        },
                        "group": None,
                    }
                ],
            },
        }
        mock_jira_client.get_filter.return_value = filter_with_schedule

        from filter_subscriptions import get_subscriptions

        result = get_subscriptions(mock_jira_client, "10042")

        subscription = result["subscriptions"]["items"][0]
        assert subscription["id"] == 789
        assert subscription["user"]["emailAddress"] == "alice@company.com"

    def test_filter_not_found(self, mock_jira_client):
        """Test error when filter doesn't exist."""
        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.get_filter.side_effect = NotFoundError(
            "Filter 99999 not found"
        )

        from filter_subscriptions import get_subscriptions

        with pytest.raises(NotFoundError):
            get_subscriptions(mock_jira_client, "99999")


@pytest.mark.search
@pytest.mark.unit
class TestFilterSubscriptionsErrorHandling:
    """Test API error handling scenarios for filter_subscriptions."""

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from jira_assistant_skills_lib import AuthenticationError

        mock_jira_client.get_filter.side_effect = AuthenticationError(
            "Invalid API token"
        )

        from filter_subscriptions import get_subscriptions

        with pytest.raises(AuthenticationError):
            get_subscriptions(mock_jira_client, "10042")

    def test_forbidden_error(self, mock_jira_client):
        """Test handling of 403 forbidden."""
        from jira_assistant_skills_lib import PermissionError

        mock_jira_client.get_filter.side_effect = PermissionError(
            "You don't have permission to view this filter"
        )

        from filter_subscriptions import get_subscriptions

        with pytest.raises(PermissionError):
            get_subscriptions(mock_jira_client, "10042")

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.get_filter.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        from filter_subscriptions import get_subscriptions

        with pytest.raises(JiraError) as exc_info:
            get_subscriptions(mock_jira_client, "10042")
        assert exc_info.value.status_code == 429

    def test_server_error(self, mock_jira_client):
        """Test handling of 500 internal server error."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.get_filter.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        from filter_subscriptions import get_subscriptions

        with pytest.raises(JiraError) as exc_info:
            get_subscriptions(mock_jira_client, "10042")
        assert exc_info.value.status_code == 500
