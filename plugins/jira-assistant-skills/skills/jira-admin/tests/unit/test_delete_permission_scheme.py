"""
Unit tests for delete_permission_scheme.py

TDD: Write tests first before implementing the script.
Tests cover:
- Deleting an unused scheme
- Checking if scheme is in use
- Error handling for scheme in use
- Confirmation requirement
"""

import pytest
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


class TestDeletePermissionScheme:
    """Tests for deleting permission schemes."""

    def test_delete_unused_scheme(self, mock_jira_client):
        """Test deleting a scheme that's not in use."""
        mock_jira_client.delete_permission_scheme.return_value = None

        from delete_permission_scheme import delete_permission_scheme

        delete_permission_scheme(mock_jira_client, scheme_id=10050, confirm=True)

        mock_jira_client.delete_permission_scheme.assert_called_once_with(10050)

    def test_delete_without_confirm(self, mock_jira_client):
        """Test that deletion requires confirmation."""
        from delete_permission_scheme import delete_permission_scheme
        from jira_assistant_skills_lib import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            delete_permission_scheme(mock_jira_client, scheme_id=10050, confirm=False)

        assert 'confirm' in str(exc_info.value).lower()
        mock_jira_client.delete_permission_scheme.assert_not_called()

    def test_scheme_not_found(self, mock_jira_client):
        """Test error when scheme doesn't exist."""
        from jira_assistant_skills_lib import NotFoundError
        mock_jira_client.delete_permission_scheme.side_effect = NotFoundError(
            "Permission scheme not found"
        )

        from delete_permission_scheme import delete_permission_scheme

        with pytest.raises(NotFoundError):
            delete_permission_scheme(mock_jira_client, scheme_id=99999, confirm=True)

    def test_scheme_in_use(self, mock_jira_client):
        """Test error when scheme is in use by projects."""
        from jira_assistant_skills_lib import ValidationError
        mock_jira_client.delete_permission_scheme.side_effect = ValidationError(
            "The permission scheme cannot be deleted because it is used by one or more projects."
        )

        from delete_permission_scheme import delete_permission_scheme

        with pytest.raises(ValidationError):
            delete_permission_scheme(mock_jira_client, scheme_id=10000, confirm=True)


class TestCheckSchemeUsage:
    """Tests for checking if scheme is in use."""

    def test_check_scheme_not_in_use(self, mock_jira_client, permission_scheme_detail):
        """Test checking a scheme not used by any project."""
        # Mock getting all projects
        mock_jira_client.get.return_value = {'values': [], 'isLast': True}

        from delete_permission_scheme import check_scheme_in_use

        in_use, projects = check_scheme_in_use(mock_jira_client, scheme_id=10050)

        assert in_use is False
        assert len(projects) == 0

    def test_check_scheme_in_use(self, mock_jira_client):
        """Test checking a scheme used by projects."""
        # Mock response showing scheme is in use
        mock_jira_client.get.return_value = {
            'values': [
                {
                    'key': 'PROJ',
                    'name': 'Test Project',
                    'permissionScheme': {'id': 10000, 'name': 'Default Scheme'}
                },
                {
                    'key': 'DEV',
                    'name': 'Development Project',
                    'permissionScheme': {'id': 10000, 'name': 'Default Scheme'}
                }
            ],
            'isLast': True
        }

        from delete_permission_scheme import check_scheme_in_use

        in_use, projects = check_scheme_in_use(mock_jira_client, scheme_id=10000)

        assert in_use is True
        assert len(projects) == 2

    def test_check_only_mode(self, mock_jira_client):
        """Test check-only mode that doesn't delete."""
        mock_jira_client.get.return_value = {'values': [], 'isLast': True}

        from delete_permission_scheme import check_scheme_in_use

        in_use, projects = check_scheme_in_use(mock_jira_client, scheme_id=10050)

        # Should not have called delete
        mock_jira_client.delete_permission_scheme.assert_not_called()


class TestDryRun:
    """Tests for dry-run mode."""

    def test_dry_run_does_not_delete(self, mock_jira_client):
        """Test that dry-run doesn't actually delete."""
        from delete_permission_scheme import delete_permission_scheme

        result = delete_permission_scheme(
            mock_jira_client,
            scheme_id=10050,
            confirm=True,
            dry_run=True
        )

        mock_jira_client.delete_permission_scheme.assert_not_called()
        assert result is True  # Would have deleted

    def test_dry_run_shows_would_delete(self, mock_jira_client, permission_scheme_detail):
        """Test that dry-run returns scheme info."""
        mock_jira_client.get_permission_scheme.return_value = permission_scheme_detail

        from delete_permission_scheme import get_scheme_for_deletion

        scheme = get_scheme_for_deletion(mock_jira_client, scheme_id=10000)

        assert scheme['name'] == 'Default Software Scheme'


