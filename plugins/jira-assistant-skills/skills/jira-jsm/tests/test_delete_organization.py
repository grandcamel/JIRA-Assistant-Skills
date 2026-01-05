"""
Tests for delete_organization.py script.
"""

import sys
from pathlib import Path
from unittest.mock import patch

scripts_path = str(Path(__file__).parent.parent / "scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


def test_delete_organization_basic(mock_jira_client):
    """Test deleting organization by ID."""
    mock_jira_client.delete_organization.return_value = None

    with patch("delete_organization.get_jira_client", return_value=mock_jira_client):
        from delete_organization import delete_organization_func

        delete_organization_func(organization_id=1)

        mock_jira_client.delete_organization.assert_called_once_with(1)


def test_delete_organization_confirmation_required(capsys):
    """Test confirmation prompt before deletion."""
    with patch("delete_organization.get_jira_client"):
        from delete_organization import main

        with patch("sys.argv", ["delete_organization.py", "1"]):
            exit_code = main()

    captured = capsys.readouterr()
    assert "Confirmation required" in captured.err
    assert exit_code == 1


def test_delete_organization_with_yes_flag(mock_jira_client, capsys):
    """Test forcing deletion with --yes flag."""
    mock_jira_client.delete_organization.return_value = None

    with patch("delete_organization.get_jira_client", return_value=mock_jira_client):
        from delete_organization import main

        with patch("sys.argv", ["delete_organization.py", "1", "--yes"]):
            exit_code = main()

    captured = capsys.readouterr()
    assert "Successfully deleted" in captured.out
    assert exit_code == 0


def test_delete_organization_not_found(mock_jira_client, capsys):
    """Test error when organization doesn't exist."""
    from jira_assistant_skills_lib import JiraError

    mock_jira_client.delete_organization.side_effect = JiraError(
        "Organization not found"
    )

    with patch("delete_organization.get_jira_client", return_value=mock_jira_client):
        from delete_organization import main

        with patch("sys.argv", ["delete_organization.py", "999", "--yes"]):
            exit_code = main()

    captured = capsys.readouterr()
    assert "Organization not found" in captured.err
    assert exit_code == 1


def test_delete_organization_dry_run(capsys):
    """Test preview without deleting."""
    with patch("delete_organization.get_jira_client"):
        from delete_organization import main

        with patch("sys.argv", ["delete_organization.py", "1", "--dry-run"]):
            exit_code = main()

    captured = capsys.readouterr()
    assert "DRY RUN MODE" in captured.out
    assert "Would delete organization 1" in captured.out
    assert exit_code == 0


def test_delete_organization_network_error(mock_jira_client, capsys):
    """Test handling network/API errors."""
    from jira_assistant_skills_lib import JiraError

    mock_jira_client.delete_organization.side_effect = JiraError("Network error")

    with patch("delete_organization.get_jira_client", return_value=mock_jira_client):
        from delete_organization import main

        with patch("sys.argv", ["delete_organization.py", "1", "--yes"]):
            exit_code = main()

    captured = capsys.readouterr()
    assert "Network error" in captured.err
    assert exit_code == 1


def test_delete_organization_permission_error(mock_jira_client, capsys):
    """Test handling insufficient permissions."""
    from jira_assistant_skills_lib import JiraError

    mock_jira_client.delete_organization.side_effect = JiraError("Permission denied")

    with patch("delete_organization.get_jira_client", return_value=mock_jira_client):
        from delete_organization import main

        with patch("sys.argv", ["delete_organization.py", "1", "--yes"]):
            exit_code = main()

    captured = capsys.readouterr()
    assert "Permission denied" in captured.err
    assert exit_code == 1


def test_delete_organization_success_message(mock_jira_client, capsys):
    """Test success message after deletion."""
    mock_jira_client.delete_organization.return_value = None

    with patch("delete_organization.get_jira_client", return_value=mock_jira_client):
        from delete_organization import main

        with patch("sys.argv", ["delete_organization.py", "1", "--yes"]):
            main()

    captured = capsys.readouterr()
    assert "Successfully deleted organization 1" in captured.out
