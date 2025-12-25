"""
Integration tests for jira-agile skill.

These tests verify end-to-end workflows combining multiple scripts.
They use mocks to simulate JIRA API responses.
"""

import sys
from pathlib import Path

test_dir = Path(__file__).parent
jira_agile_dir = test_dir.parent
skills_dir = jira_agile_dir.parent
shared_lib_path = skills_dir / 'shared' / 'scripts' / 'lib'
scripts_path = jira_agile_dir / 'scripts'

sys.path.insert(0, str(shared_lib_path))
sys.path.insert(0, str(scripts_path))

import pytest
from unittest.mock import Mock, patch, MagicMock

EPIC_LINK_FIELD = 'customfield_10014'
STORY_POINTS_FIELD = 'customfield_10016'


@pytest.mark.agile
@pytest.mark.integration
class TestEpicToSprintWorkflow:
    """
    Test workflow: Create epic → Add issues → Create sprint → Move to sprint

    This simulates a typical sprint planning workflow where:
    1. An epic is created for a feature
    2. Issues are added to the epic
    3. A sprint is created
    4. Issues from the epic are moved to the sprint
    """

    def test_epic_to_sprint_workflow(self, mock_jira_client):
        """Test complete epic-to-sprint workflow."""
        from create_epic import create_epic
        from add_to_epic import add_to_epic
        from create_sprint import create_sprint
        from move_to_sprint import move_to_sprint

        # Step 1: Create epic
        mock_jira_client.create_issue.return_value = {
            'id': '10001',
            'key': 'PROJ-100',
            'self': 'https://test.atlassian.net/rest/api/3/issue/10001'
        }

        epic_result = create_epic(
            project='PROJ',
            summary='Mobile App MVP',
            epic_name='MVP',
            client=mock_jira_client
        )
        assert epic_result['key'] == 'PROJ-100'

        # Step 2: Add issues to epic
        # Mock get_issue to return epic info for validation
        mock_jira_client.get_issue.return_value = {
            'key': 'PROJ-100',
            'fields': {
                'issuetype': {'name': 'Epic'},
                'summary': 'Mobile App MVP'
            }
        }
        mock_jira_client.update_issue.return_value = None

        add_result = add_to_epic(
            epic_key='PROJ-100',
            issue_keys=['PROJ-101', 'PROJ-102', 'PROJ-103'],
            client=mock_jira_client
        )
        assert add_result['added'] == 3

        # Step 3: Create sprint
        mock_jira_client.create_sprint.return_value = {
            'id': 456,
            'name': 'Sprint 1',
            'state': 'future'
        }

        sprint_result = create_sprint(
            board_id=123,
            name='Sprint 1',
            goal='Complete MVP features',
            client=mock_jira_client
        )
        assert sprint_result['id'] == 456

        # Step 4: Move issues to sprint
        mock_jira_client.move_issues_to_sprint.return_value = None

        move_result = move_to_sprint(
            sprint_id=456,
            issue_keys=['PROJ-101', 'PROJ-102', 'PROJ-103'],
            client=mock_jira_client
        )
        assert move_result['moved'] == 3

        # Verify all API calls were made
        assert mock_jira_client.create_issue.call_count == 1
        assert mock_jira_client.update_issue.call_count == 3
        assert mock_jira_client.create_sprint.call_count == 1
        assert mock_jira_client.move_issues_to_sprint.call_count == 1


@pytest.mark.agile
@pytest.mark.integration
class TestSprintLifecycleWorkflow:
    """
    Test workflow: Create sprint → Add issues → Set estimates → Start → Close

    This simulates a complete sprint lifecycle:
    1. Sprint is created
    2. Issues are added to sprint
    3. Story points are estimated
    4. Sprint is started
    5. Sprint is closed
    """

    def test_sprint_lifecycle_workflow(self, mock_jira_client):
        """Test complete sprint lifecycle workflow."""
        from create_sprint import create_sprint
        from move_to_sprint import move_to_sprint
        from estimate_issue import estimate_issue
        from manage_sprint import start_sprint, close_sprint

        # Step 1: Create sprint
        mock_jira_client.create_sprint.return_value = {
            'id': 456,
            'name': 'Sprint 42',
            'state': 'future',
            'goal': 'Launch beta'
        }

        sprint_result = create_sprint(
            board_id=123,
            name='Sprint 42',
            goal='Launch beta',
            start_date='2025-01-20',
            end_date='2025-02-03',
            client=mock_jira_client
        )
        assert sprint_result['id'] == 456
        assert sprint_result['state'] == 'future'

        # Step 2: Add issues to sprint
        mock_jira_client.move_issues_to_sprint.return_value = None

        move_result = move_to_sprint(
            sprint_id=456,
            issue_keys=['PROJ-1', 'PROJ-2', 'PROJ-3'],
            client=mock_jira_client
        )
        assert move_result['moved'] == 3

        # Step 3: Set story point estimates
        mock_jira_client.update_issue.return_value = None

        # Estimate each issue
        for key, points in [('PROJ-1', 5), ('PROJ-2', 8), ('PROJ-3', 3)]:
            estimate_result = estimate_issue(
                issue_keys=[key],
                points=points,
                client=mock_jira_client
            )
            assert estimate_result['updated'] == 1

        # Step 4: Start sprint
        mock_jira_client.update_sprint.return_value = {
            'id': 456,
            'state': 'active'
        }

        start_result = start_sprint(
            sprint_id=456,
            client=mock_jira_client
        )
        assert start_result['state'] == 'active'

        # Step 5: Close sprint
        mock_jira_client.update_sprint.return_value = {
            'id': 456,
            'state': 'closed'
        }

        close_result = close_sprint(
            sprint_id=456,
            client=mock_jira_client
        )
        assert close_result['state'] == 'closed'

        # Verify workflow completed
        assert mock_jira_client.create_sprint.call_count == 1
        assert mock_jira_client.move_issues_to_sprint.call_count == 1
        assert mock_jira_client.update_issue.call_count == 3  # 3 estimates
        assert mock_jira_client.update_sprint.call_count == 2  # start + close


