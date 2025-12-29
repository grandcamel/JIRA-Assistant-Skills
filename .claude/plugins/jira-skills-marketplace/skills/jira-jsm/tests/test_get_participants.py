"""
Tests for get_participants.py script.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import json
from pathlib import Path

scripts_path = str(Path(__file__).parent.parent / 'scripts')
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


@pytest.fixture
def sample_participants_response():
    """Sample participants list response from API."""
    return {
        'values': [
            {'accountId': 'id1', 'emailAddress': 'john@example.com', 'displayName': 'John Smith'},
            {'accountId': 'id2', 'emailAddress': 'jane@example.com', 'displayName': 'Jane Doe'}
        ],
        'size': 2,
        'start': 0,
        'limit': 50,
        'isLastPage': True
    }


def test_get_participants_basic(mock_jira_client, sample_participants_response):
    """Test getting all participants for request."""
    mock_jira_client.get_request_participants.return_value = sample_participants_response

    with patch('get_participants.get_jira_client', return_value=mock_jira_client):
        from get_participants import get_participants_func

        result = get_participants_func('REQ-123')

        assert len(result['values']) == 2
        mock_jira_client.get_request_participants.assert_called_once()


def test_get_participants_empty():
    """Test output when no participants exist."""
    from unittest.mock import MagicMock
    mock_client = MagicMock()
    mock_client.get_request_participants.return_value = {'values': [], 'size': 0}

    with patch('get_participants.get_jira_client', return_value=mock_client):
        from get_participants import main
        with patch('sys.argv', ['get_participants.py', 'REQ-123']):
            exit_code = main()

    assert exit_code == 0


def test_get_participants_text_format(mock_jira_client, sample_participants_response, capsys):
    """Test formatted table output."""
    mock_jira_client.get_request_participants.return_value = sample_participants_response

    with patch('get_participants.get_jira_client', return_value=mock_jira_client):
        from get_participants import main
        with patch('sys.argv', ['get_participants.py', 'REQ-123']):
            main()

    captured = capsys.readouterr()
    assert 'john@example.com' in captured.out
    assert 'Jane Doe' in captured.out
    assert 'Total: 2 participant(s)' in captured.out


def test_get_participants_json_format(mock_jira_client, sample_participants_response, capsys):
    """Test JSON output with all fields."""
    mock_jira_client.get_request_participants.return_value = sample_participants_response

    with patch('get_participants.get_jira_client', return_value=mock_jira_client):
        from get_participants import main
        with patch('sys.argv', ['get_participants.py', 'REQ-123', '--output', 'json']):
            main()

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert len(data) == 2
    assert data[0]['emailAddress'] == 'john@example.com'


def test_get_participants_pagination(mock_jira_client, sample_participants_response):
    """Test pagination for requests with many participants."""
    mock_jira_client.get_request_participants.return_value = sample_participants_response

    with patch('get_participants.get_jira_client', return_value=mock_jira_client):
        from get_participants import get_participants_func

        get_participants_func('REQ-123', start=10, limit=25)

        mock_jira_client.get_request_participants.assert_called_once_with(
            'REQ-123', start=10, limit=25
        )


def test_get_participants_count_only(mock_jira_client, sample_participants_response, capsys):
    """Test getting participant count."""
    mock_jira_client.get_request_participants.return_value = sample_participants_response

    with patch('get_participants.get_jira_client', return_value=mock_jira_client):
        from get_participants import main
        with patch('sys.argv', ['get_participants.py', 'REQ-123', '--count']):
            main()

    captured = capsys.readouterr()
    assert captured.out.strip() == '2'


def test_get_participants_request_not_found(mock_jira_client, capsys):
    """Test error when request doesn't exist."""
    from error_handler import JiraError
    mock_jira_client.get_request_participants.side_effect = JiraError("Request not found")

    with patch('get_participants.get_jira_client', return_value=mock_jira_client):
        from get_participants import main
        with patch('sys.argv', ['get_participants.py', 'REQ-999']):
            exit_code = main()

    captured = capsys.readouterr()
    assert 'Request not found' in captured.err
    assert exit_code == 1
