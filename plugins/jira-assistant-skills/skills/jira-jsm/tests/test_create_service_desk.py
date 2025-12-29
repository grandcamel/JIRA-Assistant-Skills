"""
Tests for create_service_desk.py script.
"""

import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


def test_create_service_desk(mock_jira_client):
    """Test creating a new service desk."""
    from create_service_desk import create_service_desk

    mock_jira_client.create_service_desk.return_value = {
        "id": "5",
        "projectId": "10005",
        "projectName": "New Service Desk",
        "projectKey": "NSD"
    }

    with patch('create_service_desk.get_jira_client', return_value=mock_jira_client):
        result = create_service_desk("New Service Desk", "NSD", "com.atlassian.servicedesk:simplified-it-service-desk")

        assert result is not None
        assert result['projectKey'] == "NSD"
        assert result['projectName'] == "New Service Desk"


def test_validate_project_key(mock_jira_client):
    """Test project key validation."""
    from create_service_desk import validate_project_key

    # Valid keys
    assert validate_project_key("NSD") == True
    assert validate_project_key("IT") == True
    assert validate_project_key("HR") == True

    # Invalid keys
    assert validate_project_key("n") == False  # Too short
    assert validate_project_key("TOOLONGKEY1") == False  # Too long (11 chars)
    assert validate_project_key("123") == False  # No letters
    assert validate_project_key("new-key") == False  # Invalid chars


def test_dry_run_mode(mock_jira_client, capsys):
    """Test dry-run mode without creating."""
    from create_service_desk import format_create_preview

    format_create_preview("New Service Desk", "NSD", "com.atlassian.servicedesk:simplified-it-service-desk")

    captured = capsys.readouterr()
    assert 'DRY RUN' in captured.out or 'Preview' in captured.out
    assert 'New Service Desk' in captured.out
    assert 'NSD' in captured.out


def test_format_text_output(mock_jira_client, capsys):
    """Test human-readable output."""
    from create_service_desk import format_service_desk_created_text

    service_desk = {
        "id": "5",
        "projectId": "10005",
        "projectName": "New Service Desk",
        "projectKey": "NSD"
    }

    format_service_desk_created_text(service_desk)

    captured = capsys.readouterr()
    assert 'Created Service Desk' in captured.out or 'Successfully created' in captured.out
    assert 'NSD' in captured.out


def test_format_json_output(mock_jira_client):
    """Test JSON output format."""
    from create_service_desk import format_service_desk_created_json

    service_desk = {
        "id": "5",
        "projectId": "10005",
        "projectName": "New Service Desk",
        "projectKey": "NSD"
    }

    json_output = format_service_desk_created_json(service_desk)
    parsed = json.loads(json_output)

    assert parsed['projectKey'] == "NSD"


def test_list_available_templates(mock_jira_client, capsys):
    """Test listing available project templates."""
    from create_service_desk import list_available_templates

    list_available_templates()

    captured = capsys.readouterr()
    assert 'Available Templates' in captured.out or 'com.atlassian.servicedesk' in captured.out


def test_admin_permission_required(mock_jira_client):
    """Test that admin permission is required."""
    from create_service_desk import create_service_desk
    from error_handler import JiraError

    mock_jira_client.create_service_desk.side_effect = JiraError("Insufficient permissions")

    with patch('create_service_desk.get_jira_client', return_value=mock_jira_client):
        with pytest.raises(JiraError, match="Insufficient permissions"):
            create_service_desk("New Service Desk", "NSD", "com.atlassian.servicedesk:simplified-it-service-desk")
