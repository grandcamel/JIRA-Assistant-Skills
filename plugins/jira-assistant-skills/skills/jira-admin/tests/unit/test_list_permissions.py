"""
Unit tests for list_permissions.py

TDD: Write tests first before implementing the script.
Tests cover:
- Listing all available permissions
- Filtering by type (PROJECT, GLOBAL)
- Searching by name or description
- Output formats (table, json, csv)
"""

import pytest
import json
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add script paths for imports
shared_lib_path = str(Path(__file__).parent.parent.parent.parent / 'shared' / 'scripts' / 'lib')
scripts_path = str(Path(__file__).parent.parent.parent / 'scripts')
if shared_lib_path not in sys.path:
    sys.path.insert(0, shared_lib_path)
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


class TestListPermissions:
    """Tests for listing all available permissions."""

    def test_list_all_permissions(self, mock_jira_client, all_permissions):
        """Test listing all permissions."""
        mock_jira_client.get_all_permissions.return_value = all_permissions

        from list_permissions import list_permissions

        permissions = list_permissions(mock_jira_client)

        # All permissions fixture has 27 permissions
        assert len(permissions) >= 25
        mock_jira_client.get_all_permissions.assert_called_once()

    def test_filter_by_project_type(self, mock_jira_client, all_permissions):
        """Test filtering permissions by PROJECT type."""
        mock_jira_client.get_all_permissions.return_value = all_permissions

        from list_permissions import list_permissions

        permissions = list_permissions(mock_jira_client, permission_type='PROJECT')

        # All should be PROJECT type
        for perm in permissions:
            assert perm['type'] == 'PROJECT'

    def test_filter_by_global_type(self, mock_jira_client, all_permissions):
        """Test filtering permissions by GLOBAL type."""
        mock_jira_client.get_all_permissions.return_value = all_permissions

        from list_permissions import list_permissions

        permissions = list_permissions(mock_jira_client, permission_type='GLOBAL')

        # All should be GLOBAL type
        for perm in permissions:
            assert perm['type'] == 'GLOBAL'

        # Should have at least ADMINISTER
        assert any(p['key'] == 'ADMINISTER' for p in permissions)

    def test_search_by_name(self, mock_jira_client, all_permissions):
        """Test searching permissions by name."""
        mock_jira_client.get_all_permissions.return_value = all_permissions

        from list_permissions import list_permissions

        permissions = list_permissions(mock_jira_client, search='issue')

        # Should find issue-related permissions
        assert len(permissions) > 0
        # Search matches key, name, OR description
        for perm in permissions:
            assert ('issue' in perm['key'].lower() or
                    'issue' in perm['name'].lower() or
                    'issue' in perm.get('description', '').lower())

    def test_search_by_description(self, mock_jira_client, all_permissions):
        """Test searching permissions by description."""
        mock_jira_client.get_all_permissions.return_value = all_permissions

        from list_permissions import list_permissions

        permissions = list_permissions(mock_jira_client, search='comment')

        # Should find comment-related permissions
        assert len(permissions) > 0

    def test_search_case_insensitive(self, mock_jira_client, all_permissions):
        """Test that search is case-insensitive."""
        mock_jira_client.get_all_permissions.return_value = all_permissions

        from list_permissions import list_permissions

        permissions1 = list_permissions(mock_jira_client, search='ISSUE')
        permissions2 = list_permissions(mock_jira_client, search='issue')

        assert len(permissions1) == len(permissions2)

    def test_permission_has_expected_fields(self, mock_jira_client, all_permissions):
        """Test that permissions have expected fields."""
        mock_jira_client.get_all_permissions.return_value = all_permissions

        from list_permissions import list_permissions

        permissions = list_permissions(mock_jira_client)

        for perm in permissions:
            assert 'key' in perm
            assert 'name' in perm
            assert 'type' in perm


