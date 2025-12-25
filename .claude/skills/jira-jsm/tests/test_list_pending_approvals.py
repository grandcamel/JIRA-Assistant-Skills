"""Tests for list_pending_approvals.py - List all pending approvals (agent view)."""

import pytest
from unittest.mock import Mock, patch


def test_list_all_pending_approvals(mock_jira_client):
    """Test listing all pending approvals for current user."""
    # Mock search results
    search_response = {
        "issues": [
            {
                "key": "SD-789",
                "fields": {"summary": "Database schema change"}
            },
            {
                "key": "SD-678",
                "fields": {"summary": "New server deployment"}
            }
        ]
    }

    # Mock approvals for each request
    approvals_sd789 = {
        "values": [
            {
                "id": "10055",
                "name": "Change Approval",
                "finalDecision": "pending",
                "canAnswerApproval": True,
                "createdDate": "2025-01-17T09:00:00.000+0000"
            }
        ]
    }

    approvals_sd678 = {
        "values": [
            {
                "id": "10054",
                "name": "Budget Approval",
                "finalDecision": "pending",
                "canAnswerApproval": True,
                "createdDate": "2025-01-17T08:30:00.000+0000"
            }
        ]
    }

    mock_jira_client.search_issues.return_value = search_response
    mock_jira_client.get_request_approvals.side_effect = [approvals_sd789, approvals_sd678]

    from list_pending_approvals import main
    with patch('list_pending_approvals.get_jira_client', return_value=mock_jira_client):
        result = main([])

    assert result == 0
    assert mock_jira_client.search_issues.call_count >= 1


def test_list_approvals_by_project(mock_jira_client):
    """Test filtering by service desk project."""
    search_response = {
        "issues": [
            {"key": "SD-789", "fields": {"summary": "Test"}}
        ]
    }
    approvals_response = {
        "values": [
            {
                "id": "10055",
                "name": "Approval",
                "finalDecision": "pending",
                "canAnswerApproval": True,
                "createdDate": "2025-01-17T09:00:00.000+0000"
            }
        ]
    }

    mock_jira_client.search_issues.return_value = search_response
    mock_jira_client.get_request_approvals.return_value = approvals_response

    from list_pending_approvals import main
    with patch('list_pending_approvals.get_jira_client', return_value=mock_jira_client):
        result = main(['--project', 'SD'])

    assert result == 0


def test_list_approvals_by_user(mock_jira_client):
    """Test listing approvals for specific user (admin only)."""
    search_response = {
        "issues": [
            {"key": "SD-789", "fields": {"summary": "Test"}}
        ]
    }
    approvals_response = {
        "values": [
            {
                "id": "10055",
                "name": "Approval",
                "finalDecision": "pending",
                "canAnswerApproval": True,
                "createdDate": "2025-01-17T09:00:00.000+0000"
            }
        ]
    }

    mock_jira_client.search_issues.return_value = search_response
    mock_jira_client.get_request_approvals.return_value = approvals_response

    from list_pending_approvals import main
    with patch('list_pending_approvals.get_jira_client', return_value=mock_jira_client):
        result = main(['--user', 'alice@company.com'])

    assert result == 0


def test_list_approvals_empty(mock_jira_client, capsys):
    """Test handling no pending approvals."""
    mock_jira_client.search_issues.return_value = {"issues": []}

    from list_pending_approvals import main
    with patch('list_pending_approvals.get_jira_client', return_value=mock_jira_client):
        result = main([])

    assert result == 0
    captured = capsys.readouterr()
    assert 'No pending approvals' in captured.out or '0 pending' in captured.out


def test_format_text_output(mock_jira_client, capsys):
    """Test human-readable table output."""
    search_response = {
        "issues": [
            {"key": "SD-789", "fields": {"summary": "Database schema change"}}
        ]
    }
    approvals_response = {
        "values": [
            {
                "id": "10055",
                "name": "Change Approval",
                "finalDecision": "pending",
                "canAnswerApproval": True,
                "createdDate": "2025-01-17T09:00:00.000+0000"
            }
        ]
    }

    mock_jira_client.search_issues.return_value = search_response
    mock_jira_client.get_request_approvals.return_value = approvals_response

    from list_pending_approvals import main
    with patch('list_pending_approvals.get_jira_client', return_value=mock_jira_client):
        result = main([])

    assert result == 0
    captured = capsys.readouterr()
    # Should show request, approval, and approvers
    assert 'SD-789' in captured.out
    assert '10055' in captured.out


def test_format_json_output(mock_jira_client, capsys):
    """Test JSON output format."""
    search_response = {
        "issues": [
            {"key": "SD-789", "fields": {"summary": "Database schema change"}}
        ]
    }
    approvals_response = {
        "values": [
            {
                "id": "10055",
                "name": "Change Approval",
                "finalDecision": "pending",
                "canAnswerApproval": True,
                "createdDate": "2025-01-17T09:00:00.000+0000"
            }
        ]
    }

    mock_jira_client.search_issues.return_value = search_response
    mock_jira_client.get_request_approvals.return_value = approvals_response

    from list_pending_approvals import main
    with patch('list_pending_approvals.get_jira_client', return_value=mock_jira_client):
        result = main(['--output', 'json'])

    assert result == 0
    captured = capsys.readouterr()
    # Should be valid JSON
    import json
    data = json.loads(captured.out)
    assert isinstance(data, list)


def test_efficient_api_calls(mock_jira_client):
    """Test that API calls are batched efficiently."""
    search_response = {
        "issues": [
            {"key": f"SD-{i}", "fields": {"summary": f"Request {i}"}}
            for i in range(5)
        ]
    }

    approvals_response = {
        "values": [
            {
                "id": "10055",
                "name": "Approval",
                "finalDecision": "pending",
                "canAnswerApproval": True,
                "createdDate": "2025-01-17T09:00:00.000+0000"
            }
        ]
    }

    mock_jira_client.search_issues.return_value = search_response
    mock_jira_client.get_request_approvals.return_value = approvals_response

    from list_pending_approvals import main
    with patch('list_pending_approvals.get_jira_client', return_value=mock_jira_client):
        result = main([])

    assert result == 0
    # Should call search once, then get_request_approvals for each request
    assert mock_jira_client.search_issues.call_count == 1
    assert mock_jira_client.get_request_approvals.call_count == 5
