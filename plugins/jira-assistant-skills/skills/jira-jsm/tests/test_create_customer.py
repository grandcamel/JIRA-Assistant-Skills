"""
Tests for create_customer.py script.

Following TDD methodology - these tests are written first
and should initially fail until implementation is complete.
"""

import sys
from pathlib import Path
from unittest.mock import patch

# Add scripts to path
scripts_path = str(Path(__file__).parent.parent / "scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


def test_create_customer_basic(mock_jira_client, sample_customer_response):
    """Test creating customer with email and display name."""
    mock_jira_client.create_customer.return_value = sample_customer_response

    with patch("create_customer.get_jira_client", return_value=mock_jira_client):
        from create_customer import create_customer_account

        result = create_customer_account(
            email="john@example.com", display_name="John Customer"
        )

        assert result["accountId"] == "5b10ac8d82e05b22cc7d4ef5"
        assert result["emailAddress"] == "john@example.com"
        mock_jira_client.create_customer.assert_called_once_with(
            "john@example.com", "John Customer"
        )


def test_create_customer_email_only(mock_jira_client, sample_customer_response):
    """Test creating customer with email only (display name defaults to email)."""
    mock_jira_client.create_customer.return_value = sample_customer_response

    with patch("create_customer.get_jira_client", return_value=mock_jira_client):
        from create_customer import create_customer_account

        result = create_customer_account(email="john@example.com")

        mock_jira_client.create_customer.assert_called_once()
        assert result is not None


def test_create_customer_email_validation():
    """Test email format validation before API call."""
    with patch("create_customer.get_jira_client"):
        from create_customer import validate_email

        # Valid emails
        assert validate_email("user@example.com")
        assert validate_email("user.name@example.co.uk")

        # Invalid emails
        assert not validate_email("notanemail")
        assert not validate_email("@example.com")
        assert not validate_email("user@")


def test_create_customer_json_output(
    mock_jira_client, sample_customer_response, capsys
):
    """Test JSON output format with account ID."""
    mock_jira_client.create_customer.return_value = sample_customer_response

    with patch("create_customer.get_jira_client", return_value=mock_jira_client):
        from create_customer import main

        with patch(
            "sys.argv",
            [
                "create_customer.py",
                "--email",
                "john@example.com",
                "--name",
                "John Customer",
                "--output",
                "json",
            ],
        ):
            main()

    captured = capsys.readouterr()
    assert '"accountId"' in captured.out
    assert "5b10ac8d82e05b22cc7d4ef5" in captured.out


def test_create_customer_dry_run(mock_jira_client, capsys):
    """Test dry-run mode without creating customer."""
    with patch("create_customer.get_jira_client", return_value=mock_jira_client):
        from create_customer import main

        with patch(
            "sys.argv",
            [
                "create_customer.py",
                "--email",
                "john@example.com",
                "--name",
                "John Customer",
                "--dry-run",
            ],
        ):
            main()

    # Should NOT call API in dry-run
    mock_jira_client.create_customer.assert_not_called()

    captured = capsys.readouterr()
    assert "DRY RUN" in captured.out or "Would create" in captured.out


def test_create_customer_special_characters(mock_jira_client, sample_customer_response):
    """Test customer names with special characters."""
    mock_jira_client.create_customer.return_value = sample_customer_response

    with patch("create_customer.get_jira_client", return_value=mock_jira_client):
        from create_customer import create_customer_account

        result = create_customer_account(
            email="user@example.com", display_name="O'Brien, José"
        )

        assert result is not None
        mock_jira_client.create_customer.assert_called_once_with(
            "user@example.com", "O'Brien, José"
        )
