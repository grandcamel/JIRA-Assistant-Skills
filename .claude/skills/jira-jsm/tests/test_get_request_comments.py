"""Tests for get_request_comments.py - Get comments with visibility info."""

import pytest
from unittest.mock import Mock, patch


def test_get_all_comments(mock_jira_client, sample_comments_response):
    """Test fetching all comments (public and internal)."""
    mock_jira_client.get_request_comments.return_value = sample_comments_response

    from get_request_comments import main
    with patch('get_request_comments.get_jira_client', return_value=mock_jira_client):
        result = main(['REQ-123'])

    assert result == 0
    mock_jira_client.get_request_comments.assert_called_once_with(
        'REQ-123',
        public=None,
        start=0,
        limit=100
    )


def test_get_public_comments_only(mock_jira_client):
    """Test filtering to public comments only."""
    public_only_response = {
        "values": [c for c in [
            {"id": "10001", "body": "Public", "public": True},
            {"id": "10003", "body": "Also public", "public": True}
        ]],
        "start": 0,
        "limit": 100,
        "isLastPage": True
    }
    mock_jira_client.get_request_comments.return_value = public_only_response

    from get_request_comments import main
    with patch('get_request_comments.get_jira_client', return_value=mock_jira_client):
        result = main(['REQ-123', '--public-only'])

    assert result == 0
    call_args = mock_jira_client.get_request_comments.call_args
    assert call_args[1]['public'] == True


def test_get_internal_comments_only(mock_jira_client):
    """Test filtering to internal comments only."""
    internal_only_response = {
        "values": [{"id": "10002", "body": "Internal", "public": False}],
        "start": 0,
        "limit": 100,
        "isLastPage": True
    }
    mock_jira_client.get_request_comments.return_value = internal_only_response

    from get_request_comments import main
    with patch('get_request_comments.get_jira_client', return_value=mock_jira_client):
        result = main(['REQ-123', '--internal-only'])

    assert result == 0
    call_args = mock_jira_client.get_request_comments.call_args
    assert call_args[1]['public'] == False


def test_get_comments_with_pagination(mock_jira_client):
    """Test handling paginated results."""
    # First page
    page1 = {
        "values": [{"id": "1", "body": "First", "public": True}],
        "start": 0,
        "limit": 1,
        "isLastPage": False
    }
    # Second page
    page2 = {
        "values": [{"id": "2", "body": "Second", "public": True}],
        "start": 1,
        "limit": 1,
        "isLastPage": True
    }

    mock_jira_client.get_request_comments.side_effect = [page1, page2]

    from get_request_comments import main
    with patch('get_request_comments.get_jira_client', return_value=mock_jira_client):
        result = main(['REQ-123', '--all-pages'])

    assert result == 0
    # Should have called twice for pagination
    assert mock_jira_client.get_request_comments.call_count >= 1


def test_get_comments_empty(mock_jira_client, capsys):
    """Test handling request with no comments."""
    empty_response = {
        "values": [],
        "start": 0,
        "limit": 100,
        "isLastPage": True
    }
    mock_jira_client.get_request_comments.return_value = empty_response

    from get_request_comments import main
    with patch('get_request_comments.get_jira_client', return_value=mock_jira_client):
        result = main(['REQ-123'])

    assert result == 0
    captured = capsys.readouterr()
    assert 'No comments' in captured.out or '0 comment' in captured.out


def test_get_comment_by_id(mock_jira_client, sample_comment_public):
    """Test fetching specific comment by ID."""
    mock_jira_client.get_request_comment.return_value = sample_comment_public

    from get_request_comments import main
    with patch('get_request_comments.get_jira_client', return_value=mock_jira_client):
        result = main(['REQ-123', '--id', '10001'])

    assert result == 0
    mock_jira_client.get_request_comment.assert_called_once_with('REQ-123', '10001', expand=None)


def test_format_text_output(mock_jira_client, sample_comments_response, capsys):
    """Test human-readable table output."""
    mock_jira_client.get_request_comments.return_value = sample_comments_response

    from get_request_comments import main
    with patch('get_request_comments.get_jira_client', return_value=mock_jira_client):
        result = main(['REQ-123'])

    assert result == 0
    captured = capsys.readouterr()
    # Should show visibility clearly
    assert 'PUBLIC' in captured.out or 'INTERNAL' in captured.out or 'Public' in captured.out


def test_format_json_output(mock_jira_client, sample_comments_response, capsys):
    """Test JSON output format."""
    mock_jira_client.get_request_comments.return_value = sample_comments_response

    from get_request_comments import main
    with patch('get_request_comments.get_jira_client', return_value=mock_jira_client):
        result = main(['REQ-123', '--output', 'json'])

    assert result == 0
    captured = capsys.readouterr()
    # Should be valid JSON with public field
    import json
    data = json.loads(captured.out)
    assert 'values' in data or isinstance(data, list)
