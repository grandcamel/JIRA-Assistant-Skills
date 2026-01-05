"""
Tests for remove_from_organization.py script.
"""

import sys
from pathlib import Path
from unittest.mock import patch

scripts_path = str(Path(__file__).parent.parent / "scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


def test_remove_single_user_from_organization(mock_jira_client):
    """Test removing single user by account ID."""
    mock_jira_client.remove_users_from_organization.return_value = None

    with patch(
        "remove_from_organization.get_jira_client", return_value=mock_jira_client
    ):
        from remove_from_organization import remove_users_from_organization_func

        remove_users_from_organization_func(1, ["5b10ac8d82e05b22cc7d4ef5"])

        mock_jira_client.remove_users_from_organization.assert_called_once_with(
            1, ["5b10ac8d82e05b22cc7d4ef5"]
        )


def test_remove_multiple_users_from_organization(mock_jira_client):
    """Test removing multiple users at once."""
    mock_jira_client.remove_users_from_organization.return_value = None

    with patch(
        "remove_from_organization.get_jira_client", return_value=mock_jira_client
    ):
        from remove_from_organization import remove_users_from_organization_func

        remove_users_from_organization_func(1, ["id1", "id2", "id3"])

        mock_jira_client.remove_users_from_organization.assert_called_once()
        call_args = mock_jira_client.remove_users_from_organization.call_args[0]
        assert len(call_args[1]) == 3


def test_parse_account_ids_remove():
    """Test parsing comma-separated account IDs."""
    with patch("remove_from_organization.get_jira_client"):
        from remove_from_organization import parse_account_ids

        ids = parse_account_ids("id1,id2,id3")
        assert ids == ["id1", "id2", "id3"]


def test_remove_users_confirmation_required(capsys):
    """Test confirmation prompt before removal."""
    with patch("remove_from_organization.get_jira_client"):
        from remove_from_organization import main

        with patch(
            "sys.argv", ["remove_from_organization.py", "1", "--account-id", "id1"]
        ):
            exit_code = main()

    captured = capsys.readouterr()
    assert "Confirmation required" in captured.err
    assert exit_code == 1


def test_remove_users_with_yes_flag(mock_jira_client, capsys):
    """Test removing with --yes flag."""
    mock_jira_client.remove_users_from_organization.return_value = None

    with patch(
        "remove_from_organization.get_jira_client", return_value=mock_jira_client
    ):
        from remove_from_organization import main

        with patch(
            "sys.argv",
            ["remove_from_organization.py", "1", "--account-id", "id1,id2", "--yes"],
        ):
            exit_code = main()

    captured = capsys.readouterr()
    assert "Successfully removed 2 user(s)" in captured.out
    assert exit_code == 0


def test_remove_users_dry_run(capsys):
    """Test preview without making changes."""
    with patch("remove_from_organization.get_jira_client"):
        from remove_from_organization import main

        with patch(
            "sys.argv",
            [
                "remove_from_organization.py",
                "1",
                "--account-id",
                "id1,id2",
                "--dry-run",
            ],
        ):
            exit_code = main()

    captured = capsys.readouterr()
    assert "DRY RUN MODE" in captured.out
    assert "Would remove 2 user(s)" in captured.out
    assert exit_code == 0


def test_remove_users_network_error(mock_jira_client, capsys):
    """Test handling network/API errors."""
    from jira_assistant_skills_lib import JiraError

    mock_jira_client.remove_users_from_organization.side_effect = JiraError(
        "Network error"
    )

    with patch(
        "remove_from_organization.get_jira_client", return_value=mock_jira_client
    ):
        from remove_from_organization import main

        with patch(
            "sys.argv",
            ["remove_from_organization.py", "1", "--account-id", "id1", "--yes"],
        ):
            exit_code = main()

    captured = capsys.readouterr()
    assert "Network error" in captured.err
    assert exit_code == 1


def test_remove_users_empty_account_ids(capsys):
    """Test error on empty account IDs."""
    with patch("remove_from_organization.get_jira_client"):
        from remove_from_organization import main

        with patch(
            "sys.argv",
            ["remove_from_organization.py", "1", "--account-id", "", "--yes"],
        ):
            exit_code = main()

    captured = capsys.readouterr()
    assert "Invalid or empty account IDs" in captured.err
    assert exit_code == 1


def test_remove_users_permission_error(mock_jira_client, capsys):
    """Test handling insufficient permissions."""
    from jira_assistant_skills_lib import JiraError

    mock_jira_client.remove_users_from_organization.side_effect = JiraError(
        "Permission denied"
    )

    with patch(
        "remove_from_organization.get_jira_client", return_value=mock_jira_client
    ):
        from remove_from_organization import main

        with patch(
            "sys.argv",
            ["remove_from_organization.py", "1", "--account-id", "id1", "--yes"],
        ):
            exit_code = main()

    captured = capsys.readouterr()
    assert "Permission denied" in captured.err
    assert exit_code == 1


def test_remove_users_success_message(mock_jira_client, capsys):
    """Test success message after removal."""
    mock_jira_client.remove_users_from_organization.return_value = None

    with patch(
        "remove_from_organization.get_jira_client", return_value=mock_jira_client
    ):
        from remove_from_organization import main

        with patch(
            "sys.argv",
            ["remove_from_organization.py", "1", "--account-id", "id1", "--yes"],
        ):
            main()

    captured = capsys.readouterr()
    assert "Successfully removed 1 user(s)" in captured.out
