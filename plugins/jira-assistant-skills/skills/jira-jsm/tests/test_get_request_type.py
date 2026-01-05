"""
Tests for get_request_type.py script.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def test_get_request_type(mock_jira_client):
    """Test fetching request type details."""
    from get_request_type import get_request_type

    mock_jira_client.get_request_type.return_value = {
        "id": "25",
        "name": "Get IT help",
        "description": "Request help from IT",
        "helpText": "Please provide details",
        "issueTypeId": "10001",
        "serviceDeskId": "1",
    }

    with patch("get_request_type.get_jira_client", return_value=mock_jira_client):
        result = get_request_type("1", "25")

        assert result is not None
        assert result["id"] == "25"
        assert result["name"] == "Get IT help"


def test_request_type_details(mock_jira_client):
    """Test that all detail fields are present."""
    from get_request_type import get_request_type

    mock_jira_client.get_request_type.return_value = {
        "id": "25",
        "name": "Get IT help",
        "description": "Request help from IT",
        "helpText": "Please provide details",
        "issueTypeId": "10001",
        "serviceDeskId": "1",
    }

    with patch("get_request_type.get_jira_client", return_value=mock_jira_client):
        result = get_request_type("1", "25")

        assert "id" in result
        assert "name" in result
        assert "description" in result
        assert "issueTypeId" in result


def test_format_text_output(mock_jira_client, capsys):
    """Test human-readable output with full details."""
    from get_request_type import format_request_type_text

    request_type = {
        "id": "25",
        "name": "Get IT help",
        "description": "Request help from IT",
        "helpText": "Please provide details",
        "issueTypeId": "10001",
        "serviceDeskId": "1",
    }

    format_request_type_text(request_type)

    captured = capsys.readouterr()
    assert "Request Type Details" in captured.out
    assert "Get IT help" in captured.out
    assert "Request help from IT" in captured.out


def test_format_json_output(mock_jira_client):
    """Test JSON output format."""
    from get_request_type import format_request_type_json

    request_type = {
        "id": "25",
        "name": "Get IT help",
        "description": "Request help from IT",
    }

    json_output = format_request_type_json(request_type)
    parsed = json.loads(json_output)

    assert parsed["id"] == "25"
    assert parsed["name"] == "Get IT help"


def test_request_type_not_found(mock_jira_client):
    """Test error when request type doesn't exist."""
    from get_request_type import get_request_type

    from jira_assistant_skills_lib import JiraError

    mock_jira_client.get_request_type.side_effect = JiraError("Request type not found")

    with patch("get_request_type.get_jira_client", return_value=mock_jira_client):
        with pytest.raises(JiraError, match="Request type not found"):
            get_request_type("1", "999")


def test_show_help_text(mock_jira_client, capsys):
    """Test showing request type help text for customers."""
    from get_request_type import format_request_type_text

    request_type = {
        "id": "25",
        "name": "Get IT help",
        "description": "Request help from IT",
        "helpText": "Please provide detailed information about your issue",
    }

    format_request_type_text(request_type)

    captured = capsys.readouterr()
    assert "Help Text" in captured.out or "Please provide detailed" in captured.out


def test_show_icon_info(mock_jira_client, capsys):
    """Test showing request type icon information."""
    from get_request_type import format_request_type_text

    request_type = {
        "id": "25",
        "name": "Get IT help",
        "description": "Request help from IT",
        "icon": {
            "id": "10000",
            "_links": {"iconUrls": {"48x48": "https://example.com/icon.png"}},
        },
    }

    format_request_type_text(request_type)

    captured = capsys.readouterr()
    assert "Icon" in captured.out or "10000" in captured.out
