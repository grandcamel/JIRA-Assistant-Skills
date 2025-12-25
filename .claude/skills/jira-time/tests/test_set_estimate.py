"""
Tests for set_estimate.py script.

Tests setting original and remaining estimates on JIRA issues.
"""

import pytest
from unittest.mock import Mock
import sys
from pathlib import Path

# Add paths for imports
scripts_path = str(Path(__file__).parent.parent / 'scripts')
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


class TestSetEstimate:
    """Tests for setting time estimates."""

    def test_set_original_estimate(self, mock_jira_client):
        """Test setting original estimate."""
        mock_jira_client.set_time_tracking.return_value = None
        mock_jira_client.get_time_tracking.return_value = {
            'originalEstimate': '2d',
            'originalEstimateSeconds': 57600,
            'remainingEstimate': '2d',
            'remainingEstimateSeconds': 57600
        }

        from set_estimate import set_estimate
        result = set_estimate(
            mock_jira_client, 'PROJ-123',
            original_estimate='2d'
        )

        mock_jira_client.set_time_tracking.assert_called_once()
        call_args = mock_jira_client.set_time_tracking.call_args
        assert call_args[1]['original_estimate'] == '2d'
        assert result['originalEstimate'] == '2d'

    def test_set_remaining_estimate(self, mock_jira_client):
        """Test setting remaining estimate."""
        mock_jira_client.set_time_tracking.return_value = None
        mock_jira_client.get_time_tracking.return_value = {
            'originalEstimate': '2d',
            'originalEstimateSeconds': 57600,
            'remainingEstimate': '1d 4h',
            'remainingEstimateSeconds': 43200
        }

        from set_estimate import set_estimate
        result = set_estimate(
            mock_jira_client, 'PROJ-123',
            remaining_estimate='1d 4h'
        )

        call_args = mock_jira_client.set_time_tracking.call_args
        assert call_args[1]['remaining_estimate'] == '1d 4h'

    def test_set_both_estimates(self, mock_jira_client):
        """Test setting both estimates together."""
        mock_jira_client.set_time_tracking.return_value = None
        mock_jira_client.get_time_tracking.return_value = {
            'originalEstimate': '3d',
            'originalEstimateSeconds': 86400,
            'remainingEstimate': '2d',
            'remainingEstimateSeconds': 57600
        }

        from set_estimate import set_estimate
        result = set_estimate(
            mock_jira_client, 'PROJ-123',
            original_estimate='3d',
            remaining_estimate='2d'
        )

        call_args = mock_jira_client.set_time_tracking.call_args
        assert call_args[1]['original_estimate'] == '3d'
        assert call_args[1]['remaining_estimate'] == '2d'


class TestSetEstimateValidation:
    """Tests for input validation."""

    def test_set_estimate_invalid_format(self, mock_jira_client):
        """Test validation of time format."""
        from set_estimate import set_estimate
        from error_handler import ValidationError

        with pytest.raises(ValidationError):
            set_estimate(mock_jira_client, 'PROJ-123', original_estimate='invalid')

    def test_set_estimate_no_values(self, mock_jira_client):
        """Test error when no estimate values provided."""
        from set_estimate import set_estimate
        from error_handler import ValidationError

        with pytest.raises(ValidationError):
            set_estimate(mock_jira_client, 'PROJ-123')


class TestSetEstimateErrors:
    """Tests for error handling."""

    def test_set_estimate_issue_not_found(self, mock_jira_client):
        """Test error when issue doesn't exist."""
        from error_handler import NotFoundError

        mock_jira_client.set_time_tracking.side_effect = NotFoundError(
            "Issue PROJ-999 not found"
        )

        from set_estimate import set_estimate

        with pytest.raises(NotFoundError):
            set_estimate(mock_jira_client, 'PROJ-999', original_estimate='2d')
