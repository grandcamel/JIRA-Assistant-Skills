"""
Tests for list_notification_schemes.py - TDD approach.

Test cases per implementation plan:
1. test_list_all_notification_schemes - Test fetching all available schemes
2. test_scheme_has_required_fields - Test that each scheme has id, name, description
3. test_format_text_output - Test human-readable table output
4. test_format_json_output - Test JSON output format
5. test_filter_by_name - Test filtering schemes by name pattern
6. test_show_event_count - Test showing number of events per scheme
7. test_empty_notification_schemes - Test output when no schemes exist
8. test_pagination_handling - Test handling paginated results
"""

import sys
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from io import StringIO
import pytest

# Add scripts and shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


class TestListAllNotificationSchemes:
    """Test fetching all available notification schemes."""

    def test_list_all_notification_schemes(self, mock_jira_client, sample_notification_schemes):
        """Test fetching all available notification schemes."""
        from list_notification_schemes import list_notification_schemes

        # Setup mock
        mock_jira_client.get_notification_schemes.return_value = sample_notification_schemes

        # Execute
        result = list_notification_schemes(client=mock_jira_client)

        # Verify
        assert result['total'] == 3
        assert len(result['schemes']) == 3
        mock_jira_client.get_notification_schemes.assert_called_once()


class TestSchemeRequiredFields:
    """Test that each scheme has required fields."""

    def test_scheme_has_required_fields(self, mock_jira_client, sample_notification_schemes):
        """Test that each scheme has id, name, description."""
        from list_notification_schemes import list_notification_schemes

        # Setup mock
        mock_jira_client.get_notification_schemes.return_value = sample_notification_schemes

        # Execute
        result = list_notification_schemes(client=mock_jira_client)

        # Verify all schemes have required fields
        for scheme in result['schemes']:
            assert 'id' in scheme
            assert 'name' in scheme
            assert 'description' in scheme


class TestFormatTextOutput:
    """Test human-readable table output."""

    def test_format_text_output(self, mock_jira_client, sample_notification_schemes):
        """Test human-readable table output."""
        from list_notification_schemes import list_notification_schemes, format_text_output

        # Setup mock
        mock_jira_client.get_notification_schemes.return_value = sample_notification_schemes

        # Execute
        result = list_notification_schemes(client=mock_jira_client)
        output = format_text_output(result)

        # Verify output contains expected content
        assert 'Default Notification Scheme' in output
        assert 'Development Team Notifications' in output
        assert 'Customer Support Notifications' in output
        assert '10000' in output
        assert 'Total: 3' in output


class TestFormatJsonOutput:
    """Test JSON output format."""

    def test_format_json_output(self, mock_jira_client, sample_notification_schemes):
        """Test JSON output format."""
        from list_notification_schemes import list_notification_schemes, format_json_output

        # Setup mock
        mock_jira_client.get_notification_schemes.return_value = sample_notification_schemes

        # Execute
        result = list_notification_schemes(client=mock_jira_client)
        output = format_json_output(result)

        # Verify valid JSON
        parsed = json.loads(output)
        assert parsed['total'] == 3
        assert len(parsed['schemes']) == 3


class TestFilterByName:
    """Test filtering schemes by name pattern."""

    def test_filter_by_name(self, mock_jira_client, sample_notification_schemes):
        """Test filtering schemes by name pattern."""
        from list_notification_schemes import list_notification_schemes

        # Setup mock
        mock_jira_client.get_notification_schemes.return_value = sample_notification_schemes

        # Execute with filter
        result = list_notification_schemes(
            client=mock_jira_client,
            filter_name='Default'
        )

        # Verify only matching schemes returned
        assert result['total'] == 1
        assert result['schemes'][0]['name'] == 'Default Notification Scheme'

    def test_filter_by_name_case_insensitive(self, mock_jira_client, sample_notification_schemes):
        """Test that name filtering is case-insensitive."""
        from list_notification_schemes import list_notification_schemes

        # Setup mock
        mock_jira_client.get_notification_schemes.return_value = sample_notification_schemes

        # Execute with lowercase filter
        result = list_notification_schemes(
            client=mock_jira_client,
            filter_name='development'
        )

        # Verify matching scheme found
        assert result['total'] == 1
        assert 'Development' in result['schemes'][0]['name']


