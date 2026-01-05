"""
Tests for search_workflows.py - TDD approach.

Tests for searching workflows with various filters.
"""

import sys
from pathlib import Path

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))


class TestSearchWorkflowsByName:
    """Test searching workflows by name pattern."""

    def test_search_workflows_by_name_pattern(
        self, mock_jira_client, workflow_search_response
    ):
        """Test searching workflows by name pattern."""
        from search_workflows import search_workflows

        mock_jira_client.search_workflows.return_value = workflow_search_response

        result = search_workflows(client=mock_jira_client, name="Development")

        assert len(result["workflows"]) > 0
        mock_jira_client.search_workflows.assert_called_once()
        call_kwargs = mock_jira_client.search_workflows.call_args[1]
        assert call_kwargs.get("workflow_name") == "Development"

    def test_search_workflows_no_results(
        self, mock_jira_client, empty_workflows_response
    ):
        """Test search with no matching results."""
        from search_workflows import search_workflows

        mock_jira_client.search_workflows.return_value = empty_workflows_response

        result = search_workflows(client=mock_jira_client, name="Nonexistent")

        assert len(result["workflows"]) == 0


class TestSearchWorkflowsByStatus:
    """Test searching workflows containing a specific status."""

    def test_search_workflows_with_status(
        self, mock_jira_client, workflow_search_response
    ):
        """Test finding workflows containing a specific status."""
        from search_workflows import search_workflows

        mock_jira_client.search_workflows.return_value = workflow_search_response

        result = search_workflows(
            client=mock_jira_client, status="In Progress", expand="statuses"
        )

        # Should find workflows containing the status
        assert len(result["workflows"]) > 0
        # Verify statuses were expanded
        call_kwargs = mock_jira_client.search_workflows.call_args[1]
        assert "statuses" in call_kwargs.get("expand", "")

    def test_search_workflows_filter_by_status_client_side(
        self, mock_jira_client, workflow_search_response
    ):
        """Test client-side filtering by status name."""
        from search_workflows import search_workflows

        mock_jira_client.search_workflows.return_value = workflow_search_response

        result = search_workflows(client=mock_jira_client, status="Code Review")

        # Should only return workflows with Code Review status
        for wf in result["workflows"]:
            status_names = [s.get("name", "") for s in wf.get("statuses", [])]
            assert len(status_names) > 0, "Statuses should be loaded for filtering"
            assert "Code Review" in status_names


class TestSearchWorkflowsByScope:
    """Test filtering by workflow scope."""

    def test_search_workflows_global_scope(
        self, mock_jira_client, workflow_search_response
    ):
        """Test filtering to global workflows."""
        from search_workflows import search_workflows

        mock_jira_client.search_workflows.return_value = workflow_search_response

        result = search_workflows(client=mock_jira_client, scope="global")

        assert len(result["workflows"]) > 0

    def test_search_workflows_project_scope(self, mock_jira_client):
        """Test filtering to project-scoped workflows."""
        from search_workflows import search_workflows

        project_scoped_response = {
            "values": [
                {
                    "id": {
                        "name": "Project Custom Workflow",
                        "entityId": "project-custom-123",
                    },
                    "scope": {"type": "PROJECT", "project": {"key": "PROJ"}},
                    "statuses": [],
                    "transitions": [],
                }
            ],
            "total": 1,
        }
        mock_jira_client.search_workflows.return_value = project_scoped_response

        result = search_workflows(client=mock_jira_client, scope="project")

        assert len(result["workflows"]) == 1
        assert result["workflows"][0]["scope_type"] == "PROJECT"


class TestSearchWorkflowsExpand:
    """Test expanding transition details."""

    def test_search_workflows_expand_transitions(
        self, mock_jira_client, workflow_search_response
    ):
        """Test expanding transition details in search."""
        from search_workflows import search_workflows

        mock_jira_client.search_workflows.return_value = workflow_search_response

        search_workflows(client=mock_jira_client, expand="transitions")

        call_kwargs = mock_jira_client.search_workflows.call_args[1]
        assert "transitions" in call_kwargs.get("expand", "")

    def test_search_workflows_expand_multiple(
        self, mock_jira_client, workflow_search_response
    ):
        """Test expanding multiple fields."""
        from search_workflows import search_workflows

        mock_jira_client.search_workflows.return_value = workflow_search_response

        search_workflows(client=mock_jira_client, expand="transitions,statuses")

        call_kwargs = mock_jira_client.search_workflows.call_args[1]
        expand = call_kwargs.get("expand", "")
        assert "transitions" in expand
        assert "statuses" in expand


