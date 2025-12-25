"""
Live Integration Tests: Agile Workflow

Tests for sprint, epic, and backlog operations against a real JIRA instance.
"""

import pytest
import uuid
from datetime import datetime, timedelta


class TestSprintLifecycle:
    """Tests for sprint CRUD operations."""

    def test_create_sprint(self, jira_client, test_project):
        """Test creating a sprint."""
        if not test_project.get('board_id'):
            pytest.skip("No board available")

        sprint = jira_client.create_sprint(
            board_id=test_project['board_id'],
            name=f'Test Sprint {uuid.uuid4().hex[:8]}',
            goal='Test sprint goal'
        )

        assert sprint['id'] is not None
        assert sprint['state'] == 'future'

        # Cleanup
        jira_client.delete_sprint(sprint['id'])

    def test_create_sprint_with_dates(self, jira_client, test_project):
        """Test creating a sprint with start/end dates."""
        if not test_project.get('board_id'):
            pytest.skip("No board available")

        start_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d')

        sprint = jira_client.create_sprint(
            board_id=test_project['board_id'],
            name=f'Dated Sprint {uuid.uuid4().hex[:8]}',
            start_date=f'{start_date}T00:00:00.000Z',
            end_date=f'{end_date}T00:00:00.000Z'
        )

        assert sprint['id'] is not None
        assert 'startDate' in sprint or sprint['state'] == 'future'

        # Cleanup
        jira_client.delete_sprint(sprint['id'])

    def test_get_sprint(self, jira_client, test_sprint):
        """Test fetching sprint details."""
        sprint = jira_client.get_sprint(test_sprint['id'])

        assert sprint['id'] == test_sprint['id']
        assert sprint['name'] == test_sprint['name']

    def test_update_sprint(self, jira_client, test_sprint):
        """Test updating sprint details."""
        new_goal = f'Updated goal {uuid.uuid4().hex[:8]}'

        updated = jira_client.update_sprint(
            test_sprint['id'],
            goal=new_goal
        )

        assert updated['goal'] == new_goal

    def test_get_board_sprints(self, jira_client, test_project, test_sprint):
        """Test listing sprints for a board."""
        if not test_project.get('board_id'):
            pytest.skip("No board available")

        result = jira_client.get_board_sprints(test_project['board_id'])

        assert 'values' in result
        sprint_ids = [s['id'] for s in result['values']]
        assert test_sprint['id'] in sprint_ids

    def test_delete_sprint(self, jira_client, test_project):
        """Test deleting a sprint."""
        if not test_project.get('board_id'):
            pytest.skip("No board available")

        # Create sprint to delete
        sprint = jira_client.create_sprint(
            board_id=test_project['board_id'],
            name=f'Sprint to Delete {uuid.uuid4().hex[:8]}'
        )

        # Delete it
        jira_client.delete_sprint(sprint['id'])

        # Verify it's gone (should raise error)
        from error_handler import NotFoundError
        with pytest.raises(NotFoundError):
            jira_client.get_sprint(sprint['id'])


class TestSprintIssueManagement:
    """Tests for moving issues to/from sprints."""

    # Sprint field ID - may vary by JIRA instance
    SPRINT_FIELD = 'customfield_10020'

    def _verify_issue_in_sprint(self, jira_client, sprint_id, issue_key):
        """Verify an issue is assigned to a sprint by checking its sprint field."""
        issue = jira_client.get_issue(issue_key)
        sprint_field = issue['fields'].get(self.SPRINT_FIELD, [])
        if sprint_field:
            sprint_ids = [s['id'] for s in sprint_field]
            return sprint_id in sprint_ids
        return False

    def test_move_issue_to_sprint(self, jira_client, test_sprint, test_issue):
        """Test moving an issue to a sprint."""
        jira_client.move_issues_to_sprint(
            test_sprint['id'],
            [test_issue['key']]
        )

        # Verify issue has sprint field set (direct check, not via Agile API)
        # Note: Simple boards (created by simplified templates) don't work well
        # with /rest/agile/1.0/sprint/{id}/issue endpoint
        assert self._verify_issue_in_sprint(
            jira_client, test_sprint['id'], test_issue['key']
        ), f"Issue {test_issue['key']} sprint field not set to sprint {test_sprint['id']}"

    def test_move_multiple_issues_to_sprint(self, jira_client, test_project, test_sprint):
        """Test moving multiple issues to a sprint."""
        # Create test issues
        issues = []
        for i in range(3):
            issue = jira_client.create_issue({
                'project': {'key': test_project['key']},
                'summary': f'Sprint Issue {i} {uuid.uuid4().hex[:8]}',
                'issuetype': {'name': 'Task'}
            })
            issues.append(issue)

        issue_keys = [i['key'] for i in issues]

        # Move to sprint
        jira_client.move_issues_to_sprint(test_sprint['id'], issue_keys)

        # Verify all issues have sprint field set
        for key in issue_keys:
            assert self._verify_issue_in_sprint(
                jira_client, test_sprint['id'], key
            ), f"Issue {key} sprint field not set"

        # Cleanup
        for issue in issues:
            jira_client.delete_issue(issue['key'])

    def test_get_sprint_issues(self, jira_client, test_project, test_sprint):
        """Test getting issues in a sprint.

        Note: The Agile API's /sprint/{id}/issue endpoint may not return issues
        for 'simple' type boards (created by simplified project templates).
        This test verifies the API call works and validates sprint assignment
        via the issue's sprint field as a fallback.
        """
        # Create and add an issue
        issue = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Sprint Issue {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Task'}
        })

        jira_client.move_issues_to_sprint(test_sprint['id'], [issue['key']])

        # Get sprint issues - API should return valid response structure
        result = jira_client.get_sprint_issues(test_sprint['id'])
        assert 'issues' in result

        # For simple boards, the agile API may return empty, so verify via field
        if len(result['issues']) == 0:
            # Fallback: verify sprint assignment via issue's sprint field
            assert self._verify_issue_in_sprint(
                jira_client, test_sprint['id'], issue['key']
            ), "Sprint assignment failed - issue has no sprint field"
        else:
            # Scrum boards: verify issue appears in results
            issue_keys = [i['key'] for i in result['issues']]
            assert issue['key'] in issue_keys

        # Cleanup
        jira_client.delete_issue(issue['key'])


