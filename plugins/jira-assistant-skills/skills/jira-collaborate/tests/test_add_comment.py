"""
Tests for add_comment.py - Add comments to JIRA issues.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add script path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


@pytest.fixture
def sample_comment_response():
    """Sample comment response from JIRA."""
    return {
        "id": "10001",
        "author": {"accountId": "user123", "displayName": "John Smith"},
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Test comment"}],
                }
            ],
        },
        "created": "2024-01-15T10:00:00.000+0000",
        "updated": "2024-01-15T10:00:00.000+0000",
    }


@pytest.fixture
def sample_visibility_comment():
    """Sample comment with visibility restrictions."""
    return {
        "id": "10002",
        "author": {"accountId": "user123", "displayName": "John Smith"},
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Internal note"}],
                }
            ],
        },
        "visibility": {"type": "role", "value": "Administrators"},
        "created": "2024-01-15T10:00:00.000+0000",
    }


@pytest.mark.collaborate
@pytest.mark.unit
class TestAddComment:
    """Tests for add_comment function."""

    def test_add_comment_text(self, mock_jira_client, sample_comment_response):
        """Test adding a plain text comment."""
        mock_jira_client.add_comment.return_value = sample_comment_response

        with patch("add_comment.get_jira_client", return_value=mock_jira_client):
            from add_comment import add_comment

            result = add_comment("PROJ-123", "Test comment", format_type="text")

            assert result["id"] == "10001"
            mock_jira_client.add_comment.assert_called_once()

    def test_add_comment_markdown(self, mock_jira_client, sample_comment_response):
        """Test adding a markdown comment."""
        mock_jira_client.add_comment.return_value = sample_comment_response

        with patch("add_comment.get_jira_client", return_value=mock_jira_client):
            from add_comment import add_comment

            result = add_comment("PROJ-123", "**Bold text**", format_type="markdown")

            assert result["id"] == "10001"
            mock_jira_client.add_comment.assert_called_once()

    def test_add_comment_adf(self, mock_jira_client, sample_comment_response):
        """Test adding an ADF format comment."""
        mock_jira_client.add_comment.return_value = sample_comment_response
        adf_body = json.dumps({"type": "doc", "version": 1, "content": []})

        with patch("add_comment.get_jira_client", return_value=mock_jira_client):
            from add_comment import add_comment

            result = add_comment("PROJ-123", adf_body, format_type="adf")

            assert result["id"] == "10001"
            mock_jira_client.add_comment.assert_called_once()

@pytest.mark.collaborate
@pytest.mark.unit
class TestAddCommentWithVisibility:
    """Tests for add_comment_with_visibility function."""

    def test_add_comment_with_role_visibility(
        self, mock_jira_client, sample_visibility_comment
    ):
        """Test adding comment visible to a role."""
        mock_jira_client.add_comment_with_visibility.return_value = (
            sample_visibility_comment
        )

        with patch("add_comment.get_jira_client", return_value=mock_jira_client):
            from add_comment import add_comment_with_visibility

            result = add_comment_with_visibility(
                "PROJ-123",
                "Internal note",
                visibility_type="role",
                visibility_value="Administrators",
            )

            assert result["visibility"]["type"] == "role"
            assert result["visibility"]["value"] == "Administrators"
            mock_jira_client.add_comment_with_visibility.assert_called_once()

    def test_add_comment_with_group_visibility(
        self, mock_jira_client, sample_visibility_comment
    ):
        """Test adding comment visible to a group."""
        sample_visibility_comment["visibility"]["type"] = "group"
        sample_visibility_comment["visibility"]["value"] = "developers"
        mock_jira_client.add_comment_with_visibility.return_value = (
            sample_visibility_comment
        )

        with patch("add_comment.get_jira_client", return_value=mock_jira_client):
            from add_comment import add_comment_with_visibility

            result = add_comment_with_visibility(
                "PROJ-123",
                "Dev note",
                visibility_type="group",
                visibility_value="developers",
            )

            assert result["visibility"]["type"] == "group"

    def test_add_visibility_comment_markdown(
        self, mock_jira_client, sample_visibility_comment
    ):
        """Test adding visibility-restricted markdown comment."""
        mock_jira_client.add_comment_with_visibility.return_value = (
            sample_visibility_comment
        )

        with patch("add_comment.get_jira_client", return_value=mock_jira_client):
            from add_comment import add_comment_with_visibility

            result = add_comment_with_visibility(
                "PROJ-123",
                "**Internal**",
                format_type="markdown",
                visibility_type="role",
                visibility_value="Administrators",
            )

            assert result["id"] == "10002"


@pytest.mark.collaborate
@pytest.mark.unit
class TestAddCommentMain:
    """Tests for main() function."""

    def test_main_simple_comment(
        self, mock_jira_client, sample_comment_response, capsys
    ):
        """Test main with simple text comment."""
        mock_jira_client.add_comment.return_value = sample_comment_response

        with patch("add_comment.get_jira_client", return_value=mock_jira_client):
            from add_comment import main

            main(["PROJ-123", "--body", "Test comment"])

            captured = capsys.readouterr()
            assert "Added comment" in captured.out
            assert "PROJ-123" in captured.out
            assert "10001" in captured.out

    def test_main_markdown_comment(
        self, mock_jira_client, sample_comment_response, capsys
    ):
        """Test main with markdown format."""
        mock_jira_client.add_comment.return_value = sample_comment_response

        with patch("add_comment.get_jira_client", return_value=mock_jira_client):
            from add_comment import main

            main(["PROJ-123", "--body", "**Bold**", "--format", "markdown"])

            captured = capsys.readouterr()
            assert "Added comment" in captured.out

    def test_main_adf_comment(self, mock_jira_client, sample_comment_response, capsys):
        """Test main with ADF format."""
        mock_jira_client.add_comment.return_value = sample_comment_response
        adf = '{"type":"doc","version":1,"content":[]}'

        with patch("add_comment.get_jira_client", return_value=mock_jira_client):
            from add_comment import main

            main(["PROJ-123", "--body", adf, "--format", "adf"])

            captured = capsys.readouterr()
            assert "Added comment" in captured.out

    def test_main_with_role_visibility(
        self, mock_jira_client, sample_visibility_comment, capsys
    ):
        """Test main with role visibility."""
        mock_jira_client.add_comment_with_visibility.return_value = (
            sample_visibility_comment
        )

        with patch("add_comment.get_jira_client", return_value=mock_jira_client):
            from add_comment import main

            main(
                [
                    "PROJ-123",
                    "--body",
                    "Internal",
                    "--visibility-role",
                    "Administrators",
                ]
            )

            captured = capsys.readouterr()
            assert "Added comment" in captured.out
            assert "Visibility" in captured.out
            assert "Administrators" in captured.out

    def test_main_with_group_visibility(
        self, mock_jira_client, sample_visibility_comment, capsys
    ):
        """Test main with group visibility."""
        sample_visibility_comment["visibility"]["type"] = "group"
        sample_visibility_comment["visibility"]["value"] = "developers"
        mock_jira_client.add_comment_with_visibility.return_value = (
            sample_visibility_comment
        )

        with patch("add_comment.get_jira_client", return_value=mock_jira_client):
            from add_comment import main

            main(["PROJ-123", "--body", "Dev note", "--visibility-group", "developers"])

            captured = capsys.readouterr()
            assert "Added comment" in captured.out
            assert "Visibility" in captured.out
            assert "developers" in captured.out

    def test_main_both_visibility_error(self, mock_jira_client, capsys):
        """Test main with both visibility options raises error."""
        with patch("add_comment.get_jira_client", return_value=mock_jira_client):
            from add_comment import main

            with pytest.raises(SystemExit) as exc_info:
                main(
                    [
                        "PROJ-123",
                        "--body",
                        "Note",
                        "--visibility-role",
                        "Admin",
                        "--visibility-group",
                        "dev",
                    ]
                )

            assert exc_info.value.code == 1

    def test_main_jira_error(self, mock_jira_client, capsys):
        """Test main with JIRA API error."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.add_comment.side_effect = JiraError(
            "API Error", status_code=500
        )

        with patch("add_comment.get_jira_client", return_value=mock_jira_client):
            from add_comment import main

            with pytest.raises(SystemExit) as exc_info:
                main(["PROJ-123", "--body", "Comment"])

            assert exc_info.value.code == 1

    def test_main_general_exception(self, mock_jira_client, capsys):
        """Test main with unexpected error."""
        mock_jira_client.add_comment.side_effect = Exception("Unexpected error")

        with patch("add_comment.get_jira_client", return_value=mock_jira_client):
            from add_comment import main

            with pytest.raises(SystemExit) as exc_info:
                main(["PROJ-123", "--body", "Comment"])

            assert exc_info.value.code == 1


@pytest.mark.collaborate
@pytest.mark.unit
class TestAddCommentErrors:
    """Tests for error handling."""

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from jira_assistant_skills_lib import AuthenticationError

        mock_jira_client.add_comment.side_effect = AuthenticationError("Invalid token")

        with patch("add_comment.get_jira_client", return_value=mock_jira_client):
            from add_comment import add_comment

            with pytest.raises(AuthenticationError):
                add_comment("PROJ-123", "Comment")

    def test_not_found_error(self, mock_jira_client):
        """Test handling of 404 not found."""
        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.add_comment.side_effect = NotFoundError("Issue not found")

        with patch("add_comment.get_jira_client", return_value=mock_jira_client):
            from add_comment import add_comment

            with pytest.raises(NotFoundError):
                add_comment("PROJ-999", "Comment")

    def test_permission_error(self, mock_jira_client):
        """Test handling of 403 forbidden."""
        from jira_assistant_skills_lib import PermissionError

        mock_jira_client.add_comment.side_effect = PermissionError("No permission")

        with patch("add_comment.get_jira_client", return_value=mock_jira_client):
            from add_comment import add_comment

            with pytest.raises(PermissionError):
                add_comment("PROJ-123", "Comment")
