"""
Live Integration Tests for jira-issue CRUD operations.

Tests the full lifecycle of issue operations against a real JIRA instance:
- create_issue.py: Create issues with various options
- get_issue.py: Retrieve issues and verify fields
- update_issue.py: Update issue fields
- delete_issue.py: Delete issues

Usage:
    pytest plugins/jira-assistant-skills/skills/jira-issue/tests/live_integration/ --profile development -v
"""

import pytest
import uuid
import sys
from pathlib import Path

# Add scripts to path
_this_dir = Path(__file__).parent
_scripts_path = _this_dir.parent.parent / 'scripts'
sys.path.insert(0, str(_scripts_path))

from create_issue import create_issue
from get_issue import get_issue
from update_issue import update_issue
from delete_issue import delete_issue


@pytest.mark.integration
@pytest.mark.issue
class TestCreateIssue:
    """Tests for create_issue.py functionality."""

    def test_create_issue_minimal(self, jira_client, test_project, jira_profile):
        """Test creating an issue with only required fields."""
        summary = f"Test Minimal Issue {uuid.uuid4().hex[:8]}"

        result = create_issue(
            project=test_project['key'],
            issue_type='Task',
            summary=summary,
            profile=jira_profile,
            no_defaults=True
        )

        assert 'key' in result
        assert result['key'].startswith(test_project['key'])

        # Verify issue was created
        issue = jira_client.get_issue(result['key'])
        assert issue['fields']['summary'] == summary
        assert issue['fields']['issuetype']['name'] == 'Task'

        # Cleanup
        jira_client.delete_issue(result['key'])

    def test_create_issue_with_description(self, jira_client, test_project, jira_profile):
        """Test creating an issue with a description."""
        summary = f"Test Description Issue {uuid.uuid4().hex[:8]}"
        description = "This is a test description for the issue."

        result = create_issue(
            project=test_project['key'],
            issue_type='Task',
            summary=summary,
            description=description,
            profile=jira_profile,
            no_defaults=True
        )

        assert 'key' in result

        # Verify description was set (as ADF)
        issue = jira_client.get_issue(result['key'])
        desc_content = issue['fields'].get('description', {})
        assert desc_content is not None
        # ADF format should have content
        if isinstance(desc_content, dict):
            assert 'content' in desc_content

        # Cleanup
        jira_client.delete_issue(result['key'])

    def test_create_issue_with_priority(self, jira_client, test_project, jira_profile):
        """Test creating an issue with a specific priority."""
        summary = f"Test Priority Issue {uuid.uuid4().hex[:8]}"

        result = create_issue(
            project=test_project['key'],
            issue_type='Bug',
            summary=summary,
            priority='High',
            profile=jira_profile,
            no_defaults=True
        )

        assert 'key' in result

        # Verify priority was set
        issue = jira_client.get_issue(result['key'])
        assert issue['fields']['priority']['name'] == 'High'

        # Cleanup
        jira_client.delete_issue(result['key'])

    def test_create_issue_with_labels(self, jira_client, test_project, jira_profile):
        """Test creating an issue with labels."""
        summary = f"Test Labels Issue {uuid.uuid4().hex[:8]}"
        labels = ['test-label', 'integration']

        result = create_issue(
            project=test_project['key'],
            issue_type='Task',
            summary=summary,
            labels=labels,
            profile=jira_profile,
            no_defaults=True
        )

        assert 'key' in result

        # Verify labels were set
        issue = jira_client.get_issue(result['key'])
        assert set(issue['fields']['labels']) == set(labels)

        # Cleanup
        jira_client.delete_issue(result['key'])

    def test_create_issue_with_estimate(self, jira_client, test_project, jira_profile):
        """Test creating an issue with a time estimate."""
        summary = f"Test Estimate Issue {uuid.uuid4().hex[:8]}"

        result = create_issue(
            project=test_project['key'],
            issue_type='Task',
            summary=summary,
            estimate='2d',
            profile=jira_profile,
            no_defaults=True
        )

        assert 'key' in result

        # Verify estimate was set
        issue = jira_client.get_issue(result['key'], fields=['timetracking'])
        tt = issue['fields'].get('timetracking', {})
        # Time tracking may not be enabled on all projects
        if tt:
            assert tt.get('originalEstimate') == '2d' or tt.get('originalEstimateSeconds') == 57600

        # Cleanup
        jira_client.delete_issue(result['key'])

    def test_create_issue_bug_type(self, jira_client, test_project, jira_profile):
        """Test creating a Bug issue type."""
        summary = f"Test Bug Issue {uuid.uuid4().hex[:8]}"

        result = create_issue(
            project=test_project['key'],
            issue_type='Bug',
            summary=summary,
            profile=jira_profile,
            no_defaults=True
        )

        assert 'key' in result

        # Verify issue type
        issue = jira_client.get_issue(result['key'])
        assert issue['fields']['issuetype']['name'] == 'Bug'

        # Cleanup
        jira_client.delete_issue(result['key'])

    def test_create_issue_story_type(self, jira_client, test_project, jira_profile):
        """Test creating a Story issue type."""
        summary = f"Test Story Issue {uuid.uuid4().hex[:8]}"

        result = create_issue(
            project=test_project['key'],
            issue_type='Story',
            summary=summary,
            profile=jira_profile,
            no_defaults=True
        )

        assert 'key' in result

        # Verify issue type
        issue = jira_client.get_issue(result['key'])
        assert issue['fields']['issuetype']['name'] == 'Story'

        # Cleanup
        jira_client.delete_issue(result['key'])


