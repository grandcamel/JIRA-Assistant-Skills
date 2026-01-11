"""Tests for time tracking commands."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from jira_assistant_skills.cli.commands.time_cmds import (
    _add_worklog_impl,
    _bulk_log_time_impl,
    _calculate_progress,
    _delete_worklog_impl,
    _export_timesheets_impl,
    _extract_comment_text,
    _format_bulk_log_result,
    _format_estimate_updated,
    _format_export_csv,
    _format_report_csv,
    _format_report_text,
    _format_time_tracking,
    _format_worklog_added,
    _format_worklog_deleted,
    _format_worklog_updated,
    _format_worklogs,
    _generate_progress_bar,
    _generate_report_impl,
    _get_time_tracking_impl,
    _get_worklogs_impl,
    _group_entries,
    _resolve_period_dates,
    _set_estimate_impl,
    _update_worklog_impl,
    time,
)
from jira_assistant_skills_lib import ValidationError


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_worklog():
    """Sample worklog response."""
    return {
        "id": "12345",
        "author": {
            "accountId": "abc123",
            "displayName": "John Doe",
            "emailAddress": "john@example.com",
        },
        "timeSpent": "2h",
        "timeSpentSeconds": 7200,
        "started": "2025-01-15T09:00:00.000+0000",
        "comment": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Working on bug fix"}],
                }
            ],
        },
        "updated": "2025-01-15T11:00:00.000+0000",
    }


@pytest.fixture
def sample_worklogs_response(sample_worklog):
    """Sample worklogs list response."""
    return {
        "worklogs": [
            sample_worklog,
            {
                "id": "12346",
                "author": {
                    "accountId": "def456",
                    "displayName": "Jane Smith",
                    "emailAddress": "jane@example.com",
                },
                "timeSpent": "4h",
                "timeSpentSeconds": 14400,
                "started": "2025-01-15T14:00:00.000+0000",
                "comment": {},
            },
        ],
        "startAt": 0,
        "maxResults": 50,
        "total": 2,
    }


@pytest.fixture
def sample_time_tracking():
    """Sample time tracking response."""
    return {
        "originalEstimate": "2d",
        "originalEstimateSeconds": 57600,
        "remainingEstimate": "1d 4h",
        "remainingEstimateSeconds": 43200,
        "timeSpent": "4h",
        "timeSpentSeconds": 14400,
    }


@pytest.fixture
def sample_report_entries():
    """Sample report entries."""
    return [
        {
            "issue_key": "PROJ-123",
            "issue_summary": "Fix login bug",
            "worklog_id": "12345",
            "author": "John Doe",
            "author_email": "john@example.com",
            "started": "2025-01-15T09:00:00.000+0000",
            "started_date": "2025-01-15",
            "time_spent": "2h",
            "time_seconds": 7200,
        },
        {
            "issue_key": "PROJ-124",
            "issue_summary": "Add new feature",
            "worklog_id": "12346",
            "author": "Jane Smith",
            "author_email": "jane@example.com",
            "started": "2025-01-15T14:00:00.000+0000",
            "started_date": "2025-01-15",
            "time_spent": "4h",
            "time_seconds": 14400,
        },
    ]


@pytest.fixture
def mock_client():
    """Create a mock JIRA client."""
    client = MagicMock()
    client.close = MagicMock()
    return client


# =============================================================================
# Helper Function Tests
# =============================================================================


class TestCalculateProgress:
    """Tests for _calculate_progress."""

    def test_with_progress(self):
        """Test progress calculation with time logged."""
        result = _calculate_progress({
            "originalEstimateSeconds": 100,
            "timeSpentSeconds": 50,
        })
        assert result == 50

    def test_no_estimate(self):
        """Test with no original estimate."""
        result = _calculate_progress({
            "timeSpentSeconds": 50,
        })
        assert result is None

    def test_no_time_spent(self):
        """Test with no time spent."""
        result = _calculate_progress({
            "originalEstimateSeconds": 100,
            "timeSpentSeconds": 0,
        })
        assert result == 0

    def test_over_100_percent(self):
        """Test capping at 100%."""
        result = _calculate_progress({
            "originalEstimateSeconds": 100,
            "timeSpentSeconds": 150,
        })
        assert result == 100


class TestGenerateProgressBar:
    """Tests for _generate_progress_bar."""

    def test_zero_progress(self):
        """Test with 0% progress."""
        result = _generate_progress_bar(0, width=10)
        assert result == "░" * 10

    def test_full_progress(self):
        """Test with 100% progress."""
        result = _generate_progress_bar(100, width=10)
        assert result == "█" * 10

    def test_half_progress(self):
        """Test with 50% progress."""
        result = _generate_progress_bar(50, width=10)
        assert result == "█████░░░░░"


class TestGroupEntries:
    """Tests for _group_entries."""

    def test_group_by_issue(self, sample_report_entries):
        """Test grouping by issue."""
        result = _group_entries(sample_report_entries, "issue")
        assert "PROJ-123" in result
        assert "PROJ-124" in result
        assert result["PROJ-123"]["total_seconds"] == 7200
        assert result["PROJ-124"]["total_seconds"] == 14400

    def test_group_by_day(self, sample_report_entries):
        """Test grouping by day."""
        result = _group_entries(sample_report_entries, "day")
        assert "2025-01-15" in result
        assert result["2025-01-15"]["total_seconds"] == 21600
        assert result["2025-01-15"]["entry_count"] == 2

    def test_group_by_user(self, sample_report_entries):
        """Test grouping by user."""
        result = _group_entries(sample_report_entries, "user")
        assert "John Doe" in result
        assert "Jane Smith" in result


class TestExtractCommentText:
    """Tests for _extract_comment_text."""

    def test_with_comment(self):
        """Test extracting text from ADF comment."""
        comment = {
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Hello "},
                        {"type": "text", "text": "World"},
                    ],
                }
            ]
        }
        result = _extract_comment_text(comment)
        assert result == "Hello  World"

    def test_empty_comment(self):
        """Test with empty comment."""
        result = _extract_comment_text({})
        assert result == ""

    def test_none_comment(self):
        """Test with None comment."""
        result = _extract_comment_text(None)
        assert result == ""


class TestResolvePeriodDates:
    """Tests for _resolve_period_dates."""

    def test_today(self):
        """Test 'today' period."""
        today = str(datetime.now().date())
        since, until = _resolve_period_dates("today")
        assert since == today
        assert until == today

    def test_yesterday(self):
        """Test 'yesterday' period."""
        yesterday = str(datetime.now().date() - timedelta(days=1))
        since, until = _resolve_period_dates("yesterday")
        assert since == yesterday
        assert until == yesterday

    def test_this_week(self):
        """Test 'this-week' period."""
        today = datetime.now().date()
        start = today - timedelta(days=today.weekday())
        since, until = _resolve_period_dates("this-week")
        assert since == str(start)
        assert until == str(today)

    def test_last_week(self):
        """Test 'last-week' period."""
        today = datetime.now().date()
        start = today - timedelta(days=today.weekday() + 7)
        end = start + timedelta(days=6)
        since, until = _resolve_period_dates("last-week")
        assert since == str(start)
        assert until == str(end)

    def test_this_month(self):
        """Test 'this-month' period."""
        today = datetime.now().date()
        since, until = _resolve_period_dates("this-month")
        assert since == str(today.replace(day=1))
        assert until == str(today)

    def test_last_month(self):
        """Test 'last-month' period."""
        today = datetime.now().date()
        first_of_month = today.replace(day=1)
        last_month_end = first_of_month - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        since, until = _resolve_period_dates("last-month")
        assert since == str(last_month_start)
        assert until == str(last_month_end)

    def test_year_month_format(self):
        """Test YYYY-MM format."""
        since, until = _resolve_period_dates("2025-01")
        assert since == "2025-01-01"
        assert until == "2025-01-31"

    def test_year_month_december(self):
        """Test December YYYY-MM format."""
        since, until = _resolve_period_dates("2025-12")
        assert since == "2025-12-01"
        assert until == "2025-12-31"

    def test_unknown_format(self):
        """Test unknown format returns as-is."""
        since, until = _resolve_period_dates("custom")
        assert since == "custom"
        assert until == "custom"


# =============================================================================
# Formatting Function Tests
# =============================================================================


class TestFormatWorklogAdded:
    """Tests for _format_worklog_added."""

    def test_basic_format(self, sample_worklog):
        """Test basic worklog added formatting."""
        result = _format_worklog_added(sample_worklog, "PROJ-123")
        assert "Worklog added to PROJ-123" in result
        assert "Worklog ID: 12345" in result
        assert "Time logged: 2h" in result

    def test_with_comment(self, sample_worklog):
        """Test formatting with comment."""
        result = _format_worklog_added(sample_worklog, "PROJ-123")
        assert "Comment: Working on bug fix" in result

    def test_with_visibility(self):
        """Test formatting with visibility."""
        worklog = {
            "id": "12345",
            "timeSpent": "2h",
            "timeSpentSeconds": 7200,
            "visibility": {"type": "role", "value": "Developers"},
        }
        result = _format_worklog_added(worklog, "PROJ-123")
        assert "Visibility: role = Developers" in result


class TestFormatWorklogs:
    """Tests for _format_worklogs."""

    def test_with_worklogs(self, sample_worklogs_response):
        """Test formatting worklogs list."""
        result = _format_worklogs(sample_worklogs_response, "PROJ-123")
        assert "Worklogs for PROJ-123" in result
        assert "12345" in result
        assert "John Doe" in result
        assert "Total:" in result

    def test_empty_worklogs(self):
        """Test formatting empty worklogs."""
        result = _format_worklogs({"worklogs": []}, "PROJ-123")
        assert "No worklogs found" in result


class TestFormatWorklogUpdated:
    """Tests for _format_worklog_updated."""

    def test_basic_format(self, sample_worklog):
        """Test basic worklog updated formatting."""
        result = _format_worklog_updated(sample_worklog, "12345", "PROJ-123")
        assert "Worklog 12345 updated on PROJ-123" in result
        assert "Time logged: 2h" in result
        assert "Updated:" in result


class TestFormatWorklogDeleted:
    """Tests for _format_worklog_deleted."""

    def test_dry_run(self, sample_worklog):
        """Test dry-run formatting."""
        result = _format_worklog_deleted(
            {"dry_run": True, "worklog": sample_worklog, "deleted": False},
            "12345",
            "PROJ-123",
        )
        assert "Dry-run mode" in result
        assert "would be deleted" in result
        assert "Run without --dry-run" in result

    def test_deleted(self, sample_worklog):
        """Test deleted formatting."""
        result = _format_worklog_deleted(
            {"dry_run": False, "worklog": sample_worklog, "deleted": True},
            "12345",
            "PROJ-123",
        )
        assert "Deleted worklog 12345" in result
        assert "Time removed:" in result


class TestFormatEstimateUpdated:
    """Tests for _format_estimate_updated."""

    def test_original_updated(self):
        """Test formatting when original estimate updated."""
        result = _format_estimate_updated(
            {
                "previous": {"originalEstimate": "1d"},
                "current": {"originalEstimate": "2d"},
            },
            "PROJ-123",
            updated_original=True,
            updated_remaining=False,
        )
        assert "Original estimate: 2d (was 1d)" in result

    def test_remaining_updated(self):
        """Test formatting when remaining estimate updated."""
        result = _format_estimate_updated(
            {
                "previous": {"remainingEstimate": "8h"},
                "current": {"remainingEstimate": "4h"},
            },
            "PROJ-123",
            updated_original=False,
            updated_remaining=True,
        )
        assert "Remaining estimate: 4h (was 8h)" in result


class TestFormatTimeTracking:
    """Tests for _format_time_tracking."""

    def test_with_progress(self, sample_time_tracking):
        """Test formatting with progress."""
        sample_time_tracking["progress"] = 25
        result = _format_time_tracking(sample_time_tracking, "PROJ-123")
        assert "Time Tracking for PROJ-123" in result
        assert "Original Estimate:" in result
        assert "Remaining Estimate:" in result
        assert "Time Spent:" in result
        assert "Progress:" in result
        assert "25% complete" in result

    def test_without_progress(self):
        """Test formatting without progress."""
        result = _format_time_tracking({"progress": None}, "PROJ-123")
        assert "Not set" in result


class TestFormatReportText:
    """Tests for _format_report_text."""

    def test_with_entries(self, sample_report_entries):
        """Test formatting report with entries."""
        report = {
            "entries": sample_report_entries,
            "entry_count": 2,
            "total_seconds": 21600,
            "total_formatted": "6h",
            "filters": {"project": "PROJ", "since": "2025-01-01", "until": "2025-01-31"},
        }
        result = _format_report_text(report)
        assert "Time Report: Project PROJ" in result
        assert "Total: 6h (2 entries)" in result

    def test_grouped_report(self, sample_report_entries):
        """Test formatting grouped report."""
        report = {
            "entries": sample_report_entries,
            "entry_count": 2,
            "total_seconds": 21600,
            "total_formatted": "6h",
            "filters": {},
            "grouped": {
                "PROJ-123": {"total_formatted": "2h", "entry_count": 1},
                "PROJ-124": {"total_formatted": "4h", "entry_count": 1},
            },
        }
        result = _format_report_text(report)
        assert "PROJ-123: 2h" in result
        assert "PROJ-124: 4h" in result


class TestFormatReportCsv:
    """Tests for _format_report_csv."""

    def test_csv_format(self, sample_report_entries):
        """Test CSV formatting."""
        report = {"entries": sample_report_entries}
        result = _format_report_csv(report)
        assert "Issue Key,Issue Summary,Author,Date,Time Spent,Seconds" in result
        assert "PROJ-123" in result
        assert "PROJ-124" in result


class TestFormatExportCsv:
    """Tests for _format_export_csv."""

    def test_export_csv(self):
        """Test export CSV formatting."""
        data = {
            "entries": [
                {
                    "issue_key": "PROJ-123",
                    "issue_summary": "Test",
                    "author": "John",
                    "author_email": "john@example.com",
                    "started_date": "2025-01-15",
                    "time_spent": "2h",
                    "time_seconds": 7200,
                    "comment": "Working on it",
                }
            ]
        }
        result = _format_export_csv(data)
        assert "Issue Key" in result
        assert "PROJ-123" in result
        assert "john@example.com" in result


class TestFormatBulkLogResult:
    """Tests for _format_bulk_log_result."""

    def test_dry_run(self):
        """Test dry-run formatting."""
        result = _format_bulk_log_result({
            "dry_run": True,
            "would_log_count": 3,
            "would_log_formatted": "1h 30m",
            "preview": [
                {"issue": "PROJ-1", "summary": "Task 1", "time_to_log": "30m"},
            ],
        })
        assert "Preview (dry-run)" in result
        assert "Would log 1h 30m" in result

    def test_completed(self):
        """Test completed formatting."""
        result = _format_bulk_log_result({
            "dry_run": False,
            "success_count": 3,
            "failure_count": 1,
            "total_formatted": "1h 30m",
            "failures": [{"issue": "PROJ-4", "error": "Not found"}],
        })
        assert "Bulk Time Logging Complete" in result
        assert "Successful: 3" in result
        assert "Failed: 1" in result
        assert "PROJ-4: Not found" in result


# =============================================================================
# Implementation Function Tests
# =============================================================================


class TestAddWorklogImpl:
    """Tests for _add_worklog_impl."""

    def test_add_worklog_success(self, mock_client, sample_worklog):
        """Test successful worklog addition."""
        mock_client.add_worklog.return_value = sample_worklog

        with patch("jira_assistant_skills.cli.commands.time_cmds.get_jira_client", return_value=mock_client):
            result = _add_worklog_impl("PROJ-123", "2h")

        assert result == sample_worklog
        mock_client.add_worklog.assert_called_once()
        mock_client.close.assert_called_once()

    def test_add_worklog_with_options(self, mock_client, sample_worklog):
        """Test worklog with all options."""
        mock_client.add_worklog.return_value = sample_worklog

        with patch("jira_assistant_skills.cli.commands.time_cmds.get_jira_client", return_value=mock_client):
            with patch("jira_assistant_skills.cli.commands.time_cmds.parse_relative_date") as mock_parse:
                mock_parse.return_value = datetime(2025, 1, 15, 9, 0)
                result = _add_worklog_impl(
                    "PROJ-123",
                    "2h",
                    started="2025-01-15",
                    comment="Test comment",
                    adjust_estimate="leave",
                    visibility_type="role",
                    visibility_value="Developers",
                )

        assert result == sample_worklog

    def test_empty_time_raises(self):
        """Test empty time raises validation error."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            _add_worklog_impl("PROJ-123", "")

    def test_invalid_time_format(self):
        """Test invalid time format raises validation error."""
        with pytest.raises(ValidationError, match="Invalid time format"):
            _add_worklog_impl("PROJ-123", "invalid")

    def test_visibility_type_without_value(self):
        """Test visibility type without value raises error."""
        with pytest.raises(ValidationError, match="visibility-value is required"):
            _add_worklog_impl("PROJ-123", "2h", visibility_type="role")

    def test_visibility_value_without_type(self):
        """Test visibility value without type raises error."""
        with pytest.raises(ValidationError, match="visibility-type is required"):
            _add_worklog_impl("PROJ-123", "2h", visibility_value="Developers")


