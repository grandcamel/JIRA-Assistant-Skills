"""
Tests for get_workflow.py - TDD approach.

Tests for getting detailed workflow information including statuses and transitions.
"""

import sys
from pathlib import Path

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))


class TestGetWorkflowByName:
    """Test getting workflow by name."""

    def test_get_workflow_by_name(self, mock_jira_client, software_workflow):
        """Test getting workflow by exact name."""
        from get_workflow import get_workflow

        mock_jira_client.search_workflows.return_value = {
            "values": [software_workflow],
            "total": 1,
        }

        result = get_workflow(
            client=mock_jira_client, name="Software Development Workflow"
        )

        assert result["name"] == "Software Development Workflow"
        mock_jira_client.search_workflows.assert_called_once()

    def test_get_workflow_name_not_found(self, mock_jira_client):
        """Test error when workflow name not found."""
        from get_workflow import get_workflow

        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.search_workflows.return_value = {"values": [], "total": 0}

        with pytest.raises(NotFoundError) as exc_info:
            get_workflow(client=mock_jira_client, name="Nonexistent Workflow")

        assert "not found" in str(exc_info.value).lower()


class TestGetWorkflowByEntityId:
    """Test getting workflow by entity ID."""

    def test_get_workflow_by_entity_id(self, mock_jira_client, software_workflow):
        """Test getting workflow by entity ID."""
        from get_workflow import get_workflow

        entity_id = "c6c7e6b0-19c4-4516-9a47-93f76124d4d4"
        mock_jira_client.get_workflow_bulk.return_value = {
            "workflows": [software_workflow]
        }

        result = get_workflow(client=mock_jira_client, entity_id=entity_id)

        assert result["entity_id"] == entity_id
        mock_jira_client.get_workflow_bulk.assert_called_once()

    def test_get_workflow_invalid_entity_id(self, mock_jira_client):
        """Test error for invalid entity ID."""
        from get_workflow import get_workflow

        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.get_workflow_bulk.return_value = {"workflows": []}

        with pytest.raises(NotFoundError):
            get_workflow(client=mock_jira_client, entity_id="invalid-id")


class TestGetWorkflowWithStatuses:
    """Test getting workflow with status details."""

    def test_get_workflow_show_statuses(self, mock_jira_client, software_workflow):
        """Test getting workflow with statuses listed."""
        from get_workflow import get_workflow

        mock_jira_client.search_workflows.return_value = {
            "values": [software_workflow],
            "total": 1,
        }

        result = get_workflow(
            client=mock_jira_client,
            name="Software Development Workflow",
            show_statuses=True,
        )

        assert "statuses" in result
        assert len(result["statuses"]) == 5
        assert any(s["name"] == "To Do" for s in result["statuses"])
        assert any(s["name"] == "In Progress" for s in result["statuses"])
        assert any(s["name"] == "Done" for s in result["statuses"])

    def test_get_workflow_statuses_sorted_by_category(
        self, mock_jira_client, software_workflow
    ):
        """Test that statuses are sorted by category (TODO, IN_PROGRESS, DONE)."""
        from get_workflow import get_workflow

        mock_jira_client.search_workflows.return_value = {
            "values": [software_workflow],
            "total": 1,
        }

        result = get_workflow(
            client=mock_jira_client,
            name="Software Development Workflow",
            show_statuses=True,
        )

        # Verify statuses exist with categories
        categories = [s.get("statusCategory", "UNKNOWN") for s in result["statuses"]]
        assert "TODO" in categories
        assert "IN_PROGRESS" in categories
        assert "DONE" in categories


class TestGetWorkflowWithTransitions:
    """Test getting workflow with transition details."""

    def test_get_workflow_show_transitions(self, mock_jira_client, software_workflow):
        """Test getting workflow with transitions listed."""
        from get_workflow import get_workflow

        mock_jira_client.search_workflows.return_value = {
            "values": [software_workflow],
            "total": 1,
        }

        result = get_workflow(
            client=mock_jira_client,
            name="Software Development Workflow",
            show_transitions=True,
        )

        assert "transitions" in result
        assert len(result["transitions"]) == 5
        transition_names = [t["name"] for t in result["transitions"]]
        assert "Start Progress" in transition_names
        assert "Complete" in transition_names

    def test_get_workflow_transition_from_to(self, mock_jira_client, software_workflow):
        """Test that transitions show from/to statuses."""
        from get_workflow import get_workflow

        mock_jira_client.search_workflows.return_value = {
            "values": [software_workflow],
            "total": 1,
        }

        result = get_workflow(
            client=mock_jira_client,
            name="Software Development Workflow",
            show_transitions=True,
        )

        # Find Start Progress transition
        start_transition = next(
            t for t in result["transitions"] if t["name"] == "Start Progress"
        )
        assert start_transition["from"] == ["10000"]  # From To Do
        assert start_transition["to"] == "10001"  # To In Progress


