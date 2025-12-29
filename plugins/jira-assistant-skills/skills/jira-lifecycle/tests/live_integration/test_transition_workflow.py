"""
Live Integration Tests: Transition Workflow

Tests for issue transitions and workflow operations against a real JIRA instance.
"""

import pytest
import uuid
import sys
from pathlib import Path

# Add scripts to path for testing
skills_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(skills_dir / 'scripts'))

from transition_issue import find_transition_by_name


@pytest.mark.integration
@pytest.mark.lifecycle
@pytest.mark.transition
class TestGetTransitions:
    """Tests for getting available transitions."""

    def test_get_available_transitions(self, jira_client, test_issue):
        """Test getting available transitions for an issue."""
        transitions = jira_client.get_transitions(test_issue['key'])

        assert isinstance(transitions, list)
        assert len(transitions) > 0

    def test_transition_structure(self, jira_client, test_issue):
        """Test that transitions have required fields."""
        transitions = jira_client.get_transitions(test_issue['key'])

        for t in transitions:
            assert 'id' in t
            assert 'name' in t
            assert 'to' in t

    def test_transition_to_status(self, jira_client, test_issue):
        """Test that transitions have target status info."""
        transitions = jira_client.get_transitions(test_issue['key'])

        for t in transitions:
            to_status = t.get('to', {})
            assert 'name' in to_status or 'statusCategory' in to_status


@pytest.mark.integration
@pytest.mark.lifecycle
@pytest.mark.transition
class TestTransitionIssue:
    """Tests for transitioning issues."""

    def test_transition_to_in_progress(self, jira_client, test_issue):
        """Test transitioning issue to In Progress."""
        transitions = jira_client.get_transitions(test_issue['key'])

        # Find In Progress transition
        in_progress = None
        for t in transitions:
            if 'progress' in t['name'].lower():
                in_progress = t
                break

        if not in_progress:
            pytest.skip("No 'In Progress' transition available")

        jira_client.transition_issue(test_issue['key'], in_progress['id'])

        # Verify status changed
        issue = jira_client.get_issue(test_issue['key'])
        status = issue['fields']['status']['name']
        assert 'progress' in status.lower()

    def test_transition_to_done(self, jira_client, test_issue):
        """Test transitioning issue to Done."""
        transitions = jira_client.get_transitions(test_issue['key'])

        # Find Done transition
        done = None
        for t in transitions:
            if 'done' in t['name'].lower():
                done = t
                break

        if not done:
            pytest.skip("No 'Done' transition available")

        jira_client.transition_issue(test_issue['key'], done['id'])

        # Verify status changed
        issue = jira_client.get_issue(test_issue['key'])
        status = issue['fields']['status']['name']
        assert 'done' in status.lower()

    def test_transition_with_fields(self, jira_client, test_issue):
        """Test transitioning with additional fields."""
        transitions = jira_client.get_transitions(test_issue['key'])

        if not transitions:
            pytest.skip("No transitions available")

        # Use first available transition
        transition = transitions[0]

        # Transition with fields (may or may not be required)
        try:
            jira_client.transition_issue(
                test_issue['key'],
                transition['id'],
                fields={}  # Empty fields - actual fields depend on workflow
            )
        except Exception as e:
            # Some transitions require specific fields
            if 'required' in str(e).lower():
                pytest.skip(f"Transition requires specific fields: {e}")
            raise


@pytest.mark.integration
@pytest.mark.lifecycle
@pytest.mark.transition
class TestFindTransitionByName:
    """Tests for the find_transition_by_name helper."""

    def test_find_exact_match(self, jira_client, test_issue):
        """Test finding transition by exact name."""
        transitions = jira_client.get_transitions(test_issue['key'])

        if not transitions:
            pytest.skip("No transitions available")

        # Use exact name of first transition
        exact_name = transitions[0]['name']
        found = find_transition_by_name(transitions, exact_name)

        assert found['name'] == exact_name

    def test_find_case_insensitive(self, jira_client, test_issue):
        """Test finding transition by case-insensitive name."""
        transitions = jira_client.get_transitions(test_issue['key'])

        if not transitions:
            pytest.skip("No transitions available")

        # Use lowercase version
        name = transitions[0]['name']
        found = find_transition_by_name(transitions, name.lower())

        assert found['name'].lower() == name.lower()

    def test_find_partial_match(self, jira_client, test_issue):
        """Test finding transition by partial name."""
        transitions = jira_client.get_transitions(test_issue['key'])

        if not transitions:
            pytest.skip("No transitions available")

        # Look for common partial names
        for partial in ['progress', 'done', 'to do']:
            matching = [t for t in transitions if partial in t['name'].lower()]
            if matching:
                found = find_transition_by_name(transitions, partial)
                assert found is not None
                break

    def test_find_not_found_raises(self, jira_client, test_issue):
        """Test that non-existent transition raises error."""
        from error_handler import ValidationError

        transitions = jira_client.get_transitions(test_issue['key'])

        with pytest.raises(ValidationError):
            find_transition_by_name(transitions, 'NONEXISTENT_TRANSITION_12345')


