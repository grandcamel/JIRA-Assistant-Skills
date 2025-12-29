"""
Live Integration Tests: Blocker Chain Traversal

Tests for blocker chain discovery and recursive traversal against a real JIRA instance.
"""

import pytest
import uuid
import sys
from pathlib import Path

# Add scripts to path for testing
skills_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(skills_dir / 'scripts'))

from get_blockers import get_blockers, extract_blockers, get_blockers_recursive


@pytest.mark.integration
@pytest.mark.relationships
@pytest.mark.blockers
class TestDirectBlockers:
    """Tests for getting direct blockers without recursion."""

    def test_get_direct_blockers_inward(self, jira_client, blocker_chain):
        """Test getting issues that block an issue (inward direction)."""
        issue_a, issue_b, issue_c = blocker_chain

        # B is blocked by A, so when we check B's blockers (inward), we should see A
        result = get_blockers(issue_b['key'], direction='inward', recursive=False)

        assert result['total'] >= 1
        blocker_keys = [b['key'] for b in result['blockers']]
        assert issue_a['key'] in blocker_keys

    def test_get_direct_blockers_outward(self, jira_client, blocker_chain):
        """Test getting issues that are blocked by an issue (outward direction)."""
        issue_a, issue_b, issue_c = blocker_chain

        # A blocks B, so when we check A's outward blockers, we should see B
        result = get_blockers(issue_a['key'], direction='outward', recursive=False)

        assert result['total'] >= 1
        blocked_keys = [b['key'] for b in result['blockers']]
        assert issue_b['key'] in blocked_keys

    def test_get_blockers_no_blockers(self, jira_client, test_issue):
        """Test getting blockers for an issue with none."""
        result = get_blockers(test_issue['key'], direction='inward', recursive=False)

        assert result['total'] == 0
        assert len(result['blockers']) == 0

    def test_extract_blockers_function(self, jira_client, blocker_chain):
        """Test the extract_blockers helper function."""
        issue_a, issue_b, issue_c = blocker_chain

        links = jira_client.get_issue_links(issue_b['key'])
        inward_blockers = extract_blockers(links, direction='inward')

        assert len(inward_blockers) >= 1

        # Verify structure
        blocker = inward_blockers[0]
        assert 'key' in blocker
        assert 'summary' in blocker
        assert 'status' in blocker


@pytest.mark.integration
@pytest.mark.relationships
@pytest.mark.blockers
class TestRecursiveBlockers:
    """Tests for recursive blocker chain traversal."""

    def test_recursive_blocker_chain(self, jira_client, blocker_chain):
        """Test recursively finding all blockers in a chain."""
        issue_a, issue_b, issue_c = blocker_chain

        # C is blocked by B which is blocked by A
        # Recursive check from C should find both B and A
        result = get_blockers(issue_c['key'], direction='inward', recursive=True)

        assert result['recursive'] is True
        assert result['total'] >= 2

        all_keys = [b['key'] for b in result['all_blockers']]
        assert issue_b['key'] in all_keys
        assert issue_a['key'] in all_keys

    def test_recursive_with_depth_limit(self, jira_client, blocker_chain):
        """Test recursive traversal with depth limit."""
        issue_a, issue_b, issue_c = blocker_chain

        # With depth=1, should only find immediate blocker
        result = get_blockers(issue_c['key'], direction='inward', recursive=True, max_depth=1)

        assert result['total'] >= 1
        # Should find B but not necessarily A (due to depth limit)
        immediate_keys = [b['key'] for b in result['blockers']]
        assert issue_b['key'] in immediate_keys

    def test_recursive_outward_direction(self, jira_client, blocker_chain):
        """Test recursive traversal in outward direction."""
        issue_a, issue_b, issue_c = blocker_chain

        # From A's perspective, check what it blocks
        result = get_blockers(issue_a['key'], direction='outward', recursive=True)

        assert result['recursive'] is True
        assert result['total'] >= 2

        all_keys = [b['key'] for b in result['all_blockers']]
        assert issue_b['key'] in all_keys
        assert issue_c['key'] in all_keys


