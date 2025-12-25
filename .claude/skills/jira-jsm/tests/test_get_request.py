"""
Tests for get_request.py script.

Tests viewing JSM service requests with SLA info, participants, and field values.
"""

import pytest
from unittest.mock import patch, Mock
import json
from pathlib import Path
import sys

scripts_path = str(Path(__file__).parent.parent / 'scripts')
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

import get_request


class TestGetRequest:
    """Test request retrieval functionality."""

    def test_get_request_basic(self, mock_jira_client, sample_request_response):
        """Test fetching request with all details."""
        mock_jira_client.get_request.return_value = sample_request_response

        result = get_request.get_service_request('SD-101')

        assert result['issueKey'] == 'SD-101'
        assert result['requestTypeId'] == '10'
        mock_jira_client.get_request.assert_called_once_with('SD-101', expand=None)

    def test_get_request_with_sla(self, mock_jira_client, sample_request_with_sla):
        """Test fetching request with SLA information."""
        mock_jira_client.get_request.return_value = sample_request_with_sla

        result = get_request.get_service_request('SD-101', show_sla=True)

        call_args = mock_jira_client.get_request.call_args
        assert 'sla' in call_args[1]['expand']

    def test_get_request_with_participants(self, mock_jira_client, sample_request_response):
        """Test fetching request with participant list."""
        mock_jira_client.get_request.return_value = sample_request_response

        result = get_request.get_service_request('SD-101', show_participants=True)

        call_args = mock_jira_client.get_request.call_args
        assert 'participant' in call_args[1]['expand']

    def test_get_request_format_text(self, mock_jira_client, sample_request_response):
        """Test human-readable output."""
        mock_jira_client.get_request.return_value = sample_request_response

        output = get_request.format_request_text(sample_request_response)

        assert 'SD-101' in output
        assert 'Email not working' in output
        assert 'Waiting for support' in output

    def test_get_request_format_json(self, mock_jira_client, sample_request_response):
        """Test JSON output format."""
        mock_jira_client.get_request.return_value = sample_request_response

        output = get_request.format_request_json(sample_request_response)

        data = json.loads(output)
        assert data['issueKey'] == 'SD-101'

    def test_get_request_show_field_values(self, mock_jira_client, sample_request_response):
        """Test displaying all request field values."""
        mock_jira_client.get_request.return_value = sample_request_response

        output = get_request.format_request_text(sample_request_response, show_fields=True)

        assert 'Summary' in output
        assert 'Description' in output

    def test_get_request_show_portal_link(self, mock_jira_client, sample_request_response):
        """Test displaying customer portal link."""
        mock_jira_client.get_request.return_value = sample_request_response

        output = get_request.format_request_text(sample_request_response)

        links = sample_request_response['_links']
        assert links['web'] in output

    def test_get_request_not_found(self, mock_jira_client):
        """Test error when request doesn't exist."""
        from error_handler import NotFoundError

        mock_jira_client.get_request.side_effect = NotFoundError("Request not found")

        with pytest.raises(NotFoundError, match="Request not found"):
            get_request.get_service_request('SD-999')