@pytest.mark.integration
@pytest.mark.issue
class TestGetIssue:
    """Tests for get_issue.py functionality."""

    def test_get_issue_basic(self, jira_client, test_project, test_issue, jira_profile):
        """Test retrieving an issue."""
        result = get_issue(
            issue_key=test_issue['key'],
            profile=jira_profile
        )

        assert result['key'] == test_issue['key']
        assert 'fields' in result
        assert 'summary' in result['fields']

    def test_get_issue_specific_fields(self, jira_client, test_project, test_issue, jira_profile):
        """Test retrieving specific fields only."""
        result = get_issue(
            issue_key=test_issue['key'],
            fields=['summary', 'status'],
            profile=jira_profile
        )

        assert result['key'] == test_issue['key']
        assert 'summary' in result['fields']
        assert 'status' in result['fields']
        # Other fields should not be present (except system fields)

    def test_get_issue_with_all_fields(self, jira_client, test_project, test_issue, jira_profile):
        """Test retrieving all fields."""
        result = get_issue(
            issue_key=test_issue['key'],
            profile=jira_profile
        )

        assert result['key'] == test_issue['key']
        fields = result['fields']
        # Should have standard fields
        assert 'summary' in fields
        assert 'issuetype' in fields
        assert 'status' in fields
        assert 'project' in fields

    def test_get_issue_not_found(self, jira_profile):
        """Test retrieving a non-existent issue."""
        from jira_assistant_skills_lib import NotFoundError

        with pytest.raises(NotFoundError):
            get_issue(
                issue_key='NONEXISTENT-99999',
                profile=jira_profile
            )


@pytest.mark.integration
@pytest.mark.issue
class TestUpdateIssue:
    """Tests for update_issue.py functionality."""

    def test_update_issue_summary(self, jira_client, test_project, test_issue, jira_profile):
        """Test updating issue summary."""
        new_summary = f"Updated Summary {uuid.uuid4().hex[:8]}"

        update_issue(
            issue_key=test_issue['key'],
            summary=new_summary,
            profile=jira_profile
        )

        # Verify update
        issue = jira_client.get_issue(test_issue['key'])
        assert issue['fields']['summary'] == new_summary

    def test_update_issue_description(self, jira_client, test_project, test_issue, jira_profile):
        """Test updating issue description."""
        new_description = "This is the updated description."

        update_issue(
            issue_key=test_issue['key'],
            description=new_description,
            profile=jira_profile
        )

        # Verify update
        issue = jira_client.get_issue(test_issue['key'])
        desc = issue['fields'].get('description', {})
        assert desc is not None

    def test_update_issue_priority(self, jira_client, test_project, test_issue, jira_profile):
        """Test updating issue priority."""
        update_issue(
            issue_key=test_issue['key'],
            priority='High',
            profile=jira_profile
        )

        # Verify update
        issue = jira_client.get_issue(test_issue['key'])
        assert issue['fields']['priority']['name'] == 'High'

    def test_update_issue_labels(self, jira_client, test_project, test_issue, jira_profile):
        """Test updating issue labels."""
        new_labels = ['updated-label', 'test']

        update_issue(
            issue_key=test_issue['key'],
            labels=new_labels,
            profile=jira_profile
        )

        # Verify update
        issue = jira_client.get_issue(test_issue['key'])
        assert set(issue['fields']['labels']) == set(new_labels)

    def test_update_issue_multiple_fields(self, jira_client, test_project, test_issue, jira_profile):
        """Test updating multiple fields at once."""
        new_summary = f"Multi-Update {uuid.uuid4().hex[:8]}"
        new_labels = ['multi-update']

        update_issue(
            issue_key=test_issue['key'],
            summary=new_summary,
            labels=new_labels,
            priority='Low',
            profile=jira_profile
        )

        # Verify all updates
        issue = jira_client.get_issue(test_issue['key'])
        assert issue['fields']['summary'] == new_summary
        assert set(issue['fields']['labels']) == set(new_labels)
        assert issue['fields']['priority']['name'] == 'Low'

    def test_update_issue_no_notify(self, jira_client, test_project, test_issue, jira_profile):
        """Test updating issue without sending notifications."""
        new_summary = f"Silent Update {uuid.uuid4().hex[:8]}"

        # This should not raise an error
        update_issue(
            issue_key=test_issue['key'],
            summary=new_summary,
            notify_users=False,
            profile=jira_profile
        )

        # Verify update
        issue = jira_client.get_issue(test_issue['key'])
        assert issue['fields']['summary'] == new_summary

    def test_update_issue_no_fields_error(self, test_issue, jira_profile):
        """Test that updating with no fields raises an error."""
        with pytest.raises(ValueError, match="No fields specified"):
            update_issue(
                issue_key=test_issue['key'],
                profile=jira_profile
            )


