"""
Live Integration Tests: Issue Cloning

Tests for issue cloning functionality against a real JIRA instance.
"""

import sys
import uuid
from pathlib import Path

import pytest

# Add scripts to path for testing
skills_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(skills_dir / "scripts"))

import contextlib

from clone_issue import clone_issue, extract_cloneable_fields


@pytest.mark.integration
@pytest.mark.relationships
@pytest.mark.clone
class TestBasicCloning:
    """Tests for basic issue cloning."""

    def test_clone_simple_issue(self, jira_client, test_project):
        """Test cloning a basic issue."""
        # Create original
        original = jira_client.create_issue(
            {
                "project": {"key": test_project["key"]},
                "summary": f"Original Issue {uuid.uuid4().hex[:8]}",
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {"type": "text", "text": "Original description"}
                            ],
                        }
                    ],
                },
                "issuetype": {"name": "Task"},
            }
        )

        try:
            result = clone_issue(original["key"])

            assert "clone_key" in result
            assert result["clone_key"] != original["key"]
            assert result["clone_key"].startswith(test_project["key"])

            # Verify clone exists
            clone = jira_client.get_issue(result["clone_key"])
            assert clone is not None

            # Cleanup clone
            jira_client.delete_issue(result["clone_key"])

        finally:
            jira_client.delete_issue(original["key"])

    def test_clone_with_custom_summary(self, jira_client, test_project):
        """Test cloning with a custom summary."""
        original = jira_client.create_issue(
            {
                "project": {"key": test_project["key"]},
                "summary": f"Original Summary {uuid.uuid4().hex[:8]}",
                "issuetype": {"name": "Task"},
            }
        )

        try:
            custom_summary = f"Custom Clone Summary {uuid.uuid4().hex[:8]}"
            result = clone_issue(original["key"], summary=custom_summary)

            clone = jira_client.get_issue(result["clone_key"])
            assert clone["fields"]["summary"] == custom_summary

            jira_client.delete_issue(result["clone_key"])

        finally:
            jira_client.delete_issue(original["key"])

    def test_clone_preserves_priority(self, jira_client, test_project):
        """Test that cloning preserves issue priority."""
        original = jira_client.create_issue(
            {
                "project": {"key": test_project["key"]},
                "summary": f"Priority Test {uuid.uuid4().hex[:8]}",
                "issuetype": {"name": "Task"},
                "priority": {"name": "High"},
            }
        )

        try:
            result = clone_issue(original["key"])

            clone = jira_client.get_issue(result["clone_key"])
            assert clone["fields"]["priority"]["name"] == "High"

            jira_client.delete_issue(result["clone_key"])

        finally:
            jira_client.delete_issue(original["key"])

    def test_clone_preserves_labels(self, jira_client, test_project):
        """Test that cloning preserves issue labels."""
        test_labels = ["test-label", "clone-test"]
        original = jira_client.create_issue(
            {
                "project": {"key": test_project["key"]},
                "summary": f"Labels Test {uuid.uuid4().hex[:8]}",
                "issuetype": {"name": "Task"},
                "labels": test_labels,
            }
        )

        try:
            result = clone_issue(original["key"])

            clone = jira_client.get_issue(result["clone_key"])
            assert set(clone["fields"]["labels"]) == set(test_labels)

            jira_client.delete_issue(result["clone_key"])

        finally:
            jira_client.delete_issue(original["key"])


@pytest.mark.integration
@pytest.mark.relationships
@pytest.mark.clone
class TestCloneLink:
    """Tests for clone link creation."""

    def test_clone_creates_cloners_link(self, jira_client, test_project):
        """Test that cloning creates a 'Cloners' link to original."""
        original = jira_client.create_issue(
            {
                "project": {"key": test_project["key"]},
                "summary": f"Link Test Original {uuid.uuid4().hex[:8]}",
                "issuetype": {"name": "Task"},
            }
        )

        try:
            result = clone_issue(original["key"], create_clone_link=True)
            assert result.get("clone_link_created", False) is True

            # Verify link exists
            clone_links = jira_client.get_issue_links(result["clone_key"])
            cloner_links = [l for l in clone_links if l["type"]["name"] == "Cloners"]
            assert len(cloner_links) >= 1

            jira_client.delete_issue(result["clone_key"])

        finally:
            jira_client.delete_issue(original["key"])

    def test_clone_without_link(self, jira_client, test_project):
        """Test cloning without creating a clone link."""
        original = jira_client.create_issue(
            {
                "project": {"key": test_project["key"]},
                "summary": f"No Link Test {uuid.uuid4().hex[:8]}",
                "issuetype": {"name": "Task"},
            }
        )

        try:
            result = clone_issue(original["key"], create_clone_link=False)

            # Verify no Cloners link exists
            clone_links = jira_client.get_issue_links(result["clone_key"])
            cloner_links = [l for l in clone_links if l["type"]["name"] == "Cloners"]
            assert len(cloner_links) == 0

            jira_client.delete_issue(result["clone_key"])

        finally:
            jira_client.delete_issue(original["key"])


