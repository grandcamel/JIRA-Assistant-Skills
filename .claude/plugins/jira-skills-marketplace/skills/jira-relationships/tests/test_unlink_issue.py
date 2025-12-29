"""
Tests for unlink_issue.py

TDD tests for removing issue links.
"""

import pytest
from unittest.mock import patch


@pytest.mark.relationships
@pytest.mark.unit
class TestUnlinkIssue:
    """Tests for the unlink_issue function."""

    def test_unlink_specific_link(self, mock_jira_client, sample_issue_links):
        """Test removing link between two specific issues."""
        mock_jira_client.get_issue_links.return_value = sample_issue_links

        import unlink_issue
        with patch.object(unlink_issue, 'get_jira_client', return_value=mock_jira_client):
            unlink_issue.unlink_issue(
                issue_key="PROJ-123",
                from_issue="PROJ-456"
            )

        # Should delete the link with ID "20001" (PROJ-123 blocks PROJ-456)
        mock_jira_client.delete_link.assert_called_once_with("20001")

    def test_unlink_all_of_type(self, mock_jira_client, sample_issue_links):
        """Test removing all links of a specific type."""
        mock_jira_client.get_issue_links.return_value = sample_issue_links

        import unlink_issue
        with patch.object(unlink_issue, 'get_jira_client', return_value=mock_jira_client):
            unlink_issue.unlink_issue(
                issue_key="PROJ-123",
                link_type="Blocks",
                remove_all=True
            )

        # Should delete both Blocks links (IDs "20001" and "20003")
        assert mock_jira_client.delete_link.call_count == 2
        calls = mock_jira_client.delete_link.call_args_list
        deleted_ids = {c[0][0] for c in calls}
        assert deleted_ids == {"20001", "20003"}

    def test_unlink_not_found(self, mock_jira_client, sample_issue_links):
        """Test error when link doesn't exist."""
        mock_jira_client.get_issue_links.return_value = sample_issue_links

        import unlink_issue
        from error_handler import ValidationError

        with patch.object(unlink_issue, 'get_jira_client', return_value=mock_jira_client):
            with pytest.raises(ValidationError) as exc_info:
                unlink_issue.unlink_issue(
                    issue_key="PROJ-123",
                    from_issue="PROJ-999"  # Not linked
                )

        assert "not linked" in str(exc_info.value).lower() or "not found" in str(exc_info.value).lower()

    def test_unlink_dry_run(self, mock_jira_client, sample_issue_links):
        """Test preview without deleting."""
        mock_jira_client.get_issue_links.return_value = sample_issue_links

        import unlink_issue
        with patch.object(unlink_issue, 'get_jira_client', return_value=mock_jira_client):
            result = unlink_issue.unlink_issue(
                issue_key="PROJ-123",
                from_issue="PROJ-456",
                dry_run=True
            )

        # Should NOT delete
        mock_jira_client.delete_link.assert_not_called()
        # Should return info about what would be deleted
        assert result is not None

    def test_unlink_requires_target_or_all(self, mock_jira_client):
        """Test error when neither target nor --all specified."""
        import unlink_issue
        from error_handler import ValidationError

        with patch.object(unlink_issue, 'get_jira_client', return_value=mock_jira_client):
            with pytest.raises(ValidationError) as exc_info:
                unlink_issue.unlink_issue(
                    issue_key="PROJ-123"
                )

        assert "specify" in str(exc_info.value).lower()


@pytest.mark.relationships
@pytest.mark.unit
class TestUnlinkIssueErrorHandling:
    """Test API error handling scenarios for unlink_issue."""

    def test_authentication_error(self, mock_jira_client, sample_issue_links):
        """Test handling of 401 unauthorized."""
        from error_handler import AuthenticationError

        mock_jira_client.get_issue_links.return_value = sample_issue_links
        mock_jira_client.delete_link.side_effect = AuthenticationError("Invalid token")

        import unlink_issue
        with patch.object(unlink_issue, 'get_jira_client', return_value=mock_jira_client):
            with pytest.raises(AuthenticationError):
                unlink_issue.unlink_issue(issue_key="PROJ-123", from_issue="PROJ-456")

    def test_forbidden_error(self, mock_jira_client, sample_issue_links):
        """Test handling of 403 forbidden."""
        from error_handler import PermissionError

        mock_jira_client.get_issue_links.return_value = sample_issue_links
        mock_jira_client.delete_link.side_effect = PermissionError("Insufficient permissions")

        import unlink_issue
        with patch.object(unlink_issue, 'get_jira_client', return_value=mock_jira_client):
            with pytest.raises(PermissionError):
                unlink_issue.unlink_issue(issue_key="PROJ-123", from_issue="PROJ-456")

    def test_link_not_found_error(self, mock_jira_client, sample_issue_links):
        """Test handling of 404 link not found."""
        from error_handler import NotFoundError

        mock_jira_client.get_issue_links.return_value = sample_issue_links
        mock_jira_client.delete_link.side_effect = NotFoundError("Link not found")

        import unlink_issue
        with patch.object(unlink_issue, 'get_jira_client', return_value=mock_jira_client):
            with pytest.raises(NotFoundError):
                unlink_issue.unlink_issue(issue_key="PROJ-123", from_issue="PROJ-456")

    def test_rate_limit_error(self, mock_jira_client, sample_issue_links):
        """Test handling of 429 rate limit."""
        from error_handler import JiraError

        mock_jira_client.get_issue_links.return_value = sample_issue_links
        mock_jira_client.delete_link.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        import unlink_issue
        with patch.object(unlink_issue, 'get_jira_client', return_value=mock_jira_client):
            with pytest.raises(JiraError) as exc_info:
                unlink_issue.unlink_issue(issue_key="PROJ-123", from_issue="PROJ-456")
            assert exc_info.value.status_code == 429

    def test_server_error(self, mock_jira_client, sample_issue_links):
        """Test handling of 500 server error."""
        from error_handler import JiraError

        mock_jira_client.get_issue_links.return_value = sample_issue_links
        mock_jira_client.delete_link.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        import unlink_issue
        with patch.object(unlink_issue, 'get_jira_client', return_value=mock_jira_client):
            with pytest.raises(JiraError) as exc_info:
                unlink_issue.unlink_issue(issue_key="PROJ-123", from_issue="PROJ-456")
            assert exc_info.value.status_code == 500
