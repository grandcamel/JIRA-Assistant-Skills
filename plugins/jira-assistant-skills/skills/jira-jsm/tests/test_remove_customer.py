"""
Tests for remove_customer.py script.

Following TDD methodology - these tests are written first
and should initially fail until implementation is complete.
"""

import sys
from pathlib import Path
from unittest.mock import patch

scripts_path = str(Path(__file__).parent.parent / "scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


def test_remove_single_customer(mock_jira_client):
    """Test removing single customer by account ID."""
    mock_jira_client.remove_customers_from_service_desk.return_value = None

    with patch("remove_customer.get_jira_client", return_value=mock_jira_client):
        from remove_customer import remove_customer_from_service_desk

        remove_customer_from_service_desk("SD-1", ["5b10ac8d82e05b22cc7d4ef5"])

        mock_jira_client.remove_customers_from_service_desk.assert_called_once_with(
            "SD-1", ["5b10ac8d82e05b22cc7d4ef5"]
        )


def test_remove_multiple_customers(mock_jira_client):
    """Test removing multiple customers at once."""
    mock_jira_client.remove_customers_from_service_desk.return_value = None

    with patch("remove_customer.get_jira_client", return_value=mock_jira_client):
        from remove_customer import remove_customer_from_service_desk

        account_ids = ["5b10ac8d82e05b22cc7d4ef5", "5b109f2e9729b51b54dc274d"]
        remove_customer_from_service_desk("SD-1", account_ids)

        mock_jira_client.remove_customers_from_service_desk.assert_called_once_with(
            "SD-1", account_ids
        )


def test_remove_customer_parse_comma_separated(mock_jira_client):
    """Test parsing comma-separated account IDs."""
    with patch("remove_customer.get_jira_client", return_value=mock_jira_client):
        from remove_customer import parse_account_ids

        result = parse_account_ids("id1,id2,id3")
        assert result == ["id1", "id2", "id3"]


def test_remove_customer_dry_run(mock_jira_client, capsys):
    """Test preview without making changes."""
    with patch("remove_customer.get_jira_client", return_value=mock_jira_client):
        from remove_customer import main

        with patch(
            "sys.argv",
            [
                "remove_customer.py",
                "SD-1",
                "--account-id",
                "5b10ac8d82e05b22cc7d4ef5",
                "--dry-run",
            ],
        ):
            main()

    # Should NOT call API in dry-run
    mock_jira_client.remove_customers_from_service_desk.assert_not_called()

    captured = capsys.readouterr()
    assert "DRY RUN" in captured.out or "Would remove" in captured.out


def test_remove_customer_confirmation_yes_flag(mock_jira_client):
    """Test --yes flag skips confirmation."""
    mock_jira_client.remove_customers_from_service_desk.return_value = None

    with patch("remove_customer.get_jira_client", return_value=mock_jira_client):
        from remove_customer import main

        with patch(
            "sys.argv",
            [
                "remove_customer.py",
                "SD-1",
                "--account-id",
                "5b10ac8d82e05b22cc7d4ef5",
                "--yes",
            ],
        ):
            main()

        # Should call API when --yes provided
        mock_jira_client.remove_customers_from_service_desk.assert_called_once()


def test_remove_customer_profile_flag(mock_jira_client):
    """Test --profile flag is honored."""
    mock_jira_client.remove_customers_from_service_desk.return_value = None

    with patch(
        "remove_customer.get_jira_client", return_value=mock_jira_client
    ) as mock_get_client:
        from remove_customer import main

        with patch(
            "sys.argv",
            [
                "remove_customer.py",
                "SD-1",
                "--account-id",
                "5b10ac8d82e05b22cc7d4ef5",
                "--yes",
                "--profile",
                "production",
            ],
        ):
            main()

        mock_get_client.assert_called_once_with("production")