class TestFormatPermissions:
    """Tests for formatting permissions output."""

    def test_format_table(self, all_permissions):
        """Test table format."""
        from list_permissions import format_permissions

        # Extract permissions as list
        permissions = list(all_permissions['permissions'].values())

        output = format_permissions(permissions, output_format='table')

        # Should contain table headers
        assert 'Key' in output or 'key' in output.lower()
        assert 'Name' in output or 'name' in output.lower()
        assert 'Type' in output or 'type' in output.lower()

    def test_format_json(self, all_permissions):
        """Test JSON format."""
        from list_permissions import format_permissions

        permissions = list(all_permissions['permissions'].values())

        output = format_permissions(permissions, output_format='json')

        # Should be valid JSON
        parsed = json.loads(output)
        assert isinstance(parsed, list)
        assert len(parsed) > 0

    def test_format_csv(self, all_permissions):
        """Test CSV format."""
        from list_permissions import format_permissions

        permissions = list(all_permissions['permissions'].values())

        output = format_permissions(permissions, output_format='csv')

        lines = output.strip().split('\n')
        # Header + data rows
        assert len(lines) > 1
        # Check header
        assert 'key' in lines[0].lower()

    def test_format_shows_description(self, all_permissions):
        """Test that output includes descriptions."""
        from list_permissions import format_permissions

        permissions = list(all_permissions['permissions'].values())

        output = format_permissions(permissions, output_format='table')

        # Should show descriptions (at least partially)
        assert 'browse' in output.lower() or 'ability' in output.lower()


class TestPermissionCategories:
    """Tests for permission categorization."""

    def test_group_by_type(self, mock_jira_client, all_permissions):
        """Test grouping permissions by type."""
        mock_jira_client.get_all_permissions.return_value = all_permissions

        from list_permissions import list_permissions, group_by_type

        permissions = list_permissions(mock_jira_client)
        grouped = group_by_type(permissions)

        assert 'PROJECT' in grouped
        assert 'GLOBAL' in grouped
        assert len(grouped['PROJECT']) > 0

    def test_sorted_output(self, mock_jira_client, all_permissions):
        """Test that output is sorted by key."""
        mock_jira_client.get_all_permissions.return_value = all_permissions

        from list_permissions import list_permissions

        permissions = list_permissions(mock_jira_client)

        # Should be sorted by key
        keys = [p['key'] for p in permissions]
        assert keys == sorted(keys)


class TestListPermissionsCLI:
    """Tests for the CLI main() function."""

    def test_cli_basic_list(self, mock_jira_client, all_permissions, capsys):
        """Test CLI basic list command."""
        mock_jira_client.get_all_permissions.return_value = all_permissions

        with patch('list_permissions.get_jira_client', return_value=mock_jira_client):
            with patch('sys.argv', ['list_permissions.py']):
                from list_permissions import main
                main()

        captured = capsys.readouterr()
        assert 'BROWSE_PROJECTS' in captured.out or 'Browse' in captured.out

    def test_cli_json_output(self, mock_jira_client, all_permissions, capsys):
        """Test CLI with JSON output format."""
        mock_jira_client.get_all_permissions.return_value = all_permissions

        with patch('list_permissions.get_jira_client', return_value=mock_jira_client):
            with patch('sys.argv', ['list_permissions.py', '--output', 'json']):
                from list_permissions import main
                main()

        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert len(parsed) > 0

    def test_cli_filter_by_type(self, mock_jira_client, all_permissions, capsys):
        """Test CLI filtering by type."""
        mock_jira_client.get_all_permissions.return_value = all_permissions

        with patch('list_permissions.get_jira_client', return_value=mock_jira_client):
            with patch('sys.argv', ['list_permissions.py', '--type', 'GLOBAL', '--output', 'json']):
                from list_permissions import main
                main()

        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        for perm in parsed:
            assert perm['type'] == 'GLOBAL'

    def test_cli_search(self, mock_jira_client, all_permissions, capsys):
        """Test CLI with search."""
        mock_jira_client.get_all_permissions.return_value = all_permissions

        with patch('list_permissions.get_jira_client', return_value=mock_jira_client):
            with patch('sys.argv', ['list_permissions.py', '--search', 'issue', '--output', 'json']):
                from list_permissions import main
                main()

        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert len(parsed) > 0

    def test_cli_error_handling(self, mock_jira_client, capsys):
        """Test CLI handles errors gracefully."""
        from error_handler import JiraError
        mock_jira_client.get_all_permissions.side_effect = JiraError("API Error", status_code=500)

        with patch('list_permissions.get_jira_client', return_value=mock_jira_client):
            with patch('sys.argv', ['list_permissions.py']):
                from list_permissions import main
                with pytest.raises(SystemExit) as exc_info:
                    main()

        assert exc_info.value.code == 1

    def test_cli_with_profile(self, mock_jira_client, all_permissions):
        """Test CLI with profile argument."""
        mock_jira_client.get_all_permissions.return_value = all_permissions

        with patch('list_permissions.get_jira_client', return_value=mock_jira_client) as mock_get_client:
            with patch('sys.argv', ['list_permissions.py', '--profile', 'development']):
                from list_permissions import main
                main()

        mock_get_client.assert_called_once_with(profile='development')