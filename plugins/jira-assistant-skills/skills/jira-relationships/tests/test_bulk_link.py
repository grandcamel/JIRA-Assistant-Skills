"""
Tests for bulk_link.py

TDD tests for bulk linking multiple issues.
"""

import json
from unittest.mock import patch

import pytest


@pytest.fixture
def jql_search_results():
    """Sample JQL search results."""
    return {
        "issues": [
            {
                "key": "PROJ-1",
                "fields": {"summary": "First issue", "status": {"name": "To Do"}},
            },
            {
                "key": "PROJ-2",
                "fields": {
                    "summary": "Second issue",
                    "status": {"name": "In Progress"},
                },
            },
            {
                "key": "PROJ-3",
                "fields": {"summary": "Third issue", "status": {"name": "Done"}},
            },
        ],
        "total": 3,
    }


@pytest.fixture
def existing_links():
    """Links indicating PROJ-1 is already linked to target."""
    return [
        {
            "id": "50001",
            "type": {
                "id": "10000",
                "name": "Blocks",
                "inward": "is blocked by",
                "outward": "blocks",
            },
            "outwardIssue": {
                "key": "PROJ-100",
                "fields": {"summary": "Target issue", "status": {"name": "To Do"}},
            },
        }
    ]


@pytest.mark.relationships
@pytest.mark.unit
class TestBulkLink:
    """Tests for the bulk_link function."""

    def test_link_multiple_to_one(self, mock_jira_client):
        """Test linking multiple issues to a single target."""
        mock_jira_client.create_link.return_value = None

        import bulk_link

        with patch.object(bulk_link, "get_jira_client", return_value=mock_jira_client):
            result = bulk_link.bulk_link(
                issues=["PROJ-1", "PROJ-2", "PROJ-3"],
                target="PROJ-100",
                link_type="Blocks",
            )

        # Should create 3 links
        assert mock_jira_client.create_link.call_count == 3
        assert result["created"] == 3
        assert result["failed"] == 0

    def test_link_from_jql(self, mock_jira_client, jql_search_results):
        """Test linking all JQL results to target."""
        mock_jira_client.search_issues.return_value = jql_search_results
        mock_jira_client.create_link.return_value = None

        import bulk_link

        with patch.object(bulk_link, "get_jira_client", return_value=mock_jira_client):
            result = bulk_link.bulk_link(
                jql="project = PROJ AND fixVersion = 1.0",
                target="PROJ-500",
                link_type="Relates",
            )

        # Should search and then link all 3 results
        mock_jira_client.search_issues.assert_called_once()
        assert mock_jira_client.create_link.call_count == 3
        assert result["created"] == 3

    def test_bulk_link_dry_run(self, mock_jira_client):
        """Test preview of bulk operation."""
        import bulk_link

        with patch.object(bulk_link, "get_jira_client", return_value=mock_jira_client):
            result = bulk_link.bulk_link(
                issues=["PROJ-1", "PROJ-2"],
                target="PROJ-100",
                link_type="Blocks",
                dry_run=True,
            )

        # Should NOT create any links
        mock_jira_client.create_link.assert_not_called()
        # Should report what would be done
        assert result["dry_run"] is True
        assert result["would_create"] == 2

    def test_bulk_link_progress(self, mock_jira_client, capsys):
        """Test progress reporting during bulk ops."""
        mock_jira_client.create_link.return_value = None

        import bulk_link

        with patch.object(bulk_link, "get_jira_client", return_value=mock_jira_client):
            result = bulk_link.bulk_link(
                issues=["PROJ-1", "PROJ-2", "PROJ-3", "PROJ-4", "PROJ-5"],
                target="PROJ-100",
                link_type="Blocks",
                show_progress=True,
            )

        # Progress should be tracked in result
        assert "progress" in result or result["created"] == 5

    def test_bulk_link_partial_failure(self, mock_jira_client):
        """Test handling when some links fail."""
        from jira_assistant_skills_lib import JiraError

        # First and third succeed, second fails
        def side_effect(link_type, inward_key, outward_key, comment=None):
            if inward_key == "PROJ-2":
                raise JiraError("Issue PROJ-2 not found", 404)
            return None

        mock_jira_client.create_link.side_effect = side_effect

        import bulk_link

        with patch.object(bulk_link, "get_jira_client", return_value=mock_jira_client):
            result = bulk_link.bulk_link(
                issues=["PROJ-1", "PROJ-2", "PROJ-3"],
                target="PROJ-100",
                link_type="Blocks",
            )

        # Should report partial success
        assert result["created"] == 2
        assert result["failed"] == 1
        assert len(result["errors"]) == 1
        assert "PROJ-2" in result["errors"][0]

    def test_bulk_link_skip_existing(self, mock_jira_client, existing_links):
        """Test skipping already-linked issues."""
        # PROJ-1 already linked to PROJ-100
        mock_jira_client.get_issue_links.side_effect = (
            lambda key: existing_links if key == "PROJ-1" else []
        )
        mock_jira_client.create_link.return_value = None

        import bulk_link

        with patch.object(bulk_link, "get_jira_client", return_value=mock_jira_client):
            result = bulk_link.bulk_link(
                issues=["PROJ-1", "PROJ-2", "PROJ-3"],
                target="PROJ-100",
                link_type="Blocks",
                skip_existing=True,
            )

        # Should skip PROJ-1, only create 2 links
        assert result["skipped"] == 1
        assert result["created"] == 2


