"""
Unit tests for assign_permission_scheme.py

TDD: Write tests first before implementing the script.
Tests cover:
- Assigning a scheme to a single project
- Assigning a scheme to multiple projects
- Showing current scheme assignment
- Error handling
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


class TestAssignPermissionScheme:
    """Tests for assigning permission schemes to projects."""

    def test_assign_to_single_project(self, mock_jira_client, project_permission_scheme):
        """Test assigning a scheme to a single project."""
        mock_jira_client.assign_permission_scheme_to_project.return_value = project_permission_scheme

        from assign_permission_scheme import assign_permission_scheme

        result = assign_permission_scheme(
            mock_jira_client,
            project_key='PROJ',
            scheme_id=10000
        )

        assert result['id'] == 10000
        mock_jira_client.assign_permission_scheme_to_project.assert_called_once_with(
            'PROJ', 10000
        )

    def test_assign_to_multiple_projects(self, mock_jira_client, project_permission_scheme):
        """Test assigning a scheme to multiple projects."""
        mock_jira_client.assign_permission_scheme_to_project.return_value = project_permission_scheme

        from assign_permission_scheme import assign_permission_scheme_to_projects

        projects = ['PROJ', 'DEV', 'QA']
        results = assign_permission_scheme_to_projects(
            mock_jira_client,
            project_keys=projects,
            scheme_id=10000
        )

        assert len(results) == 3
        assert mock_jira_client.assign_permission_scheme_to_project.call_count == 3

    def test_project_not_found(self, mock_jira_client):
        """Test error when project doesn't exist."""
        from error_handler import NotFoundError
        mock_jira_client.assign_permission_scheme_to_project.side_effect = NotFoundError(
            "Project not found"
        )

        from assign_permission_scheme import assign_permission_scheme

        with pytest.raises(NotFoundError):
            assign_permission_scheme(
                mock_jira_client,
                project_key='NONEXISTENT',
                scheme_id=10000
            )

    def test_scheme_not_found(self, mock_jira_client):
        """Test error when scheme doesn't exist."""
        from error_handler import NotFoundError
        mock_jira_client.assign_permission_scheme_to_project.side_effect = NotFoundError(
            "Permission scheme not found"
        )

        from assign_permission_scheme import assign_permission_scheme

        with pytest.raises(NotFoundError):
            assign_permission_scheme(
                mock_jira_client,
                project_key='PROJ',
                scheme_id=99999
            )


class TestShowCurrentScheme:
    """Tests for showing current scheme assignment."""

    def test_show_current_scheme(self, mock_jira_client, project_permission_scheme):
        """Test showing current scheme for a project."""
        mock_jira_client.get_project_permission_scheme.return_value = project_permission_scheme

        from assign_permission_scheme import get_current_scheme

        scheme = get_current_scheme(mock_jira_client, project_key='PROJ')

        assert scheme['id'] == 10000
        assert scheme['name'] == 'Default Software Scheme'

    def test_show_current_scheme_for_multiple_projects(self, mock_jira_client, project_permission_scheme):
        """Test showing current schemes for multiple projects."""
        mock_jira_client.get_project_permission_scheme.return_value = project_permission_scheme

        from assign_permission_scheme import get_current_schemes

        projects = ['PROJ', 'DEV']
        schemes = get_current_schemes(mock_jira_client, project_keys=projects)

        assert len(schemes) == 2
        assert mock_jira_client.get_project_permission_scheme.call_count == 2


class TestResolveScheme:
    """Tests for resolving scheme by ID or name."""

    def test_resolve_by_id(self, mock_jira_client, permission_scheme_detail):
        """Test resolving scheme by numeric ID."""
        mock_jira_client.get_permission_scheme.return_value = permission_scheme_detail

        from assign_permission_scheme import resolve_scheme_id

        scheme_id = resolve_scheme_id(mock_jira_client, '10000')

        assert scheme_id == 10000

    def test_resolve_by_name(self, mock_jira_client, permission_schemes_response):
        """Test resolving scheme by name."""
        mock_jira_client.get_permission_schemes.return_value = permission_schemes_response

        from assign_permission_scheme import resolve_scheme_id

        scheme_id = resolve_scheme_id(mock_jira_client, 'Default Software Scheme')

        assert scheme_id == 10000

    def test_resolve_name_not_found(self, mock_jira_client, permission_schemes_response):
        """Test error when scheme name doesn't exist."""
        mock_jira_client.get_permission_schemes.return_value = permission_schemes_response

        from assign_permission_scheme import resolve_scheme_id
        from error_handler import ValidationError

        with pytest.raises(ValidationError):
            resolve_scheme_id(mock_jira_client, 'Nonexistent Scheme')


class TestDryRun:
    """Tests for dry-run mode."""

    def test_dry_run_single_project(self, mock_jira_client, project_permission_scheme):
        """Test that dry-run doesn't assign to single project."""
        mock_jira_client.get_project_permission_scheme.return_value = project_permission_scheme

        from assign_permission_scheme import assign_permission_scheme

        result = assign_permission_scheme(
            mock_jira_client,
            project_key='PROJ',
            scheme_id=10050,
            dry_run=True
        )

        mock_jira_client.assign_permission_scheme_to_project.assert_not_called()
        assert result is not None

    def test_dry_run_shows_current_and_new(self, mock_jira_client, project_permission_scheme):
        """Test that dry-run shows current and new scheme."""
        mock_jira_client.get_project_permission_scheme.return_value = project_permission_scheme
        mock_jira_client.get_permission_scheme.return_value = {
            'id': 10050,
            'name': 'New Scheme'
        }

        from assign_permission_scheme import preview_assignment

        preview = preview_assignment(
            mock_jira_client,
            project_key='PROJ',
            scheme_id=10050
        )

        assert preview['current']['id'] == 10000
        assert preview['new']['id'] == 10050