class TestGetWorklogsImpl:
    """Tests for _get_worklogs_impl."""

    def test_get_worklogs_success(self, mock_client, sample_worklogs_response):
        """Test successful worklogs retrieval."""
        mock_client.get_worklogs.return_value = sample_worklogs_response

        with patch("jira_assistant_skills.cli.commands.time_cmds.get_jira_client", return_value=mock_client):
            result = _get_worklogs_impl("PROJ-123")

        assert result["total"] == 2
        mock_client.close.assert_called_once()

    def test_filter_by_author(self, mock_client, sample_worklogs_response):
        """Test filtering by author."""
        mock_client.get_worklogs.return_value = sample_worklogs_response

        with patch("jira_assistant_skills.cli.commands.time_cmds.get_jira_client", return_value=mock_client):
            result = _get_worklogs_impl("PROJ-123", author_filter="john@example.com")

        assert result["total"] == 1


class TestUpdateWorklogImpl:
    """Tests for _update_worklog_impl."""

    def test_update_worklog_success(self, mock_client, sample_worklog):
        """Test successful worklog update."""
        mock_client.update_worklog.return_value = sample_worklog

        with patch("jira_assistant_skills.cli.commands.time_cmds.get_jira_client", return_value=mock_client):
            result = _update_worklog_impl("PROJ-123", "12345", time_spent="3h")

        assert result == sample_worklog
        mock_client.close.assert_called_once()

    def test_no_updates_raises(self):
        """Test no updates raises validation error."""
        with pytest.raises(ValidationError, match="At least one of"):
            _update_worklog_impl("PROJ-123", "12345")


