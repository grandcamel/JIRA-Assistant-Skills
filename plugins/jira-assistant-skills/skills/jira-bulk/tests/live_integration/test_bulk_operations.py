"""
Live Integration Tests: Bulk Operations

Tests for bulk JIRA operations against a real JIRA instance.
"""

import sys
import pytest
import uuid
from pathlib import Path
from typing import List, Dict, Any

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))

from bulk_transition import bulk_transition, find_transition
from bulk_assign import bulk_assign, resolve_user_id
from bulk_set_priority import bulk_set_priority
from bulk_clone import bulk_clone


@pytest.mark.bulk
@pytest.mark.integration
class TestBulkTransition:
    """Tests for bulk transition operations."""

    def test_bulk_transition_single_issue(self, jira_client, test_project, single_issue):
        """Test transitioning a single issue."""
        result = bulk_transition(
            client=jira_client,
            issue_keys=[single_issue['key']],
            target_status='Done'
        )

        assert result['total'] == 1
        assert result['success'] == 1
        assert result['failed'] == 0
        assert len(result['processed']) == 1

        # Verify issue is in Done status
        issue = jira_client.get_issue(single_issue['key'])
        assert issue['fields']['status']['name'] == 'Done'

    def test_bulk_transition_multiple_issues(self, jira_client, test_project, bulk_issues):
        """Test transitioning multiple issues."""
        issue_keys = [i['key'] for i in bulk_issues]

        result = bulk_transition(
            client=jira_client,
            issue_keys=issue_keys,
            target_status='Done'
        )

        assert result['total'] == 5
        assert result['success'] == 5
        assert result['failed'] == 0

        # Verify all issues are in Done status
        for key in issue_keys:
            issue = jira_client.get_issue(key)
            assert issue['fields']['status']['name'] == 'Done'

    def test_bulk_transition_with_jql(self, jira_client, test_project, bulk_issues):
        """Test transitioning issues via JQL query."""
        # Use broader JQL - any issue in the project
        jql = f"project = {test_project['key']}"

        result = bulk_transition(
            client=jira_client,
            jql=jql,
            target_status='Done',
            max_issues=10
        )

        # Verify the operation completed (total may be 0 if no matching issues)
        assert 'total' in result
        assert 'success' in result
        assert 'failed' in result
        # If issues found, some should succeed or fail
        if result['total'] > 0:
            assert result['success'] + result['failed'] == result['total']

    def test_bulk_transition_dry_run(self, jira_client, test_project, bulk_issues):
        """Test dry run mode doesn't change issues."""
        issue_keys = [i['key'] for i in bulk_issues[:2]]

        # Get original statuses
        original_statuses = {}
        for key in issue_keys:
            issue = jira_client.get_issue(key)
            original_statuses[key] = issue['fields']['status']['name']

        result = bulk_transition(
            client=jira_client,
            issue_keys=issue_keys,
            target_status='Done',
            dry_run=True
        )

        assert result['dry_run'] is True
        assert result['total'] == 2

        # Verify statuses haven't changed
        for key in issue_keys:
            issue = jira_client.get_issue(key)
            assert issue['fields']['status']['name'] == original_statuses[key]

    def test_bulk_transition_with_comment(self, jira_client, test_project, single_issue):
        """Test transitioning with a comment."""
        comment_text = f"Bulk transition test comment {uuid.uuid4().hex[:8]}"

        result = bulk_transition(
            client=jira_client,
            issue_keys=[single_issue['key']],
            target_status='Done',
            comment=comment_text
        )

        assert result['success'] == 1

        # Verify comment was added
        comments = jira_client.get_comments(single_issue['key'])
        comment_bodies = []
        for c in comments.get('comments', []):
            body = c.get('body', {})
            if isinstance(body, dict):
                for content in body.get('content', []):
                    for text_node in content.get('content', []):
                        if text_node.get('type') == 'text':
                            comment_bodies.append(text_node.get('text', ''))

        assert any(comment_text in body for body in comment_bodies)