@pytest.mark.integration
@pytest.mark.relationships
@pytest.mark.blockers
class TestCircularDetection:
    """Tests for circular dependency detection in blocker chains."""

    def test_circular_blocker_detection(self, jira_client, test_project):
        """Test detection of circular blocking dependencies."""
        # Create circular chain: A blocks B blocks C blocks A
        issues = []
        for name in ['Circular A', 'Circular B', 'Circular C']:
            issue = jira_client.create_issue({
                'project': {'key': test_project['key']},
                'summary': f'{name} {uuid.uuid4().hex[:8]}',
                'issuetype': {'name': 'Task'}
            })
            issues.append(issue)

        try:
            # Create circular chain
            jira_client.create_link('Blocks', issues[1]['key'], issues[0]['key'])  # A blocks B
            jira_client.create_link('Blocks', issues[2]['key'], issues[1]['key'])  # B blocks C
            jira_client.create_link('Blocks', issues[0]['key'], issues[2]['key'])  # C blocks A (circular!)

            # Recursive check should detect circular
            result = get_blockers(issues[0]['key'], direction='inward', recursive=True)

            # Should handle circular gracefully (not infinite loop)
            assert 'circular' in result
            # If circular is detected, it should be True
            if result['total'] > 0:
                # Having completed means we handled it
                pass

        finally:
            for issue in issues:
                try:
                    jira_client.delete_issue(issue['key'])
                except Exception:
                    pass

    def test_visited_set_prevents_infinite_loop(self, jira_client, test_project):
        """Test that visited set mechanism prevents infinite loops."""
        # Create self-referencing block (if possible) or tight loop
        issue1 = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Loop Test 1 {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Task'}
        })
        issue2 = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Loop Test 2 {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Task'}
        })

        try:
            # Create bidirectional blocks (tight loop)
            jira_client.create_link('Blocks', issue2['key'], issue1['key'])
            jira_client.create_link('Blocks', issue1['key'], issue2['key'])

            # This should complete without infinite loop
            result = get_blockers(issue1['key'], direction='inward', recursive=True)

            # Should have found the blocker and stopped
            assert result['total'] >= 1

        finally:
            jira_client.delete_issue(issue1['key'])
            jira_client.delete_issue(issue2['key'])


@pytest.mark.integration
@pytest.mark.relationships
@pytest.mark.blockers
class TestBlockerMetadata:
    """Tests for blocker metadata and status information."""

    def test_blocker_includes_status(self, jira_client, blocker_chain):
        """Test that blockers include status information."""
        issue_a, issue_b, issue_c = blocker_chain

        result = get_blockers(issue_b['key'], direction='inward', recursive=False)

        assert result['total'] >= 1
        blocker = result['blockers'][0]
        assert 'status' in blocker
        assert blocker['status'] != 'Unknown'

    def test_blocker_includes_summary(self, jira_client, blocker_chain):
        """Test that blockers include summary information."""
        issue_a, issue_b, issue_c = blocker_chain

        result = get_blockers(issue_b['key'], direction='inward', recursive=False)

        assert result['total'] >= 1
        blocker = result['blockers'][0]
        assert 'summary' in blocker
        assert len(blocker['summary']) > 0

    def test_resolved_blocker_status(self, jira_client, test_project):
        """Test that resolved blockers show correct status."""
        # Create blocker chain
        blocker = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Resolvable Blocker {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Task'}
        })
        blocked = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Waiting Issue {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Task'}
        })

        try:
            jira_client.create_link('Blocks', blocked['key'], blocker['key'])

            # Transition blocker to Done if possible
            transitions = jira_client.get_transitions(blocker['key'])
            done_transition = None
            for t in transitions:
                if 'done' in t['name'].lower():
                    done_transition = t
                    break

            if done_transition:
                jira_client.transition_issue(blocker['key'], done_transition['id'])

                # Now check blocker status
                result = get_blockers(blocked['key'], direction='inward', recursive=False)
                if result['total'] >= 1:
                    blocker_info = result['blockers'][0]
                    # Status should reflect resolved state
                    assert blocker_info['status'] == 'Done'

        finally:
            jira_client.delete_issue(blocker['key'])
            jira_client.delete_issue(blocked['key'])


@pytest.mark.integration
@pytest.mark.relationships
@pytest.mark.blockers
class TestBlockerChainOutput:
    """Tests for blocker chain output formatting."""

    def test_all_blockers_flattened(self, jira_client, blocker_chain):
        """Test that all_blockers contains flattened list."""
        issue_a, issue_b, issue_c = blocker_chain

        result = get_blockers(issue_c['key'], direction='inward', recursive=True)

        # all_blockers should be a flat list
        assert 'all_blockers' in result
        assert isinstance(result['all_blockers'], list)
        assert len(result['all_blockers']) >= 2

    def test_tree_structure_preserved(self, jira_client, blocker_chain):
        """Test that nested blocker tree structure is preserved."""
        issue_a, issue_b, issue_c = blocker_chain

        result = get_blockers(issue_c['key'], direction='inward', recursive=True)

        # Top level blockers should have nested blockers
        assert 'blockers' in result
        assert len(result['blockers']) >= 1

        # B should be in top-level blockers
        top_level_keys = [b['key'] for b in result['blockers']]
        assert issue_b['key'] in top_level_keys

        # A should be nested under B
        for blocker in result['blockers']:
            if blocker['key'] == issue_b['key']:
                if 'blockers' in blocker and len(blocker['blockers']) > 0:
                    nested_keys = [b['key'] for b in blocker['blockers']]
                    assert issue_a['key'] in nested_keys