class TestDeleteWorklogImpl:
    """Tests for _delete_worklog_impl."""

    def test_delete_worklog_dry_run(self, mock_client, sample_worklog):
        """Test dry-run deletion."""
        mock_client.get_worklog.return_value = sample_worklog

        with patch("jira_assistant_skills.cli.commands.time_cmds.get_jira_client", return_value=mock_client):
            result = _delete_worklog_impl("PROJ-123", "12345", dry_run=True)

        assert result["dry_run"] is True
        assert result["deleted"] is False
        mock_client.delete_worklog.assert_not_called()

    def test_delete_worklog_actual(self, mock_client, sample_worklog):
        """Test actual deletion."""
        mock_client.get_worklog.return_value = sample_worklog
        mock_client.delete_worklog.return_value = None

        with patch("jira_assistant_skills.cli.commands.time_cmds.get_jira_client", return_value=mock_client):
            result = _delete_worklog_impl("PROJ-123", "12345")

        assert result["dry_run"] is False
        assert result["deleted"] is True
        mock_client.delete_worklog.assert_called_once()


class TestSetEstimateImpl:
    """Tests for _set_estimate_impl."""

    def test_set_estimate_success(self, mock_client, sample_time_tracking):
        """Test successful estimate setting."""
        mock_client.get_time_tracking.return_value = sample_time_tracking

        with patch("jira_assistant_skills.cli.commands.time_cmds.get_jira_client", return_value=mock_client):
            result = _set_estimate_impl("PROJ-123", original_estimate="2d")

        assert "previous" in result
        assert "current" in result
        mock_client.set_time_tracking.assert_called_once()

    def test_no_estimates_raises(self):
        """Test no estimates raises validation error."""
        with pytest.raises(ValidationError, match="At least one of"):
            _set_estimate_impl("PROJ-123")