@pytest.mark.integration
@pytest.mark.issue
class TestDeleteIssue:
    """Tests for delete_issue.py functionality."""

    def test_delete_issue_force(self, jira_client, test_project, jira_profile):
        """Test deleting an issue with force flag."""
        # Create an issue to delete
        issue = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'To Be Deleted {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Task'}
        })

        # Delete with force
        delete_issue(
            issue_key=issue['key'],
            force=True,
            profile=jira_profile
        )

        # Verify deletion
        from jira_assistant_skills_lib import NotFoundError
        with pytest.raises(NotFoundError):
            jira_client.get_issue(issue['key'])

    def test_delete_issue_not_found(self, jira_profile):
        """Test deleting a non-existent issue."""
        from jira_assistant_skills_lib import NotFoundError

        with pytest.raises(NotFoundError):
            delete_issue(
                issue_key='NONEXISTENT-99999',
                force=True,
                profile=jira_profile
            )


@pytest.mark.integration
@pytest.mark.issue
class TestIssueLifecycle:
    """Tests for full issue lifecycle operations."""

    def test_full_issue_lifecycle(self, jira_client, test_project, jira_profile):
        """Test complete lifecycle: create -> get -> update -> delete."""
        # Create
        summary = f"Lifecycle Test {uuid.uuid4().hex[:8]}"
        created = create_issue(
            project=test_project['key'],
            issue_type='Task',
            summary=summary,
            description="Initial description",
            labels=['lifecycle-test'],
            profile=jira_profile,
            no_defaults=True
        )
        issue_key = created['key']

        try:
            # Get and verify creation
            retrieved = get_issue(issue_key=issue_key, profile=jira_profile)
            assert retrieved['fields']['summary'] == summary
            assert 'lifecycle-test' in retrieved['fields']['labels']

            # Update
            new_summary = f"Updated Lifecycle {uuid.uuid4().hex[:8]}"
            update_issue(
                issue_key=issue_key,
                summary=new_summary,
                labels=['lifecycle-test', 'updated'],
                profile=jira_profile
            )

            # Verify update
            updated = get_issue(issue_key=issue_key, profile=jira_profile)
            assert updated['fields']['summary'] == new_summary
            assert 'updated' in updated['fields']['labels']

        finally:
            # Delete
            delete_issue(issue_key=issue_key, force=True, profile=jira_profile)

        # Verify deletion
        from jira_assistant_skills_lib import NotFoundError
        with pytest.raises(NotFoundError):
            get_issue(issue_key=issue_key, profile=jira_profile)

    def test_create_multiple_issues(self, jira_client, test_project, jira_profile):
        """Test creating multiple issues in sequence."""
        issue_keys = []

        try:
            for i in range(3):
                result = create_issue(
                    project=test_project['key'],
                    issue_type='Task',
                    summary=f"Multi Issue {i+1} {uuid.uuid4().hex[:8]}",
                    profile=jira_profile,
                    no_defaults=True
                )
                issue_keys.append(result['key'])

            # Verify all issues exist
            for key in issue_keys:
                issue = get_issue(issue_key=key, profile=jira_profile)
                assert issue['key'] == key

        finally:
            # Cleanup all
            for key in issue_keys:
                try:
                    delete_issue(issue_key=key, force=True, profile=jira_profile)
                except Exception:
                    pass

    def test_create_and_update_with_markdown(self, jira_client, test_project, jira_profile):
        """Test creating and updating with markdown descriptions."""
        summary = f"Markdown Test {uuid.uuid4().hex[:8]}"
        markdown_desc = """# Heading

This is a **bold** and *italic* test.

- Item 1
- Item 2

```python
print("code block")
```
"""

        result = create_issue(
            project=test_project['key'],
            issue_type='Task',
            summary=summary,
            description=markdown_desc,
            profile=jira_profile,
            no_defaults=True
        )

        try:
            # Verify creation
            issue = get_issue(issue_key=result['key'], profile=jira_profile)
            assert issue['fields'].get('description') is not None

            # Update with new markdown
            update_issue(
                issue_key=result['key'],
                description="## Updated\n\nNew description with **markdown**.",
                profile=jira_profile
            )

            # Verify update
            updated = get_issue(issue_key=result['key'], profile=jira_profile)
            assert updated['fields'].get('description') is not None

        finally:
            delete_issue(issue_key=result['key'], force=True, profile=jira_profile)
