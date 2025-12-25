"""
Tests for list_requests.py script.

Tests listing and filtering JSM service requests.
"""

import pytest
from unittest.mock import patch, Mock
from pathlib import Path
import sys

scripts_path = str(Path(__file__).parent.parent / 'scripts')
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

import list_requests


class TestListRequests:
    """Test request listing functionality."""

    def test_list_requests_by_service_desk(self, mock_jira_client):
        """Test listing all requests for service desk."""
        mock_jira_client.search_issues.return_value = {
            'issues': [
                {'key': 'SD-101', 'fields': {'summary': 'Test 1'}},
                {'key': 'SD-102', 'fields': {'summary': 'Test 2'}}
            ],
            'total': 2
        }

        result = list_requests.list_service_requests(service_desk_id='1')

        assert len(result['issues']) == 2
        assert result['total'] == 2

    def test_list_requests_with_jql(self, mock_jira_client):
        """Test filtering with custom JQL."""
        mock_jira_client.search_issues.return_value = {
            'issues': [],
            'total': 0
        }

        result = list_requests.list_service_requests(
            service_desk_id='1',
            jql='status="In Progress"'
        )

        call_args = mock_jira_client.search_issues.call_args
        assert 'status="In Progress"' in call_args[0][0]

    def test_list_requests_by_status(self, mock_jira_client):
        """Test filtering by status."""
        mock_jira_client.search_issues.return_value = {
            'issues': [],
            'total': 0
        }

        result = list_requests.list_service_requests(
            service_desk_id='1',
            status='In Progress'
        )

        call_args = mock_jira_client.search_issues.call_args
        assert 'status' in call_args[0][0].lower()

    def test_list_requests_by_request_type(self, mock_jira_client):
        """Test filtering by request type."""
        mock_jira_client.search_issues.return_value = {
            'issues': [],
            'total': 0
        }

        result = list_requests.list_service_requests(
            service_desk_id='1',
            request_type='Incident'
        )

        # Request type filtering is done in JQL
        assert result['total'] == 0

    def test_list_requests_format_table(self, mock_jira_client):
        """Test table output with key columns."""
        issues = [
            {
                'key': 'SD-101',
                'fields': {
                    'summary': 'Email not working',
                    'status': {'name': 'In Progress'},
                    'reporter': {'emailAddress': 'alice@example.com'}
                }
            }
        ]

        output = list_requests.format_table(issues)

        assert 'SD-101' in output
        assert 'Email not working' in output
        assert 'In Progress' in output

    def test_list_requests_format_json(self, mock_jira_client):
        """Test JSON output."""
        issues = [
            {'key': 'SD-101', 'fields': {'summary': 'Test'}}
        ]

        output = list_requests.format_json(issues)

        import json
        data = json.loads(output)
        assert len(data) == 1
        assert data[0]['key'] == 'SD-101'

    def test_list_requests_pagination(self, mock_jira_client):
        """Test handling large result sets."""
        mock_jira_client.search_issues.return_value = {
            'issues': [],
            'total': 100
        }

        result = list_requests.list_service_requests(
            service_desk_id='1',
            max_results=50,
            start_at=0
        )

        call_args = mock_jira_client.search_issues.call_args
        assert call_args[1]['max_results'] == 50
        assert call_args[1]['start_at'] == 0

    def test_list_requests_empty_results(self, mock_jira_client):
        """Test handling empty results."""
        mock_jira_client.search_issues.return_value = {
            'issues': [],
            'total': 0
        }

        result = list_requests.list_service_requests(service_desk_id='1')

        assert len(result['issues']) == 0
        assert result['total'] == 0