class TestGetTimeTrackingImpl:
    """Tests for _get_time_tracking_impl."""

    def test_get_time_tracking(self, mock_client, sample_time_tracking):
        """Test getting time tracking info."""
        mock_client.get_time_tracking.return_value = sample_time_tracking

        with patch("jira_assistant_skills.cli.commands.time_cmds.get_jira_client", return_value=mock_client):
            result = _get_time_tracking_impl("PROJ-123")

        assert "progress" in result
        mock_client.close.assert_called_once()


class TestGenerateReportImpl:
    """Tests for _generate_report_impl."""

    def test_generate_report(self, mock_client):
        """Test report generation."""
        mock_client.search_issues.return_value = {
            "issues": [
                {"key": "PROJ-123", "fields": {"summary": "Test issue"}}
            ]
        }
        mock_client.get_worklogs.return_value = {
            "worklogs": [
                {
                    "id": "12345",
                    "author": {"displayName": "John", "emailAddress": "john@example.com"},
                    "started": "2025-01-15T09:00:00.000+0000",
                    "timeSpent": "2h",
                    "timeSpentSeconds": 7200,
                }
            ]
        }

        with patch("jira_assistant_skills.cli.commands.time_cmds.get_jira_client", return_value=mock_client):
            result = _generate_report_impl(project="PROJ")

        assert result["entry_count"] == 1
        mock_client.close.assert_called_once()


