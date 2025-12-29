"""
Tests for get_request_status.py script.

Tests viewing JSM request status history with time calculations.
"""

import pytest
from unittest.mock import patch, Mock
from pathlib import Path
import sys

scripts_path = str(Path(__file__).parent.parent / 'scripts')
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

import get_request_status


@pytest.mark.jsm
@pytest.mark.unit
class TestGetRequestStatus:
    """Test status history functionality."""

    def test_get_status_history(self, mock_jira_client, sample_status_history):
        """Test fetching complete status history."""
        mock_jira_client.get_request_status.return_value = sample_status_history

        result = get_request_status.get_status_history('SD-101')

        assert len(result['values']) == 3
        mock_jira_client.get_request_status.assert_called_once_with('SD-101')

    def test_status_history_with_durations(self, mock_jira_client, sample_status_history):
        """Test calculating time in each status."""
        mock_jira_client.get_request_status.return_value = sample_status_history

        durations = get_request_status.calculate_durations(sample_status_history['values'])

        assert 'Open' in durations
        assert 'In Progress' in durations

    def test_status_history_format_timeline(self, mock_jira_client, sample_status_history):
        """Test timeline output format."""
        mock_jira_client.get_request_status.return_value = sample_status_history

        output = get_request_status.format_timeline(sample_status_history['values'], show_durations=True)

        assert 'Open' in output
        assert 'In Progress' in output
        assert 'Resolved' in output

    def test_status_history_format_json(self, mock_jira_client, sample_status_history):
        """Test JSON output."""
        import json

        output = get_request_status.format_json(sample_status_history['values'])

        data = json.loads(output)
        assert len(data) == 3

    def test_status_history_empty(self, mock_jira_client):
        """Test when only creation status exists."""
        mock_jira_client.get_request_status.return_value = {
            'values': [
                {
                    'status': 'Open',
                    'statusCategory': 'NEW',
                    'statusDate': {
                        'iso8601': '2025-01-15T10:30:00+0000',
                        'epochMillis': 1736936400000
                    }
                }
            ]
        }

        result = get_request_status.get_status_history('SD-101')

        assert len(result['values']) == 1

    def test_status_history_request_not_found(self, mock_jira_client):
        """Test error when request doesn't exist."""
        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.get_request_status.side_effect = NotFoundError("Request not found")

        with pytest.raises(NotFoundError, match="Request not found"):
            get_request_status.get_status_history('SD-999')

    def test_format_duration(self):
        """Test duration formatting."""
        # 30 minutes
        assert '30m' in get_request_status.format_duration(1800000)

        # 3.5 hours
        assert '3h 30m' in get_request_status.format_duration(12600000)

    def test_calculate_metrics(self, sample_status_history):
        """Test calculating status change metrics."""
        metrics = get_request_status.calculate_metrics(sample_status_history['values'])

        assert metrics['total_time'] > 0
        assert metrics['status_changes'] == 3
