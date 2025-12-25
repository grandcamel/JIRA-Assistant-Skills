"""
Tests for unlink_issue.py

TDD tests for removing issue links.
"""

import pytest
from unittest.mock import Mock, patch, call


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