class TestGetWorkflowWithRules:
    """Test getting workflow with transition rules (conditions, validators, post-functions)."""

    def test_get_workflow_show_rules(self, mock_jira_client, software_workflow):
        """Test getting workflow with transition rules."""
        from get_workflow import get_workflow

        mock_jira_client.search_workflows.return_value = {
            "values": [software_workflow],
            "total": 1,
        }

        result = get_workflow(
            client=mock_jira_client,
            name="Software Development Workflow",
            show_rules=True,
        )

        # Each transition should have rules section
        assert "transitions" in result
        for transition in result["transitions"]:
            assert "rules" in transition or "conditions" in transition


class TestGetWorkflowShowSchemes:
    """Test showing which schemes use this workflow."""

    def test_get_workflow_show_schemes(
        self, mock_jira_client, software_workflow, schemes_for_workflow
    ):
        """Test showing schemes that use this workflow."""
        from get_workflow import get_workflow

        mock_jira_client.search_workflows.return_value = {
            "values": [software_workflow],
            "total": 1,
        }
        mock_jira_client.get_workflow_schemes_for_workflow.return_value = (
            schemes_for_workflow
        )

        result = get_workflow(
            client=mock_jira_client,
            name="Software Development Workflow",
            show_schemes=True,
        )

        assert "schemes" in result
        assert len(result["schemes"]) == 2
        scheme_names = [s["name"] for s in result["schemes"]]
        assert "Software Development Scheme" in scheme_names

    def test_get_workflow_no_schemes_using(self, mock_jira_client, software_workflow):
        """Test workflow not used by any schemes."""
        from get_workflow import get_workflow

        mock_jira_client.search_workflows.return_value = {
            "values": [software_workflow],
            "total": 1,
        }
        mock_jira_client.get_workflow_schemes_for_workflow.return_value = {
            "values": [],
            "total": 0,
        }

        result = get_workflow(
            client=mock_jira_client,
            name="Software Development Workflow",
            show_schemes=True,
        )

        assert result.get("schemes", []) == []


class TestGetWorkflowOutputFormats:
    """Test output format handling."""

    def test_get_workflow_format_json(self, mock_jira_client, software_workflow):
        """Test JSON output format."""
        import json

        from get_workflow import format_workflow_json, get_workflow

        mock_jira_client.search_workflows.return_value = {
            "values": [software_workflow],
            "total": 1,
        }

        result = get_workflow(
            client=mock_jira_client, name="Software Development Workflow"
        )
        output = format_workflow_json(result)

        # Should be valid JSON
        parsed = json.loads(output)
        assert parsed["name"] == "Software Development Workflow"

    def test_get_workflow_format_table(self, mock_jira_client, software_workflow):
        """Test human-readable output format."""
        from get_workflow import format_workflow_details, get_workflow

        mock_jira_client.search_workflows.return_value = {
            "values": [software_workflow],
            "total": 1,
        }

        result = get_workflow(
            client=mock_jira_client,
            name="Software Development Workflow",
            show_statuses=True,
            show_transitions=True,
        )
        output = format_workflow_details(result)

        assert "Software Development Workflow" in output
        assert "Statuses" in output or "Status" in output
        assert "Transitions" in output or "Transition" in output


class TestGetWorkflowErrorHandling:
    """Test error handling scenarios."""

    def test_get_workflow_missing_parameters(self, mock_jira_client):
        """Test error when no name or entity_id provided."""
        from assistant_skills_lib.error_handler import ValidationError
        from get_workflow import get_workflow

        with pytest.raises(ValidationError) as exc_info:
            get_workflow(client=mock_jira_client)

        assert (
            "name" in str(exc_info.value).lower()
            or "entity" in str(exc_info.value).lower()
        )

    def test_get_workflow_no_permission(self, mock_jira_client):
        """Test error handling when user lacks admin permission."""
        from get_workflow import get_workflow

        from jira_assistant_skills_lib import PermissionError as JiraPermissionError

        mock_jira_client.search_workflows.side_effect = JiraPermissionError(
            "Requires 'Administer Jira' global permission."
        )

        with pytest.raises(JiraPermissionError):
            get_workflow(client=mock_jira_client, name="Any Workflow")