@pytest.mark.integration
@pytest.mark.lifecycle
@pytest.mark.transition
class TestTransitionWorkflow:
    """Tests for complete workflow transitions."""

    def test_full_workflow_cycle(self, jira_client, test_issue):
        """Test moving issue through full workflow."""
        # Start in To Do/Backlog

        # Try to move to In Progress
        transitions = jira_client.get_transitions(test_issue['key'])
        in_progress = None
        for t in transitions:
            if 'progress' in t['name'].lower():
                in_progress = t
                break

        if in_progress:
            jira_client.transition_issue(test_issue['key'], in_progress['id'])

            # Verify In Progress
            issue = jira_client.get_issue(test_issue['key'])
            assert 'progress' in issue['fields']['status']['name'].lower()

        # Move to Done
        transitions = jira_client.get_transitions(test_issue['key'])
        done = None
        for t in transitions:
            if 'done' in t['name'].lower():
                done = t
                break

        if done:
            jira_client.transition_issue(test_issue['key'], done['id'])

            # Verify Done
            issue = jira_client.get_issue(test_issue['key'])
            assert 'done' in issue['fields']['status']['name'].lower()

    def test_transitions_change_by_status(self, jira_client, test_issue):
        """Test that transitions are available and work correctly."""
        # Get initial status
        initial_issue = jira_client.get_issue(test_issue['key'])
        initial_status = initial_issue['fields']['status']['name']

        # Get initial transitions
        initial_transitions = jira_client.get_transitions(test_issue['key'])

        if not initial_transitions:
            pytest.skip("No transitions available")

        # Find a transition that leads to a different status
        target_transition = None
        for t in initial_transitions:
            target_status = t.get('to', {}).get('name', '')
            if target_status and target_status != initial_status:
                target_transition = t
                break

        if not target_transition:
            # All transitions lead back to current status - just verify transition works
            jira_client.transition_issue(test_issue['key'], initial_transitions[0]['id'])
            # Verify issue still exists and transition completed without error
            issue = jira_client.get_issue(test_issue['key'])
            assert issue is not None
            return

        # Transition to a different status
        jira_client.transition_issue(test_issue['key'], target_transition['id'])

        # Verify status actually changed
        issue = jira_client.get_issue(test_issue['key'])
        new_status = issue['fields']['status']['name']
        assert new_status == target_transition['to']['name'], \
            f"Expected status '{target_transition['to']['name']}', got '{new_status}'"


@pytest.mark.integration
@pytest.mark.lifecycle
@pytest.mark.transition
class TestAssignment:
    """Tests for issue assignment."""

    def test_assign_to_current_user(self, jira_client, test_issue, current_user):
        """Test assigning issue to current user."""
        jira_client.update_issue(
            test_issue['key'],
            fields={'assignee': {'accountId': current_user['accountId']}}
        )

        issue = jira_client.get_issue(test_issue['key'])
        assert issue['fields']['assignee']['accountId'] == current_user['accountId']

    def test_unassign_issue(self, jira_client, test_issue, current_user):
        """Test unassigning an issue."""
        # First assign
        jira_client.update_issue(
            test_issue['key'],
            fields={'assignee': {'accountId': current_user['accountId']}}
        )

        # Then unassign
        jira_client.update_issue(
            test_issue['key'],
            fields={'assignee': None}
        )

        issue = jira_client.get_issue(test_issue['key'])
        assert issue['fields']['assignee'] is None

    def test_reassign_issue(self, jira_client, test_issue, current_user):
        """Test reassigning an issue."""
        # Assign to current user
        jira_client.update_issue(
            test_issue['key'],
            fields={'assignee': {'accountId': current_user['accountId']}}
        )

        # Reassign to same user (just verifying reassign works)
        jira_client.update_issue(
            test_issue['key'],
            fields={'assignee': {'accountId': current_user['accountId']}}
        )

        issue = jira_client.get_issue(test_issue['key'])
        assert issue['fields']['assignee']['accountId'] == current_user['accountId']