@pytest.mark.integration
@pytest.mark.relationships
@pytest.mark.clone
class TestCloneWithSubtasks:
    """Tests for cloning issues with subtasks."""

    def test_clone_with_subtasks(self, jira_client, issue_with_subtasks):
        """Test cloning an issue including its subtasks."""
        result = clone_issue(issue_with_subtasks["key"], include_subtasks=True)

        try:
            assert result["subtasks_cloned"] >= 2

            # Verify clone has subtasks
            clone = jira_client.get_issue(result["clone_key"])
            cloned_subtasks = clone["fields"].get("subtasks", [])
            assert len(cloned_subtasks) == 2

            # Clean up cloned subtasks
            for subtask in cloned_subtasks:
                jira_client.delete_issue(subtask["key"])
            jira_client.delete_issue(result["clone_key"])

        except Exception:
            # Ensure cleanup on failure
            with contextlib.suppress(Exception):
                jira_client.delete_issue(result["clone_key"])
            raise

    def test_clone_without_subtasks(self, jira_client, issue_with_subtasks):
        """Test cloning an issue without including subtasks."""
        result = clone_issue(issue_with_subtasks["key"], include_subtasks=False)

        try:
            assert result["subtasks_cloned"] == 0

            # Verify clone has no subtasks
            clone = jira_client.get_issue(result["clone_key"])
            cloned_subtasks = clone["fields"].get("subtasks", [])
            assert len(cloned_subtasks) == 0

            jira_client.delete_issue(result["clone_key"])

        except Exception:
            with contextlib.suppress(Exception):
                jira_client.delete_issue(result["clone_key"])
            raise


@pytest.mark.integration
@pytest.mark.relationships
@pytest.mark.clone
class TestCloneWithLinks:
    """Tests for cloning issues while preserving links."""

    def test_clone_with_links(self, jira_client, test_project):
        """Test cloning an issue and preserving its links."""
        # Create original with a link
        original = jira_client.create_issue(
            {
                "project": {"key": test_project["key"]},
                "summary": f"Original with Links {uuid.uuid4().hex[:8]}",
                "issuetype": {"name": "Task"},
            }
        )
        related = jira_client.create_issue(
            {
                "project": {"key": test_project["key"]},
                "summary": f"Related Issue {uuid.uuid4().hex[:8]}",
                "issuetype": {"name": "Task"},
            }
        )

        try:
            # Link original to related
            jira_client.create_link("Relates", related["key"], original["key"])

            # Clone with links
            result = clone_issue(original["key"], include_links=True)

            # Clone should have links (at minimum the Cloners link)
            clone_links = jira_client.get_issue_links(result["clone_key"])
            assert len(clone_links) >= 1

            # Verify Cloners link exists
            has_cloners = any(l["type"]["name"] == "Cloners" for l in clone_links)
            assert has_cloners

            jira_client.delete_issue(result["clone_key"])

        finally:
            jira_client.delete_issue(original["key"])
            jira_client.delete_issue(related["key"])

    def test_clone_without_links(self, jira_client, test_project):
        """Test cloning an issue without preserving its links."""
        # Create original with a link
        original = jira_client.create_issue(
            {
                "project": {"key": test_project["key"]},
                "summary": f"Original No Links Copy {uuid.uuid4().hex[:8]}",
                "issuetype": {"name": "Task"},
            }
        )
        related = jira_client.create_issue(
            {
                "project": {"key": test_project["key"]},
                "summary": f"Related No Copy {uuid.uuid4().hex[:8]}",
                "issuetype": {"name": "Task"},
            }
        )

        try:
            jira_client.create_link("Relates", related["key"], original["key"])

            result = clone_issue(
                original["key"], include_links=False, create_clone_link=True
            )

            # Clone should only have Cloners link (not Relates)
            clone_links = jira_client.get_issue_links(result["clone_key"])
            relates_links = [l for l in clone_links if l["type"]["name"] == "Relates"]
            assert len(relates_links) == 0

            jira_client.delete_issue(result["clone_key"])

        finally:
            jira_client.delete_issue(original["key"])
            jira_client.delete_issue(related["key"])


