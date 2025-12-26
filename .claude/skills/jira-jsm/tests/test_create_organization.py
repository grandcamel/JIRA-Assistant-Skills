"""
Tests for create_organization.py script.
"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

scripts_path = str(Path(__file__).parent.parent / 'scripts')
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


@pytest.fixture
def sample_organization_response():
    """Sample organization response from API."""
    return {
        'id': '1',
        'name': 'Acme Corporation',
        '_links': {'self': 'https://example.atlassian.net/rest/servicedeskapi/organization/1'}
    }


def test_create_organization_basic(mock_jira_client, sample_organization_response):
    """Test creating organization with name."""
    mock_jira_client.create_organization.return_value = sample_organization_response

    with patch('create_organization.get_jira_client', return_value=mock_jira_client):
        from create_organization import create_organization_func

        result = create_organization_func(name="Acme Corporation")

        assert result['id'] == '1'
        assert result['name'] == 'Acme Corporation'
        mock_jira_client.create_organization.assert_called_once_with("Acme Corporation")


def test_create_organization_name_validation():
    """Test name validation (length, characters)."""
    with patch('create_organization.get_jira_client'):
        from create_organization import main

        # Empty name
        with patch('sys.argv', ['create_organization.py', '--name', '']):
            exit_code = main()
            assert exit_code == 1


def test_create_organization_json_output(mock_jira_client, sample_organization_response, capsys):
    """Test JSON output with organization ID."""
    mock_jira_client.create_organization.return_value = sample_organization_response

    with patch('create_organization.get_jira_client', return_value=mock_jira_client):
        from create_organization import main
        with patch('sys.argv', ['create_organization.py', '--name', 'Acme Corporation',
                                '--output', 'json']):
            main()

    captured = capsys.readouterr()
    assert '"id"' in captured.out
    assert '1' in captured.out


def test_create_organization_verbose_output(mock_jira_client, sample_organization_response, capsys):
    """Test verbose mode showing full response."""
    mock_jira_client.create_organization.return_value = sample_organization_response

    with patch('create_organization.get_jira_client', return_value=mock_jira_client):
        from create_organization import main
        with patch('sys.argv', ['create_organization.py', '--name', 'Acme Corporation',
                                '--verbose']):
            main()

    captured = capsys.readouterr()
    assert 'Full response' in captured.out


def test_create_organization_dry_run(capsys):
    """Test preview without creating."""
    with patch('create_organization.get_jira_client'):
        from create_organization import main
        with patch('sys.argv', ['create_organization.py', '--name', 'Test Org', '--dry-run']):
            exit_code = main()

    captured = capsys.readouterr()
    assert 'DRY RUN MODE' in captured.out
    assert 'Test Org' in captured.out
    assert exit_code == 0


def test_create_organization_network_error(mock_jira_client, capsys):
    """Test handling API errors gracefully."""
    from error_handler import JiraError
    mock_jira_client.create_organization.side_effect = JiraError("Network error")

    with patch('create_organization.get_jira_client', return_value=mock_jira_client):
        from create_organization import main
        with patch('sys.argv', ['create_organization.py', '--name', 'Acme Corporation']):
            exit_code = main()

    captured = capsys.readouterr()
    assert 'Network error' in captured.err
    assert exit_code == 1


def test_create_organization_success_message(mock_jira_client, sample_organization_response, capsys):
    """Test success message format."""
    mock_jira_client.create_organization.return_value = sample_organization_response

    with patch('create_organization.get_jira_client', return_value=mock_jira_client):
        from create_organization import main
        with patch('sys.argv', ['create_organization.py', '--name', 'Acme Corporation']):
            exit_code = main()

    captured = capsys.readouterr()
    assert 'Organization created successfully' in captured.out
    assert exit_code == 0
