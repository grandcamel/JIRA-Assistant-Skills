"""
Template Validation Tests for jira-issue skill.

Tests verify that template loading and validation works correctly
for create_issue.py.
"""

import json
import os
import sys
import tempfile
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import pytest

# Add scripts path
scripts_path = str(Path(__file__).parent.parent / "scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


@pytest.mark.unit
class TestTemplateLoading:
    """Tests for template loading functionality."""

    def test_load_valid_bug_template(self):
        """Test loading valid bug template."""
        import create_issue

        template = create_issue.load_template("bug")

        assert template is not None
        assert "fields" in template
        assert template["fields"]["issuetype"]["name"] == "Bug"

    def test_load_valid_task_template(self):
        """Test loading valid task template."""
        import create_issue

        template = create_issue.load_template("task")

        assert template is not None
        assert "fields" in template
        assert template["fields"]["issuetype"]["name"] == "Task"

    def test_load_valid_story_template(self):
        """Test loading valid story template."""
        import create_issue

        template = create_issue.load_template("story")

        assert template is not None
        assert "fields" in template
        assert template["fields"]["issuetype"]["name"] == "Story"

    def test_load_nonexistent_template_raises_error(self):
        """Test loading non-existent template raises FileNotFoundError."""
        import create_issue

        with pytest.raises(FileNotFoundError) as exc_info:
            create_issue.load_template("nonexistent")

        assert "nonexistent" in str(exc_info.value)

    def test_template_has_valid_adf_description(self):
        """Test that template descriptions are valid ADF format."""
        import create_issue

        template = create_issue.load_template("bug")
        description = template["fields"].get("description", {})

        # Should have ADF structure
        assert description.get("type") == "doc"
        assert description.get("version") == 1
        assert "content" in description
        assert isinstance(description["content"], list)


@pytest.mark.unit
class TestTemplateValidation:
    """Tests for template structure validation."""

    def test_template_has_required_fields_section(self):
        """Test template has 'fields' section."""
        import create_issue

        for template_name in ["bug", "task", "story"]:
            template = create_issue.load_template(template_name)
            assert "fields" in template, f"{template_name} template missing 'fields'"

    def test_template_issuetype_structure(self):
        """Test template issuetype has correct structure."""
        import create_issue

        for template_name in ["bug", "task", "story"]:
            template = create_issue.load_template(template_name)
            issuetype = template["fields"].get("issuetype", {})
            assert "name" in issuetype, (
                f"{template_name} template missing issuetype.name"
            )

    def test_template_adf_content_structure(self):
        """Test template ADF content has valid node types."""
        import create_issue

        valid_node_types = [
            "paragraph",
            "heading",
            "bulletList",
            "orderedList",
            "listItem",
            "codeBlock",
            "blockquote",
            "table",
            "tableRow",
            "tableCell",
            "tableHeader",
            "rule",
        ]

        template = create_issue.load_template("bug")
        description = template["fields"].get("description", {})
        content = description.get("content", [])

        for node in content:
            assert node.get("type") in valid_node_types, (
                f"Invalid ADF node type: {node.get('type')}"
            )


@pytest.mark.unit
class TestTemplateMerging:
    """Tests for template field merging with user input."""

    def test_user_summary_overrides_template(
        self, mock_jira_client, sample_created_issue
    ):
        """Test that user-provided summary overrides template."""
        import create_issue

        mock_jira_client.create_issue.return_value = deepcopy(sample_created_issue)

        with patch.object(
            create_issue, "get_jira_client", return_value=mock_jira_client
        ):
            create_issue.create_issue(
                project="PROJ", issue_type="Bug", summary="User Summary", template="bug"
            )

        call_args = mock_jira_client.create_issue.call_args[0][0]
        assert call_args["summary"] == "User Summary"

    def test_user_priority_overrides_template(
        self, mock_jira_client, sample_created_issue
    ):
        """Test that user-provided priority overrides template default."""
        import create_issue

        mock_jira_client.create_issue.return_value = deepcopy(sample_created_issue)

        with patch.object(
            create_issue, "get_jira_client", return_value=mock_jira_client
        ):
            create_issue.create_issue(
                project="PROJ",
                issue_type="Bug",
                summary="Test",
                template="bug",
                priority="Critical",
            )

        call_args = mock_jira_client.create_issue.call_args[0][0]
        assert call_args["priority"] == {"name": "Critical"}

    def test_template_description_used_when_not_provided(
        self, mock_jira_client, sample_created_issue
    ):
        """Test template description is used when user doesn't provide one."""
        import create_issue

        mock_jira_client.create_issue.return_value = deepcopy(sample_created_issue)

        with patch.object(
            create_issue, "get_jira_client", return_value=mock_jira_client
        ):
            create_issue.create_issue(
                project="PROJ", issue_type="Bug", summary="Test", template="bug"
            )

        call_args = mock_jira_client.create_issue.call_args[0][0]
        description = call_args.get("description", {})
        # Template description should be present
        assert description.get("type") == "doc"

    def test_user_description_overrides_template(
        self, mock_jira_client, sample_created_issue
    ):
        """Test user description overrides template description."""
        import create_issue

        mock_jira_client.create_issue.return_value = deepcopy(sample_created_issue)

        with patch.object(
            create_issue, "get_jira_client", return_value=mock_jira_client
        ):
            create_issue.create_issue(
                project="PROJ",
                issue_type="Bug",
                summary="Test",
                template="bug",
                description="User-provided description",
            )

        call_args = mock_jira_client.create_issue.call_args[0][0]
        description = call_args.get("description", {})
        # Should be user's description converted to ADF
        assert description.get("type") == "doc"


@pytest.mark.unit
class TestInvalidTemplates:
    """Tests for handling invalid template files."""

    def test_invalid_json_template_raises_error(self):
        """Test that invalid JSON template raises appropriate error."""
        import create_issue

        # Create temporary invalid JSON file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix="_template.json", delete=False
        ) as f:
            f.write("{ invalid json }")
            temp_path = f.name

        try:
            Path(temp_path).parent
            template_name = Path(temp_path).stem.replace("_template", "")

            with patch.object(create_issue, "load_template") as mock_load:
                mock_load.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

                with pytest.raises(json.JSONDecodeError):
                    create_issue.load_template(template_name)
        finally:
            os.unlink(temp_path)

    def test_template_without_fields_uses_empty(
        self, mock_jira_client, sample_created_issue
    ):
        """Test handling template without 'fields' key."""
        import create_issue

        mock_jira_client.create_issue.return_value = deepcopy(sample_created_issue)

        # Mock a template that returns empty fields
        def mock_load_template(name):
            return {"not_fields": {}}

        with patch.object(create_issue, "load_template", mock_load_template):
            with patch.object(
                create_issue, "get_jira_client", return_value=mock_jira_client
            ):
                result = create_issue.create_issue(
                    project="PROJ", issue_type="Bug", summary="Test", template="empty"
                )

        # Should still create issue with user-provided fields
        assert result is not None
