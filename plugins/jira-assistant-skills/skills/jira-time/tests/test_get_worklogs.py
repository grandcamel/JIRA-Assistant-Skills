"""
Tests for get_worklogs.py script.

Tests retrieving worklogs from JIRA issues with filtering options.
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
class TestGetWorklogs:
    """Tests for fetching worklogs."""

    def test_get_all_worklogs(self, mock_jira_client, sample_worklogs):
        """Test fetching all worklogs for an issue."""
        mock_jira_client.get_worklogs.return_value = sample_worklogs

        from get_worklogs import get_worklogs

        result = get_worklogs(mock_jira_client, "PROJ-123")

        mock_jira_client.get_worklogs.assert_called_once_with("PROJ-123")
        assert result["total"] == 3
        assert len(result["worklogs"]) == 3

    def test_get_worklogs_returns_list(self, mock_jira_client, sample_worklogs):
        """Test that worklogs are returned as a list."""
        mock_jira_client.get_worklogs.return_value = sample_worklogs

        from get_worklogs import get_worklogs

        result = get_worklogs(mock_jira_client, "PROJ-123")

        assert "worklogs" in result
        assert isinstance(result["worklogs"], list)


@pytest.mark.time
@pytest.mark.unit
class TestGetWorklogsFiltering:
    """Tests for filtering worklogs."""

    def test_get_worklogs_filter_by_author(self, mock_jira_client, sample_worklogs):
        """Test filtering worklogs by author."""
        mock_jira_client.get_worklogs.return_value = sample_worklogs

        from get_worklogs import get_worklogs

        result = get_worklogs(
            mock_jira_client, "PROJ-123", author_filter="alice@company.com"
        )

        # Should filter to only Alice's worklogs (2 out of 3)
        assert len(result["worklogs"]) == 2
        for worklog in result["worklogs"]:
            assert worklog["author"]["emailAddress"] == "alice@company.com"

    def test_get_worklogs_filter_by_date_range(self, mock_jira_client, sample_worklogs):
        """Test filtering by date range."""
        mock_jira_client.get_worklogs.return_value = sample_worklogs

        from get_worklogs import get_worklogs

        result = get_worklogs(
            mock_jira_client,
            "PROJ-123",
            since="2025-01-16T00:00:00.000+0000",
            until="2025-01-17T00:00:00.000+0000",
        )

        # Should only include worklogs from Jan 16
        assert len(result["worklogs"]) == 1
        assert "2025-01-16" in result["worklogs"][0]["started"]


@pytest.mark.time
@pytest.mark.unit
class TestGetWorklogsOutput:
    """Tests for output formatting."""

    def test_get_worklogs_calculates_total(self, mock_jira_client, sample_worklogs):
        """Test total time calculation."""
        mock_jira_client.get_worklogs.return_value = sample_worklogs

        from get_worklogs import get_worklogs

        result = get_worklogs(mock_jira_client, "PROJ-123")

        # Calculate expected total: 7200 + 5400 + 14400 = 27000 seconds
        total_seconds = sum(w["timeSpentSeconds"] for w in result["worklogs"])
        assert total_seconds == 27000

    def test_get_worklogs_format_text(self, mock_jira_client, sample_worklogs, capsys):
        """Test human-readable output."""
        mock_jira_client.get_worklogs.return_value = sample_worklogs

        from get_worklogs import format_worklogs_text

        output = format_worklogs_text(sample_worklogs, "PROJ-123")

        assert "PROJ-123" in output
        assert "Alice Smith" in output or "alice@company.com" in output
        assert "2h" in output or "7200" in output

    def test_get_worklogs_format_json(self, mock_jira_client, sample_worklogs):
        """Test JSON output format."""
        mock_jira_client.get_worklogs.return_value = sample_worklogs

        from get_worklogs import get_worklogs

        result = get_worklogs(mock_jira_client, "PROJ-123")

        # Should be JSON-serializable dict
        import json

        json_str = json.dumps(result)
        assert "worklogs" in json_str


@pytest.mark.time
@pytest.mark.unit
class TestGetWorklogsEmpty:
    """Tests for empty worklog handling."""

    def test_get_worklogs_empty(self, mock_jira_client, sample_empty_worklogs):
        """Test output when no worklogs exist."""
        mock_jira_client.get_worklogs.return_value = sample_empty_worklogs

        from get_worklogs import get_worklogs

        result = get_worklogs(mock_jira_client, "PROJ-123")

        assert result["total"] == 0
        assert len(result["worklogs"]) == 0


@pytest.mark.time
@pytest.mark.unit
class TestGetWorklogsErrors:
    """Tests for error handling."""

    def test_get_worklogs_issue_not_found(self, mock_jira_client):
        """Test error when issue doesn't exist."""
        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.get_worklogs.side_effect = NotFoundError(
            "Issue PROJ-999 not found"
        )

        from get_worklogs import get_worklogs

        with pytest.raises(NotFoundError):
            get_worklogs(mock_jira_client, "PROJ-999")

    def test_get_worklogs_authentication_error_401(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from jira_assistant_skills_lib import AuthenticationError

        mock_jira_client.get_worklogs.side_effect = AuthenticationError("Invalid token")

        from get_worklogs import get_worklogs

        with pytest.raises(AuthenticationError):
            get_worklogs(mock_jira_client, "PROJ-123")

    def test_get_worklogs_permission_denied_403(self, mock_jira_client):
        """Test handling of 403 forbidden."""
        from jira_assistant_skills_lib import PermissionError

        mock_jira_client.get_worklogs.side_effect = PermissionError(
            "You do not have permission to view worklogs"
        )

        from get_worklogs import get_worklogs

        with pytest.raises(PermissionError):
            get_worklogs(mock_jira_client, "PROJ-123")

    def test_get_worklogs_rate_limit_error_429(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.get_worklogs.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        from get_worklogs import get_worklogs

        with pytest.raises(JiraError) as exc_info:
            get_worklogs(mock_jira_client, "PROJ-123")
        assert exc_info.value.status_code == 429

    def test_get_worklogs_server_error_500(self, mock_jira_client):
        """Test handling of 500 server error."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.get_worklogs.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        from get_worklogs import get_worklogs

        with pytest.raises(JiraError) as exc_info:
            get_worklogs(mock_jira_client, "PROJ-123")
        assert exc_info.value.status_code == 500


@pytest.mark.time
@pytest.mark.unit
class TestGetWorklogsMain:
    """Tests for main() function."""

    def test_main_text_output(self, mock_jira_client, sample_worklogs, capsys):
        """Test main with text output."""
        mock_jira_client.get_worklogs.return_value = sample_worklogs

        from unittest.mock import patch

        with patch("get_worklogs.get_jira_client", return_value=mock_jira_client):
            from get_worklogs import main

            main(["PROJ-123"])

            captured = capsys.readouterr()
            assert "Worklogs for PROJ-123" in captured.out
            assert "Alice Smith" in captured.out

    def test_main_json_output(self, mock_jira_client, sample_worklogs, capsys):
        """Test main with JSON output."""
        import json

        mock_jira_client.get_worklogs.return_value = sample_worklogs

        from unittest.mock import patch

        with patch("get_worklogs.get_jira_client", return_value=mock_jira_client):
            from get_worklogs import main

            main(["PROJ-123", "--output", "json"])

            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert "worklogs" in output
            assert output["total"] == 3

    def test_main_with_author_filter(self, mock_jira_client, sample_worklogs, capsys):
        """Test main with --author filter."""
        mock_jira_client.get_worklogs.return_value = sample_worklogs

        from unittest.mock import patch

        with patch("get_worklogs.get_jira_client", return_value=mock_jira_client):
            from get_worklogs import main

            main(["PROJ-123", "--author", "alice@company.com"])

            captured = capsys.readouterr()
            assert "Worklogs for PROJ-123" in captured.out

    def test_main_with_current_user_filter(
        self, mock_jira_client, sample_worklogs, capsys
    ):
        """Test main with --author currentUser()."""
        mock_jira_client.get_worklogs.return_value = sample_worklogs
        mock_jira_client.get.return_value = {
            "emailAddress": "alice@company.com",
            "accountId": "5a12345",
        }

        from unittest.mock import patch

        with patch("get_worklogs.get_jira_client", return_value=mock_jira_client):
            from get_worklogs import main

            main(["PROJ-123", "--author", "currentUser()"])

            mock_jira_client.get.assert_called_once_with(
                "/rest/api/3/myself", operation="get current user"
            )

    def test_main_with_date_filters(self, mock_jira_client, sample_worklogs, capsys):
        """Test main with --since and --until."""
        mock_jira_client.get_worklogs.return_value = sample_worklogs

        from unittest.mock import patch

        with patch("get_worklogs.get_jira_client", return_value=mock_jira_client):
            from get_worklogs import main

            main(["PROJ-123", "--since", "2025-01-01", "--until", "2025-01-31"])

            captured = capsys.readouterr()
            assert "Worklogs for PROJ-123" in captured.out

    def test_main_empty_worklogs(self, mock_jira_client, sample_empty_worklogs, capsys):
        """Test main when no worklogs exist."""
        mock_jira_client.get_worklogs.return_value = sample_empty_worklogs

        from unittest.mock import patch

        with patch("get_worklogs.get_jira_client", return_value=mock_jira_client):
            from get_worklogs import main

            main(["PROJ-123"])

            captured = capsys.readouterr()
            assert "No worklogs found" in captured.out

    def test_main_jira_error(self, mock_jira_client, capsys):
        """Test main with JIRA API error."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.get_worklogs.side_effect = JiraError(
            "API Error", status_code=500
        )

        from unittest.mock import patch

        with patch("get_worklogs.get_jira_client", return_value=mock_jira_client):
            from get_worklogs import main

            with pytest.raises(SystemExit) as exc_info:
                main(["PROJ-123"])

            assert exc_info.value.code == 1

    def test_main_keyboard_interrupt(self, mock_jira_client, capsys):
        """Test main with keyboard interrupt."""
        mock_jira_client.get_worklogs.side_effect = KeyboardInterrupt()

        from unittest.mock import patch

        with patch("get_worklogs.get_jira_client", return_value=mock_jira_client):
            from get_worklogs import main

            with pytest.raises(SystemExit) as exc_info:
                main(["PROJ-123"])

            assert exc_info.value.code == 1
