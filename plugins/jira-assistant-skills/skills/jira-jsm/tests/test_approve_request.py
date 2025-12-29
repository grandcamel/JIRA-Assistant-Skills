"""Tests for approve_request.py - Approve approval request."""

import pytest
from unittest.mock import Mock, patch


def test_approve_request(mock_jira_client, sample_approval_approved):
    """Test approving an approval request."""
    mock_jira_client.get_request_approval.return_value = sample_approval_approved
    mock_jira_client.answer_approval.return_value = sample_approval_approved

    from approve_request import main
    with patch('approve_request.get_jira_client', return_value=mock_jira_client):
        with patch('builtins.input', return_value='yes'):  # Auto-confirm
            result = main(['REQ-123', '--approval-id', '10050'])

    assert result == 0
    mock_jira_client.answer_approval.assert_called_once_with('REQ-123', '10050', 'approve')


def test_approve_request_skip_confirmation(mock_jira_client, sample_approval_approved):
    """Test --yes flag skips confirmation."""
    mock_jira_client.get_request_approval.return_value = sample_approval_approved
    mock_jira_client.answer_approval.return_value = sample_approval_approved

    from approve_request import main
    with patch('approve_request.get_jira_client', return_value=mock_jira_client):
        result = main(['REQ-123', '--approval-id', '10050', '--yes'])

    assert result == 0


def test_approve_request_not_pending(mock_jira_client, sample_approval_pending):
    """Test error when approval already completed."""
    from jira_assistant_skills_lib import JiraError

    mock_jira_client.get_request_approval.return_value = sample_approval_pending
    mock_jira_client.answer_approval.side_effect = JiraError("Approval is not pending")

    from approve_request import main
    with patch('approve_request.get_jira_client', return_value=mock_jira_client):
        with patch('builtins.input', return_value='yes'):
            with pytest.raises(SystemExit) as exc_info:
                main(['REQ-123', '--approval-id', '10050'])

    assert exc_info.value.code == 1


def test_approve_request_not_approver(mock_jira_client, sample_approval_pending):
    """Test error when user is not an approver."""
    from jira_assistant_skills_lib import PermissionError

    mock_jira_client.get_request_approval.return_value = sample_approval_pending
    mock_jira_client.answer_approval.side_effect = PermissionError("Not an approver")

    from approve_request import main
    with patch('approve_request.get_jira_client', return_value=mock_jira_client):
        with patch('builtins.input', return_value='yes'):
            with pytest.raises(SystemExit) as exc_info:
                main(['REQ-123', '--approval-id', '10050'])

    assert exc_info.value.code == 1


def test_approve_request_not_found(mock_jira_client, sample_approval_pending):
    """Test error when approval doesn't exist."""
    from jira_assistant_skills_lib import NotFoundError

    mock_jira_client.get_request_approval.return_value = sample_approval_pending
    mock_jira_client.answer_approval.side_effect = NotFoundError("Approval not found")

    from approve_request import main
    with patch('approve_request.get_jira_client', return_value=mock_jira_client):
        with patch('builtins.input', return_value='yes'):
            with pytest.raises(SystemExit) as exc_info:
                main(['REQ-123', '--approval-id', '99999'])

    assert exc_info.value.code == 1


def test_approve_request_with_confirmation(mock_jira_client, sample_approval_pending, sample_approval_approved):
    """Test confirmation prompt."""
    mock_jira_client.get_request_approval.return_value = sample_approval_pending
    mock_jira_client.answer_approval.return_value = sample_approval_approved

    from approve_request import main
    with patch('approve_request.get_jira_client', return_value=mock_jira_client):
        # User confirms
        with patch('builtins.input', return_value='yes'):
            result = main(['REQ-123', '--approval-id', '10050'])

    assert result == 0


def test_approve_request_dry_run(mock_jira_client, sample_approval_pending, capsys):
    """Test dry-run mode."""
    mock_jira_client.get_request_approval.return_value = sample_approval_pending

    from approve_request import main
    with patch('approve_request.get_jira_client', return_value=mock_jira_client):
        result = main(['REQ-123', '--approval-id', '10050', '--dry-run'])

    assert result == 0
    captured = capsys.readouterr()
    assert 'DRY RUN' in captured.out
    # Should NOT call answer_approval
    mock_jira_client.answer_approval.assert_not_called()