@pytest.mark.integration
@pytest.mark.relationships
@pytest.mark.clone
class TestCloneFieldExtraction:
    """Tests for the extract_cloneable_fields helper function."""

    def test_extract_fields_basic(self, jira_client, test_issue):
        """Test extracting basic fields from an issue."""
        issue = jira_client.get_issue(test_issue["key"])
        fields = extract_cloneable_fields(issue)

        assert "project" in fields
        assert "issuetype" in fields
        assert "summary" in fields

    def test_extract_fields_to_different_project(self, jira_client, test_issue):
        """Test extracting fields for clone to different project."""
        issue = jira_client.get_issue(test_issue["key"])
        fields = extract_cloneable_fields(issue, to_project="OTHER")

        assert fields["project"]["key"] == "OTHER"

    def test_extract_fields_summary_prefixed(self, jira_client, test_issue):
        """Test that extracted summary is prefixed with clone indicator."""
        issue = jira_client.get_issue(test_issue["key"])
        fields = extract_cloneable_fields(issue)

        assert "[Clone of" in fields["summary"]


@pytest.mark.integration
@pytest.mark.relationships
@pytest.mark.clone
class TestCloneEdgeCases:
    """Tests for edge cases in issue cloning."""

    def test_clone_issue_with_description(self, jira_client, test_project):
        """Test cloning issue preserves description."""
        description_text = f"Detailed description {uuid.uuid4().hex[:8]}"
        original = jira_client.create_issue(
            {
                "project": {"key": test_project["key"]},
                "summary": f"Description Test {uuid.uuid4().hex[:8]}",
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": description_text}],
                        }
                    ],
                },
                "issuetype": {"name": "Task"},
            }
        )

        try:
            result = clone_issue(original["key"])

            clone = jira_client.get_issue(result["clone_key"])
            # Description should exist (may be ADF format)
            assert clone["fields"]["description"] is not None

            jira_client.delete_issue(result["clone_key"])

        finally:
            jira_client.delete_issue(original["key"])

    def test_clone_bug_issue_type(self, jira_client, test_project):
        """Test cloning a Bug issue type."""
        original = jira_client.create_issue(
            {
                "project": {"key": test_project["key"]},
                "summary": f"Bug Clone Test {uuid.uuid4().hex[:8]}",
                "issuetype": {"name": "Bug"},
            }
        )

        try:
            result = clone_issue(original["key"])

            clone = jira_client.get_issue(result["clone_key"])
            assert clone["fields"]["issuetype"]["name"] == "Bug"

            jira_client.delete_issue(result["clone_key"])

        finally:
            jira_client.delete_issue(original["key"])

    def test_clone_story_issue_type(self, jira_client, test_project):
        """Test cloning a Story issue type."""
        original = jira_client.create_issue(
            {
                "project": {"key": test_project["key"]},
                "summary": f"Story Clone Test {uuid.uuid4().hex[:8]}",
                "issuetype": {"name": "Story"},
            }
        )

        try:
            result = clone_issue(original["key"])

            clone = jira_client.get_issue(result["clone_key"])
            assert clone["fields"]["issuetype"]["name"] == "Story"

            jira_client.delete_issue(result["clone_key"])

        finally:
            jira_client.delete_issue(original["key"])

    def test_clone_result_structure(self, jira_client, test_project):
        """Test that clone result has expected structure."""
        original = jira_client.create_issue(
            {
                "project": {"key": test_project["key"]},
                "summary": f"Result Structure Test {uuid.uuid4().hex[:8]}",
                "issuetype": {"name": "Task"},
            }
        )

        try:
            result = clone_issue(original["key"])

            assert "original_key" in result
            assert "clone_key" in result
            assert "project" in result
            assert "links_copied" in result
            assert "subtasks_cloned" in result

            assert result["original_key"] == original["key"]

            jira_client.delete_issue(result["clone_key"])

        finally:
            jira_client.delete_issue(original["key"])
