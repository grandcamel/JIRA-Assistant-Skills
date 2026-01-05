"""
Tests for get_comments.py - Get comments on an issue.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add script path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


@pytest.mark.collaborate
@pytest.mark.unit
class TestGetComments:
    """Tests for getting comments on issues."""

    @patch("get_comments.get_jira_client")
    def test_get_all_comments(
        self, mock_get_client, mock_jira_client, sample_comments_list
    ):
        """Test fetching all comments on an issue."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_comments.return_value = sample_comments_list

        from get_comments import get_comments

        result = get_comments("PROJ-123", profile=None)

        assert len(result["comments"]) == 3
        assert result["total"] == 3
        assert result["comments"][0]["author"]["displayName"] == "Alice Smith"
        mock_jira_client.get_comments.assert_called_once_with(
            "PROJ-123", max_results=50, start_at=0, order_by="-created"
        )

    @patch("get_comments.get_jira_client")
    def test_get_comments_with_pagination(
        self, mock_get_client, mock_jira_client, sample_comments_list
    ):
        """Test paginated comment retrieval."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_comments.return_value = sample_comments_list

        from get_comments import get_comments

        get_comments("PROJ-123", limit=10, offset=5, profile=None)

        mock_jira_client.get_comments.assert_called_once_with(
            "PROJ-123", max_results=10, start_at=5, order_by="-created"
        )

    @patch("get_comments.get_jira_client")
    def test_get_comments_order_by_created(
        self, mock_get_client, mock_jira_client, sample_comments_list
    ):
        """Test ordering comments by creation date."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_comments.return_value = sample_comments_list

        from get_comments import get_comments

        # Default: newest first (-created)
        get_comments("PROJ-123", profile=None)
        mock_jira_client.get_comments.assert_called_with(
            "PROJ-123", max_results=50, start_at=0, order_by="-created"
        )

        # Oldest first (+created)
        get_comments("PROJ-123", order="asc", profile=None)
        assert mock_jira_client.get_comments.call_args[1]["order_by"] == "+created"

    @patch("get_comments.get_jira_client")
    def test_get_comments_empty(self, mock_get_client, mock_jira_client):
        """Test handling issue with no comments."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_comments.return_value = {
            "startAt": 0,
            "maxResults": 50,
            "total": 0,
            "comments": [],
        }

        from get_comments import get_comments

        result = get_comments("PROJ-123", profile=None)

        assert result["total"] == 0
        assert len(result["comments"]) == 0

    @patch("get_comments.get_jira_client")
    def test_get_single_comment(
        self, mock_get_client, mock_jira_client, sample_comment
    ):
        """Test fetching a specific comment by ID."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_comment.return_value = sample_comment

        from get_comments import get_comment_by_id

        result = get_comment_by_id("PROJ-123", "10001", profile=None)

        assert result["id"] == "10001"
        assert result["author"]["displayName"] == "Alice Smith"
        mock_jira_client.get_comment.assert_called_once_with("PROJ-123", "10001")

    def test_format_text_output(self, mock_jira_client, sample_comments_list):
        """Test human-readable table output."""
        mock_jira_client.get_comments.return_value = sample_comments_list

        from get_comments import format_comments_table

        table = format_comments_table(sample_comments_list["comments"])

        # Should contain author, date, and body preview
        assert "Alice Smith" in table
        assert "Bob Jones" in table
        assert "10003" in table  # Comment ID

    @patch("get_comments.get_jira_client")
    def test_format_json_output(
        self, mock_get_client, mock_jira_client, sample_comments_list
    ):
        """Test JSON output format."""
        import json

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_comments.return_value = sample_comments_list

        from get_comments import get_comments

        result = get_comments("PROJ-123", profile=None)

        # Should be JSON serializable
        json_str = json.dumps(result)
        assert json_str is not None
        assert "comments" in result


@pytest.mark.collaborate
@pytest.mark.unit
class TestGetCommentsErrorHandling:
    """Test API error handling scenarios for get_comments."""

    @patch("get_comments.get_jira_client")
    def test_authentication_error(self, mock_get_client, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from jira_assistant_skills_lib import AuthenticationError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_comments.side_effect = AuthenticationError(
            "Invalid API token"
        )

        from get_comments import get_comments

        with pytest.raises(AuthenticationError):
            get_comments("PROJ-123", profile=None)

    @patch("get_comments.get_jira_client")
    def test_permission_error(self, mock_get_client, mock_jira_client):
        """Test handling of 403 forbidden."""
        from jira_assistant_skills_lib import PermissionError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_comments.side_effect = PermissionError(
            "No permission to view comments"
        )

        from get_comments import get_comments

        with pytest.raises(PermissionError):
            get_comments("PROJ-123", profile=None)

    @patch("get_comments.get_jira_client")
    def test_not_found_error(self, mock_get_client, mock_jira_client):
        """Test handling of 404 not found."""
        from jira_assistant_skills_lib import NotFoundError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_comments.side_effect = NotFoundError(
            "Issue PROJ-999 not found"
        )

        from get_comments import get_comments

        with pytest.raises(NotFoundError):
            get_comments("PROJ-999", profile=None)

    @patch("get_comments.get_jira_client")
    def test_rate_limit_error(self, mock_get_client, mock_jira_client):
        """Test handling of 429 rate limit."""
        from jira_assistant_skills_lib import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_comments.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        from get_comments import get_comments

        with pytest.raises(JiraError) as exc_info:
            get_comments("PROJ-123", profile=None)
        assert exc_info.value.status_code == 429

    @patch("get_comments.get_jira_client")
    def test_server_error(self, mock_get_client, mock_jira_client):
        """Test handling of 500 server error."""
        from jira_assistant_skills_lib import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_comments.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        from get_comments import get_comments

        with pytest.raises(JiraError) as exc_info:
            get_comments("PROJ-123", profile=None)
        assert exc_info.value.status_code == 500
