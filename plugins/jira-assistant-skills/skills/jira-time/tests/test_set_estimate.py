"""
Tests for set_estimate.py script.

Tests setting original and remaining estimates on JIRA issues.
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
class TestSetEstimate:
    """Tests for setting time estimates."""

    def test_set_original_estimate(self, mock_jira_client):
        """Test setting original estimate."""
        mock_jira_client.set_time_tracking.return_value = None
        mock_jira_client.get_time_tracking.return_value = {
            "originalEstimate": "2d",
            "originalEstimateSeconds": 57600,
            "remainingEstimate": "2d",
            "remainingEstimateSeconds": 57600,
        }

        from set_estimate import set_estimate

        result = set_estimate(mock_jira_client, "PROJ-123", original_estimate="2d")

        mock_jira_client.set_time_tracking.assert_called_once()
        call_args = mock_jira_client.set_time_tracking.call_args
        assert call_args[1]["original_estimate"] == "2d"
        assert result["originalEstimate"] == "2d"

    def test_set_remaining_estimate(self, mock_jira_client):
        """Test setting remaining estimate."""
        mock_jira_client.set_time_tracking.return_value = None
        mock_jira_client.get_time_tracking.return_value = {
            "originalEstimate": "2d",
            "originalEstimateSeconds": 57600,
            "remainingEstimate": "1d 4h",
            "remainingEstimateSeconds": 43200,
        }

        from set_estimate import set_estimate

        set_estimate(mock_jira_client, "PROJ-123", remaining_estimate="1d 4h")

        call_args = mock_jira_client.set_time_tracking.call_args
        assert call_args[1]["remaining_estimate"] == "1d 4h"

    def test_set_both_estimates(self, mock_jira_client):
        """Test setting both estimates together."""
        mock_jira_client.set_time_tracking.return_value = None
        mock_jira_client.get_time_tracking.return_value = {
            "originalEstimate": "3d",
            "originalEstimateSeconds": 86400,
            "remainingEstimate": "2d",
            "remainingEstimateSeconds": 57600,
        }

        from set_estimate import set_estimate

        set_estimate(
            mock_jira_client,
            "PROJ-123",
            original_estimate="3d",
            remaining_estimate="2d",
        )

        call_args = mock_jira_client.set_time_tracking.call_args
        assert call_args[1]["original_estimate"] == "3d"
        assert call_args[1]["remaining_estimate"] == "2d"


@pytest.mark.time
@pytest.mark.unit
class TestSetEstimateValidation:
    """Tests for input validation."""

    def test_set_estimate_invalid_format(self, mock_jira_client):
        """Test validation of time format."""
        from assistant_skills_lib.error_handler import ValidationError
        from set_estimate import set_estimate

        with pytest.raises(ValidationError):
            set_estimate(mock_jira_client, "PROJ-123", original_estimate="invalid")

    def test_set_estimate_no_values(self, mock_jira_client):
        """Test error when no estimate values provided."""
        from assistant_skills_lib.error_handler import ValidationError
        from set_estimate import set_estimate

        with pytest.raises(ValidationError):
            set_estimate(mock_jira_client, "PROJ-123")


@pytest.mark.time
@pytest.mark.unit
class TestSetEstimateErrors:
    """Tests for error handling."""

    def test_set_estimate_issue_not_found(self, mock_jira_client):
        """Test error when issue doesn't exist."""
        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.set_time_tracking.side_effect = NotFoundError(
            "Issue PROJ-999 not found"
        )

        from set_estimate import set_estimate

        with pytest.raises(NotFoundError):
            set_estimate(mock_jira_client, "PROJ-999", original_estimate="2d")

    def test_set_estimate_authentication_error_401(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from jira_assistant_skills_lib import AuthenticationError

        mock_jira_client.set_time_tracking.side_effect = AuthenticationError(
            "Invalid token"
        )

        from set_estimate import set_estimate

        with pytest.raises(AuthenticationError):
            set_estimate(mock_jira_client, "PROJ-123", original_estimate="2d")

    def test_set_estimate_permission_denied_403(self, mock_jira_client):
        """Test handling of 403 forbidden."""
        from jira_assistant_skills_lib import PermissionError

        mock_jira_client.set_time_tracking.side_effect = PermissionError(
            "You do not have permission to edit time tracking"
        )

        from set_estimate import set_estimate

        with pytest.raises(PermissionError):
            set_estimate(mock_jira_client, "PROJ-123", original_estimate="2d")

    def test_set_estimate_rate_limit_error_429(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.set_time_tracking.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        from set_estimate import set_estimate

        with pytest.raises(JiraError) as exc_info:
            set_estimate(mock_jira_client, "PROJ-123", original_estimate="2d")
        assert exc_info.value.status_code == 429

    def test_set_estimate_server_error_500(self, mock_jira_client):
        """Test handling of 500 server error."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.set_time_tracking.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        from set_estimate import set_estimate

        with pytest.raises(JiraError) as exc_info:
            set_estimate(mock_jira_client, "PROJ-123", original_estimate="2d")
        assert exc_info.value.status_code == 500


@pytest.mark.time
@pytest.mark.unit
class TestSetEstimateMain:
    """Tests for main() function."""

    def test_main_set_original(self, mock_jira_client, capsys):
        """Test main setting original estimate."""
        mock_jira_client.get_time_tracking.return_value = {
            "originalEstimate": "2d",
            "originalEstimateSeconds": 57600,
        }
        mock_jira_client.set_time_tracking.return_value = None

        from unittest.mock import patch

        with patch("set_estimate.get_jira_client", return_value=mock_jira_client):
            from set_estimate import main

            main(["PROJ-123", "--original", "2d"])

            captured = capsys.readouterr()
            assert "Time estimates updated" in captured.out
            assert "Original estimate" in captured.out

    def test_main_set_remaining(self, mock_jira_client, capsys):
        """Test main setting remaining estimate."""
        mock_jira_client.get_time_tracking.return_value = {
            "remainingEstimate": "1d 4h",
            "remainingEstimateSeconds": 43200,
        }
        mock_jira_client.set_time_tracking.return_value = None

        from unittest.mock import patch

        with patch("set_estimate.get_jira_client", return_value=mock_jira_client):
            from set_estimate import main

            main(["PROJ-123", "--remaining", "1d 4h"])

            captured = capsys.readouterr()
            assert "Time estimates updated" in captured.out
            assert "Remaining estimate" in captured.out

    def test_main_set_both(self, mock_jira_client, capsys):
        """Test main setting both estimates."""
        mock_jira_client.get_time_tracking.return_value = {
            "originalEstimate": "2d",
            "remainingEstimate": "1d",
            "timeSpent": "4h",
        }
        mock_jira_client.set_time_tracking.return_value = None

        from unittest.mock import patch

        with patch("set_estimate.get_jira_client", return_value=mock_jira_client):
            from set_estimate import main

            main(["PROJ-123", "--original", "2d", "--remaining", "1d"])

            captured = capsys.readouterr()
            assert "Original estimate" in captured.out
            assert "Remaining estimate" in captured.out
            assert "Time spent" in captured.out

    def test_main_json_output(self, mock_jira_client, capsys):
        """Test main with JSON output."""
        import json

        mock_jira_client.get_time_tracking.return_value = {
            "originalEstimate": "2d",
            "originalEstimateSeconds": 57600,
        }
        mock_jira_client.set_time_tracking.return_value = None

        from unittest.mock import patch

        with patch("set_estimate.get_jira_client", return_value=mock_jira_client):
            from set_estimate import main

            main(["PROJ-123", "--original", "2d", "--output", "json"])

            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert "originalEstimate" in output

    def test_main_with_profile(self, mock_jira_client, capsys):
        """Test main with --profile."""
        mock_jira_client.get_time_tracking.return_value = {"originalEstimate": "2d"}
        mock_jira_client.set_time_tracking.return_value = None

        from unittest.mock import patch

        with patch(
            "set_estimate.get_jira_client", return_value=mock_jira_client
        ) as mock_get_client:
            from set_estimate import main

            main(["PROJ-123", "--original", "2d", "--profile", "dev"])

            mock_get_client.assert_called_with("dev")

    def test_main_jira_error(self, mock_jira_client, capsys):
        """Test main with JIRA API error."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.get_time_tracking.side_effect = JiraError(
            "API Error", status_code=500
        )

        from unittest.mock import patch

        with patch("set_estimate.get_jira_client", return_value=mock_jira_client):
            from set_estimate import main

            with pytest.raises(SystemExit) as exc_info:
                main(["PROJ-123", "--original", "2d"])

            assert exc_info.value.code == 1

    def test_main_keyboard_interrupt(self, mock_jira_client, capsys):
        """Test main with keyboard interrupt."""
        mock_jira_client.get_time_tracking.side_effect = KeyboardInterrupt()

        from unittest.mock import patch

        with patch("set_estimate.get_jira_client", return_value=mock_jira_client):
            from set_estimate import main

            with pytest.raises(SystemExit) as exc_info:
                main(["PROJ-123", "--original", "2d"])

            assert exc_info.value.code == 1