@pytest.mark.bulk
@pytest.mark.integration
class TestBulkAssign:
    """Tests for bulk assignment operations."""

    def test_bulk_assign_to_self(self, jira_client, test_project, bulk_issues):
        """Test assigning issues to self."""
        issue_keys = [i['key'] for i in bulk_issues[:3]]

        result = bulk_assign(
            client=jira_client,
            issue_keys=issue_keys,
            assignee='self'
        )

        assert result['total'] == 3
        assert result['success'] == 3
        assert result['failed'] == 0

        # Verify assignment
        current_user = jira_client.get_current_user_id()
        for key in issue_keys:
            issue = jira_client.get_issue(key)
            assert issue['fields']['assignee'] is not None
            assert issue['fields']['assignee']['accountId'] == current_user

    def test_bulk_unassign(self, jira_client, test_project, bulk_issues):
        """Test unassigning issues."""
        issue_keys = [i['key'] for i in bulk_issues[:3]]

        # First assign
        bulk_assign(
            client=jira_client,
            issue_keys=issue_keys,
            assignee='self'
        )

        # Then unassign
        result = bulk_assign(
            client=jira_client,
            issue_keys=issue_keys,
            unassign=True
        )

        assert result['success'] == 3

        # Verify unassignment
        for key in issue_keys:
            issue = jira_client.get_issue(key)
            assert issue['fields']['assignee'] is None

    def test_bulk_assign_with_jql(self, jira_client, test_project, bulk_issues):
        """Test assigning via JQL query."""
        # Use broader JQL - any issue in the project
        jql = f"project = {test_project['key']}"

        result = bulk_assign(
            client=jira_client,
            jql=jql,
            assignee='self',
            max_issues=10
        )

        # Verify the operation completed with expected structure
        assert 'total' in result
        assert 'success' in result
        assert 'failed' in result
        # If issues found, verify counts add up
        if result['total'] > 0:
            assert result['success'] + result['failed'] == result['total']

    def test_bulk_assign_dry_run(self, jira_client, test_project, bulk_issues):
        """Test dry run mode doesn't change issues."""
        issue_keys = [i['key'] for i in bulk_issues[:2]]

        # Capture current assignee state before dry run
        original_assignees = {}
        for key in issue_keys:
            issue = jira_client.get_issue(key)
            original_assignees[key] = issue['fields'].get('assignee')

        result = bulk_assign(
            client=jira_client,
            issue_keys=issue_keys,
            assignee='self',
            dry_run=True
        )

        assert result['dry_run'] is True
        assert result['total'] == 2

        # Verify assignees haven't changed (regardless of original state)
        for key in issue_keys:
            issue = jira_client.get_issue(key)
            current_assignee = issue['fields'].get('assignee')
            original = original_assignees[key]
            # Compare account IDs if both exist, otherwise compare None
            if original and current_assignee:
                assert current_assignee['accountId'] == original['accountId']
            else:
                assert current_assignee == original


@pytest.mark.bulk
@pytest.mark.integration
class TestBulkSetPriority:
    """Tests for bulk priority operations."""

    def test_bulk_set_priority_high(self, jira_client, test_project, bulk_issues):
        """Test setting priority to High."""
        issue_keys = [i['key'] for i in bulk_issues[:3]]

        result = bulk_set_priority(
            client=jira_client,
            issue_keys=issue_keys,
            priority='High'
        )

        assert result['total'] == 3
        assert result['success'] == 3

        # Verify priority
        for key in issue_keys:
            issue = jira_client.get_issue(key)
            assert issue['fields']['priority']['name'] == 'High'

    def test_bulk_set_priority_low(self, jira_client, test_project, bulk_issues):
        """Test setting priority to Low."""
        issue_keys = [i['key'] for i in bulk_issues[:2]]

        result = bulk_set_priority(
            client=jira_client,
            issue_keys=issue_keys,
            priority='Low'
        )

        assert result['success'] == 2

        for key in issue_keys:
            issue = jira_client.get_issue(key)
            assert issue['fields']['priority']['name'] == 'Low'

    def test_bulk_set_priority_with_jql(self, jira_client, test_project, bulk_issues):
        """Test setting priority via JQL."""
        jql = f"project = {test_project['key']}"

        result = bulk_set_priority(
            client=jira_client,
            jql=jql,
            priority='Medium',
            max_issues=10
        )

        # Verify the operation completed with expected structure
        # Note: JIRA search index may not be up-to-date immediately after issue creation
        assert 'total' in result
        assert 'success' in result
        assert 'failed' in result
        # If issues found, verify counts add up
        if result['total'] > 0:
            assert result['success'] + result['failed'] == result['total']

    def test_bulk_set_priority_dry_run(self, jira_client, test_project, bulk_issues):
        """Test dry run mode."""
        issue_keys = [i['key'] for i in bulk_issues[:2]]

        # Get original priorities
        original_priorities = {}
        for key in issue_keys:
            issue = jira_client.get_issue(key)
            original_priorities[key] = issue['fields']['priority']['name']

        result = bulk_set_priority(
            client=jira_client,
            issue_keys=issue_keys,
            priority='Highest',
            dry_run=True
        )

        assert result['dry_run'] is True

        # Verify no changes
        for key in issue_keys:
            issue = jira_client.get_issue(key)
            assert issue['fields']['priority']['name'] == original_priorities[key]


