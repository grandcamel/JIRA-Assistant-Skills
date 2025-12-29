"""
Tests for list_request_types.py script.
"""

import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


def test_list_request_types(mock_jira_client):
    """Test fetching all request types for a service desk."""
    from list_request_types import list_request_types

    mock_jira_client.get_request_types.return_value = {
        "values": [
            {"id": "25", "name": "Get IT help", "description": "Request help", "issueTypeId": "10001"},
            {"id": "26", "name": "Report incident", "description": "Report problem", "issueTypeId": "10002"}
        ],
        "size": 2
    }

    with patch('list_request_types.get_jira_client', return_value=mock_jira_client):
        result = list_request_types("1")

        assert result is not None
        assert 'values' in result
        assert len(result['values']) == 2


def test_request_type_required_fields(mock_jira_client):
    """Test that each request type has id, name, description, issueTypeId."""
    from list_request_types import list_request_types

    mock_jira_client.get_request_types.return_value = {
        "values": [
            {"id": "25", "name": "Get IT help", "description": "Request help", "issueTypeId": "10001"}
        ],
        "size": 1
    }

    with patch('list_request_types.get_jira_client', return_value=mock_jira_client):
        result = list_request_types("1")

        for rt in result['values']:
            assert 'id' in rt
            assert 'name' in rt
            assert 'description' in rt
            assert 'issueTypeId' in rt


def test_format_text_output(mock_jira_client, capsys):
    """Test human-readable table output."""
    from list_request_types import format_request_types_text

    request_types = {
        "values": [
            {"id": "25", "name": "Get IT help", "description": "Request help", "issueTypeId": "10001"},
            {"id": "26", "name": "Report incident", "description": "Report problem", "issueTypeId": "10002"}
        ],
        "size": 2
    }

    format_request_types_text(request_types, "IT Service Desk")

    captured = capsys.readouterr()
    assert 'Request Types' in captured.out
    assert 'Get IT help' in captured.out
    assert 'Report incident' in captured.out
    assert 'Total: 2 request types' in captured.out


def test_format_json_output(mock_jira_client):
    """Test JSON output format."""
    from list_request_types import format_request_types_json

    request_types = {
        "values": [
            {"id": "25", "name": "Get IT help", "description": "Request help", "issueTypeId": "10001"}
        ],
        "size": 1
    }

    json_output = format_request_types_json(request_types)
    parsed = json.loads(json_output)

    assert 'values' in parsed
    assert len(parsed['values']) == 1


def test_filter_by_name(mock_jira_client):
    """Test filtering request types by name pattern."""
    from list_request_types import filter_request_types

    request_types = {
        "values": [
            {"id": "25", "name": "Get IT help", "description": "Request help", "issueTypeId": "10001"},
            {"id": "26", "name": "Report incident", "description": "Report problem", "issueTypeId": "10002"}
        ],
        "size": 2
    }

    filtered = filter_request_types(request_types, name_filter="incident")

    assert len(filtered['values']) == 1
    assert filtered['values'][0]['name'] == "Report incident"


def test_show_issue_type_mapping(mock_jira_client, capsys):
    """Test showing underlying JIRA issue type."""
    from list_request_types import format_request_types_text

    request_types = {
        "values": [
            {"id": "25", "name": "Get IT help", "description": "Request help", "issueTypeId": "10001"}
        ],
        "size": 1
    }

    format_request_types_text(request_types, "IT Service Desk", show_issue_types=True)

    captured = capsys.readouterr()
    assert 'Issue Type' in captured.out or '10001' in captured.out


def test_service_desk_not_found(mock_jira_client):
    """Test error when service desk doesn't exist."""
    from list_request_types import list_request_types
    from jira_assistant_skills_lib import JiraError

    mock_jira_client.get_request_types.side_effect = JiraError("Service desk not found")

    with patch('list_request_types.get_jira_client', return_value=mock_jira_client):
        with pytest.raises(JiraError, match="Service desk not found"):
            list_request_types("999")


def test_empty_request_types(capsys):
    """Test output when service desk has no request types."""
    from list_request_types import format_request_types_text

    empty_result = {'values': [], 'size': 0}
    format_request_types_text(empty_result, "IT Service Desk")

    captured = capsys.readouterr()
    assert 'No request types found' in captured.out
