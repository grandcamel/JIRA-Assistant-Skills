"""Tests for get_approvals.py - Get pending approvals for request."""

import pytest
from unittest.mock import Mock, patch


def test_get_all_approvals(mock_jira_client, sample_approvals_response):
    """Test fetching all approvals for request."""
    mock_jira_client.get_request_approvals.return_value = sample_approvals_response

    from get_approvals import main
    with patch('get_approvals.get_jira_client', return_value=mock_jira_client):
        result = main(['REQ-123'])

    assert result == 0
    mock_jira_client.get_request_approvals.assert_called_once()


def test_get_approval_by_id(mock_jira_client, sample_approval_pending):
    """Test fetching specific approval by ID."""
    mock_jira_client.get_request_approval.return_value = sample_approval_pending

    from get_approvals import main
    with patch('get_approvals.get_jira_client', return_value=mock_jira_client):
        result = main(['REQ-123', '--id', '10050'])

    assert result == 0
    mock_jira_client.get_request_approval.assert_called_once_with('REQ-123', '10050')


def test_get_approvals_filter_pending(mock_jira_client, sample_approvals_response):
    """Test filtering to pending approvals only."""
    mock_jira_client.get_request_approvals.return_value = sample_approvals_response

    from get_approvals import main
    with patch('get_approvals.get_jira_client', return_value=mock_jira_client):
        result = main(['REQ-123', '--pending'])

    assert result == 0
    # Default should show pending only


def test_get_approvals_all_statuses(mock_jira_client):
    """Test showing all approvals (pending, approved, declined)."""
    all_statuses_response = {
        "values": [
            {"id": "10050", "name": "Pending", "finalDecision": "pending"},
            {"id": "10051", "name": "Approved", "finalDecision": "approve"},
            {"id": "10052", "name": "Declined", "finalDecision": "decline"}
        ],
        "start": 0,
        "limit": 100,
        "isLastPage": True
    }
    mock_jira_client.get_request_approvals.return_value = all_statuses_response

    from get_approvals import main
    with patch('get_approvals.get_jira_client', return_value=mock_jira_client):
        result = main(['REQ-123', '--all'])

    assert result == 0


def test_get_approvals_empty(mock_jira_client, capsys):
    """Test handling request with no approvals."""
    empty_response = {
        "values": [],
        "start": 0,
        "limit": 100,
        "isLastPage": True
    }
    mock_jira_client.get_request_approvals.return_value = empty_response

    from get_approvals import main
    with patch('get_approvals.get_jira_client', return_value=mock_jira_client):
        result = main(['REQ-123'])

    assert result == 0
    captured = capsys.readouterr()
    assert 'No approvals' in captured.out or '0 approval' in captured.out


def test_format_text_output(mock_jira_client, sample_approvals_response, capsys):
    """Test human-readable table output."""
    mock_jira_client.get_request_approvals.return_value = sample_approvals_response

    from get_approvals import main
    with patch('get_approvals.get_jira_client', return_value=mock_jira_client):
        result = main(['REQ-123'])

    assert result == 0
    captured = capsys.readouterr()
    # Should show approval status and approvers
    assert 'pending' in captured.out.lower() or 'PENDING' in captured.out
    assert 'approve' in captured.out.lower() or 'decline' in captured.out.lower()


def test_format_json_output(mock_jira_client, sample_approvals_response, capsys):
    """Test JSON output format."""
    mock_jira_client.get_request_approvals.return_value = sample_approvals_response

    from get_approvals import main
    with patch('get_approvals.get_jira_client', return_value=mock_jira_client):
        result = main(['REQ-123', '--output', 'json'])

    assert result == 0
    captured = capsys.readouterr()
    # Should be valid JSON
    import json
    data = json.loads(captured.out)
    assert 'values' in data or isinstance(data, list)
