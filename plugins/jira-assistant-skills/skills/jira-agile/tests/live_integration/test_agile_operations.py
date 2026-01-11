"""
Live Integration Tests for jira-agile operations.

Tests epic, sprint, story points, and backlog operations against a real JIRA instance.

Usage:
    pytest plugins/jira-assistant-skills/skills/jira-agile/tests/live_integration/ --profile development -v
"""

import pytest
import uuid
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add scripts to path
_this_dir = Path(__file__).parent
_scripts_path = _this_dir.parent.parent / 'scripts'
sys.path.insert(0, str(_scripts_path))

from create_epic import create_epic
from add_to_epic import add_to_epic
from create_sprint import create_sprint
from move_to_sprint import move_to_sprint
from estimate_issue import estimate_issue
from get_backlog import get_backlog
from get_epic import get_epic
from get_sprint import get_sprint


@pytest.mark.integration
@pytest.mark.agile
class TestCreateEpic:
    """Tests for create_epic.py functionality."""

    def test_create_epic_minimal(self, jira_client, test_project, jira_profile):
        """Test creating an epic with minimal fields."""
        summary = f"Test Epic {uuid.uuid4().hex[:8]}"

        result = create_epic(
            project=test_project['key'],
            summary=summary,
            profile=jira_profile,
            client=jira_client
        )

        try:
            assert 'key' in result
            assert result['key'].startswith(test_project['key'])

            # Verify epic was created
            issue = jira_client.get_issue(result['key'])
            assert issue['fields']['summary'] == summary
            assert issue['fields']['issuetype']['name'] == 'Epic'
        finally:
            jira_client.delete_issue(result['key'])

    def test_create_epic_with_description(self, jira_client, test_project, jira_profile):
        """Test creating an epic with a description."""
        summary = f"Epic with Desc {uuid.uuid4().hex[:8]}"
        description = "This is the epic description"

        result = create_epic(
            project=test_project['key'],
            summary=summary,
            description=description,
            profile=jira_profile,
            client=jira_client
        )

        try:
            assert 'key' in result
            issue = jira_client.get_issue(result['key'])
            assert issue['fields']['description'] is not None
        finally:
            jira_client.delete_issue(result['key'])

    def test_create_epic_with_priority(self, jira_client, test_project, jira_profile):
        """Test creating an epic with priority."""
        summary = f"Priority Epic {uuid.uuid4().hex[:8]}"

        result = create_epic(
            project=test_project['key'],
            summary=summary,
            priority='High',
            profile=jira_profile,
            client=jira_client
        )

        try:
            assert 'key' in result
            issue = jira_client.get_issue(result['key'])
            assert issue['fields']['priority']['name'] == 'High'
        finally:
            jira_client.delete_issue(result['key'])

    def test_create_epic_with_labels(self, jira_client, test_project, jira_profile):
        """Test creating an epic with labels."""
        summary = f"Labeled Epic {uuid.uuid4().hex[:8]}"
        labels = ['epic-label', 'test']

        result = create_epic(
            project=test_project['key'],
            summary=summary,
            labels=labels,
            profile=jira_profile,
            client=jira_client
        )

        try:
            assert 'key' in result
            issue = jira_client.get_issue(result['key'])
            assert set(issue['fields']['labels']) == set(labels)
        finally:
            jira_client.delete_issue(result['key'])


@pytest.mark.integration
@pytest.mark.agile
class TestAddToEpic:
    """Tests for add_to_epic.py functionality."""

    def test_add_issue_to_epic(self, jira_client, test_project, test_story, jira_profile):
        """Test adding an issue to an epic."""
        # Create an epic
        epic = create_epic(
            project=test_project['key'],
            summary=f"Parent Epic {uuid.uuid4().hex[:8]}",
            profile=jira_profile,
            client=jira_client
        )

        try:
            result = add_to_epic(
                epic_key=epic['key'],
                issue_keys=[test_story['key']],
                profile=jira_profile,
                client=jira_client
            )

            assert result['added'] >= 1
        finally:
            jira_client.delete_issue(epic['key'])

    def test_add_multiple_issues_to_epic(self, jira_client, test_project, jira_profile):
        """Test adding multiple issues to an epic."""
        # Create epic
        epic = create_epic(
            project=test_project['key'],
            summary=f"Multi-Issue Epic {uuid.uuid4().hex[:8]}",
            profile=jira_profile,
            client=jira_client
        )

        # Create stories
        stories = []
        for i in range(3):
            story = jira_client.create_issue({
                'project': {'key': test_project['key']},
                'summary': f'Story {i+1} {uuid.uuid4().hex[:8]}',
                'issuetype': {'name': 'Story'}
            })
            stories.append(story)

        try:
            story_keys = [s['key'] for s in stories]
            result = add_to_epic(
                epic_key=epic['key'],
                issue_keys=story_keys,
                profile=jira_profile,
                client=jira_client
            )

            assert result['added'] >= 3
        finally:
            for story in stories:
                try:
                    jira_client.delete_issue(story['key'])
                except Exception:
                    pass
            jira_client.delete_issue(epic['key'])


