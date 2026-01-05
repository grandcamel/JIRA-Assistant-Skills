"""
Tests for get_time_tracking.py script.

Tests fetching time tracking summary from JIRA issues.
"""

import sys
from pathlib import Path

import pytest

# Add paths for imports
scripts_path = str(Path(__file__).parent.parent / "scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


@pytest.mark.time
@pytest.mark.unit
class TestGetTimeTracking:
    """Tests for getting time tracking info."""

    def test_get_time_tracking_full(self, mock_jira_client, sample_time_tracking):
        """Test fetching complete time tracking info."""
        mock_jira_client.get_time_tracking.return_value = sample_time_tracking

        from get_time_tracking import get_time_tracking

        result = get_time_tracking(mock_jira_client, "PROJ-123")

        mock_jira_client.get_time_tracking.assert_called_once_with("PROJ-123")
        assert result["originalEstimate"] == "2d"
        assert result["remainingEstimate"] == "1d 4h"
        assert result["timeSpent"] == "4h"

    def test_get_time_tracking_no_work_logged(self, mock_jira_client):
        """Test when no work has been logged."""
        mock_jira_client.get_time_tracking.return_value = {
            "originalEstimate": "2d",
            "originalEstimateSeconds": 57600,
            "remainingEstimate": "2d",
            "remainingEstimateSeconds": 57600,
        }

        from get_time_tracking import get_time_tracking

        result = get_time_tracking(mock_jira_client, "PROJ-123")

        assert result.get("timeSpent") is None
        assert result.get("timeSpentSeconds") is None

    def test_get_time_tracking_no_estimates(self, mock_jira_client):
        """Test when estimates not set."""
        mock_jira_client.get_time_tracking.return_value = {}

        from get_time_tracking import get_time_tracking

        result = get_time_tracking(mock_jira_client, "PROJ-123")

        assert result.get("originalEstimate") is None
        assert result.get("remainingEstimate") is None


@pytest.mark.time
@pytest.mark.unit
class TestGetTimeTrackingProgress:
    """Tests for progress calculations."""

    def test_get_time_tracking_calculate_progress(
        self, mock_jira_client, sample_time_tracking
    ):
        """Test calculating completion percentage."""
        mock_jira_client.get_time_tracking.return_value = sample_time_tracking

        from get_time_tracking import calculate_progress, get_time_tracking

        result = get_time_tracking(mock_jira_client, "PROJ-123")
        progress = calculate_progress(result)

        # 4h logged of 16h (2d) = 25%
        assert progress == 25

    def test_calculate_progress_no_estimate(self, mock_jira_client):
        """Test progress when no estimate set."""
        from get_time_tracking import calculate_progress

        result = {"timeSpentSeconds": 7200}
        progress = calculate_progress(result)

        assert progress is None

    def test_calculate_progress_no_work(self, mock_jira_client):
        """Test progress when no work logged."""
        from get_time_tracking import calculate_progress

        result = {"originalEstimateSeconds": 57600}
        progress = calculate_progress(result)

        assert progress == 0


@pytest.mark.time
@pytest.mark.unit
class TestGetTimeTrackingErrors:
    """Tests for error handling."""

    def test_get_time_tracking_issue_not_found(self, mock_jira_client):
        """Test error when issue doesn't exist."""
        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.get_time_tracking.side_effect = NotFoundError(
            "Issue PROJ-999 not found"
        )

        from get_time_tracking import get_time_tracking

        with pytest.raises(NotFoundError):
            get_time_tracking(mock_jira_client, "PROJ-999")

    def test_get_time_tracking_authentication_error_401(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from jira_assistant_skills_lib import AuthenticationError

        mock_jira_client.get_time_tracking.side_effect = AuthenticationError(
            "Invalid token"
        )

        from get_time_tracking import get_time_tracking

        with pytest.raises(AuthenticationError):
            get_time_tracking(mock_jira_client, "PROJ-123")

    def test_get_time_tracking_permission_denied_403(self, mock_jira_client):
        """Test handling of 403 forbidden."""
        from jira_assistant_skills_lib import PermissionError

        mock_jira_client.get_time_tracking.side_effect = PermissionError(
            "You do not have permission to view this issue"
        )

        from get_time_tracking import get_time_tracking

        with pytest.raises(PermissionError):
            get_time_tracking(mock_jira_client, "PROJ-123")

    def test_get_time_tracking_rate_limit_error_429(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.get_time_tracking.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        from get_time_tracking import get_time_tracking

        with pytest.raises(JiraError) as exc_info:
            get_time_tracking(mock_jira_client, "PROJ-123")
        assert exc_info.value.status_code == 429

    def test_get_time_tracking_server_error_500(self, mock_jira_client):
        """Test handling of 500 server error."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.get_time_tracking.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        from get_time_tracking import get_time_tracking

        with pytest.raises(JiraError) as exc_info:
            get_time_tracking(mock_jira_client, "PROJ-123")
        assert exc_info.value.status_code == 500


@pytest.mark.time
@pytest.mark.unit
class TestGenerateProgressBar:
    """Tests for progress bar generation."""

    def test_progress_bar_0_percent(self):
        """Test progress bar at 0%."""
        from get_time_tracking import generate_progress_bar

        bar = generate_progress_bar(0)
        assert "█" not in bar
        assert len(bar) == 20

    def test_progress_bar_50_percent(self):
        """Test progress bar at 50%."""
        from get_time_tracking import generate_progress_bar

        bar = generate_progress_bar(50)
        assert bar.count("█") == 10
        assert bar.count("░") == 10

    def test_progress_bar_100_percent(self):
        """Test progress bar at 100%."""
        from get_time_tracking import generate_progress_bar

        bar = generate_progress_bar(100)
        assert "░" not in bar
        assert len(bar) == 20


@pytest.mark.time
@pytest.mark.unit
class TestGetTimeTrackingMain:
    """Tests for main() function."""

    def test_main_text_output(self, mock_jira_client, sample_time_tracking, capsys):
        """Test main with text output."""
        mock_jira_client.get_time_tracking.return_value = sample_time_tracking

        from unittest.mock import patch

        with patch("get_time_tracking.get_jira_client", return_value=mock_jira_client):
            from get_time_tracking import main

            main(["PROJ-123"])

            captured = capsys.readouterr()
            assert "Time Tracking for PROJ-123" in captured.out
            assert "Original Estimate" in captured.out
            assert "Remaining Estimate" in captured.out
            assert "Time Spent" in captured.out

    def test_main_with_progress_bar(
        self, mock_jira_client, sample_time_tracking, capsys
    ):
        """Test main shows progress bar when estimates exist."""
        mock_jira_client.get_time_tracking.return_value = sample_time_tracking

        from unittest.mock import patch

        with patch("get_time_tracking.get_jira_client", return_value=mock_jira_client):
            from get_time_tracking import main

            main(["PROJ-123"])

            captured = capsys.readouterr()
            assert "Progress" in captured.out
            assert "█" in captured.out or "░" in captured.out

    def test_main_json_output(self, mock_jira_client, sample_time_tracking, capsys):
        """Test main with JSON output."""
        import json

        mock_jira_client.get_time_tracking.return_value = sample_time_tracking

        from unittest.mock import patch

        with patch("get_time_tracking.get_jira_client", return_value=mock_jira_client):
            from get_time_tracking import main

            main(["PROJ-123", "--output", "json"])

            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert "originalEstimate" in output
            assert "progress" in output  # Calculated progress added

    def test_main_no_estimates(self, mock_jira_client, capsys):
        """Test main when no estimates set."""
        mock_jira_client.get_time_tracking.return_value = {}

        from unittest.mock import patch

        with patch("get_time_tracking.get_jira_client", return_value=mock_jira_client):
            from get_time_tracking import main

            main(["PROJ-123"])

            captured = capsys.readouterr()
            assert "Not set" in captured.out

    def test_main_no_work_logged(self, mock_jira_client, capsys):
        """Test main when no work logged."""
        mock_jira_client.get_time_tracking.return_value = {
            "originalEstimate": "2d",
            "originalEstimateSeconds": 57600,
            "remainingEstimate": "2d",
            "remainingEstimateSeconds": 57600,
        }

        from unittest.mock import patch

        with patch("get_time_tracking.get_jira_client", return_value=mock_jira_client):
            from get_time_tracking import main

            main(["PROJ-123"])

            captured = capsys.readouterr()
            assert "Time Spent" in captured.out

    def test_main_with_profile(self, mock_jira_client, sample_time_tracking, capsys):
        """Test main with --profile."""
        mock_jira_client.get_time_tracking.return_value = sample_time_tracking

        from unittest.mock import patch

        with patch(
            "get_time_tracking.get_jira_client", return_value=mock_jira_client
        ) as mock_get_client:
            from get_time_tracking import main

            main(["PROJ-123", "--profile", "dev"])

            mock_get_client.assert_called_with("dev")

    def test_main_jira_error(self, mock_jira_client, capsys):
        """Test main with JIRA API error."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.get_time_tracking.side_effect = JiraError(
            "API Error", status_code=500
        )

        from unittest.mock import patch

        with patch("get_time_tracking.get_jira_client", return_value=mock_jira_client):
            from get_time_tracking import main

            with pytest.raises(SystemExit) as exc_info:
                main(["PROJ-123"])

            assert exc_info.value.code == 1

    def test_main_keyboard_interrupt(self, mock_jira_client, capsys):
        """Test main with keyboard interrupt."""
        mock_jira_client.get_time_tracking.side_effect = KeyboardInterrupt()

        from unittest.mock import patch

        with patch("get_time_tracking.get_jira_client", return_value=mock_jira_client):
            from get_time_tracking import main

            with pytest.raises(SystemExit) as exc_info:
                main(["PROJ-123"])

            assert exc_info.value.code == 1