@pytest.mark.agile
@pytest.mark.integration
class TestBacklogGroomingWorkflow:
    """
    Test workflow: Get backlog → Rank issues → Estimate → Move to sprint

    This simulates backlog grooming:
    1. View current backlog
    2. Reorder priorities
    3. Add estimates
    4. Move top items to upcoming sprint
    """

    def test_backlog_grooming_workflow(self, mock_jira_client):
        """Test backlog grooming workflow."""
        from get_backlog import get_backlog
        from rank_issue import rank_issue
        from estimate_issue import estimate_issue
        from move_to_sprint import move_to_sprint

        # Step 1: Get current backlog
        mock_jira_client.get_board_backlog.return_value = {
            'issues': [
                {'key': 'PROJ-10', 'fields': {'summary': 'Feature A', STORY_POINTS_FIELD: None}},
                {'key': 'PROJ-11', 'fields': {'summary': 'Feature B', STORY_POINTS_FIELD: None}},
                {'key': 'PROJ-12', 'fields': {'summary': 'Feature C', STORY_POINTS_FIELD: 5}},
            ],
            'total': 3
        }

        backlog = get_backlog(board_id=123, client=mock_jira_client)
        assert len(backlog['issues']) == 3

        # Step 2: Reorder - move PROJ-11 before PROJ-10 (to top)
        mock_jira_client.rank_issues.return_value = None

        rank_result = rank_issue(
            issue_keys=['PROJ-11'],
            before_key='PROJ-10',
            client=mock_jira_client
        )
        assert rank_result['ranked'] == 1

        # Step 3: Estimate unestimated issues
        mock_jira_client.update_issue.return_value = None

        for key in ['PROJ-10', 'PROJ-11']:
            estimate_issue(
                issue_keys=[key],
                points=3,
                client=mock_jira_client
            )

        # Step 4: Move top 2 to sprint
        mock_jira_client.move_issues_to_sprint.return_value = None

        move_result = move_to_sprint(
            sprint_id=456,
            issue_keys=['PROJ-11', 'PROJ-10'],
            client=mock_jira_client
        )
        assert move_result['moved'] == 2


@pytest.mark.agile
@pytest.mark.integration
class TestEpicProgressTracking:
    """
    Test workflow: Create epic with children → Track progress → Get estimates

    This tests epic-level progress tracking:
    1. Create epic
    2. Add multiple issues
    3. Set estimates on issues
    4. Track epic progress
    5. Get estimation summary
    """

    def test_epic_progress_workflow(self, mock_jira_client):
        """Test epic progress tracking workflow."""
        from create_epic import create_epic
        from add_to_epic import add_to_epic
        from estimate_issue import estimate_issue
        from get_epic import get_epic
        from get_estimates import get_estimates

        # Step 1: Create epic
        mock_jira_client.create_issue.return_value = {
            'id': '10001',
            'key': 'PROJ-100'
        }

        epic = create_epic(
            project='PROJ',
            summary='User Authentication',
            epic_name='Auth',
            client=mock_jira_client
        )

        # Step 2: Add issues to epic
        # Mock get_issue to return epic info for validation
        mock_jira_client.get_issue.return_value = {
            'key': 'PROJ-100',
            'fields': {
                'issuetype': {'name': 'Epic'},
                'summary': 'User Authentication'
            }
        }
        mock_jira_client.update_issue.return_value = None

        add_to_epic(
            epic_key='PROJ-100',
            issue_keys=['PROJ-101', 'PROJ-102', 'PROJ-103'],
            client=mock_jira_client
        )

        # Step 3: Set estimates
        for key, points in [('PROJ-101', 5), ('PROJ-102', 8), ('PROJ-103', 3)]:
            estimate_issue(
                issue_keys=[key],
                points=points,
                client=mock_jira_client
            )

        # Step 4: Get epic progress
        mock_jira_client.get_issue.return_value = {
            'key': 'PROJ-100',
            'fields': {
                'summary': 'User Authentication',
                'status': {'name': 'In Progress'}
            }
        }
        mock_jira_client.search_issues.return_value = {
            'issues': [
                {'key': 'PROJ-101', 'fields': {STORY_POINTS_FIELD: 5, 'status': {'name': 'Done'}}},
                {'key': 'PROJ-102', 'fields': {STORY_POINTS_FIELD: 8, 'status': {'name': 'In Progress'}}},
                {'key': 'PROJ-103', 'fields': {STORY_POINTS_FIELD: 3, 'status': {'name': 'To Do'}}},
            ],
            'total': 3
        }

        epic_details = get_epic(
            epic_key='PROJ-100',
            with_children=True,
            client=mock_jira_client
        )
        assert epic_details['progress']['total'] == 3
        assert epic_details['progress']['done'] == 1

        # Step 5: Get estimation summary
        estimates = get_estimates(
            epic_key='PROJ-100',
            client=mock_jira_client
        )
        assert estimates['total_points'] == 16  # 5 + 8 + 3
        assert estimates['by_status']['Done'] == 5