@pytest.mark.integration
@pytest.mark.agile
class TestCreateSprint:
    """Tests for create_sprint.py functionality."""

    def test_create_sprint_minimal(self, jira_client, test_project, jira_profile):
        """Test creating a sprint with minimal fields."""
        if not test_project.get('board_id'):
            pytest.skip("No board available")

        sprint_name = f"Test Sprint {uuid.uuid4().hex[:8]}"

        result = create_sprint(
            board_id=test_project['board_id'],
            name=sprint_name,
            profile=jira_profile,
            client=jira_client
        )

        try:
            assert 'id' in result
            assert result['name'] == sprint_name
            assert result['state'] == 'future'
        finally:
            try:
                jira_client.delete_sprint(result['id'])
            except Exception:
                pass

    def test_create_sprint_with_goal(self, jira_client, test_project, jira_profile):
        """Test creating a sprint with a goal."""
        if not test_project.get('board_id'):
            pytest.skip("No board available")

        sprint_name = f"Goal Sprint {uuid.uuid4().hex[:8]}"
        goal = "Complete the MVP features"

        result = create_sprint(
            board_id=test_project['board_id'],
            name=sprint_name,
            goal=goal,
            profile=jira_profile,
            client=jira_client
        )

        try:
            assert 'id' in result
            assert result.get('goal') == goal
        finally:
            try:
                jira_client.delete_sprint(result['id'])
            except Exception:
                pass

    def test_create_sprint_with_dates(self, jira_client, test_project, jira_profile):
        """Test creating a sprint with start and end dates."""
        if not test_project.get('board_id'):
            pytest.skip("No board available")

        sprint_name = f"Dated Sprint {uuid.uuid4().hex[:8]}"
        start_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d')

        result = create_sprint(
            board_id=test_project['board_id'],
            name=sprint_name,
            start_date=start_date,
            end_date=end_date,
            profile=jira_profile,
            client=jira_client
        )

        try:
            assert 'id' in result
            # Dates should be set
            assert result.get('startDate') or result.get('start_date')
        finally:
            try:
                jira_client.delete_sprint(result['id'])
            except Exception:
                pass


@pytest.mark.integration
@pytest.mark.agile
class TestMoveToSprint:
    """Tests for move_to_sprint.py functionality."""

    def test_move_issue_to_sprint(self, jira_client, test_project, test_issue, test_sprint, jira_profile):
        """Test moving an issue to a sprint."""
        result = move_to_sprint(
            sprint_id=test_sprint['id'],
            issue_keys=[test_issue['key']],
            profile=jira_profile,
            client=jira_client
        )

        assert result['moved'] >= 1

    def test_move_multiple_issues_to_sprint(self, jira_client, test_project, test_sprint, jira_profile):
        """Test moving multiple issues to a sprint."""
        # Create issues
        issues = []
        for i in range(3):
            issue = jira_client.create_issue({
                'project': {'key': test_project['key']},
                'summary': f'Sprint Issue {i+1} {uuid.uuid4().hex[:8]}',
                'issuetype': {'name': 'Task'}
            })
            issues.append(issue)

        try:
            issue_keys = [i['key'] for i in issues]
            result = move_to_sprint(
                sprint_id=test_sprint['id'],
                issue_keys=issue_keys,
                profile=jira_profile,
                client=jira_client
            )

            assert result['moved'] >= 3
        finally:
            for issue in issues:
                try:
                    jira_client.delete_issue(issue['key'])
                except Exception:
                    pass


