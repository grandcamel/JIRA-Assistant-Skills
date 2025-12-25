"""Tests for decline_request.py - Decline approval request."""

import pytest
from unittest.mock import Mock, patch


def test_decline_request(mock_jira_client):
    """Test declining an approval request."""
    declined_approval = {
        "id": "10050",
        "name": "Change Approval",
        "finalDecision": "decline",
        "completedDate": "2025-01-17T14:30:00.000+0000"
    }
    mock_jira_client.answer_approval.return_value = declined_approval

    from decline_request import main
    with patch('decline_request.get_jira_client', return_value=mock_jira_client):
        with patch('builtins.input', return_value='yes'):
            result = main(['REQ-123', '--approval-id', '10050'])

    assert result == 0
    mock_jira_client.answer_approval.assert_called_once_with('REQ-123', '10050', 'decline')


def test_decline_request_not_pending(mock_jira_client):
    """Test error when approval already completed."""
    from error_handler import JiraError

    mock_jira_client.answer_approval.side_effect = JiraError("Approval is not pending")

    from decline_request import main
    with patch('decline_request.get_jira_client', return_value=mock_jira_client):
        with patch('builtins.input', return_value='yes'):
            result = main(['REQ-123', '--approval-id', '10050'])

    assert result == 1


def test_decline_request_not_approver(mock_jira_client):
    """Test error when user is not an approver."""
    from error_handler import PermissionError

    mock_jira_client.answer_approval.side_effect = PermissionError("Not an approver")

    from decline_request import main
    with patch('decline_request.get_jira_client', return_value=mock_jira_client):
        with patch('builtins.input', return_value='yes'):
            result = main(['REQ-123', '--approval-id', '10050'])

    assert result == 1


def test_decline_with_confirmation(mock_jira_client, sample_approval_pending):
    """Test confirmation prompt."""
    mock_jira_client.get_request_approval.return_value = sample_approval_pending
    declined_approval = {**sample_approval_pending, "finalDecision": "decline"}
    mock_jira_client.answer_approval.return_value = declined_approval

    from decline_request import main
    with patch('decline_request.get_jira_client', return_value=mock_jira_client):
        with patch('builtins.input', return_value='yes'):
            result = main(['REQ-123', '--approval-id', '10050'])

    assert result == 0


def test_decline_dry_run(mock_jira_client, sample_approval_pending, capsys):
    """Test dry-run mode."""
    mock_jira_client.get_request_approval.return_value = sample_approval_pending

    from decline_request import main
    with patch('decline_request.get_jira_client', return_value=mock_jira_client):
        result = main(['REQ-123', '--approval-id', '10050', '--dry-run'])

    assert result == 0
    captured = capsys.readouterr()
    assert 'DRY RUN' in captured.out or 'would decline' in captured.out.lower()
    mock_jira_client.answer_approval.assert_not_called()


def test_decline_request_output(mock_jira_client, capsys):
    """Test output shows decline result."""
    declined_approval = {
        "id": "10050",
        "name": "Change Approval",
        "finalDecision": "decline",
        "completedDate": "2025-01-17T14:30:00.000+0000"
    }
    mock_jira_client.get_request_approval.return_value = {
        "id": "10050",
        "name": "Change Approval",
        "finalDecision": "pending"
    }
    mock_jira_client.answer_approval.return_value = declined_approval

    from decline_request import main
    with patch('decline_request.get_jira_client', return_value=mock_jira_client):
        with patch('builtins.input', return_value='yes'):
            result = main(['REQ-123', '--approval-id', '10050'])

    assert result == 0
    captured = capsys.readouterr()
    assert 'DECLINED' in captured.out or 'decline' in captured.out.lower()