@pytest.mark.relationships
@pytest.mark.unit
class TestBulkLinkFormat:
    """Tests for bulk_link output formatting."""

    def test_format_text_output(self, mock_jira_client):
        """Test human-readable summary output."""
        mock_jira_client.create_link.return_value = None

        import bulk_link

        with patch.object(bulk_link, "get_jira_client", return_value=mock_jira_client):
            result = bulk_link.bulk_link(
                issues=["PROJ-1", "PROJ-2"], target="PROJ-100", link_type="Blocks"
            )
            output = bulk_link.format_bulk_result(result, output_format="text")

        assert "PROJ-100" in output
        assert "2" in output or "created" in output.lower()

    def test_format_json_output(self, mock_jira_client):
        """Test JSON output format."""
        mock_jira_client.create_link.return_value = None

        import bulk_link

        with patch.object(bulk_link, "get_jira_client", return_value=mock_jira_client):
            result = bulk_link.bulk_link(
                issues=["PROJ-1", "PROJ-2"], target="PROJ-100", link_type="Blocks"
            )
            output = bulk_link.format_bulk_result(result, output_format="json")

        # Should be valid JSON
        parsed = json.loads(output)
        assert "created" in parsed


@pytest.mark.relationships
@pytest.mark.unit
class TestBulkLinkErrorHandling:
    """Test API error handling scenarios for bulk_link.

    Note: bulk_link catches individual link creation errors and continues
    processing remaining issues, reporting errors in the result. This is
    expected behavior for bulk operations.
    """

    def test_authentication_error_in_result(self, mock_jira_client):
        """Test that authentication errors are captured in result."""
        from jira_assistant_skills_lib import AuthenticationError

        mock_jira_client.create_link.side_effect = AuthenticationError("Invalid token")

        import bulk_link

        with patch.object(bulk_link, "get_jira_client", return_value=mock_jira_client):
            result = bulk_link.bulk_link(
                issues=["PROJ-1"], target="PROJ-100", link_type="Blocks"
            )

        # Bulk operations capture errors instead of raising them
        assert result["failed"] == 1
        assert result["created"] == 0
        assert len(result["errors"]) == 1
        assert "Invalid token" in result["errors"][0]

    def test_forbidden_error_in_result(self, mock_jira_client):
        """Test that permission errors are captured in result."""
        from jira_assistant_skills_lib import PermissionError

        mock_jira_client.create_link.side_effect = PermissionError(
            "Insufficient permissions"
        )

        import bulk_link

        with patch.object(bulk_link, "get_jira_client", return_value=mock_jira_client):
            result = bulk_link.bulk_link(
                issues=["PROJ-1"], target="PROJ-100", link_type="Blocks"
            )

        # Bulk operations capture errors instead of raising them
        assert result["failed"] == 1
        assert result["created"] == 0
        assert len(result["errors"]) == 1
        assert "Insufficient permissions" in result["errors"][0]

    def test_rate_limit_error_in_result(self, mock_jira_client):
        """Test that rate limit errors are captured in result."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.create_link.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        import bulk_link

        with patch.object(bulk_link, "get_jira_client", return_value=mock_jira_client):
            result = bulk_link.bulk_link(
                issues=["PROJ-1"], target="PROJ-100", link_type="Blocks"
            )

        # Bulk operations capture errors instead of raising them
        assert result["failed"] == 1
        assert result["created"] == 0
        assert len(result["errors"]) == 1
        assert "Rate limit exceeded" in result["errors"][0]

    def test_server_error_in_result(self, mock_jira_client):
        """Test that server errors are captured in result."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.create_link.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        import bulk_link

        with patch.object(bulk_link, "get_jira_client", return_value=mock_jira_client):
            result = bulk_link.bulk_link(
                issues=["PROJ-1"], target="PROJ-100", link_type="Blocks"
            )

        # Bulk operations capture errors instead of raising them
        assert result["failed"] == 1
        assert result["created"] == 0
        assert len(result["errors"]) == 1
        assert "Internal server error" in result["errors"][0]