class TestShowEventCount:
    """Test showing number of configured events per scheme."""

    def test_show_event_count(self, mock_jira_client):
        """Test showing number of configured events per scheme."""
        from list_notification_schemes import list_notification_schemes

        # Setup mock with expanded schemes
        schemes_with_events = {
            'values': [
                {
                    'id': '10000',
                    'name': 'Test Scheme',
                    'description': 'Test',
                    'notificationSchemeEvents': [
                        {'event': {'id': '1'}, 'notifications': []},
                        {'event': {'id': '2'}, 'notifications': []},
                        {'event': {'id': '3'}, 'notifications': []}
                    ]
                }
            ],
            'total': 1
        }
        mock_jira_client.get_notification_schemes.return_value = schemes_with_events

        # Execute with show_events flag
        result = list_notification_schemes(
            client=mock_jira_client,
            show_events=True
        )

        # Verify event count is included
        assert result['schemes'][0]['events'] == 3

    def test_show_event_count_in_output(self, mock_jira_client):
        """Test that event count appears in text output."""
        from list_notification_schemes import list_notification_schemes, format_text_output

        # Setup mock with expanded schemes
        schemes_with_events = {
            'values': [
                {
                    'id': '10000',
                    'name': 'Test Scheme',
                    'description': 'Test',
                    'notificationSchemeEvents': [
                        {'event': {'id': '1'}, 'notifications': []},
                        {'event': {'id': '2'}, 'notifications': []},
                    ]
                }
            ],
            'total': 1
        }
        mock_jira_client.get_notification_schemes.return_value = schemes_with_events

        # Execute
        result = list_notification_schemes(client=mock_jira_client, show_events=True)
        output = format_text_output(result, show_events=True)

        # Verify event count in output
        assert 'Events' in output
        assert '2' in output


class TestEmptyNotificationSchemes:
    """Test output when no schemes exist."""

    def test_empty_notification_schemes(self, mock_jira_client, empty_notification_schemes):
        """Test output when no schemes exist."""
        from list_notification_schemes import list_notification_schemes

        # Setup mock
        mock_jira_client.get_notification_schemes.return_value = empty_notification_schemes

        # Execute
        result = list_notification_schemes(client=mock_jira_client)

        # Verify
        assert result['total'] == 0
        assert result['schemes'] == []

    def test_empty_schemes_text_output(self, mock_jira_client, empty_notification_schemes):
        """Test text output shows message when no schemes exist."""
        from list_notification_schemes import list_notification_schemes, format_text_output

        # Setup mock
        mock_jira_client.get_notification_schemes.return_value = empty_notification_schemes

        # Execute
        result = list_notification_schemes(client=mock_jira_client)
        output = format_text_output(result)

        # Verify helpful message
        assert 'No notification schemes found' in output or 'Total: 0' in output


class TestPaginationHandling:
    """Test handling paginated results."""

    def test_pagination_handling(self, mock_jira_client):
        """Test handling paginated results (startAt/maxResults)."""
        from list_notification_schemes import list_notification_schemes

        # Setup mock with paginated response
        page1 = {
            'values': [
                {'id': '10000', 'name': 'Scheme 1', 'description': 'Desc 1'},
                {'id': '10001', 'name': 'Scheme 2', 'description': 'Desc 2'}
            ],
            'startAt': 0,
            'maxResults': 2,
            'total': 5,
            'isLast': False
        }
        page2 = {
            'values': [
                {'id': '10002', 'name': 'Scheme 3', 'description': 'Desc 3'},
                {'id': '10003', 'name': 'Scheme 4', 'description': 'Desc 4'}
            ],
            'startAt': 2,
            'maxResults': 2,
            'total': 5,
            'isLast': False
        }
        page3 = {
            'values': [
                {'id': '10004', 'name': 'Scheme 5', 'description': 'Desc 5'}
            ],
            'startAt': 4,
            'maxResults': 2,
            'total': 5,
            'isLast': True
        }

        # Return different pages based on start_at
        def mock_get_schemes(start_at=0, max_results=50, expand=None):
            if start_at == 0:
                return page1
            elif start_at == 2:
                return page2
            else:
                return page3

        mock_jira_client.get_notification_schemes.side_effect = mock_get_schemes

        # Execute with pagination
        result = list_notification_schemes(
            client=mock_jira_client,
            max_results=2,
            fetch_all=True
        )

        # Verify all schemes are returned
        assert result['total'] == 5
        assert len(result['schemes']) == 5

    def test_single_page_results(self, mock_jira_client, sample_notification_schemes):
        """Test that single page results don't make extra API calls."""
        from list_notification_schemes import list_notification_schemes

        # Setup mock
        mock_jira_client.get_notification_schemes.return_value = sample_notification_schemes

        # Execute
        result = list_notification_schemes(client=mock_jira_client)

        # Verify only one API call made
        assert mock_jira_client.get_notification_schemes.call_count == 1
        assert result['total'] == 3
