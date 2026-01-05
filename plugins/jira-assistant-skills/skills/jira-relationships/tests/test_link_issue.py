"""
Tests for link_issue.py

TDD tests for creating links between issues.
"""

from unittest.mock import patch

import pytest

# Import will be done inside tests after path setup via conftest


@pytest.mark.relationships
@pytest.mark.unit
class TestLinkIssue:
    """Tests for the link_issue function."""

    def test_link_blocks(self, mock_jira_client, sample_link_types):
        """Test creating 'blocks' link between two issues."""
        mock_jira_client.get_link_types.return_value = sample_link_types

        import link_issue

        with patch.object(link_issue, "get_jira_client", return_value=mock_jira_client):
            link_issue.link_issue(issue_key="PROJ-1", blocks="PROJ-2")

        mock_jira_client.create_link.assert_called_once_with(
            "Blocks", "PROJ-2", "PROJ-1", None
        )

    def test_link_duplicates(self, mock_jira_client, sample_link_types):
        """Test creating 'duplicates' link."""
        mock_jira_client.get_link_types.return_value = sample_link_types

        import link_issue

        with patch.object(link_issue, "get_jira_client", return_value=mock_jira_client):
            link_issue.link_issue(issue_key="PROJ-1", duplicates="PROJ-2")

        mock_jira_client.create_link.assert_called_once_with(
            "Duplicate", "PROJ-2", "PROJ-1", None
        )

    def test_link_relates_to(self, mock_jira_client, sample_link_types):
        """Test creating 'relates to' link."""
        mock_jira_client.get_link_types.return_value = sample_link_types

        import link_issue

        with patch.object(link_issue, "get_jira_client", return_value=mock_jira_client):
            link_issue.link_issue(issue_key="PROJ-1", relates_to="PROJ-2")

        mock_jira_client.create_link.assert_called_once_with(
            "Relates", "PROJ-2", "PROJ-1", None
        )

    def test_link_clones(self, mock_jira_client, sample_link_types):
        """Test creating 'clones' link."""
        mock_jira_client.get_link_types.return_value = sample_link_types

        import link_issue

        with patch.object(link_issue, "get_jira_client", return_value=mock_jira_client):
            link_issue.link_issue(issue_key="PROJ-1", clones="PROJ-2")

        mock_jira_client.create_link.assert_called_once_with(
            "Cloners", "PROJ-2", "PROJ-1", None
        )

    def test_link_with_comment(self, mock_jira_client, sample_link_types):
        """Test adding comment when creating link."""
        mock_jira_client.get_link_types.return_value = sample_link_types

        import link_issue

        with patch.object(link_issue, "get_jira_client", return_value=mock_jira_client):
            link_issue.link_issue(
                issue_key="PROJ-1",
                blocks="PROJ-2",
                comment="Dependency added for release",
            )

        # Verify comment was passed (as ADF)
        call_args = mock_jira_client.create_link.call_args
        assert call_args[0][3] is not None  # comment argument

    def test_link_type_not_found(self, mock_jira_client, sample_link_types):
        """Test error when link type doesn't exist."""
        mock_jira_client.get_link_types.return_value = sample_link_types

        import link_issue
        from assistant_skills_lib.error_handler import ValidationError

        with patch.object(link_issue, "get_jira_client", return_value=mock_jira_client):
            with pytest.raises(ValidationError) as exc_info:
                link_issue.link_issue(
                    issue_key="PROJ-1", link_type="NonExistent", target_issue="PROJ-2"
                )

        assert "not found" in str(exc_info.value).lower()

    def test_link_invalid_issue(self, mock_jira_client, sample_link_types):
        """Test error when issue key is invalid."""
        import link_issue
        from assistant_skills_lib.error_handler import ValidationError

        with patch.object(link_issue, "get_jira_client", return_value=mock_jira_client):
            with pytest.raises(ValidationError):
                link_issue.link_issue(issue_key="invalid", blocks="PROJ-2")

    def test_link_self_reference(self, mock_jira_client, sample_link_types):
        """Test validation preventing linking issue to itself."""
        import link_issue
        from assistant_skills_lib.error_handler import ValidationError

        with patch.object(link_issue, "get_jira_client", return_value=mock_jira_client):
            with pytest.raises(ValidationError) as exc_info:
                link_issue.link_issue(issue_key="PROJ-1", blocks="PROJ-1")

        assert "itself" in str(exc_info.value).lower()

    def test_link_with_explicit_type(self, mock_jira_client, sample_link_types):
        """Test using explicit --type flag."""
        mock_jira_client.get_link_types.return_value = sample_link_types

        import link_issue

        with patch.object(link_issue, "get_jira_client", return_value=mock_jira_client):
            link_issue.link_issue(
                issue_key="PROJ-1", link_type="Blocks", target_issue="PROJ-2"
            )

        mock_jira_client.create_link.assert_called_once()

    def test_dry_run_mode(self, mock_jira_client, sample_link_types):
        """Test preview without creating link."""
        mock_jira_client.get_link_types.return_value = sample_link_types

        import link_issue

        with patch.object(link_issue, "get_jira_client", return_value=mock_jira_client):
            result = link_issue.link_issue(
                issue_key="PROJ-1", blocks="PROJ-2", dry_run=True
            )

        # Should NOT call create_link
        mock_jira_client.create_link.assert_not_called()
        # Should return preview info
        assert result is not None
        assert "PROJ-1" in str(result)
        assert "PROJ-2" in str(result)


