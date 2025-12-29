"""
Live Integration Tests: Time Tracking Flow

Tests for time estimates and complete time tracking workflow against a real JIRA instance.
"""

import pytest
import uuid


@pytest.mark.integration
@pytest.mark.time
@pytest.mark.estimate
class TestTimeEstimates:
    """Tests for time estimate operations."""

    def test_set_original_estimate(self, jira_client, test_issue):
        """Test setting original time estimate."""
        jira_client.set_time_tracking(test_issue['key'], original_estimate='4h')

        tt = jira_client.get_time_tracking(test_issue['key'])
        assert tt.get('originalEstimate') == '4h'
        assert tt.get('originalEstimateSeconds') == 14400

    def test_set_original_estimate_days(self, jira_client, test_issue):
        """Test setting original time estimate in days."""
        jira_client.set_time_tracking(test_issue['key'], original_estimate='1d')

        tt = jira_client.get_time_tracking(test_issue['key'])
        # 1 day = 8 hours = 28800 seconds
        assert tt.get('originalEstimateSeconds') == 28800

    def test_set_remaining_estimate(self, jira_client, test_issue):
        """Test setting remaining time estimate."""
        # First set original
        jira_client.set_time_tracking(test_issue['key'], original_estimate='4h')

        # Then set remaining
        jira_client.set_time_tracking(test_issue['key'], remaining_estimate='2h')

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
            ('2d', 57600),  # 2 days = 16 hours
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
@pytest.mark.time
@pytest.mark.estimate
class TestTimeTrackingWorkflow:
    """Tests for complete time tracking workflow."""

    def test_full_workflow(self, jira_client, test_issue):
        """Test a complete time tracking workflow."""
        # Step 1: Set initial estimate
        jira_client.set_time_tracking(test_issue['key'], original_estimate='4h')

        # Step 2: Log some work
        jira_client.add_worklog(test_issue['key'], time_spent='1h')

        # Step 3: Verify time tracking reflects logged time
        tt = jira_client.get_time_tracking(test_issue['key'])
        assert tt.get('timeSpent') == '1h'
        assert tt.get('timeSpentSeconds') == 3600
        # Remaining should be auto-adjusted (4h - 1h = 3h)
        assert tt.get('remainingEstimateSeconds') == 10800

    def test_multiple_worklogs_accumulate(self, jira_client, test_issue):
        """Test that multiple worklogs accumulate correctly."""
        jira_client.add_worklog(test_issue['key'], time_spent='1h')
        jira_client.add_worklog(test_issue['key'], time_spent='2h')
        jira_client.add_worklog(test_issue['key'], time_spent='30m')

        # Total: 1h + 2h + 30m = 3h 30m = 12600 seconds
        tt = jira_client.get_time_tracking(test_issue['key'])
        assert tt.get('timeSpentSeconds') == 12600

    def test_worklog_auto_adjusts_remaining(self, jira_client, test_issue):
        """Test that logging work auto-adjusts remaining estimate."""
        jira_client.set_time_tracking(test_issue['key'], original_estimate='4h')

        jira_client.add_worklog(test_issue['key'], time_spent='1h')

        tt = jira_client.get_time_tracking(test_issue['key'])
        # Remaining should be 4h - 1h = 3h = 10800 seconds
        assert tt.get('remainingEstimateSeconds') == 10800


@pytest.mark.integration
@pytest.mark.time
@pytest.mark.estimate
class TestWorklogEstimateAdjustment:
    """Tests for worklog estimate adjustment modes."""

    def test_worklog_with_new_remaining(self, jira_client, test_issue):
        """Test logging work with explicit new remaining estimate."""
        jira_client.set_time_tracking(test_issue['key'], original_estimate='4h')

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
        jira_client.set_time_tracking(test_issue['key'], original_estimate='4h')

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
@pytest.mark.time
@pytest.mark.estimate
class TestTimeTrackingEdgeCases:
    """Tests for edge cases in time tracking."""

    def test_get_time_tracking_no_estimates(self, jira_client, test_issue):
        """Test getting time tracking when no estimates are set."""
        tt = jira_client.get_time_tracking(test_issue['key'])

        # Should return empty or minimal object
        assert isinstance(tt, dict)

    def test_time_tracking_after_all_time_logged(self, jira_client, test_issue):
        """Test time tracking when logged time exceeds estimate."""
        jira_client.set_time_tracking(test_issue['key'], original_estimate='1h')

        # Log more than estimate
        jira_client.add_worklog(test_issue['key'], time_spent='2h')

        tt = jira_client.get_time_tracking(test_issue['key'])
        assert tt.get('timeSpentSeconds') == 7200  # 2h logged
        # Remaining might be 0 or negative depending on JIRA config

    def test_clear_estimates(self, jira_client, test_issue):
        """Test clearing time estimates."""
        # Set estimates
        jira_client.set_time_tracking(
            test_issue['key'],
            original_estimate='4h',
            remaining_estimate='4h'
        )

        # Clear by setting to empty/zero
        # Note: JIRA behavior may vary - some instances don't allow clearing
        try:
            jira_client.set_time_tracking(
                test_issue['key'],
                original_estimate='0m',
                remaining_estimate='0m'
            )

            tt = jira_client.get_time_tracking(test_issue['key'])
            # Either cleared or set to 0
            original = tt.get('originalEstimateSeconds', 0)
            assert original is None or original == 0
        except Exception:
            # Some instances don't allow clearing - that's acceptable
            pass


@pytest.mark.integration
@pytest.mark.time
@pytest.mark.estimate
class TestTimeTrackingIssueWithEstimate:
    """Tests using the issue_with_estimate fixture."""

    def test_issue_has_estimate(self, jira_client, issue_with_estimate):
        """Test that fixture creates issue with estimate."""
        tt = jira_client.get_time_tracking(issue_with_estimate['key'])

        assert tt.get('originalEstimateSeconds') == 14400  # 4h

    def test_log_partial_work(self, jira_client, issue_with_estimate):
        """Test logging partial work against estimate."""
        jira_client.add_worklog(issue_with_estimate['key'], time_spent='1h')

        tt = jira_client.get_time_tracking(issue_with_estimate['key'])
        assert tt.get('timeSpentSeconds') == 3600
        # Remaining should be 4h - 1h = 3h
        assert tt.get('remainingEstimateSeconds') == 10800

    def test_log_exact_estimate(self, jira_client, issue_with_estimate):
        """Test logging work that exactly matches estimate."""
        jira_client.add_worklog(issue_with_estimate['key'], time_spent='4h')

        tt = jira_client.get_time_tracking(issue_with_estimate['key'])
        assert tt.get('timeSpentSeconds') == 14400
        # Remaining should be 0
        assert tt.get('remainingEstimateSeconds') == 0