class TestBacklog:
    """Tests for backlog operations."""

    def test_get_backlog(self, jira_client, test_project):
        """Test getting backlog issues."""
        if not test_project.get('board_id'):
            pytest.skip("No board available")

        # Create an issue (should go to backlog)
        issue = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Backlog Issue {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Story'}
        })

        # Get backlog
        result = jira_client.get_board_backlog(test_project['board_id'])

        assert 'issues' in result

        # Cleanup
        jira_client.delete_issue(issue['key'])

    def test_rank_issues(self, jira_client, test_project):
        """Test ranking issues in backlog."""
        # Create two issues
        issue1 = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Rank Issue 1 {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Story'}
        })
        issue2 = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Rank Issue 2 {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Story'}
        })

        # Rank issue2 before issue1
        jira_client.rank_issues([issue2['key']], rank_before=issue1['key'])

        # Verify ranking (issue2 should come before issue1 in backlog)
        if test_project.get('board_id'):
            result = jira_client.get_board_backlog(test_project['board_id'])
            keys = [i['key'] for i in result.get('issues', [])]
            if issue1['key'] in keys and issue2['key'] in keys:
                assert keys.index(issue2['key']) < keys.index(issue1['key'])

        # Cleanup
        jira_client.delete_issue(issue1['key'])
        jira_client.delete_issue(issue2['key'])


class TestEpicOperations:
    """Tests for epic operations."""

    def test_create_epic(self, jira_client, test_project):
        """Test creating an epic."""
        epic = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Test Epic {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Epic'},
            'customfield_10011': f'Epic-{uuid.uuid4().hex[:6]}'  # Epic Name
        })

        assert epic['key'].startswith(test_project['key'])

        # Verify it's an epic
        epic_data = jira_client.get_issue(epic['key'])
        assert epic_data['fields']['issuetype']['name'] == 'Epic'

        # Cleanup
        jira_client.delete_issue(epic['key'])

    def test_add_issue_to_epic(self, jira_client, test_project, test_epic):
        """Test adding an issue to an epic."""
        # Create a story
        story = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Epic Story {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Story'}
        })

        # Add to epic using epic link field
        jira_client.update_issue(story['key'], {
            'customfield_10014': test_epic['key']  # Epic Link
        })

        # Verify
        updated_story = jira_client.get_issue(story['key'])
        # Check parent or epic link field
        parent = updated_story['fields'].get('parent', {})
        epic_link = updated_story['fields'].get('customfield_10014')

        assert parent.get('key') == test_epic['key'] or epic_link == test_epic['key']

        # Cleanup
        jira_client.delete_issue(story['key'])

    def test_get_epic_children(self, jira_client, test_project, test_epic):
        """Test getting issues in an epic."""
        # Create stories in epic
        stories = []
        for i in range(2):
            story = jira_client.create_issue({
                'project': {'key': test_project['key']},
                'summary': f'Epic Child {i} {uuid.uuid4().hex[:8]}',
                'issuetype': {'name': 'Story'},
                'customfield_10014': test_epic['key']  # Epic Link
            })
            stories.append(story)

        # Search for issues in epic
        result = jira_client.search_issues(
            f'"Epic Link" = {test_epic["key"]}',
            fields=['key', 'summary']
        )

        assert result['total'] >= 2
        result_keys = [i['key'] for i in result['issues']]
        for story in stories:
            assert story['key'] in result_keys

        # Cleanup
        for story in stories:
            jira_client.delete_issue(story['key'])


class TestBoardOperations:
    """Tests for board operations."""

    def test_get_board(self, jira_client, test_project):
        """Test getting board details."""
        if not test_project.get('board_id'):
            pytest.skip("No board available")

        board = jira_client.get_board(test_project['board_id'])

        assert board['id'] == test_project['board_id']
        assert 'name' in board
        assert 'type' in board

    def test_get_all_boards(self, jira_client, test_project):
        """Test listing all boards."""
        result = jira_client.get_all_boards(project_key=test_project['key'])

        assert 'values' in result
        if result['values']:
            board_project_keys = [b['location']['projectKey'] for b in result['values']]
            assert test_project['key'] in board_project_keys