class TestAssignPermissionSchemeCLI:
    """Tests for the CLI main() function."""

    def test_cli_assign_single_project(self, mock_jira_client, permission_schemes_response, project_permission_scheme, capsys):
        """Test CLI assign to single project."""
        mock_jira_client.get_permission_schemes.return_value = permission_schemes_response
        mock_jira_client.get_permission_scheme.return_value = {
            'id': 10000,
            'name': 'Default Software Scheme'
        }
        mock_jira_client.assign_permission_scheme_to_project.return_value = project_permission_scheme

        with patch('assign_permission_scheme.get_jira_client', return_value=mock_jira_client):
            with patch('sys.argv', ['assign_permission_scheme.py', '--project', 'PROJ', '--scheme', '10000']):
                from assign_permission_scheme import main
                main()

        mock_jira_client.assign_permission_scheme_to_project.assert_called_once_with('PROJ', 10000)

    def test_cli_assign_multiple_projects(self, mock_jira_client, permission_schemes_response, project_permission_scheme, capsys):
        """Test CLI assign to multiple projects."""
        mock_jira_client.get_permission_schemes.return_value = permission_schemes_response
        mock_jira_client.get_permission_scheme.return_value = {
            'id': 10000,
            'name': 'Default Software Scheme'
        }
        mock_jira_client.assign_permission_scheme_to_project.return_value = project_permission_scheme

        with patch('assign_permission_scheme.get_jira_client', return_value=mock_jira_client):
            with patch('sys.argv', ['assign_permission_scheme.py', '--projects', 'PROJ,DEV,QA', '--scheme', '10000']):
                from assign_permission_scheme import main
                main()

        assert mock_jira_client.assign_permission_scheme_to_project.call_count == 3

    def test_cli_show_current(self, mock_jira_client, project_permission_scheme, capsys):
        """Test CLI show current scheme."""
        mock_jira_client.get_project_permission_scheme.return_value = project_permission_scheme

        with patch('assign_permission_scheme.get_jira_client', return_value=mock_jira_client):
            with patch('sys.argv', ['assign_permission_scheme.py', '--project', 'PROJ', '--show-current']):
                from assign_permission_scheme import main
                main()

        mock_jira_client.get_project_permission_scheme.assert_called_once()
        captured = capsys.readouterr()
        assert 'Default Software Scheme' in captured.out or 'PROJ' in captured.out

    def test_cli_dry_run(self, mock_jira_client, permission_schemes_response, project_permission_scheme, capsys):
        """Test CLI dry-run mode."""
        mock_jira_client.get_permission_schemes.return_value = permission_schemes_response
        mock_jira_client.get_permission_scheme.return_value = {
            'id': 10050,
            'name': 'New Scheme'
        }
        mock_jira_client.get_project_permission_scheme.return_value = project_permission_scheme

        with patch('assign_permission_scheme.get_jira_client', return_value=mock_jira_client):
            with patch('sys.argv', ['assign_permission_scheme.py', '--project', 'PROJ', '--scheme', '10050', '--dry-run']):
                from assign_permission_scheme import main
                main()

        mock_jira_client.assign_permission_scheme_to_project.assert_not_called()
        captured = capsys.readouterr()
        assert 'DRY RUN' in captured.out

    def test_cli_assign_by_name(self, mock_jira_client, permission_schemes_response, project_permission_scheme, capsys):
        """Test CLI assign by scheme name."""
        mock_jira_client.get_permission_schemes.return_value = permission_schemes_response
        mock_jira_client.get_permission_scheme.return_value = {
            'id': 10000,
            'name': 'Default Software Scheme'
        }
        mock_jira_client.assign_permission_scheme_to_project.return_value = project_permission_scheme

        with patch('assign_permission_scheme.get_jira_client', return_value=mock_jira_client):
            with patch('sys.argv', ['assign_permission_scheme.py', '--project', 'PROJ', '--scheme', 'Default Software Scheme']):
                from assign_permission_scheme import main
                main()

        # Should have resolved name to ID
        mock_jira_client.get_permission_schemes.assert_called()

    def test_cli_error_handling(self, mock_jira_client, capsys):
        """Test CLI handles errors gracefully."""
        from error_handler import NotFoundError
        mock_jira_client.get_permission_schemes.return_value = {'permissionSchemes': []}

        with patch('assign_permission_scheme.get_jira_client', return_value=mock_jira_client):
            with patch('sys.argv', ['assign_permission_scheme.py', '--project', 'PROJ', '--scheme', 'Nonexistent']):
                from assign_permission_scheme import main
                with pytest.raises(SystemExit) as exc_info:
                    main()

        assert exc_info.value.code == 1

    def test_cli_with_profile(self, mock_jira_client, permission_schemes_response, project_permission_scheme):
        """Test CLI with profile argument."""
        mock_jira_client.get_permission_schemes.return_value = permission_schemes_response
        mock_jira_client.get_permission_scheme.return_value = {
            'id': 10000,
            'name': 'Default Software Scheme'
        }
        mock_jira_client.assign_permission_scheme_to_project.return_value = project_permission_scheme

        with patch('assign_permission_scheme.get_jira_client', return_value=mock_jira_client) as mock_get_client:
            with patch('sys.argv', ['assign_permission_scheme.py', '--project', 'PROJ', '--scheme', '10000',
                                   '--profile', 'development']):
                from assign_permission_scheme import main
                main()

        mock_get_client.assert_called_once_with(profile='development')