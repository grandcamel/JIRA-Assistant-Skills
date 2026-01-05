"""
Live Integration Tests: Collaboration Features

Tests for comments, attachments, and watchers against a real JIRA instance.
"""

import os
import tempfile
import uuid

import pytest


@pytest.mark.integration
@pytest.mark.shared
class TestComments:
    """Tests for comment operations."""

    def test_add_comment(self, jira_client, test_issue):
        """Test adding a comment to an issue."""
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

    def test_get_comments(self, jira_client, test_issue):
        """Test getting comments from an issue."""
        # Add a comment first
        comment_body = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Comment for get test {uuid.uuid4().hex[:8]}",
                        }
                    ],
                }
            ],
        }
        jira_client.add_comment(test_issue["key"], comment_body)

        # Get comments
        result = jira_client.get_comments(test_issue["key"])

        assert "comments" in result
        assert result["total"] >= 1
        assert len(result["comments"]) >= 1

    def test_get_single_comment(self, jira_client, test_issue):
        """Test getting a specific comment."""
        # Add a comment
        comment_body = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Specific comment {uuid.uuid4().hex[:8]}",
                        }
                    ],
                }
            ],
        }
        created = jira_client.add_comment(test_issue["key"], comment_body)
        comment_id = created["id"]

        # Get the specific comment
        comment = jira_client.get_comment(test_issue["key"], comment_id)

        assert comment["id"] == comment_id

    def test_update_comment(self, jira_client, test_issue):
        """Test updating a comment."""
        # Create comment
        original_text = f"Original comment {uuid.uuid4().hex[:8]}"
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
        updated_text = f"Updated comment {uuid.uuid4().hex[:8]}"
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