class TestSearchWorkflowsActiveFilter:
    """Test filtering by active status."""

    def test_search_workflows_active_only(
        self, mock_jira_client, workflow_search_response
    ):
        """Test filtering to active workflows only."""
        from search_workflows import search_workflows

        mock_jira_client.search_workflows.return_value = workflow_search_response

        search_workflows(client=mock_jira_client, is_active=True)

        call_kwargs = mock_jira_client.search_workflows.call_args[1]
        assert call_kwargs.get("is_active")

    def test_search_workflows_inactive_only(
        self, mock_jira_client, empty_workflows_response
    ):
        """Test filtering to inactive workflows only."""
        from search_workflows import search_workflows

        mock_jira_client.search_workflows.return_value = empty_workflows_response

        search_workflows(client=mock_jira_client, is_active=False)

        call_kwargs = mock_jira_client.search_workflows.call_args[1]
        assert not call_kwargs.get("is_active")


class TestSearchWorkflowsOrdering:
    """Test result ordering."""

    def test_search_workflows_order_by_name(
        self, mock_jira_client, workflow_search_response
    ):
        """Test ordering results by name."""
        from search_workflows import search_workflows

        mock_jira_client.search_workflows.return_value = workflow_search_response

        search_workflows(client=mock_jira_client, order_by="name")

        call_kwargs = mock_jira_client.search_workflows.call_args[1]
        assert call_kwargs.get("order_by") == "name"

    def test_search_workflows_order_by_created(
        self, mock_jira_client, workflow_search_response
    ):
        """Test ordering results by creation date."""
        from search_workflows import search_workflows

        mock_jira_client.search_workflows.return_value = workflow_search_response

        search_workflows(client=mock_jira_client, order_by="created")

        call_kwargs = mock_jira_client.search_workflows.call_args[1]
        assert call_kwargs.get("order_by") == "created"


class TestSearchWorkflowsCombinedFilters:
    """Test combining multiple filters."""

    def test_search_workflows_combined_filters(
        self, mock_jira_client, workflow_search_response
    ):
        """Test combining name, scope, and active filters."""
        from search_workflows import search_workflows

        mock_jira_client.search_workflows.return_value = workflow_search_response

        search_workflows(
            client=mock_jira_client, name="Software", scope="global", is_active=True
        )

        call_kwargs = mock_jira_client.search_workflows.call_args[1]
        assert call_kwargs.get("workflow_name") == "Software"
        assert call_kwargs.get("is_active")


class TestSearchWorkflowsOutputFormats:
    """Test output format handling."""

    def test_search_workflows_format_table(
        self, mock_jira_client, workflow_search_response
    ):
        """Test table output format."""
        from search_workflows import format_search_results, search_workflows

        mock_jira_client.search_workflows.return_value = workflow_search_response

        result = search_workflows(client=mock_jira_client)
        output = format_search_results(result["workflows"])

        assert "Software Development Workflow" in output
        assert "Bug Workflow" in output

    def test_search_workflows_format_json(
        self, mock_jira_client, workflow_search_response
    ):
        """Test JSON output format."""
        import json

        from search_workflows import format_search_json, search_workflows

        mock_jira_client.search_workflows.return_value = workflow_search_response

        result = search_workflows(client=mock_jira_client)
        output = format_search_json(result["workflows"])

        # Should be valid JSON
        parsed = json.loads(output)
        assert len(parsed) > 0


class TestSearchWorkflowsErrorHandling:
    """Test error handling scenarios."""

    def test_search_workflows_api_error(self, mock_jira_client):
        """Test handling of API errors."""
        from search_workflows import search_workflows

        from jira_assistant_skills_lib import JiraError

        mock_jira_client.search_workflows.side_effect = JiraError("API Error")

        with pytest.raises(JiraError):
            search_workflows(client=mock_jira_client)