@pytest.mark.integration
@pytest.mark.agile
class TestEstimateIssue:
    """Tests for estimate_issue.py functionality."""

    def test_estimate_single_issue(self, jira_client, test_project, test_story, jira_profile):
        """Test setting story points on a single issue."""
        result = estimate_issue(
            issue_keys=[test_story['key']],
            points=5,
            profile=jira_profile,
            client=jira_client
        )

        assert result['updated'] == 1
        assert test_story['key'] in result['issues']
        assert result['points'] == 5

    def test_estimate_multiple_issues(self, jira_client, test_project, jira_profile):
        """Test setting story points on multiple issues."""
        # Create stories
        stories = []
        for i in range(3):
            story = jira_client.create_issue({
                'project': {'key': test_project['key']},
                'summary': f'Estimate Story {i+1} {uuid.uuid4().hex[:8]}',
                'issuetype': {'name': 'Story'}
            })
            stories.append(story)

        try:
            story_keys = [s['key'] for s in stories]
            result = estimate_issue(
                issue_keys=story_keys,
                points=3,
                profile=jira_profile,
                client=jira_client
            )

            assert result['updated'] == 3
            assert result['points'] == 3
        finally:
            for story in stories:
                try:
                    jira_client.delete_issue(story['key'])
                except Exception:
                    pass

    def test_clear_estimate(self, jira_client, test_project, test_story, jira_profile):
        """Test clearing story points (set to 0)."""
        # First set a value
        estimate_issue(
            issue_keys=[test_story['key']],
            points=5,
            profile=jira_profile,
            client=jira_client
        )

        # Then clear it
        result = estimate_issue(
            issue_keys=[test_story['key']],
            points=0,
            profile=jira_profile,
            client=jira_client
        )

        assert result['updated'] == 1
        assert result['points'] == 0

    def test_fibonacci_validation(self, jira_profile):
        """Test Fibonacci validation rejects non-Fibonacci values."""
        from jira_assistant_skills_lib import ValidationError

        with pytest.raises(ValidationError):
            estimate_issue(
                issue_keys=['FAKE-1'],
                points=4,  # Not Fibonacci
                validate_fibonacci=True,
                profile=jira_profile
            )


@pytest.mark.integration
@pytest.mark.agile
class TestGetBacklog:
    """Tests for get_backlog.py functionality."""

    def test_get_backlog(self, jira_client, test_project, test_issue, jira_profile):
        """Test getting backlog issues."""
        if not test_project.get('board_id'):
            pytest.skip("No board available")

        result = get_backlog(
            board_id=test_project['board_id'],
            profile=jira_profile,
            client=jira_client
        )

        assert 'issues' in result
        # Our test issue should be in backlog
        issue_keys = [i['key'] for i in result['issues']]
        assert test_issue['key'] in issue_keys


@pytest.mark.integration
@pytest.mark.agile
class TestGetEpic:
    """Tests for get_epic.py functionality."""

    def test_get_epic_details(self, jira_client, test_project, jira_profile):
        """Test getting epic details."""
        # Create an epic
        epic = create_epic(
            project=test_project['key'],
            summary=f"Get Epic Test {uuid.uuid4().hex[:8]}",
            profile=jira_profile,
            client=jira_client
        )

        try:
            result = get_epic(
                epic_key=epic['key'],
                profile=jira_profile,
                client=jira_client
            )

            assert result['key'] == epic['key']
            assert result['fields']['issuetype']['name'] == 'Epic'
        finally:
            jira_client.delete_issue(epic['key'])

    def test_get_epic_with_issues(self, jira_client, test_project, jira_profile):
        """Test getting epic with child issues."""
        # Create epic
        epic = create_epic(
            project=test_project['key'],
            summary=f"Epic with Children {uuid.uuid4().hex[:8]}",
            profile=jira_profile,
            client=jira_client
        )

        # Create and link stories
        stories = []
        for i in range(2):
            story = jira_client.create_issue({
                'project': {'key': test_project['key']},
                'summary': f'Child Story {i+1} {uuid.uuid4().hex[:8]}',
                'issuetype': {'name': 'Story'}
            })
            stories.append(story)

        add_to_epic(
            epic_key=epic['key'],
            issue_keys=[s['key'] for s in stories],
            profile=jira_profile,
            client=jira_client
        )

        try:
            result = get_epic(
                epic_key=epic['key'],
                with_children=True,
                profile=jira_profile,
                client=jira_client
            )

            assert result['key'] == epic['key']
            # Should have child issues
            if 'children' in result:
                assert len(result['children']) >= 2
        finally:
            for story in stories:
                try:
                    jira_client.delete_issue(story['key'])
                except Exception:
                    pass
            jira_client.delete_issue(epic['key'])


