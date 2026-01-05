"""
Unit tests for create_issue.py script.

Tests cover:
- Creating a new issue with required fields
- Creating issues with optional fields (priority, assignee, labels, etc.)
- Creating issues with Agile fields (epic, story points)
- Creating issues with time estimates
- Creating issues with links (blocks, relates-to)
- Template loading
- Validation errors (invalid project key, invalid issue key)
- Permission errors
- Authentication errors
- Output formatting (text and JSON)
"""

import json
import sys
from copy import deepcopy
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add scripts path
scripts_path = str(Path(__file__).parent.parent / "scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

# Import after path setup
import create_issue as create_issue_module


@pytest.mark.unit
class TestCreateIssueBasic:
    """Tests for basic issue creation."""

    def test_create_issue_success(self, mock_jira_client, sample_created_issue):
        """Test creating a new issue with required fields."""
        mock_jira_client.create_issue.return_value = deepcopy(sample_created_issue)

        with patch.object(
            create_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            result = create_issue_module.create_issue(
                project="PROJ", issue_type="Bug", summary="Test Bug", profile=None
            )

        mock_jira_client.create_issue.assert_called_once()
        call_args = mock_jira_client.create_issue.call_args[0][0]
        assert call_args["project"] == {"key": "PROJ"}
        assert call_args["issuetype"] == {"name": "Bug"}
        assert call_args["summary"] == "Test Bug"
        assert result["key"] == "PROJ-130"

    def test_create_issue_returns_key(self, mock_jira_client, sample_created_issue):
        """Test that created issue includes key."""
        mock_jira_client.create_issue.return_value = deepcopy(sample_created_issue)

        with patch.object(
            create_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            result = create_issue_module.create_issue(
                project="PROJ", issue_type="Task", summary="Test Task"
            )

        assert result["key"] == "PROJ-130"
        assert result["id"] == "10010"

    def test_create_issue_with_description(
        self, mock_jira_client, sample_created_issue
    ):
        """Test creating an issue with a description."""
        mock_jira_client.create_issue.return_value = deepcopy(sample_created_issue)

        with patch.object(
            create_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            create_issue_module.create_issue(
                project="PROJ",
                issue_type="Bug",
                summary="Test Bug",
                description="This is a detailed description",
            )

        call_args = mock_jira_client.create_issue.call_args[0][0]
        assert "description" in call_args
        # Description should be converted to ADF format
        assert isinstance(call_args["description"], dict)


@pytest.mark.unit
class TestCreateIssueOptionalFields:
    """Tests for creating issues with optional fields."""

    def test_create_issue_with_priority(self, mock_jira_client, sample_created_issue):
        """Test creating an issue with priority."""
        mock_jira_client.create_issue.return_value = deepcopy(sample_created_issue)

        with patch.object(
            create_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            create_issue_module.create_issue(
                project="PROJ",
                issue_type="Bug",
                summary="High Priority Bug",
                priority="High",
            )

        call_args = mock_jira_client.create_issue.call_args[0][0]
        assert call_args["priority"] == {"name": "High"}

    def test_create_issue_with_assignee_account_id(
        self, mock_jira_client, sample_created_issue
    ):
        """Test creating an issue with assignee by account ID."""
        mock_jira_client.create_issue.return_value = deepcopy(sample_created_issue)

        with patch.object(
            create_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            create_issue_module.create_issue(
                project="PROJ",
                issue_type="Task",
                summary="Assigned Task",
                assignee="557058:test-user-id",
            )

        call_args = mock_jira_client.create_issue.call_args[0][0]
        assert call_args["assignee"] == {"accountId": "557058:test-user-id"}

    def test_create_issue_with_assignee_email(
        self, mock_jira_client, sample_created_issue
    ):
        """Test creating an issue with assignee by email."""
        mock_jira_client.create_issue.return_value = deepcopy(sample_created_issue)

        with patch.object(
            create_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            create_issue_module.create_issue(
                project="PROJ",
                issue_type="Task",
                summary="Assigned Task",
                assignee="test@example.com",
            )

        call_args = mock_jira_client.create_issue.call_args[0][0]
        assert call_args["assignee"] == {"emailAddress": "test@example.com"}

    def test_create_issue_with_assignee_self(
        self, mock_jira_client, sample_created_issue
    ):
        """Test creating an issue with assignee set to self."""
        mock_jira_client.create_issue.return_value = deepcopy(sample_created_issue)
        mock_jira_client.get_current_user_id.return_value = "557058:current-user"

        with patch.object(
            create_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            create_issue_module.create_issue(
                project="PROJ",
                issue_type="Task",
                summary="Self-assigned Task",
                assignee="self",
            )

        mock_jira_client.get_current_user_id.assert_called()
        call_args = mock_jira_client.create_issue.call_args[0][0]
        assert call_args["assignee"] == {"accountId": "557058:current-user"}

    def test_create_issue_with_labels(self, mock_jira_client, sample_created_issue):
        """Test creating an issue with labels."""
        mock_jira_client.create_issue.return_value = deepcopy(sample_created_issue)

        with patch.object(
            create_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            create_issue_module.create_issue(
                project="PROJ",
                issue_type="Bug",
                summary="Labeled Bug",
                labels=["urgent", "backend", "api"],
            )

        call_args = mock_jira_client.create_issue.call_args[0][0]
        assert call_args["labels"] == ["urgent", "backend", "api"]

    def test_create_issue_with_components(self, mock_jira_client, sample_created_issue):
        """Test creating an issue with components."""
        mock_jira_client.create_issue.return_value = deepcopy(sample_created_issue)

        with patch.object(
            create_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            create_issue_module.create_issue(
                project="PROJ",
                issue_type="Bug",
                summary="Component Bug",
                components=["Backend", "API"],
            )

        call_args = mock_jira_client.create_issue.call_args[0][0]
        assert call_args["components"] == [{"name": "Backend"}, {"name": "API"}]

    def test_create_issue_with_custom_fields(
        self, mock_jira_client, sample_created_issue
    ):
        """Test creating an issue with custom fields."""
        mock_jira_client.create_issue.return_value = deepcopy(sample_created_issue)

        with patch.object(
            create_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            create_issue_module.create_issue(
                project="PROJ",
                issue_type="Bug",
                summary="Custom Field Bug",
                custom_fields={"customfield_12345": "custom value"},
            )

        call_args = mock_jira_client.create_issue.call_args[0][0]
        assert call_args["customfield_12345"] == "custom value"


@pytest.mark.unit
class TestCreateIssueAgileFields:
    """Tests for creating issues with Agile fields."""

    def test_create_issue_with_epic(self, mock_jira_client, sample_created_issue):
        """Test creating an issue linked to an epic."""
        mock_jira_client.create_issue.return_value = deepcopy(sample_created_issue)

        with patch.object(
            create_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            create_issue_module.create_issue(
                project="PROJ",
                issue_type="Story",
                summary="Story in Epic",
                epic="PROJ-100",
            )

        call_args = mock_jira_client.create_issue.call_args[0][0]
        assert call_args["customfield_10014"] == "PROJ-100"  # Epic Link field

    def test_create_issue_with_story_points(
        self, mock_jira_client, sample_created_issue
    ):
        """Test creating an issue with story points."""
        mock_jira_client.create_issue.return_value = deepcopy(sample_created_issue)

        with patch.object(
            create_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            create_issue_module.create_issue(
                project="PROJ",
                issue_type="Story",
                summary="Pointed Story",
                story_points=5.0,
            )

        call_args = mock_jira_client.create_issue.call_args[0][0]
        assert call_args["customfield_10016"] == 5.0  # Story Points field

    def test_create_issue_with_sprint(self, mock_jira_client, sample_created_issue):
        """Test creating an issue and adding it to a sprint."""
        mock_jira_client.create_issue.return_value = deepcopy(sample_created_issue)
        mock_jira_client.move_issues_to_sprint = Mock()

        with patch.object(
            create_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            create_issue_module.create_issue(
                project="PROJ", issue_type="Story", summary="Sprint Story", sprint=42
            )

        mock_jira_client.move_issues_to_sprint.assert_called_once_with(42, ["PROJ-130"])


@pytest.mark.unit
class TestCreateIssueTimeTracking:
    """Tests for creating issues with time estimates."""

    def test_create_issue_with_estimate(self, mock_jira_client, sample_created_issue):
        """Test creating an issue with time estimate."""
        mock_jira_client.create_issue.return_value = deepcopy(sample_created_issue)

        with patch.object(
            create_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            create_issue_module.create_issue(
                project="PROJ",
                issue_type="Task",
                summary="Estimated Task",
                estimate="2d",
            )

        call_args = mock_jira_client.create_issue.call_args[0][0]
        assert call_args["timetracking"] == {"originalEstimate": "2d"}


@pytest.mark.unit
class TestCreateIssueLinks:
    """Tests for creating issues with links."""

    def test_create_issue_with_blocks(self, mock_jira_client, sample_created_issue):
        """Test creating an issue that blocks other issues."""
        mock_jira_client.create_issue.return_value = deepcopy(sample_created_issue)
        mock_jira_client.create_link = Mock()

        with patch.object(
            create_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            result = create_issue_module.create_issue(
                project="PROJ",
                issue_type="Bug",
                summary="Blocking Bug",
                blocks=["PROJ-123", "PROJ-124"],
            )

        assert mock_jira_client.create_link.call_count == 2
        mock_jira_client.create_link.assert_any_call("Blocks", "PROJ-130", "PROJ-123")
        mock_jira_client.create_link.assert_any_call("Blocks", "PROJ-130", "PROJ-124")
        assert "links_created" in result

    def test_create_issue_with_relates_to(self, mock_jira_client, sample_created_issue):
        """Test creating an issue related to other issues."""
        mock_jira_client.create_issue.return_value = deepcopy(sample_created_issue)
        mock_jira_client.create_link = Mock()

        with patch.object(
            create_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            result = create_issue_module.create_issue(
                project="PROJ",
                issue_type="Task",
                summary="Related Task",
                relates_to=["PROJ-456"],
            )

        mock_jira_client.create_link.assert_called_once_with(
            "Relates", "PROJ-130", "PROJ-456"
        )
        assert "links_created" in result

    def test_create_issue_link_failure_continues(
        self, mock_jira_client, sample_created_issue
    ):
        """Test that recoverable link creation failure does not fail issue creation."""
        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.create_issue.return_value = deepcopy(sample_created_issue)
        mock_jira_client.create_link = Mock(
            side_effect=NotFoundError("Issue", "PROJ-999")
        )

        with patch.object(
            create_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            result = create_issue_module.create_issue(
                project="PROJ",
                issue_type="Bug",
                summary="Bug with Failed Link",
                blocks=["PROJ-999"],
            )

        # Issue should still be created successfully
        assert result["key"] == "PROJ-130"
        # Failed link should be tracked
        assert "links_failed" in result
        assert len(result["links_failed"]) == 1
        assert "blocks PROJ-999" in result["links_failed"][0]

    def test_create_issue_link_failure_reraises_auth_error(
        self, mock_jira_client, sample_created_issue
    ):
        """Test that non-recoverable errors are re-raised during link creation."""
        from jira_assistant_skills_lib import AuthenticationError

        mock_jira_client.create_issue.return_value = deepcopy(sample_created_issue)
        mock_jira_client.create_link = Mock(
            side_effect=AuthenticationError("Token expired")
        )

        with (
            patch.object(
                create_issue_module, "get_jira_client", return_value=mock_jira_client
            ),
            pytest.raises(AuthenticationError),
        ):
            create_issue_module.create_issue(
                project="PROJ",
                issue_type="Bug",
                summary="Bug with Auth Error on Link",
                blocks=["PROJ-999"],
            )


@pytest.mark.unit
class TestCreateIssueValidation:
    """Tests for input validation."""

    def test_create_issue_invalid_project_key_raises_error(self, mock_jira_client):
        """Test that invalid project key raises ValidationError."""
        from assistant_skills_lib.error_handler import ValidationError

        with (
            patch.object(
                create_issue_module, "get_jira_client", return_value=mock_jira_client
            ),
            pytest.raises(ValidationError),
        ):
            create_issue_module.create_issue(
                project="invalid-project", issue_type="Bug", summary="Test"
            )

    def test_create_issue_empty_project_key_raises_error(self, mock_jira_client):
        """Test that empty project key raises ValidationError."""
        from assistant_skills_lib.error_handler import ValidationError

        with (
            patch.object(
                create_issue_module, "get_jira_client", return_value=mock_jira_client
            ),
            pytest.raises(ValidationError),
        ):
            create_issue_module.create_issue(
                project="", issue_type="Bug", summary="Test"
            )

    def test_create_issue_invalid_epic_key_raises_error(self, mock_jira_client):
        """Test that invalid epic key raises ValidationError."""
        from assistant_skills_lib.error_handler import ValidationError

        with (
            patch.object(
                create_issue_module, "get_jira_client", return_value=mock_jira_client
            ),
            pytest.raises(ValidationError),
        ):
            create_issue_module.create_issue(
                project="PROJ",
                issue_type="Story",
                summary="Test Story",
                epic="invalid-epic",
            )


@pytest.mark.unit
class TestCreateIssueErrors:
    """Tests for error handling."""

    def test_create_issue_permission_denied(self, mock_jira_client):
        """Test handling permission denied error."""
        from jira_assistant_skills_lib import PermissionError

        mock_jira_client.create_issue.side_effect = PermissionError(
            "You do not have permission to create issues in this project"
        )

        with (
            patch.object(
                create_issue_module, "get_jira_client", return_value=mock_jira_client
            ),
            pytest.raises(PermissionError) as exc_info,
        ):
            create_issue_module.create_issue(
                project="PROJ", issue_type="Bug", summary="Forbidden Bug"
            )

        assert "permission" in str(exc_info.value).lower()

    def test_create_issue_authentication_error(self, mock_jira_client):
        """Test handling authentication error."""
        from jira_assistant_skills_lib import AuthenticationError

        mock_jira_client.create_issue.side_effect = AuthenticationError(
            "Authentication failed"
        )

        with (
            patch.object(
                create_issue_module, "get_jira_client", return_value=mock_jira_client
            ),
            pytest.raises(AuthenticationError),
        ):
            create_issue_module.create_issue(
                project="PROJ", issue_type="Bug", summary="Auth Failed Bug"
            )

    def test_create_issue_validation_error_from_api(self, mock_jira_client):
        """Test handling validation error from API."""
        from assistant_skills_lib.error_handler import ValidationError

        mock_jira_client.create_issue.side_effect = ValidationError(
            "Issue type 'InvalidType' is not valid for project 'PROJ'"
        )

        with (
            patch.object(
                create_issue_module, "get_jira_client", return_value=mock_jira_client
            ),
            pytest.raises(ValidationError),
        ):
            create_issue_module.create_issue(
                project="PROJ", issue_type="InvalidType", summary="Invalid Type Bug"
            )


@pytest.mark.unit
class TestCreateIssueTemplate:
    """Tests for template loading."""

    def test_load_template_not_found_raises_error(self):
        """Test that loading non-existent template raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError) as exc_info:
            create_issue_module.load_template("nonexistent_template")

        assert "nonexistent_template" in str(exc_info.value)


@pytest.mark.unit
class TestCreateIssueDescriptionFormats:
    """Tests for description format handling."""

    def test_create_issue_with_markdown_description(
        self, mock_jira_client, sample_created_issue
    ):
        """Test creating issue with markdown description."""
        mock_jira_client.create_issue.return_value = deepcopy(sample_created_issue)

        with patch.object(
            create_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            create_issue_module.create_issue(
                project="PROJ",
                issue_type="Bug",
                summary="Markdown Bug",
                description="**Bold** and *italic* text\n\n- Item 1\n- Item 2",
            )

        call_args = mock_jira_client.create_issue.call_args[0][0]
        # Description should be converted to ADF
        assert isinstance(call_args["description"], dict)
        assert call_args["description"].get("type") == "doc"

    def test_create_issue_with_adf_description(
        self, mock_jira_client, sample_created_issue
    ):
        """Test creating issue with pre-formatted ADF description."""
        mock_jira_client.create_issue.return_value = deepcopy(sample_created_issue)
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
            create_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            create_issue_module.create_issue(
                project="PROJ",
                issue_type="Bug",
                summary="ADF Bug",
                description=adf_description,
            )

        call_args = mock_jira_client.create_issue.call_args[0][0]
        # Description should be parsed JSON
        assert isinstance(call_args["description"], dict)
        assert call_args["description"]["type"] == "doc"

    def test_create_issue_with_plain_text_description(
        self, mock_jira_client, sample_created_issue
    ):
        """Test creating issue with plain text description."""
        mock_jira_client.create_issue.return_value = deepcopy(sample_created_issue)

        with patch.object(
            create_issue_module, "get_jira_client", return_value=mock_jira_client
        ):
            create_issue_module.create_issue(
                project="PROJ",
                issue_type="Bug",
                summary="Plain Text Bug",
                description="Simple plain text description",
            )

        call_args = mock_jira_client.create_issue.call_args[0][0]
        # Description should be converted to ADF
        assert isinstance(call_args["description"], dict)


@pytest.mark.unit
class TestCreateIssueProfile:
    """Tests for profile handling."""

    def test_create_issue_with_profile(self, mock_jira_client, sample_created_issue):
        """Test creating issue with specific profile."""
        mock_jira_client.create_issue.return_value = deepcopy(sample_created_issue)

        with patch.object(
            create_issue_module, "get_jira_client", return_value=mock_jira_client
        ) as mock_get_client:
            create_issue_module.create_issue(
                project="PROJ",
                issue_type="Bug",
                summary="Profiled Bug",
                profile="development",
            )

        # Verify get_jira_client was called with profile
        mock_get_client.assert_called_with("development")
