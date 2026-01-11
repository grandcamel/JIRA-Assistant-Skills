"""
Tests for list_customers.py script.

Following TDD methodology - these tests are written first
and should initially fail until implementation is complete.
"""

import sys
from pathlib import Path
from unittest.mock import patch

scripts_path = str(Path(__file__).parent.parent / "scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


def test_list_all_customers(mock_jira_client, sample_customers_list_response):
    """Test listing all customers for service desk."""
    mock_jira_client.get_service_desk_customers.return_value = (
        sample_customers_list_response
    )

    with patch("list_customers.get_jira_client", return_value=mock_jira_client):
        from list_customers import list_service_desk_customers

        result = list_service_desk_customers("SD-1")

        assert len(result["values"]) == 3
        mock_jira_client.get_service_desk_customers.assert_called_once()


def test_list_customers_with_query(mock_jira_client, sample_customers_list_response):
    """Test filtering customers by email/name search."""
    mock_jira_client.get_service_desk_customers.return_value = (
        sample_customers_list_response
    )

    with patch("list_customers.get_jira_client", return_value=mock_jira_client):
        from list_customers import list_service_desk_customers

        list_service_desk_customers("SD-1", query="john")

        mock_jira_client.get_service_desk_customers.assert_called_with(
            "SD-1", query="john", start=0, limit=50
        )


def test_list_customers_pagination(mock_jira_client, sample_customers_list_response):
    """Test pagination with start and limit."""
    mock_jira_client.get_service_desk_customers.return_value = (
        sample_customers_list_response
    )

    with patch("list_customers.get_jira_client", return_value=mock_jira_client):
        from list_customers import list_service_desk_customers

        list_service_desk_customers("SD-1", start=10, limit=25)

        mock_jira_client.get_service_desk_customers.assert_called_with(
            "SD-1", query=None, start=10, limit=25
        )


def test_list_customers_empty_service_desk(mock_jira_client, capsys):
    """Test output when no customers exist."""
    empty_response = {
        "size": 0,
        "start": 0,
        "limit": 50,
        "isLastPage": True,
        "values": [],
    }
    mock_jira_client.get_service_desk_customers.return_value = empty_response

    with patch("list_customers.get_jira_client", return_value=mock_jira_client):
        from list_customers import main

        with patch("sys.argv", ["list_customers.py", "SD-1"]):
            main()

    captured = capsys.readouterr()
    assert "no customers" in captured.out.lower() or "0" in captured.out


def test_list_customers_text_format(
    mock_jira_client, sample_customers_list_response, capsys
):
    """Test formatted table output."""
    mock_jira_client.get_service_desk_customers.return_value = (
        sample_customers_list_response
    )

    with patch("list_customers.get_jira_client", return_value=mock_jira_client):
        from list_customers import main

        with patch("sys.argv", ["list_customers.py", "SD-1"]):
            main()

    captured = capsys.readouterr()
    assert "john@example.com" in captured.out
    assert "Jane Smith" in captured.out
    assert "Total: 3" in captured.out or "3 customers" in captured.out


def test_list_customers_json_format(
    mock_jira_client, sample_customers_list_response, capsys
):
    """Test JSON output with all fields."""
    mock_jira_client.get_service_desk_customers.return_value = (
        sample_customers_list_response
    )

    with patch("list_customers.get_jira_client", return_value=mock_jira_client):
        from list_customers import main

        with patch("sys.argv", ["list_customers.py", "SD-1", "--output", "json"]):
            main()

    captured = capsys.readouterr()
    assert '"accountId"' in captured.out
    assert "5b10ac8d82e05b22cc7d4ef5" in captured.out


def test_list_customers_count_only(
    mock_jira_client, sample_customers_list_response, capsys
):
    """Test getting customer count without details."""
    mock_jira_client.get_service_desk_customers.return_value = (
        sample_customers_list_response
    )

    with patch("list_customers.get_jira_client", return_value=mock_jira_client):
        from list_customers import main

        with patch("sys.argv", ["list_customers.py", "SD-1", "--count"]):
            main()

    captured = capsys.readouterr()
    assert "3" in captured.out