@pytest.mark.integration
@pytest.mark.agile
class TestGetSprint:
    """Tests for get_sprint.py functionality."""

    def test_get_sprint_details(self, jira_client, test_project, test_sprint, jira_profile):
        """Test getting sprint details."""
        result = get_sprint(
            sprint_id=test_sprint['id'],
            profile=jira_profile,
            client=jira_client
        )

        assert result['id'] == test_sprint['id']
        assert result['name'] == test_sprint['name']
        assert result['state'] == 'future'

    def test_get_sprint_with_issues(self, jira_client, test_project, test_sprint, test_issue, jira_profile):
        """Test getting sprint with its issues."""
        # Move issue to sprint
        move_to_sprint(
            sprint_id=test_sprint['id'],
            issue_keys=[test_issue['key']],
            profile=jira_profile,
            client=jira_client
        )

        result = get_sprint(
            sprint_id=test_sprint['id'],
            with_issues=True,
            profile=jira_profile,
            client=jira_client
        )

        assert result['id'] == test_sprint['id']
        if 'issues' in result:
            issue_keys = [i['key'] for i in result['issues']]
            assert test_issue['key'] in issue_keys


@pytest.mark.integration
@pytest.mark.agile
class TestAgileWorkflow:
    """Tests for complete agile workflow."""

    def test_full_agile_workflow(self, jira_client, test_project, jira_profile):
        """Test complete agile workflow: epic -> stories -> sprint -> estimate."""
        if not test_project.get('board_id'):
            pytest.skip("No board available")

        # 1. Create Epic
        epic = create_epic(
            project=test_project['key'],
            summary=f"Workflow Epic {uuid.uuid4().hex[:8]}",
            profile=jira_profile,
            client=jira_client
        )

        # 2. Create Stories
        stories = []
        for i in range(2):
            story = jira_client.create_issue({
                'project': {'key': test_project['key']},
                'summary': f'Workflow Story {i+1} {uuid.uuid4().hex[:8]}',
                'issuetype': {'name': 'Story'}
            })
            stories.append(story)

        # 3. Create Sprint
        sprint = create_sprint(
            board_id=test_project['board_id'],
            name=f'Workflow Sprint {uuid.uuid4().hex[:8]}',
            goal='Complete workflow test',
            profile=jira_profile,
            client=jira_client
        )

        try:
            # 4. Add stories to epic
            add_result = add_to_epic(
                epic_key=epic['key'],
                issue_keys=[s['key'] for s in stories],
                profile=jira_profile,
                client=jira_client
            )
            assert add_result['added'] >= 2

            # 5. Move stories to sprint
            move_result = move_to_sprint(
                sprint_id=sprint['id'],
                issue_keys=[s['key'] for s in stories],
                profile=jira_profile,
                client=jira_client
            )
            assert move_result['moved'] >= 2

            # 6. Estimate stories
            estimate_result = estimate_issue(
                issue_keys=[s['key'] for s in stories],
                points=5,
                profile=jira_profile,
                client=jira_client
            )
            assert estimate_result['updated'] >= 2

            # 7. Verify sprint has stories
            sprint_data = get_sprint(
                sprint_id=sprint['id'],
                with_issues=True,
                profile=jira_profile,
                client=jira_client
            )
            assert sprint_data['id'] == sprint['id']

        finally:
            # Cleanup
            for story in stories:
                try:
                    jira_client.delete_issue(story['key'])
                except Exception:
                    pass
            try:
                jira_client.delete_sprint(sprint['id'])
            except Exception:
                pass
            jira_client.delete_issue(epic['key'])
