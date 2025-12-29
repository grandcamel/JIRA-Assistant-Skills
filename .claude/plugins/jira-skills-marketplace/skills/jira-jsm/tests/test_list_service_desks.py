"""
Tests for list_service_desks.py script.
"""

import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


def test_list_all_service_desks(mock_jira_client):
    """Test fetching all available service desks."""
    from list_service_desks import list_service_desks

    with patch('list_service_desks.get_jira_client', return_value=mock_jira_client):
        result = list_service_desks()

        assert result is not None
        assert 'values' in result
        assert len(result['values']) == 3
        mock_jira_client.get_service_desks.assert_called_once()


def test_service_desk_has_required_fields(mock_jira_client):
    """Test that each service desk has id, projectId, projectName, projectKey."""
    from list_service_desks import list_service_desks

    with patch('list_service_desks.get_jira_client', return_value=mock_jira_client):
        result = list_service_desks()

        for sd in result['values']:
            assert 'id' in sd
            assert 'projectId' in sd
            assert 'projectName' in sd
            assert 'projectKey' in sd


def test_format_text_output(mock_jira_client, capsys):
    """Test human-readable table output."""
    from list_service_desks import format_service_desks_text

    service_desks = mock_jira_client.get_service_desks()
    format_service_desks_text(service_desks)

    captured = capsys.readouterr()
    assert 'Available Service Desks' in captured.out
    assert 'IT Service Desk' in captured.out
    assert 'HR Service Desk' in captured.out
    assert 'Total: 3 service desks' in captured.out


def test_format_json_output(mock_jira_client):
    """Test JSON output format."""
    from list_service_desks import format_service_desks_json

    service_desks = mock_jira_client.get_service_desks()
    json_output = format_service_desks_json(service_desks)

    parsed = json.loads(json_output)
    assert 'values' in parsed
    assert len(parsed['values']) == 3


def test_filter_by_project_key(mock_jira_client):
    """Test filtering service desks by project key pattern."""
    from list_service_desks import filter_service_desks

    service_desks = mock_jira_client.get_service_desks()
    filtered = filter_service_desks(service_desks, project_key_filter='ITS')

    assert len(filtered['values']) == 1
    assert filtered['values'][0]['projectKey'] == 'ITS'


def test_empty_service_desks(capsys):
    """Test output when no service desks exist."""
    from list_service_desks import format_service_desks_text

    empty_result = {'values': [], 'size': 0}
    format_service_desks_text(empty_result)

    captured = capsys.readouterr()
    assert 'No service desks found' in captured.out


def test_pagination_handling(mock_jira_client):
    """Test handling paginated results (limit/start)."""
    from list_service_desks import list_service_desks

    with patch('list_service_desks.get_jira_client', return_value=mock_jira_client):
        result = list_service_desks(start=0, limit=2)

        mock_jira_client.get_service_desks.assert_called_with(start=0, limit=2)
