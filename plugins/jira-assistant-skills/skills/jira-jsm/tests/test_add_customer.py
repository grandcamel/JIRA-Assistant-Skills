"""
Tests for add_customer.py script.

Following TDD methodology - these tests are written first
and should initially fail until implementation is complete.
"""

import sys
from pathlib import Path
from unittest.mock import patch

scripts_path = str(Path(__file__).parent.parent / "scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


def test_add_single_customer(mock_jira_client):
    """Test adding single customer by account ID."""
    mock_jira_client.add_customers_to_service_desk.return_value = None

    with patch("add_customer.get_jira_client", return_value=mock_jira_client):
        from add_customer import add_customer_to_service_desk

        add_customer_to_service_desk("SD-1", ["5b10ac8d82e05b22cc7d4ef5"])

        mock_jira_client.add_customers_to_service_desk.assert_called_once_with(
            "SD-1", ["5b10ac8d82e05b22cc7d4ef5"]
        )


def test_add_multiple_customers(mock_jira_client):
    """Test adding multiple customers at once."""
    mock_jira_client.add_customers_to_service_desk.return_value = None

    with patch("add_customer.get_jira_client", return_value=mock_jira_client):
        from add_customer import add_customer_to_service_desk

        account_ids = ["5b10ac8d82e05b22cc7d4ef5", "5b109f2e9729b51b54dc274d"]
        add_customer_to_service_desk("SD-1", account_ids)

        mock_jira_client.add_customers_to_service_desk.assert_called_once_with(
            "SD-1", account_ids
        )


def test_add_customer_parse_comma_separated(mock_jira_client):
    """Test parsing comma-separated account IDs."""
    with patch("add_customer.get_jira_client", return_value=mock_jira_client):
        from add_customer import parse_account_ids

        result = parse_account_ids("id1,id2,id3")
        assert result == ["id1", "id2", "id3"]


def test_add_customer_dry_run(mock_jira_client, capsys):
    """Test preview without making changes."""
    with patch("add_customer.get_jira_client", return_value=mock_jira_client):
        from add_customer import main

        with patch(
            "sys.argv",
            [
                "add_customer.py",
                "SD-1",
                "--account-id",
                "5b10ac8d82e05b22cc7d4ef5",
                "--dry-run",
            ],
        ):
            main()

    # Should NOT call API in dry-run
    mock_jira_client.add_customers_to_service_desk.assert_not_called()

    captured = capsys.readouterr()
    assert "DRY RUN" in captured.out or "Would add" in captured.out


def test_add_customer_validation(mock_jira_client):
    """Test account ID validation."""
    with patch("add_customer.get_jira_client", return_value=mock_jira_client):
        from add_customer import validate_account_ids

        # Valid IDs
        assert validate_account_ids(["5b10ac8d82e05b22cc7d4ef5"])

        # Invalid IDs (empty)
        assert not validate_account_ids([])
        assert not validate_account_ids([""])


def test_add_customer_profile_flag(mock_jira_client):
    """Test --profile flag is honored."""
    mock_jira_client.add_customers_to_service_desk.return_value = None

    with patch(
        "add_customer.get_jira_client", return_value=mock_jira_client
    ) as mock_get_client:
        from add_customer import main

        with patch(
            "sys.argv",
            [
                "add_customer.py",
                "SD-1",
                "--account-id",
                "5b10ac8d82e05b22cc7d4ef5",
                "--profile",
                "production",
            ],
        ):
            main()

        mock_get_client.assert_called_once_with("production")