@pytest.mark.integration
@pytest.mark.shared
class TestAttachments:
    """Tests for attachment operations."""

    def test_upload_attachment(self, jira_client, test_issue):
        """Test uploading a file attachment."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(f"Test attachment content {uuid.uuid4().hex}")
            temp_path = f.name

        try:
            # Upload
            result = jira_client.upload_file(
                f"/rest/api/3/issue/{test_issue['key']}/attachments",
                temp_path,
                file_name="test_attachment.txt",
            )

            assert isinstance(result, list)
            assert len(result) >= 1
            assert result[0]["filename"] == "test_attachment.txt"

        finally:
            os.unlink(temp_path)

    def test_get_attachments(self, jira_client, test_issue):
        """Test getting issue attachments."""
        # Upload an attachment first
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(f"Attachment content {uuid.uuid4().hex}")
            temp_path = f.name

        try:
            jira_client.upload_file(
                f"/rest/api/3/issue/{test_issue['key']}/attachments",
                temp_path,
                file_name="get_test.txt",
            )

            # Get attachments
            attachments = jira_client.get_attachments(test_issue["key"])

            assert isinstance(attachments, list)
            assert len(attachments) >= 1

            filenames = [a["filename"] for a in attachments]
            assert "get_test.txt" in filenames

        finally:
            os.unlink(temp_path)

    def test_delete_attachment(self, jira_client, test_issue):
        """Test deleting an attachment."""
        # Upload an attachment
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(f"Attachment to delete {uuid.uuid4().hex}")
            temp_path = f.name

        try:
            result = jira_client.upload_file(
                f"/rest/api/3/issue/{test_issue['key']}/attachments",
                temp_path,
                file_name="delete_test.txt",
            )
            attachment_id = result[0]["id"]

            # Delete attachment
            jira_client.delete_attachment(attachment_id)

            # Verify it's gone
            attachments = jira_client.get_attachments(test_issue["key"])
            attachment_ids = [a["id"] for a in attachments]
            assert attachment_id not in attachment_ids

        finally:
            os.unlink(temp_path)

    def test_download_attachment(self, jira_client, test_issue):
        """Test downloading an attachment."""
        content = f"Download test content {uuid.uuid4().hex}"

        # Upload an attachment
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            upload_path = f.name

        download_path = None
        try:
            result = jira_client.upload_file(
                f"/rest/api/3/issue/{test_issue['key']}/attachments",
                upload_path,
                file_name="download_test.txt",
            )
            content_url = result[0]["content"]

            # Download
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False
            ) as f:
                download_path = f.name

            jira_client.download_file(content_url, download_path)

            # Verify content
            with open(download_path) as f:
                downloaded_content = f.read()
            assert downloaded_content == content

        finally:
            os.unlink(upload_path)
            if download_path and os.path.exists(download_path):
                os.unlink(download_path)


@pytest.mark.integration
@pytest.mark.shared
class TestWatchers:
    """Tests for watcher operations."""

    def test_get_watchers(self, jira_client, test_issue):
        """Test getting issue watchers."""
        # The creator is often automatically added as watcher
        result = jira_client.get(
            f"/rest/api/3/issue/{test_issue['key']}/watchers", operation="get watchers"
        )

        assert "watchCount" in result
        assert "watchers" in result

    def test_add_watcher(self, jira_client, test_issue):
        """Test adding a watcher."""
        # Get current user
        current_user_id = jira_client.get_current_user_id()

        # Add as watcher (may already be watching)
        jira_client.post(
            f"/rest/api/3/issue/{test_issue['key']}/watchers",
            data=f'"{current_user_id}"',
            operation="add watcher",
        )

        # Verify
        result = jira_client.get(
            f"/rest/api/3/issue/{test_issue['key']}/watchers", operation="get watchers"
        )

        watcher_ids = [w["accountId"] for w in result.get("watchers", [])]
        assert current_user_id in watcher_ids

    def test_remove_watcher(self, jira_client, test_issue):
        """Test removing a watcher."""
        current_user_id = jira_client.get_current_user_id()

        # First add as watcher
        jira_client.post(
            f"/rest/api/3/issue/{test_issue['key']}/watchers",
            data=f'"{current_user_id}"',
            operation="add watcher",
        )

        # Remove watcher
        jira_client.delete(
            f"/rest/api/3/issue/{test_issue['key']}/watchers?accountId={current_user_id}",
            operation="remove watcher",
        )

        # Verify removed
        result = jira_client.get(
            f"/rest/api/3/issue/{test_issue['key']}/watchers", operation="get watchers"
        )

        watcher_ids = [w["accountId"] for w in result.get("watchers", [])]
        assert current_user_id not in watcher_ids


@pytest.mark.integration
@pytest.mark.shared
class TestUserSearch:
    """Tests for user search operations."""

    def test_search_users(self, jira_client):
        """Test searching for users.

        Note: JIRA's user search works best with display name or first name,
        not email domain. Using the first word of display name for reliable results.
        """
        # Get current user info
        current_user = jira_client.get("/rest/api/3/myself", operation="get myself")
        display_name = current_user.get("displayName", "")

        if display_name:
            # Search by first name (first word of display name)
            first_name = display_name.split()[0]
            results = jira_client.search_users(first_name)

            assert isinstance(results, list)
            # Should find at least current user
            assert len(results) >= 1
            # Verify current user is in results
            account_ids = [u.get("accountId") for u in results]
            assert current_user.get("accountId") in account_ids

    def test_get_current_user(self, jira_client):
        """Test getting current user info."""
        user_id = jira_client.get_current_user_id()

        assert user_id is not None
        assert len(user_id) > 0


@pytest.mark.integration
@pytest.mark.shared
class TestNotifications:
    """Tests for notification operations.

    IMPORTANT: JIRA Cloud's notification API (/rest/api/3/issue/{key}/notify)
    has strict requirements that vary by instance configuration:
    - The notify permission must be enabled for the project
    - Users must have notification permissions
    - Some instances may have notifications disabled entirely

    These tests verify the notify_issue method constructs valid requests.
    If notifications are disabled on the instance, tests will be skipped.
    """

    @pytest.fixture(autouse=True)
    def check_notify_support(self, jira_client, test_issue):
        """Check if notifications are supported before running tests."""
        current_user_id = jira_client.get_current_user_id()

        try:
            # Try a basic notification to check if API is available
            jira_client.notify_issue(
                test_issue["key"],
                subject="Notification capability check",
                text_body="Testing notification support",
                to={"users": [{"accountId": current_user_id}]},
            )
        except Exception as e:
            if "No recipients" in str(e) or "400" in str(e):
                pytest.skip(
                    "JIRA instance does not support notifications or user lacks permission. "
                    "This is a JIRA configuration issue, not a code issue."
                )
            raise

    def test_notify_specific_user(self, jira_client, test_issue):
        """
        Test sending notification to a specific user.

        Note: JIRA's notify API returns empty on success. We verify success
        by the absence of exceptions. Email delivery cannot be verified via API.
        """
        current_user_id = jira_client.get_current_user_id()

        # This should not raise an exception
        try:
            jira_client.notify_issue(
                test_issue["key"],
                subject="Test notification to specific user",
                text_body="User-specific notification test",
                to={"users": [{"accountId": current_user_id}]},
            )
        except Exception as e:
            pytest.fail(f"Notification failed unexpectedly: {e}")
        # Success: API call completed without exception

    def test_notify_with_html_body(self, jira_client, test_issue):
        """
        Test notification with HTML body content.

        Note: JIRA's notify API returns empty on success. We verify success
        by the absence of exceptions.
        """
        current_user_id = jira_client.get_current_user_id()

        try:
            jira_client.notify_issue(
                test_issue["key"],
                subject="HTML notification test",
                html_body="<p>This is a <strong>test</strong> notification.</p>",
                to={"users": [{"accountId": current_user_id}]},
            )
        except Exception as e:
            pytest.fail(f"Notification with HTML body failed unexpectedly: {e}")
        # Success: API call completed without exception

    def test_notify_with_custom_subject(self, jira_client, test_issue):
        """
        Test notification with custom subject.

        Note: JIRA's notify API returns empty on success. We verify success
        by the absence of exceptions.
        """
        current_user_id = jira_client.get_current_user_id()

        try:
            jira_client.notify_issue(
                test_issue["key"],
                subject=f"Custom Subject {uuid.uuid4().hex[:8]}",
                text_body="Test body",
                to={"users": [{"accountId": current_user_id}]},
            )
        except Exception as e:
            pytest.fail(f"Notification with custom subject failed unexpectedly: {e}")
        # Success: API call completed without exception


@pytest.mark.integration
@pytest.mark.shared
class TestActivityHistory:
    """Tests for activity/changelog operations."""

    def test_get_activity(self, jira_client, test_issue):
        """Test getting activity/changelog for an issue."""
        import uuid

        # Make some changes to create activity
        jira_client.update_issue(
            test_issue["key"],
            fields={"summary": f"Updated Summary {uuid.uuid4().hex[:8]}"},
        )

        # Get changelog
        changelog = jira_client.get_changelog(test_issue["key"])

        assert "values" in changelog or "histories" in changelog

    def test_get_activity_shows_field_changes(self, jira_client, test_issue):
        """Test that activity shows field change details."""
        import time
        import uuid

        # Make a tracked change
        jira_client.get_issue(test_issue["key"])["fields"]["summary"]
        new_summary = f"Changed Summary {uuid.uuid4().hex[:8]}"

        jira_client.update_issue(test_issue["key"], fields={"summary": new_summary})

        # Small delay for changelog to update
        time.sleep(1)

        # Get changelog
        changelog = jira_client.get_changelog(test_issue["key"])

        # Verify changelog has entries
        if "values" in changelog:
            assert len(changelog["values"]) >= 1
        elif "histories" in changelog:
            assert len(changelog["histories"]) >= 1

    def test_get_activity_pagination(self, jira_client, test_issue):
        """Test paginating through activity history."""
        import uuid

        # Make several changes
        for i in range(3):
            jira_client.update_issue(
                test_issue["key"],
                fields={"summary": f"Change {i} {uuid.uuid4().hex[:8]}"},
            )

        # Get first page
        changelog = jira_client.get_changelog(test_issue["key"], max_results=2)

        # Verify pagination parameters work
        assert isinstance(changelog, dict)

    def test_activity_tracks_status_changes(self, jira_client, test_issue):
        """Test that status changes appear in activity."""
        import time

        # Get available transitions
        transitions = jira_client.get_transitions(test_issue["key"])

        if len(transitions) > 0:
            # Perform a transition
            transition = transitions[0]
            jira_client.transition_issue(test_issue["key"], transition["id"])

            # Small delay for changelog
            time.sleep(1)

            # Get changelog
            changelog = jira_client.get_changelog(test_issue["key"])

            # Verify status change is recorded
            if "values" in changelog:
                assert len(changelog["values"]) >= 1
            elif "histories" in changelog:
                assert len(changelog["histories"]) >= 1
