"""
Tests for update_comment.py - Update existing comment.
"""

import copy
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add script path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


@pytest.mark.collaborate
@pytest.mark.unit
class TestUpdateComment:
    """Tests for updating comments."""

    @patch("update_comment.get_jira_client")
    def test_update_comment_body(
        self, mock_get_client, mock_jira_client, sample_comment
    ):
        """Test updating comment body."""
        mock_get_client.return_value = mock_jira_client
        updated_comment = copy.deepcopy(sample_comment)
        updated_comment["body"]["content"][0]["content"][0]["text"] = "Updated text"
        mock_jira_client.update_comment.return_value = updated_comment

        from update_comment import update_comment

        result = update_comment(
            "PROJ-123", "10001", "Updated text", format_type="text", profile=None
        )

        assert result["id"] == "10001"
        mock_jira_client.update_comment.assert_called_once()
        call_args = mock_jira_client.update_comment.call_args
        assert call_args[0][0] == "PROJ-123"
        assert call_args[0][1] == "10001"
        # Body should be ADF format
        assert "type" in call_args[0][2]

    @patch("update_comment.get_jira_client")
    def test_update_comment_with_markdown(
        self, mock_get_client, mock_jira_client, sample_comment
    ):
        """Test updating with markdown format."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.update_comment.return_value = sample_comment

        from update_comment import update_comment

        update_comment(
            "PROJ-123",
            "10001",
            "## New heading\n**Bold text**",
            format_type="markdown",
            profile=None,
        )

        call_args = mock_jira_client.update_comment.call_args
        body_adf = call_args[0][2]
        # Should have converted markdown to ADF
        assert body_adf["type"] == "doc"

    @patch("update_comment.get_jira_client")
    def test_update_comment_not_author(self, mock_get_client, mock_jira_client):
        """Test error when not comment author."""
        from jira_assistant_skills_lib import PermissionError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.update_comment.side_effect = PermissionError(
            "You do not have permission to edit this comment"
        )

        from update_comment import update_comment

        with pytest.raises(PermissionError):
            update_comment("PROJ-123", "10001", "Updated text", profile=None)

    @patch("update_comment.get_jira_client")
    def test_update_comment_not_found(self, mock_get_client, mock_jira_client):
        """Test error when comment doesn't exist."""
        from jira_assistant_skills_lib import NotFoundError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.update_comment.side_effect = NotFoundError(
            "Comment 99999 not found"
        )

        from update_comment import update_comment

        with pytest.raises(NotFoundError):
            update_comment("PROJ-123", "99999", "Updated text", profile=None)

    @patch("update_comment.get_jira_client")
    def test_update_preserves_visibility(
        self, mock_get_client, mock_jira_client, sample_comment_with_visibility
    ):
        """Test that visibility is preserved on update."""
        # The implementation should use the existing comment's visibility
        # This test verifies that update_comment doesn't strip visibility
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.update_comment.return_value = sample_comment_with_visibility

        from update_comment import update_comment

        result = update_comment(
            "PROJ-123", "10002", "Updated internal note", profile=None
        )

        # Visibility should still be present in result
        assert result.get("visibility") is not None
        assert result["visibility"]["type"] == "role"


@pytest.mark.collaborate
@pytest.mark.unit
class TestUpdateCommentErrorHandling:
    """Test API error handling scenarios for update_comment."""

    @patch("update_comment.get_jira_client")
    def test_authentication_error(self, mock_get_client, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from jira_assistant_skills_lib import AuthenticationError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.update_comment.side_effect = AuthenticationError(
            "Invalid API token"
        )

        from update_comment import update_comment

        with pytest.raises(AuthenticationError):
            update_comment("PROJ-123", "10001", "Updated text", profile=None)

    @patch("update_comment.get_jira_client")
    def test_rate_limit_error(self, mock_get_client, mock_jira_client):
        """Test handling of 429 rate limit."""
        from jira_assistant_skills_lib import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.update_comment.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        from update_comment import update_comment

        with pytest.raises(JiraError) as exc_info:
            update_comment("PROJ-123", "10001", "Updated text", profile=None)
        assert exc_info.value.status_code == 429

    @patch("update_comment.get_jira_client")
    def test_server_error(self, mock_get_client, mock_jira_client):
        """Test handling of 500 server error."""
        from jira_assistant_skills_lib import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.update_comment.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        from update_comment import update_comment

        with pytest.raises(JiraError) as exc_info:
            update_comment("PROJ-123", "10001", "Updated text", profile=None)
        assert exc_info.value.status_code == 500
