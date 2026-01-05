"""
Tests for remove_participant.py script.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

scripts_path = str(Path(__file__).parent.parent / "scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


@pytest.fixture
def sample_remove_participant_response():
    """Sample remove participant response from API."""
    return {"success": True}


def test_remove_single_participant(
    mock_jira_client, sample_remove_participant_response
):
    """Test removing single participant by account ID."""
    mock_jira_client.remove_request_participants.return_value = (
        sample_remove_participant_response
    )

    with patch("remove_participant.get_jira_client", return_value=mock_jira_client):
        from remove_participant import remove_participant_func

        remove_participant_func("REQ-123", account_ids=["id1"])

        mock_jira_client.remove_request_participants.assert_called_once_with(
            "REQ-123", account_ids=["id1"], usernames=None
        )


def test_remove_multiple_participants(
    mock_jira_client, sample_remove_participant_response
):
    """Test removing multiple participants at once."""
    mock_jira_client.remove_request_participants.return_value = (
        sample_remove_participant_response
    )

    with patch("remove_participant.get_jira_client", return_value=mock_jira_client):
        from remove_participant import remove_participant_func

        remove_participant_func("REQ-123", account_ids=["id1", "id2"])

        call_args = mock_jira_client.remove_request_participants.call_args
        assert len(call_args[1]["account_ids"]) == 2


def test_parse_account_ids_remove_participant():
    """Test parsing comma-separated account IDs."""
    with patch("remove_participant.get_jira_client"):
        from remove_participant import parse_account_ids

        ids = parse_account_ids("id1,id2")
        assert ids == ["id1", "id2"]


def test_remove_participants_confirmation_required(capsys):
    """Test confirmation prompt before removal."""
    with patch("remove_participant.get_jira_client"):
        from remove_participant import main

        with patch(
            "sys.argv", ["remove_participant.py", "REQ-123", "--account-id", "id1"]
        ):
            exit_code = main()

    captured = capsys.readouterr()
    assert "Confirmation required" in captured.err
    assert exit_code == 1


def test_remove_participants_with_yes_flag(
    mock_jira_client, sample_remove_participant_response, capsys
):
    """Test removing with --yes flag."""
    mock_jira_client.remove_request_participants.return_value = (
        sample_remove_participant_response
    )

    with patch("remove_participant.get_jira_client", return_value=mock_jira_client):
        from remove_participant import main

        with patch(
            "sys.argv",
            ["remove_participant.py", "REQ-123", "--account-id", "id1", "--yes"],
        ):
            exit_code = main()

    captured = capsys.readouterr()
    assert "Successfully removed 1 participant(s)" in captured.out
    assert exit_code == 0


def test_remove_participants_dry_run(capsys):
    """Test preview without making changes."""
    with patch("remove_participant.get_jira_client"):
        from remove_participant import main

        with patch(
            "sys.argv",
            [
                "remove_participant.py",
                "REQ-123",
                "--account-id",
                "id1,id2",
                "--dry-run",
            ],
        ):
            exit_code = main()

    captured = capsys.readouterr()
    assert "DRY RUN MODE" in captured.out
    assert "Would remove participants" in captured.out
    assert exit_code == 0


def test_remove_participants_network_error(mock_jira_client, capsys):
    """Test handling network/API errors."""
    from jira_assistant_skills_lib import JiraError

    mock_jira_client.remove_request_participants.side_effect = JiraError(
        "Network error"
    )

    with patch("remove_participant.get_jira_client", return_value=mock_jira_client):
        from remove_participant import main

        with patch(
            "sys.argv",
            ["remove_participant.py", "REQ-123", "--account-id", "id1", "--yes"],
        ):
            exit_code = main()

    captured = capsys.readouterr()
    assert "Network error" in captured.err
    assert exit_code == 1


def test_remove_participants_no_identifiers(capsys):
    """Test error when neither account-id nor username provided."""
    with patch("remove_participant.get_jira_client"):
        from remove_participant import main

        with patch("sys.argv", ["remove_participant.py", "REQ-123", "--yes"]):
            exit_code = main()

    captured = capsys.readouterr()
    assert "Either --account-id or --username is required" in captured.err
    assert exit_code == 1
