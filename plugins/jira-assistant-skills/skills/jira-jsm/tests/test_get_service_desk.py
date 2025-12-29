"""
Tests for get_service_desk.py script.
"""

import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


def test_get_service_desk_by_id(mock_jira_client):
    """Test fetching service desk by ID."""
    from get_service_desk import get_service_desk

    mock_jira_client.get_service_desk.return_value = {
        "id": "1",
        "projectId": "10000",
        "projectName": "IT Service Desk",
        "projectKey": "ITS"
    }

    with patch('get_service_desk.get_jira_client', return_value=mock_jira_client):
        result = get_service_desk("1")

        assert result is not None
        assert result['id'] == "1"
        assert result['projectKey'] == "ITS"
        mock_jira_client.get_service_desk.assert_called_once_with("1")


def test_service_desk_details(mock_jira_client):
    """Test that all detail fields are present."""
    from get_service_desk import get_service_desk

    mock_jira_client.get_service_desk.return_value = {
        "id": "1",
        "projectId": "10000",
        "projectName": "IT Service Desk",
        "projectKey": "ITS",
        "_links": {
            "self": "https://test.atlassian.net/rest/servicedeskapi/servicedesk/1"
        }
    }

    with patch('get_service_desk.get_jira_client', return_value=mock_jira_client):
        result = get_service_desk("1")

        assert 'id' in result
        assert 'projectId' in result
        assert 'projectName' in result
        assert 'projectKey' in result


def test_format_text_output(mock_jira_client, capsys):
    """Test human-readable output with full details."""
    from get_service_desk import format_service_desk_text

    service_desk = {
        "id": "1",
        "projectId": "10000",
        "projectName": "IT Service Desk",
        "projectKey": "ITS"
    }

    format_service_desk_text(service_desk)

    captured = capsys.readouterr()
    assert 'Service Desk Details' in captured.out
    assert 'IT Service Desk' in captured.out
    assert 'ITS' in captured.out
    assert 'ID:' in captured.out


def test_format_json_output(mock_jira_client):
    """Test JSON output format."""
    from get_service_desk import format_service_desk_json

    service_desk = {
        "id": "1",
        "projectId": "10000",
        "projectName": "IT Service Desk",
        "projectKey": "ITS"
    }

    json_output = format_service_desk_json(service_desk)
    parsed = json.loads(json_output)

    assert parsed['id'] == "1"
    assert parsed['projectKey'] == "ITS"


def test_service_desk_not_found(mock_jira_client):
    """Test error when service desk ID doesn't exist."""
    from get_service_desk import get_service_desk
    from jira_assistant_skills_lib import JiraError

    mock_jira_client.get_service_desk.side_effect = JiraError("Service desk not found")

    with patch('get_service_desk.get_jira_client', return_value=mock_jira_client):
        with pytest.raises(JiraError, match="Service desk not found"):
            get_service_desk("999")


def test_show_request_type_count(mock_jira_client, capsys):
    """Test showing number of request types available."""
    from get_service_desk import format_service_desk_text

    service_desk = {
        "id": "1",
        "projectId": "10000",
        "projectName": "IT Service Desk",
        "projectKey": "ITS"
    }

    # Mock request types call
    mock_jira_client.get_request_types.return_value = {
        "values": [{"id": "25"}, {"id": "26"}, {"id": "27"}],
        "size": 3
    }

    with patch('get_service_desk.get_jira_client', return_value=mock_jira_client):
        format_service_desk_text(service_desk, show_request_types=True, client=mock_jira_client)

    captured = capsys.readouterr()
    assert 'Request Types' in captured.out or '3' in captured.out
