"""
Live Integration Tests: Component Operations

Tests for component CRUD operations against a real JIRA instance.
"""

import uuid

import pytest


@pytest.mark.integration
@pytest.mark.lifecycle
@pytest.mark.component
class TestComponentCreation:
    """Tests for creating components."""

    def test_create_simple_component(self, jira_client, test_project):
        """Test creating a basic component."""
        component_name = f"Test Component {uuid.uuid4().hex[:8]}"

        component = jira_client.create_component(
            project=test_project["key"], name=component_name
        )

        try:
            assert "id" in component
            assert component["name"] == component_name
        finally:
            jira_client.delete_component(component["id"])

    def test_create_component_with_description(self, jira_client, test_project):
        """Test creating a component with description."""
        component_name = f"Test Component Desc {uuid.uuid4().hex[:8]}"
        description = "This is a test component with description"

        component = jira_client.create_component(
            project=test_project["key"], name=component_name, description=description
        )

        try:
            assert component["description"] == description
        finally:
            jira_client.delete_component(component["id"])

    def test_create_component_with_lead(self, jira_client, test_project, current_user):
        """Test creating a component with a lead."""
        component_name = f"Test Component Lead {uuid.uuid4().hex[:8]}"

        component = jira_client.create_component(
            project=test_project["key"],
            name=component_name,
            lead_account_id=current_user["accountId"],
        )

        try:
            assert (
                component.get("lead", {}).get("accountId") == current_user["accountId"]
            )
        finally:
            jira_client.delete_component(component["id"])

    def test_create_component_with_assignee_type(self, jira_client, test_project):
        """Test creating a component with assignee type."""
        component_name = f"Test Component Assignee {uuid.uuid4().hex[:8]}"

        component = jira_client.create_component(
            project=test_project["key"],
            name=component_name,
            assignee_type="PROJECT_DEFAULT",
        )

        try:
            assert component.get("assigneeType") == "PROJECT_DEFAULT"
        finally:
            jira_client.delete_component(component["id"])


@pytest.mark.integration
@pytest.mark.lifecycle
@pytest.mark.component
class TestComponentRetrieval:
    """Tests for retrieving components."""

    def test_get_project_components(self, jira_client, test_project, test_component):
        """Test getting all components for a project."""
        components = jira_client.get_project_components(test_project["key"])

        assert isinstance(components, list)
        assert len(components) >= 1

        component_names = [c["name"] for c in components]
        assert test_component["name"] in component_names

    def test_get_component_by_id(self, jira_client, test_component):
        """Test getting a specific component by ID."""
        component = jira_client.get_component(test_component["id"])

        assert component["id"] == test_component["id"]
        assert component["name"] == test_component["name"]


@pytest.mark.integration
@pytest.mark.lifecycle
@pytest.mark.component
class TestComponentUpdate:
    """Tests for updating components."""

    def test_update_component_name(self, jira_client, test_component):
        """Test updating a component's name."""
        new_name = f"Updated Component {uuid.uuid4().hex[:8]}"

        updated = jira_client.update_component(test_component["id"], name=new_name)

        assert updated["name"] == new_name

    def test_update_component_description(self, jira_client, test_component):
        """Test updating a component's description."""
        new_description = "Updated component description"

        updated = jira_client.update_component(
            test_component["id"], description=new_description
        )

        assert updated["description"] == new_description

    def test_update_component_lead(self, jira_client, test_component, current_user):
        """Test updating a component's lead."""
        updated = jira_client.update_component(
            test_component["id"], lead_account_id=current_user["accountId"]
        )

        assert updated.get("lead", {}).get("accountId") == current_user["accountId"]

    def test_update_component_assignee_type(self, jira_client, test_component):
        """Test updating a component's assignee type."""
        updated = jira_client.update_component(
            test_component["id"], assignee_type="UNASSIGNED"
        )

        assert updated.get("assigneeType") == "UNASSIGNED"


