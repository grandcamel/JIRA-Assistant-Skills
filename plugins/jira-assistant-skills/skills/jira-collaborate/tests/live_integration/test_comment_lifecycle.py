"""
Live Integration Tests: Comment Lifecycle

Tests for complete comment lifecycle (add, get, update, delete) against a real JIRA instance.
"""

import uuid

import pytest


@pytest.mark.integration
@pytest.mark.collaborate
@pytest.mark.comments
class TestCommentCreation:
    """Tests for creating comments."""

    def test_add_simple_comment(self, jira_client, test_issue):
        """Test adding a basic comment to an issue."""
        comment_text = f"Test comment {uuid.uuid4().hex[:8]}"
        comment_body = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": comment_text}],
                }
            ],
        }

        result = jira_client.add_comment(test_issue["key"], comment_body)

        assert "id" in result
        assert result["body"]["content"][0]["content"][0]["text"] == comment_text

    def test_add_comment_with_formatting(self, jira_client, test_issue):
        """Test adding a comment with rich text formatting."""
        comment_body = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "This is "},
                        {"type": "text", "text": "bold", "marks": [{"type": "strong"}]},
                        {"type": "text", "text": " and "},
                        {"type": "text", "text": "italic", "marks": [{"type": "em"}]},
                        {"type": "text", "text": " text."},
                    ],
                }
            ],
        }

        result = jira_client.add_comment(test_issue["key"], comment_body)

        assert "id" in result
        # Verify content was preserved
        content = result["body"]["content"][0]["content"]
        assert len(content) >= 3

    def test_add_multiple_comments(self, jira_client, test_issue):
        """Test adding multiple comments to the same issue."""
        comment_ids = []

        for i in range(3):
            comment_body = {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": f"Comment {i + 1}"}],
                    }
                ],
            }
            result = jira_client.add_comment(test_issue["key"], comment_body)
            comment_ids.append(result["id"])

        # Verify all comments were created
        assert len(comment_ids) == 3
        assert len(set(comment_ids)) == 3  # All unique IDs


@pytest.mark.integration
@pytest.mark.collaborate
@pytest.mark.comments
class TestCommentRetrieval:
    """Tests for retrieving comments."""

    def test_get_all_comments(self, jira_client, test_issue):
        """Test getting all comments from an issue."""
        # Add comments first
        for i in range(2):
            comment_body = {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": f"Retrieval test comment {i + 1}"}
                        ],
                    }
                ],
            }
            jira_client.add_comment(test_issue["key"], comment_body)

        # Get all comments
        result = jira_client.get_comments(test_issue["key"])

        assert "comments" in result
        assert result["total"] >= 2
        assert len(result["comments"]) >= 2

    def test_get_single_comment_by_id(self, jira_client, test_issue):
        """Test getting a specific comment by ID."""
        # Create a comment
        comment_text = f"Single comment test {uuid.uuid4().hex[:8]}"
        comment_body = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": comment_text}],
                }
            ],
        }
        created = jira_client.add_comment(test_issue["key"], comment_body)
        comment_id = created["id"]

        # Get the specific comment
        comment = jira_client.get_comment(test_issue["key"], comment_id)

        assert comment["id"] == comment_id
        assert comment["body"]["content"][0]["content"][0]["text"] == comment_text

    def test_get_comments_pagination(self, jira_client, test_issue):
        """Test paginating through comments."""
        # Add multiple comments
        for i in range(5):
            comment_body = {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": f"Pagination test {i + 1}"}
                        ],
                    }
                ],
            }
            jira_client.add_comment(test_issue["key"], comment_body)

        # Get first page
        result = jira_client.get_comments(test_issue["key"], start_at=0, max_results=2)

        assert len(result["comments"]) == 2
        assert result["total"] >= 5

    def test_get_comments_empty_issue(self, jira_client, test_project):
        """Test getting comments from issue with no comments."""
        # Create fresh issue without comments
        issue = jira_client.create_issue(
            {
                "project": {"key": test_project["key"]},
                "summary": f"Empty comments test {uuid.uuid4().hex[:8]}",
                "issuetype": {"name": "Task"},
            }
        )

        try:
            result = jira_client.get_comments(issue["key"])

            assert "comments" in result
            assert result["total"] == 0
            assert len(result["comments"]) == 0
        finally:
            jira_client.delete_issue(issue["key"])