@pytest.mark.relationships
@pytest.mark.unit
class TestLinkIssueErrorHandling:
    """Test API error handling scenarios for link_issue."""

    def test_authentication_error(self, mock_jira_client, sample_link_types):
        """Test handling of 401 unauthorized."""
        from jira_assistant_skills_lib import AuthenticationError

        mock_jira_client.get_link_types.return_value = sample_link_types
        mock_jira_client.create_link.side_effect = AuthenticationError("Invalid token")

        import link_issue

        with patch.object(link_issue, "get_jira_client", return_value=mock_jira_client):
            with pytest.raises(AuthenticationError):
                link_issue.link_issue(issue_key="PROJ-1", blocks="PROJ-2")

    def test_forbidden_error(self, mock_jira_client, sample_link_types):
        """Test handling of 403 forbidden."""
        from jira_assistant_skills_lib import PermissionError

        mock_jira_client.get_link_types.return_value = sample_link_types
        mock_jira_client.create_link.side_effect = PermissionError(
            "Insufficient permissions"
        )

        import link_issue

        with patch.object(link_issue, "get_jira_client", return_value=mock_jira_client):
            with pytest.raises(PermissionError):
                link_issue.link_issue(issue_key="PROJ-1", blocks="PROJ-2")

    def test_issue_not_found_error(self, mock_jira_client, sample_link_types):
        """Test handling of 404 issue not found."""
        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.get_link_types.return_value = sample_link_types
        mock_jira_client.create_link.side_effect = NotFoundError(
            "Issue PROJ-2 not found"
        )

        import link_issue

        with patch.object(link_issue, "get_jira_client", return_value=mock_jira_client):
            with pytest.raises(NotFoundError):
                link_issue.link_issue(issue_key="PROJ-1", blocks="PROJ-2")

    def test_rate_limit_error(self, mock_jira_client, sample_link_types):
        """Test handling of 429 rate limit."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.get_link_types.return_value = sample_link_types
        mock_jira_client.create_link.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        import link_issue

        with patch.object(link_issue, "get_jira_client", return_value=mock_jira_client):
            with pytest.raises(JiraError) as exc_info:
                link_issue.link_issue(issue_key="PROJ-1", blocks="PROJ-2")
            assert exc_info.value.status_code == 429

    def test_server_error(self, mock_jira_client, sample_link_types):
        """Test handling of 500 server error."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.get_link_types.return_value = sample_link_types
        mock_jira_client.create_link.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        import link_issue

        with patch.object(link_issue, "get_jira_client", return_value=mock_jira_client):
            with pytest.raises(JiraError) as exc_info:
                link_issue.link_issue(issue_key="PROJ-1", blocks="PROJ-2")
            assert exc_info.value.status_code == 500