class TestExportTimesheetsImpl:
    """Tests for _export_timesheets_impl."""

    def test_export_timesheets(self, mock_client):
        """Test timesheet export."""
        mock_client.search_issues.return_value = {
            "issues": [
                {"key": "PROJ-123", "fields": {"summary": "Test issue"}}
            ]
        }
        mock_client.get_worklogs.return_value = {
            "worklogs": [
                {
                    "id": "12345",
                    "author": {"displayName": "John", "emailAddress": "john@example.com"},
                    "started": "2025-01-15T09:00:00.000+0000",
                    "timeSpent": "2h",
                    "timeSpentSeconds": 7200,
                }
            ]
        }

        with patch("jira_assistant_skills.cli.commands.time_cmds.get_jira_client", return_value=mock_client):
            result = _export_timesheets_impl(project="PROJ")

        assert "generated_at" in result
        assert result["entry_count"] == 1


class TestBulkLogTimeImpl:
    """Tests for _bulk_log_time_impl."""

    def test_bulk_log_dry_run(self, mock_client):
        """Test dry-run bulk logging."""
        mock_client.get_issue.return_value = {
            "key": "PROJ-1",
            "fields": {"summary": "Test"},
        }

        with patch("jira_assistant_skills.cli.commands.time_cmds.get_jira_client", return_value=mock_client):
            result = _bulk_log_time_impl(
                issues=["PROJ-1", "PROJ-2"],
                time_spent="30m",
                dry_run=True,
            )

        assert result["dry_run"] is True
        assert result["would_log_count"] == 2
        mock_client.add_worklog.assert_not_called()

    def test_bulk_log_actual(self, mock_client, sample_worklog):
        """Test actual bulk logging."""
        mock_client.add_worklog.return_value = sample_worklog

        with patch("jira_assistant_skills.cli.commands.time_cmds.get_jira_client", return_value=mock_client):
            result = _bulk_log_time_impl(
                issues=["PROJ-1", "PROJ-2"],
                time_spent="30m",
            )

        assert result["success_count"] == 2
        assert result["failure_count"] == 0

    def test_bulk_log_invalid_time(self):
        """Test invalid time format raises error."""
        with pytest.raises(ValidationError, match="Invalid time format"):
            _bulk_log_time_impl(issues=["PROJ-1"], time_spent="invalid")


