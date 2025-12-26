"""
Tests for transition_request.py script.

Tests transitioning JSM requests with SLA awareness and public/internal comments.
"""

import pytest
from unittest.mock import patch, Mock
from pathlib import Path
import sys

scripts_path = str(Path(__file__).parent.parent / 'scripts')
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

import transition_request


@pytest.mark.jsm
@pytest.mark.unit
class TestTransitionRequest:
    """Test request transition functionality."""

    def test_transition_request_by_id(self, mock_jira_client):
        """Test transitioning request using transition ID."""
        mock_jira_client.transition_request.return_value = None

        transition_request.transition_service_request(
            issue_key='SD-101',
            transition_id='11'
        )

        mock_jira_client.transition_request.assert_called_once_with(
            'SD-101', '11', comment=None, public=True
        )

    def test_transition_request_by_name(self, mock_jira_client, sample_transitions_response):
        """Test transitioning request using transition name."""
        mock_jira_client.get_request_transitions.return_value = sample_transitions_response['values']
        mock_jira_client.transition_request.return_value = None

        transition_request.transition_service_request(
            issue_key='SD-101',
            transition_name='Start Progress'
        )

        # Should lookup transition ID
        mock_jira_client.get_request_transitions.assert_called_once_with('SD-101')
        mock_jira_client.transition_request.assert_called_once_with(
            'SD-101', '11', comment=None, public=True
        )

    def test_transition_with_comment(self, mock_jira_client):
        """Test adding comment during transition."""
        mock_jira_client.transition_request.return_value = None

        transition_request.transition_service_request(
            issue_key='SD-101',
            transition_id='11',
            comment='Starting investigation'
        )

        call_args = mock_jira_client.transition_request.call_args
        assert call_args[1]['comment'] == 'Starting investigation'

    def test_transition_with_public_comment(self, mock_jira_client):
        """Test adding public (customer-visible) comment."""
        mock_jira_client.transition_request.return_value = None

        transition_request.transition_service_request(
            issue_key='SD-101',
            transition_id='11',
            comment='Please provide more details',
            public=True
        )

        call_args = mock_jira_client.transition_request.call_args
        assert call_args[1]['public'] is True

    def test_transition_with_internal_comment(self, mock_jira_client):
        """Test adding internal (agent-only) comment."""
        mock_jira_client.transition_request.return_value = None

        transition_request.transition_service_request(
            issue_key='SD-101',
            transition_id='11',
            comment='Escalating to L2',
            public=False
        )

        call_args = mock_jira_client.transition_request.call_args
        assert call_args[1]['public'] is False

    def test_transition_invalid_transition(self, mock_jira_client, sample_transitions_response):
        """Test error when transition not available."""
        mock_jira_client.get_request_transitions.return_value = sample_transitions_response['values']

        with pytest.raises(ValueError, match="Transition .* not found"):
            transition_request.transition_service_request(
                issue_key='SD-101',
                transition_name='Invalid Transition'
            )

    def test_transition_request_not_found(self, mock_jira_client):
        """Test error when request doesn't exist."""
        from error_handler import NotFoundError

        mock_jira_client.transition_request.side_effect = NotFoundError("Request not found")

        with pytest.raises(NotFoundError, match="Request not found"):
            transition_request.transition_service_request(
                issue_key='SD-999',
                transition_id='11'
            )