@pytest.mark.integration
@pytest.mark.lifecycle
@pytest.mark.component
class TestComponentDeletion:
    """Tests for deleting components."""

    def test_delete_component(self, jira_client, test_project):
        """Test deleting a component."""
        component_name = f"Test Delete Component {uuid.uuid4().hex[:8]}"
        component = jira_client.create_component(
            project=test_project["key"], name=component_name
        )

        # Delete the component
        jira_client.delete_component(component["id"])

        # Verify it's gone
        from jira_assistant_skills_lib import NotFoundError

        with pytest.raises(NotFoundError):
            jira_client.get_component(component["id"])


@pytest.mark.integration
@pytest.mark.lifecycle
@pytest.mark.component
class TestComponentWithIssues:
    """Tests for components with associated issues."""

    def test_assign_issue_to_component(self, jira_client, test_issue, test_component):
        """Test assigning an issue to a component."""
        jira_client.update_issue(
            test_issue["key"], fields={"components": [{"id": test_component["id"]}]}
        )

        issue = jira_client.get_issue(test_issue["key"])
        components = issue["fields"].get("components", [])
        component_ids = [c["id"] for c in components]

        assert test_component["id"] in component_ids

    def test_remove_issue_from_component(self, jira_client, test_issue, test_component):
        """Test removing an issue from a component."""
        # First assign
        jira_client.update_issue(
            test_issue["key"], fields={"components": [{"id": test_component["id"]}]}
        )

        # Then remove
        jira_client.update_issue(test_issue["key"], fields={"components": []})

        issue = jira_client.get_issue(test_issue["key"])
        components = issue["fields"].get("components", [])

        assert len(components) == 0

    def test_assign_multiple_components(self, jira_client, test_issue, test_project):
        """Test assigning multiple components to an issue."""
        # Create two components
        c1 = jira_client.create_component(
            project=test_project["key"], name=f"Test C1 {uuid.uuid4().hex[:8]}"
        )
        c2 = jira_client.create_component(
            project=test_project["key"], name=f"Test C2 {uuid.uuid4().hex[:8]}"
        )

        try:
            jira_client.update_issue(
                test_issue["key"],
                fields={"components": [{"id": c1["id"]}, {"id": c2["id"]}]},
            )

            issue = jira_client.get_issue(test_issue["key"])
            components = issue["fields"].get("components", [])

            assert len(components) == 2
        finally:
            jira_client.delete_component(c1["id"])
            jira_client.delete_component(c2["id"])


@pytest.mark.integration
@pytest.mark.lifecycle
@pytest.mark.component
class TestComponentAssigneeTypes:
    """Tests for different component assignee types."""

    def test_assignee_type_component_lead(
        self, jira_client, test_project, current_user
    ):
        """Test COMPONENT_LEAD assignee type."""
        component = jira_client.create_component(
            project=test_project["key"],
            name=f"Test Lead Type {uuid.uuid4().hex[:8]}",
            lead_account_id=current_user["accountId"],
            assignee_type="COMPONENT_LEAD",
        )

        try:
            assert component.get("assigneeType") == "COMPONENT_LEAD"
            assert (
                component.get("lead", {}).get("accountId") == current_user["accountId"]
            )
        finally:
            jira_client.delete_component(component["id"])

    def test_assignee_type_project_lead(self, jira_client, test_project):
        """Test PROJECT_LEAD assignee type."""
        component = jira_client.create_component(
            project=test_project["key"],
            name=f"Test Project Lead Type {uuid.uuid4().hex[:8]}",
            assignee_type="PROJECT_LEAD",
        )

        try:
            assert component.get("assigneeType") == "PROJECT_LEAD"
        finally:
            jira_client.delete_component(component["id"])

    def test_assignee_type_unassigned(self, jira_client, test_project):
        """Test UNASSIGNED assignee type."""
        component = jira_client.create_component(
            project=test_project["key"],
            name=f"Test Unassigned Type {uuid.uuid4().hex[:8]}",
            assignee_type="UNASSIGNED",
        )

        try:
            assert component.get("assigneeType") == "UNASSIGNED"
        finally:
            jira_client.delete_component(component["id"])
