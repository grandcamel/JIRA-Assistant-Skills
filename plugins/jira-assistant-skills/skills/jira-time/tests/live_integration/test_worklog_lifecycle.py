"""
Live Integration Tests: Worklog Lifecycle

Tests for complete worklog lifecycle (add, get, update, delete) against a real JIRA instance.
"""

import pytest
import uuid
from datetime import datetime, timedelta


def make_adf_comment(text: str) -> dict:
    """Create an ADF-formatted comment."""
    return {
        'type': 'doc',
        'version': 1,
        'content': [{
            'type': 'paragraph',
            'content': [{'type': 'text', 'text': text}]
        }]
    }


@pytest.mark.integration
@pytest.mark.time
@pytest.mark.worklog
class TestWorklogCreation:
    """Tests for creating worklogs."""

    def test_add_simple_worklog(self, jira_client, test_issue):
        """Test adding a basic worklog entry."""
        result = jira_client.add_worklog(
            test_issue['key'],
            time_spent='1h'
        )

        assert 'id' in result
        assert result['timeSpent'] == '1h'
        assert result['timeSpentSeconds'] == 3600

    def test_add_worklog_with_comment(self, jira_client, test_issue):
        """Test adding a worklog with a comment."""
        comment = make_adf_comment(f'Worklog comment {uuid.uuid4().hex[:8]}')
        result = jira_client.add_worklog(
            test_issue['key'],
            time_spent='30m',
            comment=comment
        )

        assert 'id' in result
        assert result['timeSpent'] == '30m'
        assert 'comment' in result

    def test_add_worklog_with_date(self, jira_client, test_issue):
        """Test adding a worklog with specific started date."""
        yesterday = datetime.now() - timedelta(days=1)
        started = yesterday.strftime('%Y-%m-%dT09:00:00.000+0000')

        result = jira_client.add_worklog(
            test_issue['key'],
            time_spent='2h',
            started=started
        )

        assert 'id' in result
        assert result['timeSpent'] == '2h'
        assert yesterday.strftime('%Y-%m-%d') in result['started']

    def test_add_worklog_various_formats(self, jira_client, test_issue):
        """Test adding worklogs with various time formats."""
        test_cases = [
            ('30m', 1800),
            ('1h 30m', 5400),
            ('2h', 7200),
        ]

        for time_spent, expected_seconds in test_cases:
            result = jira_client.add_worklog(
                test_issue['key'],
                time_spent=time_spent
            )

            assert result['timeSpentSeconds'] == expected_seconds, f"Failed for {time_spent}"


@pytest.mark.integration
@pytest.mark.time
@pytest.mark.worklog
class TestWorklogRetrieval:
    """Tests for retrieving worklogs."""

    def test_get_all_worklogs(self, jira_client, issue_with_worklog):
        """Test getting all worklogs from an issue."""
        result = jira_client.get_worklogs(issue_with_worklog['key'])

        assert 'worklogs' in result
        assert result['total'] >= 1
        assert len(result['worklogs']) >= 1

    def test_get_single_worklog(self, jira_client, issue_with_worklog):
        """Test getting a specific worklog by ID."""
        worklog_id = issue_with_worklog['worklog_id']

        worklog = jira_client.get_worklog(issue_with_worklog['key'], worklog_id)

        assert worklog['id'] == worklog_id
        assert 'timeSpent' in worklog

    def test_get_worklogs_pagination(self, jira_client, test_issue):
        """Test paginating through worklogs."""
        # Add multiple worklogs
        for _ in range(5):
            jira_client.add_worklog(test_issue['key'], time_spent='15m')

        # Get first page
        page1 = jira_client.get_worklogs(test_issue['key'], start_at=0, max_results=2)
        assert len(page1['worklogs']) == 2

        # Get second page
        page2 = jira_client.get_worklogs(test_issue['key'], start_at=2, max_results=2)
        assert len(page2['worklogs']) == 2

        # Verify different worklogs
        page1_ids = {w['id'] for w in page1['worklogs']}
        page2_ids = {w['id'] for w in page2['worklogs']}
        assert page1_ids.isdisjoint(page2_ids)

    def test_get_worklogs_empty_issue(self, jira_client, test_project):
        """Test getting worklogs from issue with none."""
        issue = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Empty Worklogs Test {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Task'}
        })

        try:
            result = jira_client.get_worklogs(issue['key'])

            assert 'worklogs' in result
            assert result['total'] == 0
            assert len(result['worklogs']) == 0
        finally:
            jira_client.delete_issue(issue['key'])


