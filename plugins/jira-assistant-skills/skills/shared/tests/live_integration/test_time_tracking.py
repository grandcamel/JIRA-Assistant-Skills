"""
Live Integration Tests: Time Tracking

Tests for worklog operations, time estimates, and time tracking against a real JIRA instance.

Note: Worklog comments require ADF format. These tests omit comments for simplicity,
as the API accepts worklogs without comments.
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
@pytest.mark.shared
class TestWorklogs:
    """Tests for worklog operations."""

    def test_add_worklog(self, jira_client, test_issue):
        """Test adding a worklog entry."""
        result = jira_client.add_worklog(
            test_issue['key'],
            time_spent='1h'
        )

        assert 'id' in result
        assert result['timeSpent'] == '1h'
        assert result['timeSpentSeconds'] == 3600

    def test_add_worklog_with_comment(self, jira_client, test_issue):
        """Test adding a worklog with an ADF comment."""
        comment = make_adf_comment(f'Test worklog {uuid.uuid4().hex[:8]}')
        result = jira_client.add_worklog(
            test_issue['key'],
            time_spent='30m',
            comment=comment
        )

        assert 'id' in result
        assert result['timeSpent'] == '30m'
        assert 'comment' in result

    def test_add_worklog_with_date(self, jira_client, test_issue):
        """Test adding a worklog with a specific started date."""
        # Use yesterday's date
        yesterday = datetime.now() - timedelta(days=1)
        started = yesterday.strftime('%Y-%m-%dT09:00:00.000+0000')

        result = jira_client.add_worklog(
            test_issue['key'],
            time_spent='2h',
            started=started
        )

        assert 'id' in result
        assert result['timeSpent'] == '2h'
        assert result['timeSpentSeconds'] == 7200
        # Started date should reflect yesterday
        assert yesterday.strftime('%Y-%m-%d') in result['started']

    def test_add_worklog_with_different_formats(self, jira_client, test_issue):
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

    def test_get_worklogs(self, jira_client, test_issue):
        """Test getting worklogs from an issue."""
        # Add a worklog first
        jira_client.add_worklog(
            test_issue['key'],
            time_spent='1h'
        )

        # Get worklogs
        result = jira_client.get_worklogs(test_issue['key'])

        assert 'worklogs' in result
        assert result['total'] >= 1
        assert len(result['worklogs']) >= 1

    def test_get_single_worklog(self, jira_client, test_issue):
        """Test getting a specific worklog."""
        # Add a worklog
        created = jira_client.add_worklog(
            test_issue['key'],
            time_spent='45m'
        )
        worklog_id = created['id']

        # Get the specific worklog
        worklog = jira_client.get_worklog(test_issue['key'], worklog_id)

        assert worklog['id'] == worklog_id
        assert worklog['timeSpent'] == '45m'

    def test_update_worklog(self, jira_client, test_issue):
        """Test updating a worklog."""
        # Create worklog
        created = jira_client.add_worklog(
            test_issue['key'],
            time_spent='1h'
        )
        worklog_id = created['id']

        # Update worklog
        updated = jira_client.update_worklog(
            test_issue['key'],
            worklog_id,
            time_spent='2h'
        )

        assert updated['timeSpent'] == '2h'
        assert updated['timeSpentSeconds'] == 7200

    def test_delete_worklog(self, jira_client, test_issue):
        """Test deleting a worklog."""
        # Create worklog
        created = jira_client.add_worklog(
            test_issue['key'],
            time_spent='30m'
        )
        worklog_id = created['id']

        # Delete worklog
        jira_client.delete_worklog(test_issue['key'], worklog_id)

        # Verify it's gone
        from jira_assistant_skills_lib import NotFoundError
        with pytest.raises(NotFoundError):
            jira_client.get_worklog(test_issue['key'], worklog_id)


@pytest.mark.integration
@pytest.mark.shared
class TestTimeEstimates:
    """Tests for time estimate operations."""

    def test_set_original_estimate(self, jira_client, test_issue):
        """Test setting original time estimate."""
        jira_client.set_time_tracking(
            test_issue['key'],
            original_estimate='4h'
        )

        # Verify
        tt = jira_client.get_time_tracking(test_issue['key'])
        assert tt.get('originalEstimate') == '4h'
        assert tt.get('originalEstimateSeconds') == 14400

    def test_set_original_estimate_days(self, jira_client, test_issue):
        """Test setting original time estimate in days."""
        # JIRA normalizes 8h to 1d (1 working day = 8 hours)
        jira_client.set_time_tracking(
            test_issue['key'],
            original_estimate='1d'
        )

        tt = jira_client.get_time_tracking(test_issue['key'])
        # Should be 1d = 8 hours = 28800 seconds
        assert tt.get('originalEstimateSeconds') == 28800
        # Display format may be '1d' or '8h' depending on settings
        assert tt.get('originalEstimate') in ['1d', '8h']

    def test_set_remaining_estimate(self, jira_client, test_issue):
        """Test setting remaining time estimate."""
        # First set original
        jira_client.set_time_tracking(
            test_issue['key'],
            original_estimate='4h'
        )

        # Then set remaining
        jira_client.set_time_tracking(
            test_issue['key'],
            remaining_estimate='2h'
        )

        # Verify
        tt = jira_client.get_time_tracking(test_issue['key'])
        assert tt.get('remainingEstimate') == '2h'
        assert tt.get('remainingEstimateSeconds') == 7200

    def test_set_both_estimates(self, jira_client, test_issue):
        """Test setting both original and remaining estimates."""
        jira_client.set_time_tracking(
            test_issue['key'],
            original_estimate='2d',
            remaining_estimate='1d'
        )

        tt = jira_client.get_time_tracking(test_issue['key'])
        # 2d = 16h = 57600 seconds
        assert tt.get('originalEstimateSeconds') == 57600
        # 1d = 8h = 28800 seconds
        assert tt.get('remainingEstimateSeconds') == 28800

    def test_estimate_formats(self, jira_client, test_issue):
        """Test various estimate formats."""
        test_cases = [
            ('2d', 57600),  # 2 days = 16 hours = 57600 seconds (8h work day)
            ('4h', 14400),
            ('30m', 1800),
        ]

        for estimate, expected_seconds in test_cases:
            jira_client.set_time_tracking(
                test_issue['key'],
                original_estimate=estimate
            )

            tt = jira_client.get_time_tracking(test_issue['key'])
            assert tt.get('originalEstimateSeconds') == expected_seconds, f"Failed for {estimate}"


@pytest.mark.integration
@pytest.mark.shared
class TestTimeTrackingWorkflow:
    """Tests for complete time tracking workflow."""

    def test_full_time_tracking_workflow(self, jira_client, test_issue):
        """Test a complete time tracking workflow."""
        # Step 1: Set initial estimate
        jira_client.set_time_tracking(
            test_issue['key'],
            original_estimate='4h'
        )

        # Step 2: Log some work
        jira_client.add_worklog(
            test_issue['key'],
            time_spent='1h'
        )

        # Step 3: Verify time tracking reflects logged time
        tt = jira_client.get_time_tracking(test_issue['key'])
        assert tt.get('timeSpent') == '1h'
        assert tt.get('timeSpentSeconds') == 3600
        # Remaining should be auto-adjusted (4h - 1h = 3h)
        assert tt.get('remainingEstimateSeconds') == 10800

    def test_multiple_worklogs_accumulate(self, jira_client, test_issue):
        """Test that multiple worklogs accumulate correctly."""
        # Log multiple entries
        jira_client.add_worklog(test_issue['key'], time_spent='1h')
        jira_client.add_worklog(test_issue['key'], time_spent='2h')
        jira_client.add_worklog(test_issue['key'], time_spent='30m')

        # Verify total (1h + 2h + 30m = 3h 30m = 12600 seconds)
        tt = jira_client.get_time_tracking(test_issue['key'])
        assert tt.get('timeSpentSeconds') == 12600

    def test_worklog_with_auto_adjust(self, jira_client, test_issue):
        """Test that logging work auto-adjusts remaining estimate."""
        # Set original estimate
        jira_client.set_time_tracking(test_issue['key'], original_estimate='4h')

        # Log work with auto-adjust (default behavior)
        jira_client.add_worklog(
            test_issue['key'],
            time_spent='1h'
        )

        tt = jira_client.get_time_tracking(test_issue['key'])
        # Remaining should be 4h - 1h = 3h = 10800 seconds
        assert tt.get('remainingEstimateSeconds') == 10800

    def test_worklog_with_new_remaining(self, jira_client, test_issue):
        """Test logging work with explicit new remaining estimate."""
        # Set original estimate
        jira_client.set_time_tracking(test_issue['key'], original_estimate='4h')

        # Log work with explicit remaining
        jira_client.add_worklog(
            test_issue['key'],
            time_spent='1h',
            adjust_estimate='new',
            new_estimate='2h'
        )

        tt = jira_client.get_time_tracking(test_issue['key'])
        assert tt.get('timeSpentSeconds') == 3600  # 1h logged
        assert tt.get('remainingEstimateSeconds') == 7200  # 2h remaining (explicit)

    def test_worklog_leave_estimate(self, jira_client, test_issue):
        """Test logging work without adjusting estimate."""
        # Set original estimate
        jira_client.set_time_tracking(test_issue['key'], original_estimate='4h')

        # Log work with 'leave' - don't adjust remaining
        jira_client.add_worklog(
            test_issue['key'],
            time_spent='1h',
            adjust_estimate='leave'
        )

        tt = jira_client.get_time_tracking(test_issue['key'])
        assert tt.get('timeSpentSeconds') == 3600  # 1h logged
        # Remaining should still be 4h (not adjusted)
        assert tt.get('remainingEstimateSeconds') == 14400


@pytest.mark.integration
@pytest.mark.shared
class TestTimeTrackingEdgeCases:
    """Tests for edge cases in time tracking."""

    def test_get_time_tracking_no_estimates(self, jira_client, test_issue):
        """Test getting time tracking when no estimates are set."""
        tt = jira_client.get_time_tracking(test_issue['key'])

        # Should return empty or minimal object
        assert isinstance(tt, dict)

    def test_worklog_pagination(self, jira_client, test_issue):
        """Test paginating through worklogs."""
        # Add several worklogs
        for i in range(5):
            jira_client.add_worklog(
                test_issue['key'],
                time_spent='15m'
            )

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

    def test_update_worklog_preserve_started(self, jira_client, test_issue):
        """Test that updating a worklog preserves the started date."""
        # Create worklog
        created = jira_client.add_worklog(
            test_issue['key'],
            time_spent='1h'
        )
        worklog_id = created['id']
        original_started = created['started']

        # Update only the time
        updated = jira_client.update_worklog(
            test_issue['key'],
            worklog_id,
            time_spent='2h'
        )

        # Started date should be preserved
        assert updated['started'] == original_started
        assert updated['timeSpent'] == '2h'

    def test_update_worklog_with_comment(self, jira_client, test_issue):
        """Test updating a worklog with a new comment."""
        # Create worklog without comment
        created = jira_client.add_worklog(
            test_issue['key'],
            time_spent='1h'
        )
        worklog_id = created['id']

        # Update with comment
        comment = make_adf_comment('Added comment on update')
        updated = jira_client.update_worklog(
            test_issue['key'],
            worklog_id,
            comment=comment
        )

        assert 'comment' in updated
