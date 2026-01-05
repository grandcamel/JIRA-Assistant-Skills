"""
Tests for get_organization.py script.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

scripts_path = str(Path(__file__).parent.parent / "scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


@pytest.fixture
def sample_organization_detail():
    """Sample organization detail response from API."""
    return {
        "id": "1",
        "name": "Acme Corporation",
        "_links": {
            "self": "https://example.atlassian.net/rest/servicedeskapi/organization/1"
        },
    }


def test_get_organization_basic(mock_jira_client, sample_organization_detail):
    """Test getting organization details by ID."""
    mock_jira_client.get_organization.return_value = sample_organization_detail

    with patch("get_organization.get_jira_client", return_value=mock_jira_client):
        from get_organization import get_organization_func

        result = get_organization_func(organization_id=1)

        assert result["id"] == "1"
        assert result["name"] == "Acme Corporation"
        mock_jira_client.get_organization.assert_called_once_with(1)


def test_get_organization_text_format(
    mock_jira_client, sample_organization_detail, capsys
):
    """Test formatted text output."""
    mock_jira_client.get_organization.return_value = sample_organization_detail

    with patch("get_organization.get_jira_client", return_value=mock_jira_client):
        from get_organization import main

        with patch("sys.argv", ["get_organization.py", "1"]):
            main()

    captured = capsys.readouterr()
    assert "Acme Corporation" in captured.out
    assert "ID: 1" in captured.out


def test_get_organization_json_format(
    mock_jira_client, sample_organization_detail, capsys
):
    """Test JSON output with all fields."""
    mock_jira_client.get_organization.return_value = sample_organization_detail

    with patch("get_organization.get_jira_client", return_value=mock_jira_client):
        from get_organization import main

        with patch("sys.argv", ["get_organization.py", "1", "--output", "json"]):
            main()

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["id"] == "1"
    assert data["name"] == "Acme Corporation"


def test_get_organization_not_found(mock_jira_client, capsys):
    """Test error when organization doesn't exist."""
    from jira_assistant_skills_lib import JiraError

    mock_jira_client.get_organization.side_effect = JiraError("Organization not found")

    with patch("get_organization.get_jira_client", return_value=mock_jira_client):
        from get_organization import main

        with patch("sys.argv", ["get_organization.py", "999"]):
            exit_code = main()

    captured = capsys.readouterr()
    assert "Organization not found" in captured.err
    assert exit_code == 1


def test_get_organization_verbose_output(
    mock_jira_client, sample_organization_detail, capsys
):
    """Test verbose mode showing full response."""
    mock_jira_client.get_organization.return_value = sample_organization_detail

    with patch("get_organization.get_jira_client", return_value=mock_jira_client):
        from get_organization import main

        with patch("sys.argv", ["get_organization.py", "1", "--verbose"]):
            main()

    captured = capsys.readouterr()
    assert "Full response" in captured.out


def test_get_organization_network_error(mock_jira_client, capsys):
    """Test handling network/API errors."""
    from jira_assistant_skills_lib import JiraError

    mock_jira_client.get_organization.side_effect = JiraError("Network error")

    with patch("get_organization.get_jira_client", return_value=mock_jira_client):
        from get_organization import main

        with patch("sys.argv", ["get_organization.py", "1"]):
            exit_code = main()

    captured = capsys.readouterr()
    assert "Network error" in captured.err
    assert exit_code == 1


def test_get_organization_success(mock_jira_client, sample_organization_detail):
    """Test successful retrieval."""
    mock_jira_client.get_organization.return_value = sample_organization_detail

    with patch("get_organization.get_jira_client", return_value=mock_jira_client):
        from get_organization import main

        with patch("sys.argv", ["get_organization.py", "1"]):
            exit_code = main()

    assert exit_code == 0
