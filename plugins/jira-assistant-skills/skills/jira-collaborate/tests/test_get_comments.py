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

        result = get_comments("PROJ-123")

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

        get_comments("PROJ-123", limit=10, offset=5)

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
        get_comments("PROJ-123")
        mock_jira_client.get_comments.assert_called_with(
            "PROJ-123", max_results=50, start_at=0, order_by="-created"
        )

        # Oldest first (+created)
        get_comments("PROJ-123", order="asc")
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

        result = get_comments("PROJ-123")

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

        result = get_comment_by_id("PROJ-123", "10001")

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

        result = get_comments("PROJ-123")

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
            get_comments("PROJ-123")

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
            get_comments("PROJ-123")

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
            get_comments("PROJ-999")

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
            get_comments("PROJ-123")
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
            get_comments("PROJ-123")
        assert exc_info.value.status_code == 500


@pytest.mark.collaborate
@pytest.mark.unit
class TestGetCommentsMain:
    """Tests for main() function."""

    @patch("get_comments.get_jira_client")
    def test_main_get_all_comments(
        self, mock_get_client, mock_jira_client, sample_comments_list, capsys
    ):
        """Test main getting all comments."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_comments.return_value = sample_comments_list

        from get_comments import main

        main(["PROJ-123"])

        captured = capsys.readouterr()
        assert "Comments on PROJ-123" in captured.out
        assert "3 total" in captured.out

    @patch("get_comments.get_jira_client")
    def test_main_get_comment_by_id(
        self, mock_get_client, mock_jira_client, sample_comment, capsys
    ):
        """Test main getting specific comment by ID."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_comment.return_value = sample_comment

        from get_comments import main

        main(["PROJ-123", "--id", "10001"])

        captured = capsys.readouterr()
        assert "Comment 10001" in captured.out
        assert "Alice Smith" in captured.out

    @patch("get_comments.get_jira_client")
    def test_main_json_output(
        self, mock_get_client, mock_jira_client, sample_comments_list, capsys
    ):
        """Test main with JSON output."""
        import json

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_comments.return_value = sample_comments_list

        from get_comments import main

        main(["PROJ-123", "--output", "json"])

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert "comments" in output

    @patch("get_comments.get_jira_client")
    def test_main_json_single_comment(
        self, mock_get_client, mock_jira_client, sample_comment, capsys
    ):
        """Test main with JSON output for single comment."""
        import json

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_comment.return_value = sample_comment

        from get_comments import main

        main(["PROJ-123", "--id", "10001", "--output", "json"])

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["id"] == "10001"

    @patch("get_comments.get_jira_client")
    def test_main_with_pagination(
        self, mock_get_client, mock_jira_client, sample_comments_list, capsys
    ):
        """Test main with limit and offset."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_comments.return_value = sample_comments_list

        from get_comments import main

        main(["PROJ-123", "--limit", "10", "--offset", "5"])

        mock_jira_client.get_comments.assert_called_with(
            "PROJ-123", max_results=10, start_at=5, order_by="-created"
        )

    @patch("get_comments.get_jira_client")
    def test_main_order_asc(
        self, mock_get_client, mock_jira_client, sample_comments_list, capsys
    ):
        """Test main with ascending order."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_comments.return_value = sample_comments_list

        from get_comments import main

        main(["PROJ-123", "--order", "asc"])

        mock_jira_client.get_comments.assert_called_with(
            "PROJ-123", max_results=50, start_at=0, order_by="+created"
        )

    @patch("get_comments.get_jira_client")
    def test_main_no_comments(self, mock_get_client, mock_jira_client, capsys):
        """Test main with no comments."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_comments.return_value = {"total": 0, "comments": []}

        from get_comments import main

        main(["PROJ-123"])

        captured = capsys.readouterr()
        assert "No comments found" in captured.out

    @patch("get_comments.get_jira_client")
    def test_main_with_visibility(self, mock_get_client, mock_jira_client, capsys):
        """Test main showing comment with visibility."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_comment.return_value = {
            "id": "10001",
            "author": {"displayName": "Alice"},
            "created": "2024-01-15T10:00:00.000+0000",
            "body": {"type": "doc", "version": 1, "content": []},
            "visibility": {"type": "role", "value": "Administrators"},
        }

        from get_comments import main

        main(["PROJ-123", "--id", "10001"])

        captured = capsys.readouterr()
        assert "Visibility" in captured.out
        assert "Administrators" in captured.out

    @patch("get_comments.get_jira_client")
    def test_main_public_visibility(
        self, mock_get_client, mock_jira_client, sample_comment, capsys
    ):
        """Test main showing public comment."""
        mock_get_client.return_value = mock_jira_client
        # Ensure no visibility field
        sample_comment.pop("visibility", None)
        mock_jira_client.get_comment.return_value = sample_comment

        from get_comments import main

        main(["PROJ-123", "--id", "10001"])

        captured = capsys.readouterr()
        assert "Public" in captured.out

    @patch("get_comments.get_jira_client")
    def test_main_pagination_hint(self, mock_get_client, mock_jira_client, capsys):
        """Test main shows pagination hint when more comments exist."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_comments.return_value = {
            "total": 100,
            "comments": [
                {
                    "id": "1",
                    "author": {"displayName": "Test"},
                    "created": "2024-01-15T10:00:00.000+0000",
                    "body": {},
                }
            ],
        }

        from get_comments import main

        main(["PROJ-123"])

        captured = capsys.readouterr()
        assert "100 total" in captured.out
        assert "Use --limit" in captured.out

    @patch("get_comments.get_jira_client")
    def test_main_jira_error(self, mock_get_client, mock_jira_client):
        """Test main with JIRA API error."""
        from jira_assistant_skills_lib import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_comments.side_effect = JiraError(
            "API Error", status_code=500
        )

        from get_comments import main

        with pytest.raises(SystemExit) as exc_info:
            main(["PROJ-123"])

        assert exc_info.value.code == 1

    @patch("get_comments.get_jira_client")
    def test_main_general_exception(self, mock_get_client, mock_jira_client):
        """Test main with unexpected error."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_comments.side_effect = Exception("Unexpected error")

        from get_comments import main

        with pytest.raises(SystemExit) as exc_info:
            main(["PROJ-123"])

        assert exc_info.value.code == 1


@pytest.mark.collaborate
@pytest.mark.unit
class TestFormatCommentBody:
    """Tests for format_comment_body function."""

    def test_format_short_body(self):
        """Test formatting short comment body."""
        from get_comments import format_comment_body

        body = {
            "type": "doc",
            "version": 1,
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": "Short"}]}
            ],
        }

        result = format_comment_body(body)
        assert result == "Short"

    def test_format_long_body_truncates(self):
        """Test formatting long comment body truncates."""
        from get_comments import format_comment_body

        long_text = "A" * 100
        body = {
            "type": "doc",
            "version": 1,
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": long_text}]}
            ],
        }

        result = format_comment_body(body, max_length=50)
        assert len(result) == 53  # 50 chars + '...'
        assert result.endswith("...")