# =============================================================================
# CLI Command Tests
# =============================================================================


class TestTimeLogCommand:
    """Tests for time log command."""

    def test_log_time(self, mock_client, sample_worklog):
        """Test logging time."""
        mock_client.add_worklog.return_value = sample_worklog

        with patch("jira_assistant_skills.cli.commands.time_cmds.get_jira_client", return_value=mock_client):
            runner = CliRunner()
            result = runner.invoke(time, ["log", "PROJ-123", "--time", "2h"])

        assert result.exit_code == 0
        assert "Worklog added" in result.output

    def test_log_time_json(self, mock_client, sample_worklog):
        """Test logging time with JSON output."""
        mock_client.add_worklog.return_value = sample_worklog

        with patch("jira_assistant_skills.cli.commands.time_cmds.get_jira_client", return_value=mock_client):
            runner = CliRunner()
            result = runner.invoke(time, ["log", "PROJ-123", "--time", "2h", "-o", "json"])

        assert result.exit_code == 0
        assert '"id": "12345"' in result.output


class TestTimeWorklogsCommand:
    """Tests for time worklogs command."""

    def test_get_worklogs(self, mock_client, sample_worklogs_response):
        """Test getting worklogs."""
        mock_client.get_worklogs.return_value = sample_worklogs_response

        with patch("jira_assistant_skills.cli.commands.time_cmds.get_jira_client", return_value=mock_client):
            runner = CliRunner()
            result = runner.invoke(time, ["worklogs", "PROJ-123"])

        assert result.exit_code == 0
        assert "Worklogs for PROJ-123" in result.output


