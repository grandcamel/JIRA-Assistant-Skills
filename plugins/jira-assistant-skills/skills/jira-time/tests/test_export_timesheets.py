"""
Tests for export_timesheets.py script.

Tests exporting timesheets to CSV/JSON formats.
"""

import csv
import json
import sys
from io import StringIO
from pathlib import Path

import pytest

# Add paths for imports
scripts_path = str(Path(__file__).parent.parent / "scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


@pytest.fixture
def sample_timesheet_data():
    """Sample timesheet data for export."""
    return {
        "entries": [
            {
                "issue_key": "PROJ-123",
                "issue_summary": "Authentication refactor",
                "author": "Alice",
                "author_email": "alice@company.com",
                "started": "2025-01-15T09:00:00.000+0000",
                "started_date": "2025-01-15",
                "time_spent": "4h",
                "time_seconds": 14400,
                "comment": "Debugging auth issue",
            },
            {
                "issue_key": "PROJ-124",
                "issue_summary": "API documentation",
                "author": "Alice",
                "author_email": "alice@company.com",
                "started": "2025-01-16T10:00:00.000+0000",
                "started_date": "2025-01-16",
                "time_spent": "2h",
                "time_seconds": 7200,
                "comment": "Updated endpoints",
            },
        ],
        "total_seconds": 21600,
        "entry_count": 2,
    }


@pytest.mark.time
@pytest.mark.unit
class TestExportFormats:
    """Tests for export format generation."""

    def test_export_csv_format(self, sample_timesheet_data):
        """Test CSV export with proper headers."""
        from export_timesheets import format_csv

        csv_output = format_csv(sample_timesheet_data)

        # Parse CSV and check structure
        reader = csv.DictReader(StringIO(csv_output))
        rows = list(reader)

        assert len(rows) == 2
        assert "Issue Key" in reader.fieldnames
        assert "Time Spent" in reader.fieldnames
        assert rows[0]["Issue Key"] == "PROJ-123"

    def test_export_json_format(self, sample_timesheet_data):
        """Test JSON export structure."""
        from export_timesheets import format_json

        json_output = format_json(sample_timesheet_data)

        # Parse and verify JSON structure
        data = json.loads(json_output)
        assert "entries" in data
        assert "total_seconds" in data
        assert len(data["entries"]) == 2

    def test_export_includes_all_fields(self, sample_timesheet_data):
        """Test all required fields are included."""
        from export_timesheets import format_csv

        csv_output = format_csv(sample_timesheet_data)

        # Check all expected columns are present
        lines = csv_output.strip().split("\n")
        header = lines[0]

        assert "Issue Key" in header
        assert "Issue Summary" in header
        assert "Author" in header
        assert "Date" in header
        assert "Time Spent" in header
        assert "Seconds" in header


@pytest.mark.time
@pytest.mark.unit
class TestExportFile:
    """Tests for file export."""

    def test_export_to_file(self, sample_timesheet_data, tmp_path):
        """Test writing to output file."""
        from export_timesheets import write_export

        output_file = tmp_path / "timesheet.csv"
        write_export(sample_timesheet_data, str(output_file), "csv")

        assert output_file.exists()
        content = output_file.read_text()
        assert "PROJ-123" in content

    def test_export_json_to_file(self, sample_timesheet_data, tmp_path):
        """Test JSON export to file."""
        from export_timesheets import write_export

        output_file = tmp_path / "timesheet.json"
        write_export(sample_timesheet_data, str(output_file), "json")

        assert output_file.exists()
        data = json.loads(output_file.read_text())
        assert len(data["entries"]) == 2


@pytest.mark.time
@pytest.mark.unit
class TestFetchTimesheetData:
    """Tests for fetching timesheet data."""

    def test_fetch_timesheet_data_basic(self, mock_jira_client):
        """Test fetching timesheet data without filters."""
        mock_jira_client.search_issues.return_value = {
            "issues": [{"key": "PROJ-123", "fields": {"summary": "Test issue"}}]
        }
        mock_jira_client.get_worklogs.return_value = {
            "worklogs": [
                {
                    "id": "10045",
                    "author": {
                        "displayName": "Alice",
                        "emailAddress": "alice@company.com",
                    },
                    "started": "2025-01-15T09:00:00.000+0000",
                    "timeSpent": "2h",
                    "timeSpentSeconds": 7200,
                }
            ]
        }

        from export_timesheets import fetch_timesheet_data

        result = fetch_timesheet_data(mock_jira_client)

        assert result["entry_count"] == 1
        assert result["entries"][0]["issue_key"] == "PROJ-123"

    def test_fetch_timesheet_data_with_project(self, mock_jira_client):
        """Test filtering by project."""
        mock_jira_client.search_issues.return_value = {"issues": []}

        from export_timesheets import fetch_timesheet_data

        fetch_timesheet_data(mock_jira_client, project="PROJ")

        # Check JQL includes project
        call_args = mock_jira_client.search_issues.call_args
        assert "project = PROJ" in call_args[0][0]

    def test_fetch_timesheet_data_with_author(self, mock_jira_client):
        """Test filtering by author."""
        mock_jira_client.search_issues.return_value = {
            "issues": [{"key": "PROJ-123", "fields": {"summary": "Test"}}]
        }
        mock_jira_client.get_worklogs.return_value = {
            "worklogs": [
                {
                    "id": "10045",
                    "author": {
                        "displayName": "Alice",
                        "emailAddress": "alice@company.com",
                    },
                    "started": "2025-01-15T09:00:00.000+0000",
                    "timeSpent": "2h",
                    "timeSpentSeconds": 7200,
                },
                {
                    "id": "10046",
                    "author": {
                        "displayName": "Bob",
                        "emailAddress": "bob@company.com",
                    },
                    "started": "2025-01-15T10:00:00.000+0000",
                    "timeSpent": "1h",
                    "timeSpentSeconds": 3600,
                },
            ]
        }

        from export_timesheets import fetch_timesheet_data

        result = fetch_timesheet_data(mock_jira_client, author="alice@company.com")

        # Should only include Alice's entries
        assert result["entry_count"] == 1
        assert result["entries"][0]["author_email"] == "alice@company.com"


@pytest.mark.time
@pytest.mark.unit
class TestExportTimesheetsMain:
    """Tests for main() function."""

    def test_main_csv_output(self, mock_jira_client, capsys):
        """Test main with CSV output to stdout."""
        from unittest.mock import patch

        mock_jira_client.search_issues.return_value = {
            "issues": [{"key": "PROJ-123", "fields": {"summary": "Test"}}]
        }
        mock_jira_client.get_worklogs.return_value = {
            "worklogs": [
                {
                    "id": "10045",
                    "author": {
                        "displayName": "Alice",
                        "emailAddress": "alice@company.com",
                    },
                    "started": "2025-01-15T09:00:00.000+0000",
                    "timeSpent": "2h",
                    "timeSpentSeconds": 7200,
                }
            ]
        }

        with patch("export_timesheets.get_jira_client", return_value=mock_jira_client):
            from export_timesheets import main

            main(["--project", "PROJ"])

            captured = capsys.readouterr()
            assert "Issue Key" in captured.out
            assert "PROJ-123" in captured.out

    def test_main_json_output(self, mock_jira_client, capsys):
        """Test main with JSON output."""
        from unittest.mock import patch

        mock_jira_client.search_issues.return_value = {
            "issues": [{"key": "PROJ-123", "fields": {"summary": "Test"}}]
        }
        mock_jira_client.get_worklogs.return_value = {
            "worklogs": [
                {
                    "id": "10045",
                    "author": {
                        "displayName": "Alice",
                        "emailAddress": "alice@company.com",
                    },
                    "started": "2025-01-15T09:00:00.000+0000",
                    "timeSpent": "2h",
                    "timeSpentSeconds": 7200,
                }
            ]
        }

        with patch("export_timesheets.get_jira_client", return_value=mock_jira_client):
            from export_timesheets import main

            main(["--project", "PROJ", "--format", "json"])

            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert "entries" in output
            assert output["entry_count"] == 1

    def test_main_with_output_file(self, mock_jira_client, tmp_path, capsys):
        """Test main with --output file."""
        from unittest.mock import patch

        mock_jira_client.search_issues.return_value = {
            "issues": [{"key": "PROJ-123", "fields": {"summary": "Test"}}]
        }
        mock_jira_client.get_worklogs.return_value = {
            "worklogs": [
                {
                    "id": "10045",
                    "author": {
                        "displayName": "Alice",
                        "emailAddress": "alice@company.com",
                    },
                    "started": "2025-01-15T09:00:00.000+0000",
                    "timeSpent": "2h",
                    "timeSpentSeconds": 7200,
                }
            ]
        }

        output_file = tmp_path / "export.csv"
        with patch("export_timesheets.get_jira_client", return_value=mock_jira_client):
            from export_timesheets import main

            main(["--project", "PROJ", "--output", str(output_file)])

            captured = capsys.readouterr()
            assert "Exported 1 entries" in captured.out
            assert output_file.exists()

    def test_main_with_period_this_month(self, mock_jira_client, capsys):
        """Test main with --period this-month."""
        from unittest.mock import patch

        mock_jira_client.search_issues.return_value = {"issues": []}

        with patch("export_timesheets.get_jira_client", return_value=mock_jira_client):
            from export_timesheets import main

            main(["--period", "this-month"])

            # Should not error
            captured = capsys.readouterr()
            assert "Issue Key" in captured.out

    def test_main_with_period_last_month(self, mock_jira_client, capsys):
        """Test main with --period last-month."""
        from unittest.mock import patch

        mock_jira_client.search_issues.return_value = {"issues": []}

        with patch("export_timesheets.get_jira_client", return_value=mock_jira_client):
            from export_timesheets import main

            main(["--period", "last-month"])

            captured = capsys.readouterr()
            assert "Issue Key" in captured.out

    def test_main_with_period_year_month(self, mock_jira_client, capsys):
        """Test main with --period 2025-01."""
        from unittest.mock import patch

        mock_jira_client.search_issues.return_value = {"issues": []}

        with patch("export_timesheets.get_jira_client", return_value=mock_jira_client):
            from export_timesheets import main

            main(["--period", "2025-01"])

            captured = capsys.readouterr()
            assert "Issue Key" in captured.out

    def test_main_with_user_filter(self, mock_jira_client, capsys):
        """Test main with --user filter."""
        from unittest.mock import patch

        mock_jira_client.search_issues.return_value = {"issues": []}

        with patch("export_timesheets.get_jira_client", return_value=mock_jira_client):
            from export_timesheets import main

            main(["--user", "alice@company.com"])

            captured = capsys.readouterr()
            assert "Issue Key" in captured.out

    def test_main_jira_error(self, mock_jira_client, capsys):
        """Test main with JIRA API error."""
        from unittest.mock import patch

        from jira_assistant_skills_lib import JiraError

        mock_jira_client.search_issues.side_effect = JiraError(
            "API Error", status_code=500
        )

        with patch("export_timesheets.get_jira_client", return_value=mock_jira_client):
            from export_timesheets import main

            with pytest.raises(SystemExit) as exc_info:
                main(["--project", "PROJ"])

            assert exc_info.value.code == 1

    def test_main_keyboard_interrupt(self, mock_jira_client, capsys):
        """Test main with keyboard interrupt."""
        from unittest.mock import patch

        mock_jira_client.search_issues.side_effect = KeyboardInterrupt()

        with patch("export_timesheets.get_jira_client", return_value=mock_jira_client):
            from export_timesheets import main

            with pytest.raises(SystemExit) as exc_info:
                main(["--project", "PROJ"])

            assert exc_info.value.code == 1