class TestDeletePermissionSchemeCLI:
    """Tests for the CLI main() function."""

    def test_cli_delete_with_confirm(self, mock_jira_client, permission_scheme_detail, capsys):
        """Test CLI delete with confirm flag."""
        mock_jira_client.get_permission_scheme.return_value = permission_scheme_detail
        mock_jira_client.get.return_value = {'values': [], 'isLast': True}  # No projects using scheme
        mock_jira_client.delete_permission_scheme.return_value = None

        with patch('delete_permission_scheme.get_jira_client', return_value=mock_jira_client):
            with patch('sys.argv', ['delete_permission_scheme.py', '10050', '--confirm']):
                from delete_permission_scheme import main
                main()

        mock_jira_client.delete_permission_scheme.assert_called_once_with(10050)
        captured = capsys.readouterr()
        assert 'Deleted' in captured.out

    def test_cli_check_only(self, mock_jira_client, permission_scheme_detail, capsys):
        """Test CLI check-only mode."""
        mock_jira_client.get_permission_scheme.return_value = permission_scheme_detail
        mock_jira_client.get.return_value = {'values': [], 'isLast': True}

        with patch('delete_permission_scheme.get_jira_client', return_value=mock_jira_client):
            with patch('sys.argv', ['delete_permission_scheme.py', '10050', '--check-only']):
                from delete_permission_scheme import main
                main()

        mock_jira_client.delete_permission_scheme.assert_not_called()
        captured = capsys.readouterr()
        assert 'NOT in use' in captured.out or 'not in use' in captured.out.lower()

    def test_cli_check_only_in_use(self, mock_jira_client, permission_scheme_detail, capsys):
        """Test CLI check-only when scheme is in use."""
        mock_jira_client.get_permission_scheme.return_value = permission_scheme_detail
        mock_jira_client.get.return_value = {
            'values': [
                {
                    'key': 'PROJ',
                    'name': 'Test Project',
                    'permissionScheme': {'id': 10000, 'name': 'Default Scheme'}
                }
            ],
            'isLast': True
        }

        with patch('delete_permission_scheme.get_jira_client', return_value=mock_jira_client):
            with patch('sys.argv', ['delete_permission_scheme.py', '10000', '--check-only']):
                from delete_permission_scheme import main
                main()

        captured = capsys.readouterr()
        assert 'IN USE' in captured.out or 'in use' in captured.out.lower()

    def test_cli_dry_run(self, mock_jira_client, permission_scheme_detail, capsys):
        """Test CLI dry-run mode."""
        mock_jira_client.get_permission_scheme.return_value = permission_scheme_detail
        mock_jira_client.get.return_value = {'values': [], 'isLast': True}

        with patch('delete_permission_scheme.get_jira_client', return_value=mock_jira_client):
            with patch('sys.argv', ['delete_permission_scheme.py', '10050', '--confirm', '--dry-run']):
                from delete_permission_scheme import main
                main()

        mock_jira_client.delete_permission_scheme.assert_not_called()
        captured = capsys.readouterr()
        assert 'DRY RUN' in captured.out

    def test_cli_without_confirm_exits(self, mock_jira_client, permission_scheme_detail, capsys):
        """Test CLI without confirm flag exits."""
        mock_jira_client.get_permission_scheme.return_value = permission_scheme_detail
        mock_jira_client.get.return_value = {'values': [], 'isLast': True}

        with patch('delete_permission_scheme.get_jira_client', return_value=mock_jira_client):
            with patch('sys.argv', ['delete_permission_scheme.py', '10050']):
                from delete_permission_scheme import main
                with pytest.raises(SystemExit) as exc_info:
                    main()

        assert exc_info.value.code == 1

    def test_cli_error_handling(self, mock_jira_client, capsys):
        """Test CLI handles errors gracefully."""
        from jira_assistant_skills_lib import NotFoundError
        mock_jira_client.get_permission_scheme.side_effect = NotFoundError("Scheme not found")

        with patch('delete_permission_scheme.get_jira_client', return_value=mock_jira_client):
            with patch('sys.argv', ['delete_permission_scheme.py', '99999', '--confirm']):
                from delete_permission_scheme import main
                with pytest.raises(SystemExit) as exc_info:
                    main()

        assert exc_info.value.code == 1

    def test_cli_with_profile(self, mock_jira_client, permission_scheme_detail):
        """Test CLI with profile argument."""
        mock_jira_client.get_permission_scheme.return_value = permission_scheme_detail
        mock_jira_client.get.return_value = {'values': [], 'isLast': True}
        mock_jira_client.delete_permission_scheme.return_value = None

        with patch('delete_permission_scheme.get_jira_client', return_value=mock_jira_client) as mock_get_client:
            with patch('sys.argv', ['delete_permission_scheme.py', '10050', '--confirm',
                                   '--profile', 'development']):
                from delete_permission_scheme import main
                main()

        mock_get_client.assert_called_once_with(profile='development')