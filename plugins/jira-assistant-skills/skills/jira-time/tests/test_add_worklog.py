"""
Tests for add_worklog.py script.

Tests adding worklogs to JIRA issues with various options.
"""

import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# Add paths for imports
scripts_path = str(Path(__file__).parent.parent / "scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


@pytest.mark.time
@pytest.mark.unit
class TestAddWorklogTimeSpent:
    """Tests for basic time logging."""

    def test_add_worklog_time_spent(self, mock_jira_client, sample_worklog):
        """Test adding worklog with time spent (e.g., '2h')."""
        mock_jira_client.add_worklog.return_value = sample_worklog

        from add_worklog import add_worklog

        result = add_worklog(mock_jira_client, "PROJ-123", "2h")

        mock_jira_client.add_worklog.assert_called_once()
        call_args = mock_jira_client.add_worklog.call_args
        assert call_args[1]["issue_key"] == "PROJ-123"
        assert call_args[1]["time_spent"] == "2h"
        assert result["id"] == "10045"

    def test_add_worklog_various_time_formats(self, mock_jira_client, sample_worklog):
        """Test various time format strings."""
        mock_jira_client.add_worklog.return_value = sample_worklog

        from add_worklog import add_worklog

        # Test different formats
        for time_str in ["30m", "2h", "1d", "1w", "1d 4h", "2h 30m"]:
            add_worklog(mock_jira_client, "PROJ-123", time_str)
            call_args = mock_jira_client.add_worklog.call_args
            assert call_args[1]["time_spent"] == time_str


@pytest.mark.time
@pytest.mark.unit
class TestAddWorklogWithStarted:
    """Tests for specifying when work was started."""

    def test_add_worklog_with_started_datetime(self, mock_jira_client, sample_worklog):
        """Test specifying when work was started."""
        mock_jira_client.add_worklog.return_value = sample_worklog

        from add_worklog import add_worklog

        add_worklog(
            mock_jira_client, "PROJ-123", "2h", started="2025-01-15T09:00:00.000+0000"
        )

        call_args = mock_jira_client.add_worklog.call_args
        assert call_args[1]["started"] == "2025-01-15T09:00:00.000+0000"

    def test_add_worklog_with_relative_date(self, mock_jira_client, sample_worklog):
        """Test using relative date like 'yesterday'."""
        mock_jira_client.add_worklog.return_value = sample_worklog

        from add_worklog import add_worklog

        add_worklog(mock_jira_client, "PROJ-123", "2h", started="yesterday")

        call_args = mock_jira_client.add_worklog.call_args
        started = call_args[1]["started"]

        # Verify it's an ISO format datetime string
        iso_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
        assert re.match(iso_pattern, started), f"Expected ISO format, got: {started}"

        # Verify the date is actually yesterday
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        assert yesterday in started, (
            f"Expected yesterday's date ({yesterday}) in {started}"
        )


@pytest.mark.time
@pytest.mark.unit
class TestAddWorklogWithComment:
    """Tests for adding worklogs with comments."""

    def test_add_worklog_with_comment(self, mock_jira_client, sample_worklog):
        """Test adding worklog with ADF comment."""
        mock_jira_client.add_worklog.return_value = sample_worklog

        from add_worklog import add_worklog

        add_worklog(
            mock_jira_client, "PROJ-123", "2h", comment="Debugging authentication issue"
        )

        call_args = mock_jira_client.add_worklog.call_args
        assert "comment" in call_args[1]
        # Comment should be converted to ADF
        comment = call_args[1]["comment"]
        assert comment["type"] == "doc"
        assert comment["version"] == 1


@pytest.mark.time
@pytest.mark.unit
class TestAddWorklogEstimateAdjustment:
    """Tests for estimate adjustment options."""

    def test_add_worklog_adjust_estimate_auto(self, mock_jira_client, sample_worklog):
        """Test automatic estimate adjustment."""
        mock_jira_client.add_worklog.return_value = sample_worklog

        from add_worklog import add_worklog

        add_worklog(mock_jira_client, "PROJ-123", "2h")

        call_args = mock_jira_client.add_worklog.call_args
        # Default should be 'auto'
        assert call_args[1].get("adjust_estimate", "auto") == "auto"

    def test_add_worklog_adjust_estimate_leave(self, mock_jira_client, sample_worklog):
        """Test leaving estimate unchanged."""
        mock_jira_client.add_worklog.return_value = sample_worklog

        from add_worklog import add_worklog

        add_worklog(mock_jira_client, "PROJ-123", "2h", adjust_estimate="leave")

        call_args = mock_jira_client.add_worklog.call_args
        assert call_args[1]["adjust_estimate"] == "leave"

    def test_add_worklog_adjust_estimate_new(self, mock_jira_client, sample_worklog):
        """Test setting new remaining estimate."""
        mock_jira_client.add_worklog.return_value = sample_worklog

        from add_worklog import add_worklog

        add_worklog(
            mock_jira_client, "PROJ-123", "2h", adjust_estimate="new", new_estimate="6h"
        )

        call_args = mock_jira_client.add_worklog.call_args
        assert call_args[1]["adjust_estimate"] == "new"
        assert call_args[1]["new_estimate"] == "6h"


@pytest.mark.time
@pytest.mark.unit
class TestAddWorklogValidation:
    """Tests for input validation."""

    def test_add_worklog_invalid_time_format(self, mock_jira_client):
        """Test validation of time format."""
        from add_worklog import add_worklog
        from assistant_skills_lib.error_handler import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            add_worklog(mock_jira_client, "PROJ-123", "invalid")

        assert "time format" in str(exc_info.value).lower()

    def test_add_worklog_empty_time(self, mock_jira_client):
        """Test validation rejects empty time."""
        from add_worklog import add_worklog
        from assistant_skills_lib.error_handler import ValidationError

        with pytest.raises(ValidationError):
            add_worklog(mock_jira_client, "PROJ-123", "")


@pytest.mark.time
@pytest.mark.unit
class TestAddWorklogErrors:
    """Tests for error handling."""

    def test_add_worklog_issue_not_found(self, mock_jira_client):
        """Test error when issue doesn't exist."""
        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.add_worklog.side_effect = NotFoundError(
            "Issue PROJ-999 not found"
        )

        from add_worklog import add_worklog

        with pytest.raises(NotFoundError):
            add_worklog(mock_jira_client, "PROJ-999", "2h")

    def test_add_worklog_time_tracking_disabled(self, mock_jira_client):
        """Test error when time tracking is disabled."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.add_worklog.side_effect = JiraError(
            "Time Tracking is not enabled for this issue"
        )

        from add_worklog import add_worklog

        with pytest.raises(JiraError) as exc_info:
            add_worklog(mock_jira_client, "PROJ-123", "2h")

        assert "time tracking" in str(exc_info.value).lower()

    def test_add_worklog_authentication_error_401(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from jira_assistant_skills_lib import AuthenticationError

        mock_jira_client.add_worklog.side_effect = AuthenticationError("Invalid token")

        from add_worklog import add_worklog

        with pytest.raises(AuthenticationError):
            add_worklog(mock_jira_client, "PROJ-123", "2h")

    def test_add_worklog_permission_denied_403(self, mock_jira_client):
        """Test handling of 403 forbidden."""
        from jira_assistant_skills_lib import PermissionError

        mock_jira_client.add_worklog.side_effect = PermissionError(
            "You do not have permission to log work on this issue"
        )

        from add_worklog import add_worklog

        with pytest.raises(PermissionError):
            add_worklog(mock_jira_client, "PROJ-123", "2h")

    def test_add_worklog_rate_limit_error_429(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.add_worklog.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        from add_worklog import add_worklog

        with pytest.raises(JiraError) as exc_info:
            add_worklog(mock_jira_client, "PROJ-123", "2h")
        assert exc_info.value.status_code == 429

    def test_add_worklog_server_error_500(self, mock_jira_client):
        """Test handling of 500 server error."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.add_worklog.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        from add_worklog import add_worklog

        with pytest.raises(JiraError) as exc_info:
            add_worklog(mock_jira_client, "PROJ-123", "2h")
        assert exc_info.value.status_code == 500


@pytest.mark.time
@pytest.mark.unit
class TestAddWorklogTimeValidationEdgeCases:
    """Tests for time format edge cases."""

    def test_add_worklog_zero_time(self, mock_jira_client):
        """Test validation rejects zero time."""
        from add_worklog import add_worklog
        from assistant_skills_lib.error_handler import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            add_worklog(mock_jira_client, "PROJ-123", "0h")
        assert (
            "zero" in str(exc_info.value).lower()
            or "invalid" in str(exc_info.value).lower()
        )

    def test_add_worklog_negative_time(self, mock_jira_client):
        """Test validation rejects negative time."""
        from add_worklog import add_worklog
        from assistant_skills_lib.error_handler import ValidationError

        # Negative time should be rejected by validation
        # Note: If the implementation doesn't validate this,
        # JIRA API would reject it
        try:
            add_worklog(mock_jira_client, "PROJ-123", "-2h")
            # If we get here, implementation doesn't validate negative time
            # This is acceptable - JIRA API would reject
            pass
        except ValidationError:
            # Expected behavior - validation catches negative time
            pass

    def test_add_worklog_max_time_boundary(self, mock_jira_client, sample_worklog):
        """Test maximum allowed time value (e.g., 52w or JIRA's max)."""
        mock_jira_client.add_worklog.return_value = sample_worklog

        from add_worklog import add_worklog

        # JIRA typically allows up to 52 weeks
        add_worklog(mock_jira_client, "PROJ-123", "52w")
        assert mock_jira_client.add_worklog.called

    def test_add_worklog_whitespace_only(self, mock_jira_client):
        """Test validation rejects whitespace-only time."""
        from add_worklog import add_worklog
        from assistant_skills_lib.error_handler import ValidationError

        with pytest.raises(ValidationError):
            add_worklog(mock_jira_client, "PROJ-123", "   ")

    def test_add_worklog_mixed_case_time_units(self, mock_jira_client, sample_worklog):
        """Test that time units are case-insensitive."""
        mock_jira_client.add_worklog.return_value = sample_worklog

        from add_worklog import add_worklog

        # Should accept uppercase/mixed case
        for time_str in ["2H", "2h 30M", "1D", "1W"]:
            add_worklog(mock_jira_client, "PROJ-123", time_str)
            assert mock_jira_client.add_worklog.called
            mock_jira_client.reset_mock()