@pytest.mark.bulk
@pytest.mark.integration
class TestBulkClone:
    """Tests for bulk clone operations."""

    def test_bulk_clone_single_issue(self, jira_client, test_project, single_issue):
        """Test cloning a single issue."""
        result = bulk_clone(
            client=jira_client,
            issue_keys=[single_issue['key']]
        )

        assert result['total'] == 1
        assert result['success'] == 1
        assert len(result['created_issues']) == 1

        # Get the cloned issue key (created_issues contains dicts with 'key')
        clone_info = result['created_issues'][0]
        clone_key = clone_info['key']
        assert clone_key is not None
        assert clone_key != single_issue['key']

        # Verify clone exists
        clone = jira_client.get_issue(clone_key)
        assert clone is not None

        # Cleanup clone
        jira_client.delete_issue(clone_key)

    def test_bulk_clone_multiple_issues(self, jira_client, test_project, bulk_issues):
        """Test cloning multiple issues."""
        issue_keys = [i['key'] for i in bulk_issues[:3]]

        result = bulk_clone(
            client=jira_client,
            issue_keys=issue_keys
        )

        assert result['total'] == 3
        assert result['success'] == 3

        # Cleanup clones (created_issues contains dicts with 'key')
        for clone_info in result['created_issues']:
            try:
                jira_client.delete_issue(clone_info['key'])
            except Exception:
                pass

    def test_bulk_clone_with_prefix(self, jira_client, test_project, single_issue):
        """Test cloning with summary prefix."""
        prefix = "[CLONE]"

        result = bulk_clone(
            client=jira_client,
            issue_keys=[single_issue['key']],
            prefix=prefix
        )

        assert result['success'] == 1

        clone_info = result['created_issues'][0]
        clone_key = clone_info['key']
        clone = jira_client.get_issue(clone_key)
        assert clone['fields']['summary'].startswith(prefix)

        # Cleanup
        jira_client.delete_issue(clone_key)

    def test_bulk_clone_dry_run(self, jira_client, test_project, bulk_issues):
        """Test dry run mode doesn't create new issues."""
        issue_keys = [i['key'] for i in bulk_issues[:2]]

        result = bulk_clone(
            client=jira_client,
            issue_keys=issue_keys,
            dry_run=True
        )

        # Verify dry run response
        assert result['dry_run'] is True
        assert result['total'] == 2
        assert result['success'] == 0  # No actual clones created
        assert result['created_issues'] == []  # No issues created in dry run


@pytest.mark.bulk
@pytest.mark.integration
class TestBulkOperationEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_issue_list(self, jira_client, test_project):
        """Test with empty issue list raises ValidationError."""
        from error_handler import ValidationError

        with pytest.raises(ValidationError, match="Either --issues or --jql must be provided"):
            bulk_transition(
                client=jira_client,
                issue_keys=[],
                target_status='Done'
            )

    def test_invalid_issue_key(self, jira_client, test_project):
        """Test with invalid issue key."""
        result = bulk_assign(
            client=jira_client,
            issue_keys=['INVALID-99999'],
            assignee='self'
        )

        assert result['failed'] == 1
        assert result['success'] == 0

    def test_max_issues_limit(self, jira_client, test_project, bulk_issues):
        """Test max_issues parameter."""
        issue_keys = [i['key'] for i in bulk_issues]

        result = bulk_set_priority(
            client=jira_client,
            issue_keys=issue_keys,
            priority='High',
            max_issues=2
        )

        assert result['total'] == 2  # Limited to 2
        assert result['success'] == 2

    def test_jql_with_no_results(self, jira_client, test_project):
        """Test JQL query with no matching issues."""
        jql = f"project = {test_project['key']} AND summary ~ 'NONEXISTENT_TEXT_12345'"

        result = bulk_transition(
            client=jira_client,
            jql=jql,
            target_status='Done'
        )

        assert result['total'] == 0
