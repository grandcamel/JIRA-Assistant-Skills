"""
Unit tests for update_issue.py script.

Tests cover:
- Updating issue summary
- Updating issue description
- Updating issue priority
- Updating issue assignee (account ID, email, self, unassign)
- Updating issue labels
- Updating issue components
- Updating with custom fields
- Notification control (--no-notify)
- Validation errors (invalid issue key, no fields)
- Not found errors
- Permission errors
- Authentication errors
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add scripts path
scripts_path = str(Path(__file__).parent.parent / "scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

# Import after path setup
import update_issue as update_issue_module


@pytest.mark.unit
class TestUpdateIssueSummary:
    """Tests for updating issue summary."""

    def test_update_issue_summary_success(self, mock_jira_client):
        """Test updating issue summary."""
        mock_jira_client.update_issue.return_value = None

        with patch.object(
            update_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            update_issue_module.update_issue(
                issue_key="PROJ-123", summary="Updated Summary"
            )

        mock_jira_client.update_issue.assert_called_once()
        call_args = mock_jira_client.update_issue.call_args
        assert call_args[0][0] == "PROJ-123"
        assert call_args[0][1]["summary"] == "Updated Summary"

    def test_update_issue_normalizes_key(self, mock_jira_client):
        """Test that issue key is normalized to uppercase."""
        mock_jira_client.update_issue.return_value = None

        with patch.object(
            update_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            update_issue_module.update_issue(
                issue_key="proj-123", summary="Updated Summary"
            )

        call_args = mock_jira_client.update_issue.call_args
        assert call_args[0][0] == "PROJ-123"


@pytest.mark.unit
class TestUpdateIssueDescription:
    """Tests for updating issue description."""

    def test_update_issue_description_plain_text(self, mock_jira_client):
        """Test updating issue with plain text description."""
        mock_jira_client.update_issue.return_value = None

        with patch.object(
            update_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            update_issue_module.update_issue(
                issue_key="PROJ-123", description="Simple plain text description"
            )

        call_args = mock_jira_client.update_issue.call_args
        assert "description" in call_args[0][1]
        # Description should be converted to ADF
        assert isinstance(call_args[0][1]["description"], dict)

    def test_update_issue_description_markdown(self, mock_jira_client):
        """Test updating issue with markdown description."""
        mock_jira_client.update_issue.return_value = None

        with patch.object(
            update_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            update_issue_module.update_issue(
                issue_key="PROJ-123",
                description="**Bold** and *italic* text\n\n- Item 1",
            )

        call_args = mock_jira_client.update_issue.call_args
        assert "description" in call_args[0][1]
        # Description should be converted to ADF
        assert isinstance(call_args[0][1]["description"], dict)
        assert call_args[0][1]["description"].get("type") == "doc"

    def test_update_issue_description_adf(self, mock_jira_client):
        """Test updating issue with pre-formatted ADF description."""
        mock_jira_client.update_issue.return_value = None
        adf_description = json.dumps(
            {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "ADF text"}],
                    }
                ],
            }
        )

        with patch.object(
            update_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            update_issue_module.update_issue(
                issue_key="PROJ-123", description=adf_description
            )

        call_args = mock_jira_client.update_issue.call_args
        assert call_args[0][1]["description"]["type"] == "doc"


@pytest.mark.unit
class TestUpdateIssuePriority:
    """Tests for updating issue priority."""

    def test_update_issue_priority(self, mock_jira_client):
        """Test updating issue priority."""
        mock_jira_client.update_issue.return_value = None

        with patch.object(
            update_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            update_issue_module.update_issue(issue_key="PROJ-123", priority="High")

        call_args = mock_jira_client.update_issue.call_args
        assert call_args[0][1]["priority"] == {"name": "High"}


@pytest.mark.unit
class TestUpdateIssueAssignee:
    """Tests for updating issue assignee."""

    def test_update_issue_assignee_account_id(self, mock_jira_client):
        """Test updating issue assignee by account ID."""
        mock_jira_client.update_issue.return_value = None

        with patch.object(
            update_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            update_issue_module.update_issue(
                issue_key="PROJ-123", assignee="557058:test-user-id"
            )

        call_args = mock_jira_client.update_issue.call_args
        assert call_args[0][1]["assignee"] == {"accountId": "557058:test-user-id"}

    def test_update_issue_assignee_email(self, mock_jira_client):
        """Test updating issue assignee by email."""
        mock_jira_client.update_issue.return_value = None

        with patch.object(
            update_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            update_issue_module.update_issue(
                issue_key="PROJ-123", assignee="user@example.com"
            )

        call_args = mock_jira_client.update_issue.call_args
        assert call_args[0][1]["assignee"] == {"emailAddress": "user@example.com"}

    def test_update_issue_assignee_self(self, mock_jira_client):
        """Test updating issue assignee to self."""
        mock_jira_client.update_issue.return_value = None
        mock_jira_client.get_current_user_id.return_value = "557058:current-user"

        with patch.object(
            update_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            update_issue_module.update_issue(issue_key="PROJ-123", assignee="self")

        mock_jira_client.get_current_user_id.assert_called()
        call_args = mock_jira_client.update_issue.call_args
        assert call_args[0][1]["assignee"] == {"accountId": "557058:current-user"}

    def test_update_issue_unassign_none(self, mock_jira_client):
        """Test unassigning issue with 'none'."""
        mock_jira_client.update_issue.return_value = None

        with patch.object(
            update_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            update_issue_module.update_issue(issue_key="PROJ-123", assignee="none")

        call_args = mock_jira_client.update_issue.call_args
        assert call_args[0][1]["assignee"] is None

    def test_update_issue_unassign_unassigned(self, mock_jira_client):
        """Test unassigning issue with 'unassigned'."""
        mock_jira_client.update_issue.return_value = None

        with patch.object(
            update_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            update_issue_module.update_issue(
                issue_key="PROJ-123", assignee="unassigned"
            )

        call_args = mock_jira_client.update_issue.call_args
        assert call_args[0][1]["assignee"] is None


@pytest.mark.unit
class TestUpdateIssueLabels:
    """Tests for updating issue labels."""

    def test_update_issue_labels(self, mock_jira_client):
        """Test updating issue labels."""
        mock_jira_client.update_issue.return_value = None

        with patch.object(
            update_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            update_issue_module.update_issue(
                issue_key="PROJ-123", labels=["bug", "urgent", "backend"]
            )

        call_args = mock_jira_client.update_issue.call_args
        assert call_args[0][1]["labels"] == ["bug", "urgent", "backend"]

    def test_update_issue_empty_labels(self, mock_jira_client):
        """Test clearing issue labels with empty list."""
        mock_jira_client.update_issue.return_value = None

        with patch.object(
            update_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            update_issue_module.update_issue(issue_key="PROJ-123", labels=[])

        call_args = mock_jira_client.update_issue.call_args
        assert call_args[0][1]["labels"] == []


@pytest.mark.unit
class TestUpdateIssueComponents:
    """Tests for updating issue components."""

    def test_update_issue_components(self, mock_jira_client):
        """Test updating issue components."""
        mock_jira_client.update_issue.return_value = None

        with patch.object(
            update_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            update_issue_module.update_issue(
                issue_key="PROJ-123", components=["Backend", "API", "Database"]
            )

        call_args = mock_jira_client.update_issue.call_args
        assert call_args[0][1]["components"] == [
            {"name": "Backend"},
            {"name": "API"},
            {"name": "Database"},
        ]


@pytest.mark.unit
class TestUpdateIssueCustomFields:
    """Tests for updating custom fields."""

    def test_update_issue_custom_fields(self, mock_jira_client):
        """Test updating custom fields."""
        mock_jira_client.update_issue.return_value = None

        with patch.object(
            update_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            update_issue_module.update_issue(
                issue_key="PROJ-123",
                custom_fields={
                    "customfield_12345": "custom value",
                    "customfield_67890": 42,
                },
            )

        call_args = mock_jira_client.update_issue.call_args
        assert call_args[0][1]["customfield_12345"] == "custom value"
        assert call_args[0][1]["customfield_67890"] == 42


@pytest.mark.unit
class TestUpdateIssueNotifications:
    """Tests for notification control."""

    def test_update_issue_with_notifications(self, mock_jira_client):
        """Test updating issue with notifications enabled (default)."""
        mock_jira_client.update_issue.return_value = None

        with patch.object(
            update_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            update_issue_module.update_issue(
                issue_key="PROJ-123", summary="Updated Summary", notify_users=True
            )

        call_args = mock_jira_client.update_issue.call_args
        assert call_args[1]["notify_users"] is True

    def test_update_issue_without_notifications(self, mock_jira_client):
        """Test updating issue with notifications disabled."""
        mock_jira_client.update_issue.return_value = None

        with patch.object(
            update_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            update_issue_module.update_issue(
                issue_key="PROJ-123", summary="Silent Update", notify_users=False
            )

        call_args = mock_jira_client.update_issue.call_args
        assert call_args[1]["notify_users"] is False


@pytest.mark.unit
class TestUpdateIssueMultipleFields:
    """Tests for updating multiple fields at once."""

    def test_update_issue_multiple_fields(self, mock_jira_client):
        """Test updating multiple fields in one call."""
        mock_jira_client.update_issue.return_value = None

        with patch.object(
            update_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            update_issue_module.update_issue(
                issue_key="PROJ-123",
                summary="New Summary",
                priority="High",
                labels=["urgent"],
                assignee="user@example.com",
            )

        call_args = mock_jira_client.update_issue.call_args
        fields = call_args[0][1]
        assert fields["summary"] == "New Summary"
        assert fields["priority"] == {"name": "High"}
        assert fields["labels"] == ["urgent"]
        assert fields["assignee"] == {"emailAddress": "user@example.com"}


@pytest.mark.unit
class TestUpdateIssueValidation:
    """Tests for input validation."""

    def test_update_issue_invalid_key_raises_error(self, mock_jira_client):
        """Test that invalid issue key raises ValidationError."""
        from assistant_skills_lib.error_handler import ValidationError

        with (
            patch.object(
                update_issue_module, "get_jira_client", return_value=mock_jira_client
            ),
            pytest.raises(ValidationError),
        ):
            update_issue_module.update_issue(issue_key="invalid-key", summary="Test")

    def test_update_issue_empty_key_raises_error(self, mock_jira_client):
        """Test that empty issue key raises ValidationError."""
        from assistant_skills_lib.error_handler import ValidationError

        with (
            patch.object(
                update_issue_module, "get_jira_client", return_value=mock_jira_client
            ),
            pytest.raises(ValidationError),
        ):
            update_issue_module.update_issue(issue_key="", summary="Test")

    def test_update_issue_no_fields_raises_error(self, mock_jira_client):
        """Test that updating with no fields raises ValueError."""
        with (
            patch.object(
                update_issue_module, "get_jira_client", return_value=mock_jira_client
            ),
            pytest.raises(ValueError) as exc_info,
        ):
            update_issue_module.update_issue(issue_key="PROJ-123")

        assert "No fields specified" in str(exc_info.value)


@pytest.mark.unit
class TestUpdateIssueErrors:
    """Tests for error handling."""

    def test_update_issue_not_found(self, mock_jira_client):
        """Test handling issue not found error."""
        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.update_issue.side_effect = NotFoundError("Issue", "PROJ-999")

        with (
            patch.object(
                update_issue_module, "get_jira_client", return_value=mock_jira_client
            ),
            pytest.raises(NotFoundError) as exc_info,
        ):
            update_issue_module.update_issue(issue_key="PROJ-999", summary="Not Found")

        assert "not found" in str(exc_info.value).lower()

    def test_update_issue_permission_denied(self, mock_jira_client):
        """Test handling permission denied error."""
        from jira_assistant_skills_lib import PermissionError

        mock_jira_client.update_issue.side_effect = PermissionError(
            "You do not have permission to edit this issue"
        )

        with (
            patch.object(
                update_issue_module, "get_jira_client", return_value=mock_jira_client
            ),
            pytest.raises(PermissionError) as exc_info,
        ):
            update_issue_module.update_issue(
                issue_key="PROJ-123", summary="Forbidden Update"
            )

        assert "permission" in str(exc_info.value).lower()

    def test_update_issue_authentication_error(self, mock_jira_client):
        """Test handling authentication error."""
        from jira_assistant_skills_lib import AuthenticationError

        mock_jira_client.update_issue.side_effect = AuthenticationError(
            "Authentication failed"
        )

        with (
            patch.object(
                update_issue_module, "get_jira_client", return_value=mock_jira_client
            ),
            pytest.raises(AuthenticationError),
        ):
            update_issue_module.update_issue(
                issue_key="PROJ-123", summary="Auth Failed Update"
            )

    def test_update_issue_validation_error_from_api(self, mock_jira_client):
        """Test handling validation error from API."""
        from assistant_skills_lib.error_handler import ValidationError

        mock_jira_client.update_issue.side_effect = ValidationError(
            "Priority 'InvalidPriority' is not valid"
        )

        with (
            patch.object(
                update_issue_module, "get_jira_client", return_value=mock_jira_client
            ),
            pytest.raises(ValidationError),
        ):
            update_issue_module.update_issue(
                issue_key="PROJ-123", priority="InvalidPriority"
            )


@pytest.mark.unit
class TestUpdateIssueProfile:
    """Tests for profile handling."""
