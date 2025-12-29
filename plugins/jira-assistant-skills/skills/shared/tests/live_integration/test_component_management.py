"""
Live Integration Tests: Component Management

Tests for component CRUD operations against a real JIRA instance.
"""

import pytest
import uuid


@pytest.mark.integration
@pytest.mark.shared
class TestComponentCRUD:
    """Tests for component create, read, update, delete operations."""

    def test_create_component(self, jira_client, test_project):
        """Test creating a basic component."""
        component_name = f"Component-{uuid.uuid4().hex[:8]}"

        component = jira_client.create_component(
            project=test_project['key'],
            name=component_name,
            description="Test component"
        )

        assert component['name'] == component_name
        assert component['description'] == "Test component"
        assert 'id' in component

        # Cleanup
        jira_client.delete_component(component['id'])

    def test_create_component_with_lead(self, jira_client, test_project):
        """Test creating a component with a lead."""
        component_name = f"Component-{uuid.uuid4().hex[:8]}"
        current_user_id = jira_client.get_current_user_id()

        component = jira_client.create_component(
            project=test_project['key'],
            name=component_name,
            lead_account_id=current_user_id
        )

        assert component['name'] == component_name
        assert 'lead' in component
        assert component['lead']['accountId'] == current_user_id

        # Cleanup
        jira_client.delete_component(component['id'])

    def test_create_component_with_assignee_type(self, jira_client, test_project):
        """Test creating a component with assignee type."""
        component_name = f"Component-{uuid.uuid4().hex[:8]}"

        component = jira_client.create_component(
            project=test_project['key'],
            name=component_name,
            assignee_type='PROJECT_LEAD'
        )

        assert component['name'] == component_name
        assert component['assigneeType'] == 'PROJECT_LEAD'

        # Cleanup
        jira_client.delete_component(component['id'])

    def test_get_components(self, jira_client, test_project):
        """Test getting all components for a project."""
        # Create a test component
        component_name = f"Component-{uuid.uuid4().hex[:8]}"
        created = jira_client.create_component(
            project=test_project['key'],
            name=component_name
        )

        try:
            # Get all components
            components = jira_client.get_project_components(test_project['key'])

            assert isinstance(components, list)
            assert len(components) >= 1

            # Our component should be in the list
            component_names = [c['name'] for c in components]
            assert component_name in component_names

        finally:
            jira_client.delete_component(created['id'])

    def test_get_component_by_id(self, jira_client, test_project):
        """Test getting a specific component by ID."""
        component_name = f"Component-{uuid.uuid4().hex[:8]}"
        created = jira_client.create_component(
            project=test_project['key'],
            name=component_name,
            description="Specific component test"
        )

        try:
            # Get the component by ID
            component = jira_client.get_component(created['id'])

            assert component['id'] == created['id']
            assert component['name'] == component_name
            assert component['description'] == "Specific component test"

        finally:
            jira_client.delete_component(created['id'])

    def test_update_component_name(self, jira_client, test_project):
        """Test updating a component's name."""
        component_name = f"Component-{uuid.uuid4().hex[:8]}"
        created = jira_client.create_component(
            project=test_project['key'],
            name=component_name
        )

        try:
            new_name = f"Component-{uuid.uuid4().hex[:8]}-updated"

            # Update component
            updated = jira_client.update_component(
                created['id'],
                name=new_name
            )

            assert updated['name'] == new_name

        finally:
            jira_client.delete_component(created['id'])

    def test_update_component_description(self, jira_client, test_project):
        """Test updating a component's description."""
        component_name = f"Component-{uuid.uuid4().hex[:8]}"
        created = jira_client.create_component(
            project=test_project['key'],
            name=component_name
        )

        try:
            new_description = "Updated description"

            # Update component
            updated = jira_client.update_component(
                created['id'],
                description=new_description
            )

            assert updated['description'] == new_description

        finally:
            jira_client.delete_component(created['id'])

    def test_update_component_lead(self, jira_client, test_project):
        """Test updating a component's lead."""
        component_name = f"Component-{uuid.uuid4().hex[:8]}"
        current_user_id = jira_client.get_current_user_id()

        created = jira_client.create_component(
            project=test_project['key'],
            name=component_name
        )

        try:
            # Update component lead
            updated = jira_client.update_component(
                created['id'],
                lead_account_id=current_user_id
            )

            assert 'lead' in updated
            assert updated['lead']['accountId'] == current_user_id

        finally:
            jira_client.delete_component(created['id'])

    def test_delete_component(self, jira_client, test_project):
        """Test deleting a component."""
        component_name = f"Component-{uuid.uuid4().hex[:8]}"
        created = jira_client.create_component(
            project=test_project['key'],
            name=component_name
        )

        # Delete the component
        jira_client.delete_component(created['id'])

        # Verify it's gone
        from jira_assistant_skills_lib import NotFoundError
        with pytest.raises(NotFoundError):
            jira_client.get_component(created['id'])


