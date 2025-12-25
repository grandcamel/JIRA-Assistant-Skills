"""
Tests for get_time_tracking.py script.

Tests fetching time tracking summary from JIRA issues.
"""

import pytest
from unittest.mock import Mock
import sys
from pathlib import Path

# Add paths for imports
scripts_path = str(Path(__file__).parent.parent / 'scripts')
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


class TestGetTimeTracking:
    """Tests for getting time tracking info."""

    def test_get_time_tracking_full(self, mock_jira_client, sample_time_tracking):
        """Test fetching complete time tracking info."""
        mock_jira_client.get_time_tracking.return_value = sample_time_tracking

        from get_time_tracking import get_time_tracking
        result = get_time_tracking(mock_jira_client, 'PROJ-123')

        mock_jira_client.get_time_tracking.assert_called_once_with('PROJ-123')
        assert result['originalEstimate'] == '2d'
        assert result['remainingEstimate'] == '1d 4h'
        assert result['timeSpent'] == '4h'

    def test_get_time_tracking_no_work_logged(self, mock_jira_client):
        """Test when no work has been logged."""
        mock_jira_client.get_time_tracking.return_value = {
            'originalEstimate': '2d',
            'originalEstimateSeconds': 57600,
            'remainingEstimate': '2d',
            'remainingEstimateSeconds': 57600
        }

        from get_time_tracking import get_time_tracking
        result = get_time_tracking(mock_jira_client, 'PROJ-123')

        assert result.get('timeSpent') is None
        assert result.get('timeSpentSeconds') is None

    def test_get_time_tracking_no_estimates(self, mock_jira_client):
        """Test when estimates not set."""
        mock_jira_client.get_time_tracking.return_value = {}

        from get_time_tracking import get_time_tracking
        result = get_time_tracking(mock_jira_client, 'PROJ-123')

        assert result.get('originalEstimate') is None
        assert result.get('remainingEstimate') is None


class TestGetTimeTrackingProgress:
    """Tests for progress calculations."""

    def test_get_time_tracking_calculate_progress(self, mock_jira_client, sample_time_tracking):
        """Test calculating completion percentage."""
        mock_jira_client.get_time_tracking.return_value = sample_time_tracking

        from get_time_tracking import get_time_tracking, calculate_progress
        result = get_time_tracking(mock_jira_client, 'PROJ-123')
        progress = calculate_progress(result)

        # 4h logged of 16h (2d) = 25%
        assert progress == 25

    def test_calculate_progress_no_estimate(self, mock_jira_client):
        """Test progress when no estimate set."""
        from get_time_tracking import calculate_progress

        result = {'timeSpentSeconds': 7200}
        progress = calculate_progress(result)

        assert progress is None

    def test_calculate_progress_no_work(self, mock_jira_client):
        """Test progress when no work logged."""
        from get_time_tracking import calculate_progress

        result = {
            'originalEstimateSeconds': 57600
        }
        progress = calculate_progress(result)

        assert progress == 0
