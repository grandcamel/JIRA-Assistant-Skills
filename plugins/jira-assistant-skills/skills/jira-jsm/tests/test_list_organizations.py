"""
Tests for list_organizations.py script.
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
def sample_organizations_response():
    """Sample organizations list response from API."""
    return {
        "values": [
            {"id": "1", "name": "Acme Corporation"},
            {"id": "2", "name": "Beta Industries"},
            {"id": "3", "name": "Gamma Enterprises"},
        ],
        "size": 3,
        "start": 0,
        "limit": 50,
        "isLastPage": True,
    }


def test_list_all_organizations(mock_jira_client, sample_organizations_response):
    """Test listing all organizations."""
    mock_jira_client.get_organizations.return_value = sample_organizations_response

    with patch("list_organizations.get_jira_client", return_value=mock_jira_client):
        from list_organizations import list_organizations_func

        result = list_organizations_func()

        assert len(result["values"]) == 3
        mock_jira_client.get_organizations.assert_called_once()


def test_list_organizations_pagination(mock_jira_client, sample_organizations_response):
    """Test pagination with start and limit."""
    mock_jira_client.get_organizations.return_value = sample_organizations_response

    with patch("list_organizations.get_jira_client", return_value=mock_jira_client):
        from list_organizations import list_organizations_func

        list_organizations_func(start=10, limit=25)

        mock_jira_client.get_organizations.assert_called_once_with(start=10, limit=25)


def test_list_organizations_empty():
    """Test output when no organizations exist."""
    from unittest.mock import MagicMock

    mock_client = MagicMock()
    mock_client.get_organizations.return_value = {"values": [], "size": 0}

    with patch("list_organizations.get_jira_client", return_value=mock_client):
        from list_organizations import main

        with patch("sys.argv", ["list_organizations.py"]):
            exit_code = main()

    assert exit_code == 0


def test_list_organizations_text_format(
    mock_jira_client, sample_organizations_response, capsys
):
    """Test formatted table output."""
    mock_jira_client.get_organizations.return_value = sample_organizations_response

    with patch("list_organizations.get_jira_client", return_value=mock_jira_client):
        from list_organizations import main

        with patch("sys.argv", ["list_organizations.py"]):
            main()

    captured = capsys.readouterr()
    assert "Acme Corporation" in captured.out
    assert "Beta Industries" in captured.out
    assert "Total: 3 organization(s)" in captured.out


def test_list_organizations_json_format(
    mock_jira_client, sample_organizations_response, capsys
):
    """Test JSON output with all fields."""
    mock_jira_client.get_organizations.return_value = sample_organizations_response

    with patch("list_organizations.get_jira_client", return_value=mock_jira_client):
        from list_organizations import main

        with patch("sys.argv", ["list_organizations.py", "--output", "json"]):
            main()

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert len(data) == 3
    assert data[0]["name"] == "Acme Corporation"


def test_list_organizations_csv_format(
    mock_jira_client, sample_organizations_response, capsys
):
    """Test CSV output."""
    mock_jira_client.get_organizations.return_value = sample_organizations_response

    with patch("list_organizations.get_jira_client", return_value=mock_jira_client):
        from list_organizations import main

        with patch("sys.argv", ["list_organizations.py", "--output", "csv"]):
            main()

    captured = capsys.readouterr()
    assert "ID,Name" in captured.out
    assert "1,Acme Corporation" in captured.out


def test_list_organizations_count_only(
    mock_jira_client, sample_organizations_response, capsys
):
    """Test getting organization count."""
    mock_jira_client.get_organizations.return_value = sample_organizations_response

    with patch("list_organizations.get_jira_client", return_value=mock_jira_client):
        from list_organizations import main

        with patch("sys.argv", ["list_organizations.py", "--count"]):
            main()

    captured = capsys.readouterr()
    assert captured.out.strip() == "3"


def test_list_organizations_network_error(mock_jira_client, capsys):
    """Test handling network/API errors."""
    from jira_assistant_skills_lib import JiraError

    mock_jira_client.get_organizations.side_effect = JiraError("Network error")

    with patch("list_organizations.get_jira_client", return_value=mock_jira_client):
        from list_organizations import main

        with patch("sys.argv", ["list_organizations.py"]):
            exit_code = main()

    captured = capsys.readouterr()
    assert "Network error" in captured.err
    assert exit_code == 1


