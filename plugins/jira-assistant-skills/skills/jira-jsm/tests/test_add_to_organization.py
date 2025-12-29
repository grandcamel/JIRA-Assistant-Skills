"""
Tests for add_to_organization.py script.
"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

scripts_path = str(Path(__file__).parent.parent / 'scripts')
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


def test_add_single_user_to_organization(mock_jira_client):
    """Test adding single user by account ID."""
    mock_jira_client.add_users_to_organization.return_value = None

    with patch('add_to_organization.get_jira_client', return_value=mock_jira_client):
        from add_to_organization import add_users_to_organization_func

        add_users_to_organization_func(1, ['5b10ac8d82e05b22cc7d4ef5'])

        mock_jira_client.add_users_to_organization.assert_called_once_with(
            1, ['5b10ac8d82e05b22cc7d4ef5']
        )


def test_add_multiple_users_to_organization(mock_jira_client):
    """Test adding multiple users at once."""
    mock_jira_client.add_users_to_organization.return_value = None

    with patch('add_to_organization.get_jira_client', return_value=mock_jira_client):
        from add_to_organization import add_users_to_organization_func

        add_users_to_organization_func(1, ['id1', 'id2', 'id3'])

        mock_jira_client.add_users_to_organization.assert_called_once()
        call_args = mock_jira_client.add_users_to_organization.call_args[0]
        assert len(call_args[1]) == 3


def test_parse_account_ids():
    """Test parsing comma-separated account IDs."""
    with patch('add_to_organization.get_jira_client'):
        from add_to_organization import parse_account_ids

        ids = parse_account_ids("id1,id2,id3")
        assert ids == ['id1', 'id2', 'id3']

        ids_with_spaces = parse_account_ids("id1, id2 , id3")
        assert ids_with_spaces == ['id1', 'id2', 'id3']


def test_add_users_dry_run(capsys):
    """Test preview without making changes."""
    with patch('add_to_organization.get_jira_client'):
        from add_to_organization import main
        with patch('sys.argv', ['add_to_organization.py', '1',
                                '--account-id', 'id1,id2', '--dry-run']):
            exit_code = main()

    captured = capsys.readouterr()
    assert 'DRY RUN MODE' in captured.out
    assert 'Would add 2 user(s)' in captured.out
    assert exit_code == 0


def test_add_users_success_message(mock_jira_client, capsys):
    """Test success message after adding users."""
    mock_jira_client.add_users_to_organization.return_value = None

    with patch('add_to_organization.get_jira_client', return_value=mock_jira_client):
        from add_to_organization import main
        with patch('sys.argv', ['add_to_organization.py', '1',
                                '--account-id', 'id1,id2']):
            main()

    captured = capsys.readouterr()
    assert 'Successfully added 2 user(s)' in captured.out


def test_add_users_network_error(mock_jira_client, capsys):
    """Test handling network/API errors."""
    from jira_assistant_skills_lib import JiraError
    mock_jira_client.add_users_to_organization.side_effect = JiraError("Network error")

    with patch('add_to_organization.get_jira_client', return_value=mock_jira_client):
        from add_to_organization import main
        with patch('sys.argv', ['add_to_organization.py', '1',
                                '--account-id', 'id1']):
            exit_code = main()

    captured = capsys.readouterr()
    assert 'Network error' in captured.err
    assert exit_code == 1


def test_add_users_empty_account_ids(capsys):
    """Test error on empty account IDs."""
    with patch('add_to_organization.get_jira_client'):
        from add_to_organization import main
        with patch('sys.argv', ['add_to_organization.py', '1', '--account-id', '']):
            exit_code = main()

    captured = capsys.readouterr()
    assert 'Invalid or empty account IDs' in captured.err
    assert exit_code == 1


def test_add_users_permission_error(mock_jira_client, capsys):
    """Test handling insufficient permissions."""
    from jira_assistant_skills_lib import JiraError
    mock_jira_client.add_users_to_organization.side_effect = JiraError("Permission denied")

    with patch('add_to_organization.get_jira_client', return_value=mock_jira_client):
        from add_to_organization import main
        with patch('sys.argv', ['add_to_organization.py', '1', '--account-id', 'id1']):
            exit_code = main()

    captured = capsys.readouterr()
    assert 'Permission denied' in captured.err
    assert exit_code == 1


def test_add_users_multiple_batches(mock_jira_client):
    """Test adding large number of users."""
    mock_jira_client.add_users_to_organization.return_value = None

    with patch('add_to_organization.get_jira_client', return_value=mock_jira_client):
        from add_to_organization import main
        ids = ','.join([f'id{i}' for i in range(10)])
        with patch('sys.argv', ['add_to_organization.py', '1', '--account-id', ids]):
            exit_code = main()

    assert exit_code == 0


def test_add_users_with_profile(mock_jira_client):
    """Test using specific profile."""
    mock_jira_client.add_users_to_organization.return_value = None

    with patch('add_to_organization.get_jira_client', return_value=mock_jira_client):
        from add_to_organization import add_users_to_organization_func

        add_users_to_organization_func(1, ['id1'], profile='staging')
