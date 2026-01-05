"""
Tests for get_request_type_fields.py script.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def test_get_request_type_fields(mock_jira_client):
    """Test fetching fields for a request type."""
    from get_request_type_fields import get_request_type_fields

    mock_jira_client.get_request_type_fields.return_value = {
        "requestTypeFields": [
            {
                "fieldId": "summary",
                "name": "Summary",
                "required": True,
                "jiraSchema": {"type": "string"},
            },
            {
                "fieldId": "description",
                "name": "Description",
                "required": False,
                "jiraSchema": {"type": "string"},
            },
        ],
        "canRaiseOnBehalfOf": False,
        "canAddRequestParticipants": True,
    }

    with patch(
        "get_request_type_fields.get_jira_client", return_value=mock_jira_client
    ):
        result = get_request_type_fields("1", "25")

        assert result is not None
        assert "requestTypeFields" in result
        assert len(result["requestTypeFields"]) == 2


def test_required_fields_marked(mock_jira_client):
    """Test that required fields are clearly marked."""
    from get_request_type_fields import get_request_type_fields

    mock_jira_client.get_request_type_fields.return_value = {
        "requestTypeFields": [
            {"fieldId": "summary", "name": "Summary", "required": True},
            {"fieldId": "description", "name": "Description", "required": False},
        ]
    }

    with patch(
        "get_request_type_fields.get_jira_client", return_value=mock_jira_client
    ):
        result = get_request_type_fields("1", "25")

        fields = result["requestTypeFields"]
        assert fields[0]["required"]
        assert not fields[1]["required"]


def test_field_types(mock_jira_client):
    """Test that field types are correctly identified."""
    from get_request_type_fields import get_request_type_fields

    mock_jira_client.get_request_type_fields.return_value = {
        "requestTypeFields": [
            {
                "fieldId": "summary",
                "name": "Summary",
                "required": True,
                "jiraSchema": {"type": "string"},
            },
            {
                "fieldId": "customfield_10050",
                "name": "Category",
                "required": True,
                "jiraSchema": {"type": "option"},
            },
        ]
    }

    with patch(
        "get_request_type_fields.get_jira_client", return_value=mock_jira_client
    ):
        result = get_request_type_fields("1", "25")

        fields = result["requestTypeFields"]
        assert fields[0]["jiraSchema"]["type"] == "string"
        assert fields[1]["jiraSchema"]["type"] == "option"


def test_valid_values(mock_jira_client):
    """Test showing valid values for select/option fields."""
    from get_request_type_fields import get_request_type_fields

    mock_jira_client.get_request_type_fields.return_value = {
        "requestTypeFields": [
            {
                "fieldId": "customfield_10050",
                "name": "Category",
                "required": True,
                "validValues": [
                    {"value": "Hardware", "label": "Hardware"},
                    {"value": "Software", "label": "Software"},
                ],
            }
        ]
    }

    with patch(
        "get_request_type_fields.get_jira_client", return_value=mock_jira_client
    ):
        result = get_request_type_fields("1", "25")

        field = result["requestTypeFields"][0]
        assert "validValues" in field
        assert len(field["validValues"]) == 2


def test_default_values(mock_jira_client):
    """Test showing default values when present."""
    from get_request_type_fields import get_request_type_fields

    mock_jira_client.get_request_type_fields.return_value = {
        "requestTypeFields": [
            {
                "fieldId": "customfield_10050",
                "name": "Priority",
                "required": False,
                "defaultValues": [{"value": "Medium"}],
            }
        ]
    }

    with patch(
        "get_request_type_fields.get_jira_client", return_value=mock_jira_client
    ):
        result = get_request_type_fields("1", "25")

        field = result["requestTypeFields"][0]
        assert "defaultValues" in field
        assert len(field["defaultValues"]) == 1


def test_format_text_output(mock_jira_client, capsys):
    """Test human-readable table output with field details."""
    from get_request_type_fields import format_fields_text

    fields_data = {
        "requestTypeFields": [
            {
                "fieldId": "summary",
                "name": "Summary",
                "required": True,
                "jiraSchema": {"type": "string"},
            },
            {
                "fieldId": "description",
                "name": "Description",
                "required": False,
                "jiraSchema": {"type": "string"},
            },
        ],
        "canRaiseOnBehalfOf": False,
        "canAddRequestParticipants": True,
    }

    format_fields_text(fields_data, "Get IT help")

    captured = capsys.readouterr()
    assert "Request Type Fields" in captured.out
    assert "Summary" in captured.out
    assert "Required Fields" in captured.out


def test_format_json_output(mock_jira_client):
    """Test JSON output format."""
    from get_request_type_fields import format_fields_json

    fields_data = {
        "requestTypeFields": [
            {"fieldId": "summary", "name": "Summary", "required": True}
        ]
    }

    json_output = format_fields_json(fields_data)
    parsed = json.loads(json_output)

    assert "requestTypeFields" in parsed
    assert len(parsed["requestTypeFields"]) == 1


def test_filter_required_only(mock_jira_client):
    """Test showing only required fields."""
    from get_request_type_fields import filter_fields

    fields_data = {
        "requestTypeFields": [
            {"fieldId": "summary", "name": "Summary", "required": True},
            {"fieldId": "description", "name": "Description", "required": False},
            {"fieldId": "priority", "name": "Priority", "required": True},
        ]
    }

    filtered = filter_fields(fields_data, required_only=True)

    assert len(filtered["requestTypeFields"]) == 2
    for field in filtered["requestTypeFields"]:
        assert field["required"]