@pytest.mark.integration
@pytest.mark.shared
class TestComponentIssueManagement:
    """Tests for managing component assignments."""

    def test_assign_issue_to_component(self, jira_client, test_project):
        """Test assigning an issue to a component."""
        # Create component
        component_name = f"Component-{uuid.uuid4().hex[:8]}"
        component = jira_client.create_component(
            project=test_project['key'],
            name=component_name
        )

        # Create issue
        issue = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Component Test {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Bug'}
        })

        try:
            # Assign to component
            jira_client.update_issue(
                issue['key'],
                fields={'components': [{'name': component_name}]}
            )

            # Verify
            updated = jira_client.get_issue(issue['key'])
            components = updated['fields'].get('components', [])
            assert len(components) >= 1
            assert components[0]['name'] == component_name

        finally:
            jira_client.delete_issue(issue['key'])
            jira_client.delete_component(component['id'])

    def test_assign_multiple_components_to_issue(self, jira_client, test_project):
        """Test assigning multiple components to an issue."""
        # Create two components
        component1_name = f"Comp1-{uuid.uuid4().hex[:8]}"
        component2_name = f"Comp2-{uuid.uuid4().hex[:8]}"

        component1 = jira_client.create_component(
            project=test_project['key'],
            name=component1_name
        )
        component2 = jira_client.create_component(
            project=test_project['key'],
            name=component2_name
        )

        # Create issue
        issue = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Multi Component Test {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Task'}
        })

        try:
            # Assign to both components
            jira_client.update_issue(
                issue['key'],
                fields={'components': [
                    {'name': component1_name},
                    {'name': component2_name}
                ]}
            )

            # Verify
            updated = jira_client.get_issue(issue['key'])
            components = updated['fields'].get('components', [])
            assert len(components) == 2
            component_names = {c['name'] for c in components}
            assert component1_name in component_names
            assert component2_name in component_names

        finally:
            jira_client.delete_issue(issue['key'])
            jira_client.delete_component(component1['id'])
            jira_client.delete_component(component2['id'])

    def test_remove_component_from_issue(self, jira_client, test_project):
        """Test removing a component from an issue."""
        component_name = f"Component-{uuid.uuid4().hex[:8]}"
        component = jira_client.create_component(
            project=test_project['key'],
            name=component_name
        )

        # Create issue with component
        issue = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Remove Component Test {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Task'},
            'components': [{'name': component_name}]
        })

        try:
            # Remove component from issue
            jira_client.update_issue(
                issue['key'],
                fields={'components': []}
            )

            # Verify
            updated = jira_client.get_issue(issue['key'])
            components = updated['fields'].get('components', [])
            assert len(components) == 0

        finally:
            jira_client.delete_issue(issue['key'])
            jira_client.delete_component(component['id'])

    def test_delete_component_with_issues(self, jira_client, test_project):
        """Test deleting a component that has issues assigned to it."""
        # Create two components
        component1_name = f"Comp1-{uuid.uuid4().hex[:8]}"
        component2_name = f"Comp2-{uuid.uuid4().hex[:8]}"

        component1 = jira_client.create_component(
            project=test_project['key'],
            name=component1_name
        )
        component2 = jira_client.create_component(
            project=test_project['key'],
            name=component2_name
        )

        # Create issue with first component
        issue = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Delete Component Test {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Story'},
            'components': [{'name': component1_name}]
        })

        try:
            # Delete component1 and move issues to component2
            jira_client.delete_component(
                component1['id'],
                move_issues_to=component2['id']
            )

            # Verify issue now has component2
            updated = jira_client.get_issue(issue['key'])
            components = updated['fields'].get('components', [])
            assert len(components) >= 1
            component_names = [c['name'] for c in components]
            assert component2_name in component_names
            assert component1_name not in component_names

        finally:
            jira_client.delete_issue(issue['key'])
            jira_client.delete_component(component2['id'])


@pytest.mark.integration
@pytest.mark.shared
class TestComponentWorkflow:
    """Tests for complete component lifecycle workflows."""

    def test_component_lifecycle(self, jira_client, test_project):
        """
        Test complete component lifecycle:
        1. Create component
        2. Assign issues
        3. Update component
        4. Delete component
        """
        component_name = f"Lifecycle-{uuid.uuid4().hex[:8]}"

        try:
            # Step 1: Create component
            print(f"\n  Creating component {component_name}...")
            component = jira_client.create_component(
                project=test_project['key'],
                name=component_name,
                description="Lifecycle test component"
            )
            assert 'id' in component

            # Step 2: Create and assign issues
            print("  Creating and assigning issues...")
            issues = []
            for i in range(2):
                issue = jira_client.create_issue({
                    'project': {'key': test_project['key']},
                    'summary': f'Component Issue {i} {uuid.uuid4().hex[:8]}',
                    'issuetype': {'name': 'Task'},
                    'components': [{'name': component_name}]
                })
                issues.append(issue)

            # Step 3: Update component
            print("  Updating component...")
            updated = jira_client.update_component(
                component['id'],
                description="Updated lifecycle test component"
            )
            assert updated['description'] == "Updated lifecycle test component"

            # Step 4: Clean up issues then component
            print("  Cleaning up...")
            for issue in issues:
                jira_client.delete_issue(issue['key'])
            jira_client.delete_component(component['id'])

            print("  Complete component lifecycle test passed!")

        except Exception as e:
            # Emergency cleanup
            try:
                if 'issues' in locals():
                    for issue in issues:
                        jira_client.delete_issue(issue['key'])
            except Exception:
                pass
            try:
                if 'component' in locals():
                    jira_client.delete_component(component['id'])
            except Exception:
                pass
            raise e