class TestTimeUpdateWorklogCommand:
    """Tests for time update-worklog command."""

    def test_update_worklog(self, mock_client, sample_worklog):
        """Test updating worklog."""
        mock_client.update_worklog.return_value = sample_worklog

        with patch("jira_assistant_skills.cli.commands.time_cmds.get_jira_client", return_value=mock_client):
            runner = CliRunner()
            result = runner.invoke(
                time, ["update-worklog", "PROJ-123", "-w", "12345", "-t", "3h"]
            )

        assert result.exit_code == 0
        assert "updated" in result.output


class TestTimeDeleteWorklogCommand:
    """Tests for time delete-worklog command."""

    def test_delete_worklog_dry_run(self, mock_client, sample_worklog):
        """Test dry-run deletion."""
        mock_client.get_worklog.return_value = sample_worklog

        with patch("jira_assistant_skills.cli.commands.time_cmds.get_jira_client", return_value=mock_client):
            runner = CliRunner()
            result = runner.invoke(
                time, ["delete-worklog", "PROJ-123", "-w", "12345", "--dry-run"]
            )

        assert result.exit_code == 0
        assert "Dry-run" in result.output


class TestTimeEstimateCommand:
    """Tests for time estimate command."""

    def test_set_estimate(self, mock_client, sample_time_tracking):
        """Test setting estimate."""
        mock_client.get_time_tracking.return_value = sample_time_tracking

        with patch("jira_assistant_skills.cli.commands.time_cmds.get_jira_client", return_value=mock_client):
            runner = CliRunner()
            result = runner.invoke(time, ["estimate", "PROJ-123", "--original", "2d"])

        assert result.exit_code == 0
        assert "estimates updated" in result.output

    def test_estimate_requires_option(self):
        """Test estimate requires at least one option."""
        runner = CliRunner()
        result = runner.invoke(time, ["estimate", "PROJ-123"])
        assert result.exit_code != 0
        assert "At least one of" in result.output


