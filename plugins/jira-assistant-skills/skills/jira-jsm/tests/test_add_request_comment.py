"""Tests for add_request_comment.py - Add JSM comment with public/internal visibility."""

import pytest
from unittest.mock import Mock, patch, call
import sys
from io import StringIO


def test_add_public_comment(mock_jira_client, sample_comment_public):
    """Test adding public (customer-visible) comment."""
    mock_jira_client.add_request_comment.return_value = sample_comment_public

    from add_request_comment import main
    with patch('add_request_comment.get_jira_client', return_value=mock_jira_client):
        result = main(['REQ-123', '--body', 'Your issue has been resolved.'])

    assert result == 0
    mock_jira_client.add_request_comment.assert_called_once_with(
        'REQ-123',
        'Your issue has been resolved.',
        public=True
    )


def test_add_internal_comment(mock_jira_client, sample_comment_internal):
    """Test adding internal (agent-only) comment."""
    mock_jira_client.add_request_comment.return_value = sample_comment_internal

    from add_request_comment import main
    with patch('add_request_comment.get_jira_client', return_value=mock_jira_client):
        result = main(['REQ-123', '--body', 'Escalating to Tier 2', '--internal'])

    assert result == 0
    mock_jira_client.add_request_comment.assert_called_once_with(
        'REQ-123',
        'Escalating to Tier 2',
        public=False
    )


def test_add_comment_default_public(mock_jira_client, sample_comment_public):
    """Test default behavior when --internal not specified."""
    mock_jira_client.add_request_comment.return_value = sample_comment_public

    from add_request_comment import main
    with patch('add_request_comment.get_jira_client', return_value=mock_jira_client):
        result = main(['REQ-123', '--body', 'Test comment'])

    assert result == 0
    # Should default to public=True
    call_args = mock_jira_client.add_request_comment.call_args
    assert call_args[1]['public'] == True


def test_add_comment_with_body(mock_jira_client, sample_comment_public):
    """Test comment body handling."""
    mock_jira_client.add_request_comment.return_value = sample_comment_public

    from add_request_comment import main
    with patch('add_request_comment.get_jira_client', return_value=mock_jira_client):
        result = main(['REQ-123', '--body', 'Simple comment text'])

    assert result == 0
    call_args = mock_jira_client.add_request_comment.call_args
    assert call_args[0][1] == 'Simple comment text'


def test_add_comment_multiline(mock_jira_client, sample_comment_public):
    """Test multiline comment text."""
    import copy
    multiline_body = """Issue resolved.

Root cause: Database connection timeout.
Fix: Increased timeout to 30s."""

    comment_response = copy.deepcopy(sample_comment_public)
    comment_response['body'] = multiline_body
    mock_jira_client.add_request_comment.return_value = comment_response

    from add_request_comment import main
    with patch('add_request_comment.get_jira_client', return_value=mock_jira_client):
        result = main(['REQ-123', '--body', multiline_body])

    assert result == 0
    call_args = mock_jira_client.add_request_comment.call_args
    assert call_args[0][1] == multiline_body


def test_add_comment_issue_not_found(mock_jira_client):
    """Test error when request doesn't exist."""
    from jira_assistant_skills_lib import NotFoundError

    mock_jira_client.add_request_comment.side_effect = NotFoundError("Request not found")

    from add_request_comment import main
    with patch('add_request_comment.get_jira_client', return_value=mock_jira_client):
        with pytest.raises(SystemExit) as exc_info:
            result = main(['NONEXIST-999', '--body', 'Test'])

    assert exc_info.value.code == 1


def test_add_comment_not_service_desk(mock_jira_client):
    """Test error when issue is not a JSM request."""
    from jira_assistant_skills_lib import JiraError

    mock_jira_client.add_request_comment.side_effect = JiraError(
        "Issue is not a JSM request"
    )

    from add_request_comment import main
    with patch('add_request_comment.get_jira_client', return_value=mock_jira_client):
        with pytest.raises(SystemExit) as exc_info:
            result = main(['PROJ-123', '--body', 'Test'])

    assert exc_info.value.code == 1


def test_add_comment_output_format(mock_jira_client, sample_comment_public, capsys):
    """Test output shows visibility clearly."""
    mock_jira_client.add_request_comment.return_value = sample_comment_public

    from add_request_comment import main
    with patch('add_request_comment.get_jira_client', return_value=mock_jira_client):
        result = main(['REQ-123', '--body', 'Test'])

    assert result == 0
    captured = capsys.readouterr()
    # Should indicate public visibility
    assert 'Public' in captured.out or 'public' in captured.out.lower()


def test_add_comment_from_stdin(mock_jira_client, sample_comment_public, monkeypatch):
    """Test reading comment body from stdin."""
    stdin_content = "Comment from stdin"
    monkeypatch.setattr('sys.stdin', StringIO(stdin_content))

    mock_jira_client.add_request_comment.return_value = sample_comment_public

    from add_request_comment import main
    with patch('add_request_comment.get_jira_client', return_value=mock_jira_client):
        # Passing '-' or no --body should read from stdin
        result = main(['REQ-123', '--body', '-'])

    assert result == 0
    call_args = mock_jira_client.add_request_comment.call_args
    assert call_args[0][1].strip() == stdin_content