@pytest.mark.integration
@pytest.mark.collaborate
@pytest.mark.comments
class TestCommentUpdate:
    """Tests for updating comments."""

    def test_update_comment_text(self, jira_client, test_issue):
        """Test updating a comment's text content."""
        # Create original comment
        original_text = f"Original text {uuid.uuid4().hex[:8]}"
        comment_body = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": original_text}],
                }
            ],
        }
        created = jira_client.add_comment(test_issue["key"], comment_body)
        comment_id = created["id"]

        # Update comment
        updated_text = f"Updated text {uuid.uuid4().hex[:8]}"
        updated_body = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": updated_text}],
                }
            ],
        }
        result = jira_client.update_comment(test_issue["key"], comment_id, updated_body)

        assert result["body"]["content"][0]["content"][0]["text"] == updated_text

    def test_update_comment_preserves_id(self, jira_client, test_issue):
        """Test that updating a comment preserves its ID."""
        # Create comment
        comment_body = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "To be updated"}],
                }
            ],
        }
        created = jira_client.add_comment(test_issue["key"], comment_body)
        original_id = created["id"]

        # Update comment
        updated_body = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Now updated"}],
                }
            ],
        }
        result = jira_client.update_comment(
            test_issue["key"], original_id, updated_body
        )

        assert result["id"] == original_id

    def test_update_comment_multiple_times(self, jira_client, test_issue):
        """Test updating a comment multiple times."""
        # Create comment
        comment_body = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Version 1"}],
                }
            ],
        }
        created = jira_client.add_comment(test_issue["key"], comment_body)
        comment_id = created["id"]

        # Update multiple times
        for version in range(2, 5):
            updated_body = {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": f"Version {version}"}],
                    }
                ],
            }
            jira_client.update_comment(test_issue["key"], comment_id, updated_body)

        # Verify final state
        final = jira_client.get_comment(test_issue["key"], comment_id)
        assert "Version 4" in final["body"]["content"][0]["content"][0]["text"]


@pytest.mark.integration
@pytest.mark.collaborate
@pytest.mark.comments
class TestCommentDeletion:
    """Tests for deleting comments."""

    def test_delete_comment(self, jira_client, test_issue):
        """Test deleting a comment."""
        # Create comment
        comment_body = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Comment to delete {uuid.uuid4().hex[:8]}",
                        }
                    ],
                }
            ],
        }
        created = jira_client.add_comment(test_issue["key"], comment_body)
        comment_id = created["id"]

        # Delete comment
        jira_client.delete_comment(test_issue["key"], comment_id)

        # Verify it's gone
        from jira_assistant_skills_lib import NotFoundError

        with pytest.raises(NotFoundError):
            jira_client.get_comment(test_issue["key"], comment_id)

    def test_delete_comment_updates_count(self, jira_client, test_issue):
        """Test that deleting a comment updates the comment count."""
        # Add two comments
        comment_ids = []
        for i in range(2):
            comment_body = {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": f"Count test {i + 1}"}],
                    }
                ],
            }
            result = jira_client.add_comment(test_issue["key"], comment_body)
            comment_ids.append(result["id"])

        # Get initial count
        initial_result = jira_client.get_comments(test_issue["key"])
        initial_count = initial_result["total"]

        # Delete one comment
        jira_client.delete_comment(test_issue["key"], comment_ids[0])

        # Verify count decreased
        final_result = jira_client.get_comments(test_issue["key"])
        assert final_result["total"] == initial_count - 1


@pytest.mark.integration
@pytest.mark.collaborate
@pytest.mark.comments
class TestCommentAuthorship:
    """Tests for comment authorship and metadata."""

    def test_comment_has_author(self, jira_client, test_issue, current_user):
        """Test that comments have author information."""
        comment_body = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Author test comment"}],
                }
            ],
        }
        result = jira_client.add_comment(test_issue["key"], comment_body)

        assert "author" in result
        assert result["author"]["accountId"] == current_user["accountId"]

    def test_comment_has_timestamps(self, jira_client, test_issue):
        """Test that comments have created and updated timestamps."""
        comment_body = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Timestamp test comment"}],
                }
            ],
        }
        result = jira_client.add_comment(test_issue["key"], comment_body)

        assert "created" in result
        assert "updated" in result

    def test_update_changes_updated_timestamp(self, jira_client, test_issue):
        """Test that updating a comment changes the updated timestamp."""
        import time

        # Create comment
        comment_body = {
            "type": "doc",
            "version": 1,
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": "Original"}]}
            ],
        }
        created = jira_client.add_comment(test_issue["key"], comment_body)
        original_updated = created["updated"]

        # Wait a moment
        time.sleep(1)

        # Update comment
        updated_body = {
            "type": "doc",
            "version": 1,
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": "Updated"}]}
            ],
        }
        result = jira_client.update_comment(
            test_issue["key"], created["id"], updated_body
        )

        assert result["updated"] != original_updated
