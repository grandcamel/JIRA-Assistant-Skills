"""
Tests for export_timesheets.py script.

Tests exporting timesheets to CSV/JSON formats.
"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path
import json
import csv
from io import StringIO

# Add paths for imports
scripts_path = str(Path(__file__).parent.parent / 'scripts')
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


@pytest.fixture
def sample_timesheet_data():
    """Sample timesheet data for export."""
    return {
        'entries': [
            {
                'issue_key': 'PROJ-123',
                'issue_summary': 'Authentication refactor',
                'author': 'Alice',
                'author_email': 'alice@company.com',
                'started': '2025-01-15T09:00:00.000+0000',
                'started_date': '2025-01-15',
                'time_spent': '4h',
                'time_seconds': 14400,
                'comment': 'Debugging auth issue'
            },
            {
                'issue_key': 'PROJ-124',
                'issue_summary': 'API documentation',
                'author': 'Alice',
                'author_email': 'alice@company.com',
                'started': '2025-01-16T10:00:00.000+0000',
                'started_date': '2025-01-16',
                'time_spent': '2h',
                'time_seconds': 7200,
                'comment': 'Updated endpoints'
            }
        ],
        'total_seconds': 21600,
        'entry_count': 2
    }


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
        assert 'Issue Key' in reader.fieldnames
        assert 'Time Spent' in reader.fieldnames
        assert rows[0]['Issue Key'] == 'PROJ-123'

    def test_export_json_format(self, sample_timesheet_data):
        """Test JSON export structure."""
        from export_timesheets import format_json
        json_output = format_json(sample_timesheet_data)

        # Parse and verify JSON structure
        data = json.loads(json_output)
        assert 'entries' in data
        assert 'total_seconds' in data
        assert len(data['entries']) == 2

    def test_export_includes_all_fields(self, sample_timesheet_data):
        """Test all required fields are included."""
        from export_timesheets import format_csv
        csv_output = format_csv(sample_timesheet_data)

        # Check all expected columns are present
        lines = csv_output.strip().split('\n')
        header = lines[0]

        assert 'Issue Key' in header
        assert 'Issue Summary' in header
        assert 'Author' in header
        assert 'Date' in header
        assert 'Time Spent' in header
        assert 'Seconds' in header


class TestExportFile:
    """Tests for file export."""

    def test_export_to_file(self, sample_timesheet_data, tmp_path):
        """Test writing to output file."""
        from export_timesheets import write_export

        output_file = tmp_path / "timesheet.csv"
        write_export(sample_timesheet_data, str(output_file), 'csv')

        assert output_file.exists()
        content = output_file.read_text()
        assert 'PROJ-123' in content

    def test_export_json_to_file(self, sample_timesheet_data, tmp_path):
        """Test JSON export to file."""
        from export_timesheets import write_export

        output_file = tmp_path / "timesheet.json"
        write_export(sample_timesheet_data, str(output_file), 'json')

        assert output_file.exists()
        data = json.loads(output_file.read_text())
        assert len(data['entries']) == 2