class TestTimeTrackingCommand:
    """Tests for time tracking command."""

    def test_get_tracking(self, mock_client, sample_time_tracking):
        """Test getting time tracking."""
        mock_client.get_time_tracking.return_value = sample_time_tracking

        with patch("jira_assistant_skills.cli.commands.time_cmds.get_jira_client", return_value=mock_client):
            runner = CliRunner()
            result = runner.invoke(time, ["tracking", "PROJ-123"])

        assert result.exit_code == 0
        assert "Time Tracking for PROJ-123" in result.output


class TestTimeReportCommand:
    """Tests for time report command."""

    def test_generate_report(self, mock_client):
        """Test generating report."""
        mock_client.search_issues.return_value = {"issues": []}

        with patch("jira_assistant_skills.cli.commands.time_cmds.get_jira_client", return_value=mock_client):
            runner = CliRunner()
            result = runner.invoke(time, ["report", "--project", "PROJ"])

        assert result.exit_code == 0
        assert "Time Report" in result.output


class TestTimeExportCommand:
    """Tests for time export command."""

    def test_export_csv(self, mock_client):
        """Test exporting CSV."""
        mock_client.search_issues.return_value = {"issues": []}

        with patch("jira_assistant_skills.cli.commands.time_cmds.get_jira_client", return_value=mock_client):
            runner = CliRunner()
            result = runner.invoke(time, ["export", "--project", "PROJ"])

        assert result.exit_code == 0
        assert "Issue Key" in result.output


class TestTimeBulkLogCommand:
    """Tests for time bulk-log command."""

    def test_bulk_log_dry_run(self, mock_client):
        """Test dry-run bulk logging."""
        mock_client.get_issue.return_value = {
            "key": "PROJ-1",
            "fields": {"summary": "Test"},
        }

        with patch("jira_assistant_skills.cli.commands.time_cmds.get_jira_client", return_value=mock_client):
            runner = CliRunner()
            result = runner.invoke(
                time, ["bulk-log", "-i", "PROJ-1,PROJ-2", "-t", "30m", "--dry-run"]
            )

        assert result.exit_code == 0
        assert "Preview" in result.output

    def test_bulk_log_requires_issues_or_jql(self):
        """Test bulk-log requires issues or JQL."""
        runner = CliRunner()
        result = runner.invoke(time, ["bulk-log", "-t", "30m"])
        assert result.exit_code != 0
        assert "Either --jql or --issues" in result.output

    def test_bulk_log_mutually_exclusive(self):
        """Test issues and JQL are mutually exclusive."""
        runner = CliRunner()
        result = runner.invoke(
            time, ["bulk-log", "-i", "PROJ-1", "-j", "project=PROJ", "-t", "30m"]
        )
        assert result.exit_code != 0
        assert "mutually exclusive" in result.output
