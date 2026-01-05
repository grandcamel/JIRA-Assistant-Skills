"""
Tests for get_links.py

TDD tests for viewing issue links.
"""

import json
from unittest.mock import patch

import pytest


@pytest.mark.relationships
@pytest.mark.unit
class TestGetLinks:
    """Tests for the get_links function."""

    def test_get_all_links(self, mock_jira_client, sample_issue_links):
        """Test fetching all links for an issue."""
        mock_jira_client.get_issue_links.return_value = sample_issue_links

        import get_links

        with patch.object(get_links, "get_jira_client", return_value=mock_jira_client):
            result = get_links.get_links("PROJ-123")

        assert len(result) == 3
        mock_jira_client.get_issue_links.assert_called_once_with("PROJ-123")

    def test_get_outward_links(self, mock_jira_client, sample_issue_links):
        """Test filtering to only outward links (where queried issue is the actor)."""
        mock_jira_client.get_issue_links.return_value = sample_issue_links

        import get_links

        with patch.object(get_links, "get_jira_client", return_value=mock_jira_client):
            result = get_links.get_links("PROJ-123", direction="outward")

        # sample_issue_links has 1 link where queried issue is outward (inwardIssue present)
        # PROJ-123 blocks PROJ-100
        assert len(result) == 1
        for link in result:
            assert (
                "inwardIssue" in link
            )  # When queried issue is outward, other is inward

    def test_get_inward_links(self, mock_jira_client, sample_issue_links):
        """Test filtering to only inward links (where queried issue receives action)."""
        mock_jira_client.get_issue_links.return_value = sample_issue_links

        import get_links

        with patch.object(get_links, "get_jira_client", return_value=mock_jira_client):
            result = get_links.get_links("PROJ-123", direction="inward")

        # sample_issue_links has 2 links where queried issue is inward (outwardIssue present)
        # PROJ-456 blocks PROJ-123, PROJ-789 relates to PROJ-123
        assert len(result) == 2
        for link in result:
            assert (
                "outwardIssue" in link
            )  # When queried issue is inward, other is outward

    def test_filter_by_link_type(self, mock_jira_client, sample_issue_links):
        """Test filtering by specific link type (e.g., blocks)."""
        mock_jira_client.get_issue_links.return_value = sample_issue_links

        import get_links

        with patch.object(get_links, "get_jira_client", return_value=mock_jira_client):
            result = get_links.get_links("PROJ-123", link_type="Blocks")

        # sample_issue_links has 2 Blocks links
        assert len(result) == 2
        for link in result:
            assert link["type"]["name"] == "Blocks"

    def test_format_text_output(self, mock_jira_client, sample_issue_links):
        """Test human-readable output."""
        mock_jira_client.get_issue_links.return_value = sample_issue_links

        import get_links

        with patch.object(get_links, "get_jira_client", return_value=mock_jira_client):
            output = get_links.format_links(
                sample_issue_links, "PROJ-123", output_format="text"
            )

        # Should contain issue keys
        assert "PROJ-456" in output
        assert "PROJ-789" in output
        assert "PROJ-100" in output
        # Should show link directions
        assert "blocks" in output or "Blocks" in output

    def test_format_json_output(self, mock_jira_client, sample_issue_links):
        """Test JSON output format."""
        mock_jira_client.get_issue_links.return_value = sample_issue_links

        import get_links

        with patch.object(get_links, "get_jira_client", return_value=mock_jira_client):
            output = get_links.format_links(
                sample_issue_links, "PROJ-123", output_format="json"
            )

        # Should be valid JSON
        parsed = json.loads(output)
        assert isinstance(parsed, list)
        assert len(parsed) == 3

    def test_issue_no_links(self, mock_jira_client):
        """Test output when issue has no links."""
        mock_jira_client.get_issue_links.return_value = []

        import get_links

        with patch.object(get_links, "get_jira_client", return_value=mock_jira_client):
            result = get_links.get_links("PROJ-124")

        assert len(result) == 0

    def test_issue_not_found(self, mock_jira_client):
        """Test error when issue doesn't exist."""
        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.get_issue_links.side_effect = NotFoundError("Issue not found")

        import get_links

        with patch.object(get_links, "get_jira_client", return_value=mock_jira_client):
            with pytest.raises(NotFoundError):
                get_links.get_links("PROJ-999")


@pytest.mark.relationships
@pytest.mark.unit
class TestGetLinksErrorHandling:
    """Test API error handling scenarios for get_links."""

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from jira_assistant_skills_lib import AuthenticationError

        mock_jira_client.get_issue_links.side_effect = AuthenticationError(
            "Invalid token"
        )

        import get_links

        with patch.object(get_links, "get_jira_client", return_value=mock_jira_client):
            with pytest.raises(AuthenticationError):
                get_links.get_links("PROJ-123")

    def test_forbidden_error(self, mock_jira_client):
        """Test handling of 403 forbidden."""
        from jira_assistant_skills_lib import PermissionError

        mock_jira_client.get_issue_links.side_effect = PermissionError(
            "Insufficient permissions"
        )

        import get_links

        with patch.object(get_links, "get_jira_client", return_value=mock_jira_client):
            with pytest.raises(PermissionError):
                get_links.get_links("PROJ-123")

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.get_issue_links.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        import get_links

        with patch.object(get_links, "get_jira_client", return_value=mock_jira_client):
            with pytest.raises(JiraError) as exc_info:
                get_links.get_links("PROJ-123")
            assert exc_info.value.status_code == 429

    def test_server_error(self, mock_jira_client):
        """Test handling of 500 server error."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.get_issue_links.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        import get_links

        with patch.object(get_links, "get_jira_client", return_value=mock_jira_client):
            with pytest.raises(JiraError) as exc_info:
                get_links.get_links("PROJ-123")
            assert exc_info.value.status_code == 500