@pytest.mark.integration
@pytest.mark.time
@pytest.mark.worklog
class TestWorklogUpdate:
    """Tests for updating worklogs."""

    def test_update_worklog_time(self, jira_client, issue_with_worklog):
        """Test updating a worklog's time spent."""
        worklog_id = issue_with_worklog['worklog_id']

        updated = jira_client.update_worklog(
            issue_with_worklog['key'],
            worklog_id,
            time_spent='2h'
        )

        assert updated['timeSpent'] == '2h'
        assert updated['timeSpentSeconds'] == 7200

    def test_update_worklog_preserves_started(self, jira_client, issue_with_worklog):
        """Test that updating a worklog preserves the started date."""
        worklog_id = issue_with_worklog['worklog_id']

        original = jira_client.get_worklog(issue_with_worklog['key'], worklog_id)
        original_started = original['started']

        updated = jira_client.update_worklog(
            issue_with_worklog['key'],
            worklog_id,
            time_spent='2h'
        )

        assert updated['started'] == original_started

    def test_update_worklog_with_comment(self, jira_client, issue_with_worklog):
        """Test updating a worklog with a new comment."""
        worklog_id = issue_with_worklog['worklog_id']
        comment = make_adf_comment('Updated worklog comment')

        updated = jira_client.update_worklog(
            issue_with_worklog['key'],
            worklog_id,
            comment=comment
        )

        assert 'comment' in updated


@pytest.mark.integration
@pytest.mark.time
@pytest.mark.worklog
class TestWorklogDeletion:
    """Tests for deleting worklogs."""

    def test_delete_worklog(self, jira_client, test_issue):
        """Test deleting a worklog."""
        # Create worklog
        created = jira_client.add_worklog(test_issue['key'], time_spent='30m')
        worklog_id = created['id']

        # Delete worklog
        jira_client.delete_worklog(test_issue['key'], worklog_id)

        # Verify it's gone
        from jira_assistant_skills_lib import NotFoundError
        with pytest.raises(NotFoundError):
            jira_client.get_worklog(test_issue['key'], worklog_id)

    def test_delete_worklog_updates_total(self, jira_client, test_issue):
        """Test that deleting a worklog updates the total time."""
        # Add two worklogs
        wl1 = jira_client.add_worklog(test_issue['key'], time_spent='1h')
        wl2 = jira_client.add_worklog(test_issue['key'], time_spent='1h')

        # Get initial time tracking
        initial_tt = jira_client.get_time_tracking(test_issue['key'])
        initial_spent = initial_tt.get('timeSpentSeconds', 0)

        # Delete one worklog
        jira_client.delete_worklog(test_issue['key'], wl1['id'])

        # Verify time decreased
        final_tt = jira_client.get_time_tracking(test_issue['key'])
        final_spent = final_tt.get('timeSpentSeconds', 0)

        assert final_spent == initial_spent - 3600


@pytest.mark.integration
@pytest.mark.time
@pytest.mark.worklog
class TestWorklogMetadata:
    """Tests for worklog metadata."""

    def test_worklog_has_author(self, jira_client, test_issue):
        """Test that worklogs have author information."""
        result = jira_client.add_worklog(test_issue['key'], time_spent='30m')

        assert 'author' in result
        assert 'accountId' in result['author']

    def test_worklog_has_timestamps(self, jira_client, test_issue):
        """Test that worklogs have created and updated timestamps."""
        result = jira_client.add_worklog(test_issue['key'], time_spent='30m')

        assert 'created' in result
        assert 'updated' in result
        assert 'started' in result

    def test_worklog_started_defaults_to_now(self, jira_client, test_issue):
        """Test that worklog started date defaults to current time."""
        today = datetime.now().strftime('%Y-%m-%d')

        result = jira_client.add_worklog(test_issue['key'], time_spent='30m')

        assert today in result['started']
