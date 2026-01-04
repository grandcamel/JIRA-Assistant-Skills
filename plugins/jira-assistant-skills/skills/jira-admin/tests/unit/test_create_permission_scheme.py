"""
Unit tests for create_permission_scheme.py

TDD: Write tests first before implementing the script.
Tests cover:
- Creating a basic scheme
- Creating with description
- Creating with initial grants
- Creating from template file
- Cloning an existing scheme
- Error handling
"""

import copy
import pytest
import json
from unittest.mock import Mock, patch, mock_open
import sys
from pathlib import Path

# Add script paths for imports
shared_lib_path = str(Path(__file__).parent.parent.parent.parent / 'shared' / 'scripts' / 'lib')
scripts_path = str(Path(__file__).parent.parent.parent / 'scripts')
if shared_lib_path not in sys.path:
    sys.path.insert(0, shared_lib_path)
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


class TestCreatePermissionScheme:
    """Tests for creating permission schemes."""

    def test_create_basic_scheme(self, mock_jira_client, created_permission_scheme):
        """Test creating a basic scheme with just name."""
        mock_jira_client.create_permission_scheme.return_value = created_permission_scheme

        from create_permission_scheme import create_permission_scheme

        scheme = create_permission_scheme(
            mock_jira_client,
            name='New Test Scheme'
        )

        assert scheme['id'] == 10100
        assert scheme['name'] == 'New Test Scheme'
        mock_jira_client.create_permission_scheme.assert_called_once()

    def test_create_with_description(self, mock_jira_client, created_permission_scheme):
        """Test creating a scheme with description."""
        expected = copy.deepcopy(created_permission_scheme)
        expected['description'] = 'Test description'
        mock_jira_client.create_permission_scheme.return_value = expected

        from create_permission_scheme import create_permission_scheme

        scheme = create_permission_scheme(
            mock_jira_client,
            name='New Test Scheme',
            description='Test description'
        )

        assert scheme['description'] == 'Test description'
        call_args = mock_jira_client.create_permission_scheme.call_args
        assert call_args[1]['description'] == 'Test description'

    def test_create_with_grants(self, mock_jira_client, created_scheme_with_grants):
        """Test creating a scheme with initial grants."""
        mock_jira_client.create_permission_scheme.return_value = created_scheme_with_grants

        from create_permission_scheme import create_permission_scheme

        grants = [
            'BROWSE_PROJECTS:anyone',
            'CREATE_ISSUES:group:jira-developers'
        ]

        scheme = create_permission_scheme(
            mock_jira_client,
            name='New Scheme with Grants',
            grants=grants
        )

        assert len(scheme.get('permissions', [])) == 2
        mock_jira_client.create_permission_scheme.assert_called_once()

    def test_grant_parsing(self, mock_jira_client, created_permission_scheme):
        """Test that grant strings are correctly parsed."""
        mock_jira_client.create_permission_scheme.return_value = created_permission_scheme

        from create_permission_scheme import parse_grants

        grants = [
            'BROWSE_PROJECTS:anyone',
            'CREATE_ISSUES:group:jira-developers',
            'EDIT_ISSUES:projectRole:Developers'
        ]

        parsed = parse_grants(grants)

        assert len(parsed) == 3
        assert parsed[0]['permission'] == 'BROWSE_PROJECTS'
        assert parsed[0]['holder']['type'] == 'anyone'
        assert parsed[1]['holder']['parameter'] == 'jira-developers'
        assert parsed[2]['holder']['type'] == 'projectRole'


class TestCreateFromTemplate:
    """Tests for creating schemes from template files."""

    def test_create_from_template(self, mock_jira_client, created_scheme_with_grants, tmp_path):
        """Test creating a scheme from a template file."""
        mock_jira_client.create_permission_scheme.return_value = created_scheme_with_grants

        # Create template file
        template = [
            'BROWSE_PROJECTS:anyone',
            'CREATE_ISSUES:group:jira-developers'
        ]
        template_file = tmp_path / "template.json"
        with open(template_file, 'w') as f:
            json.dump(template, f)

        from create_permission_scheme import create_permission_scheme, load_template

        grants = load_template(str(template_file))
        scheme = create_permission_scheme(
            mock_jira_client,
            name='From Template',
            grants=grants
        )

        assert scheme is not None
        assert len(grants) == 2

    def test_template_file_not_found(self):
        """Test error when template file doesn't exist."""
        from create_permission_scheme import load_template
        from assistant_skills_lib.error_handler import ValidationError

        with pytest.raises((ValidationError, FileNotFoundError)):
            load_template('/nonexistent/path/template.json')

    def test_invalid_template_format(self, tmp_path):
        """Test error when template has invalid format."""
        # Create invalid template
        template_file = tmp_path / "invalid.json"
        with open(template_file, 'w') as f:
            f.write("not valid json")

        from create_permission_scheme import load_template
        from assistant_skills_lib.error_handler import ValidationError

        with pytest.raises((ValidationError, json.JSONDecodeError)):
            load_template(str(template_file))


class TestCloneScheme:
    """Tests for cloning existing schemes."""

    def test_clone_existing_scheme(self, mock_jira_client, permission_scheme_detail, created_permission_scheme):
        """Test cloning an existing scheme."""
        mock_jira_client.get_permission_scheme.return_value = permission_scheme_detail
        mock_jira_client.create_permission_scheme.return_value = created_permission_scheme

        from create_permission_scheme import clone_permission_scheme

        scheme = clone_permission_scheme(
            mock_jira_client,
            source_id=10000,
            new_name='Cloned Scheme'
        )

        # Should have created a new scheme
        mock_jira_client.create_permission_scheme.assert_called_once()
        # Call should include the grants from the source
        call_args = mock_jira_client.create_permission_scheme.call_args

        assert call_args[1]['name'] == 'Cloned Scheme'
        assert 'permissions' in call_args[1]
        assert len(call_args[1]['permissions']) > 0

    def test_clone_source_not_found(self, mock_jira_client):
        """Test error when source scheme doesn't exist."""
        from jira_assistant_skills_lib import NotFoundError
        mock_jira_client.get_permission_scheme.side_effect = NotFoundError(
            "Scheme not found"
        )

        from create_permission_scheme import clone_permission_scheme

        with pytest.raises(NotFoundError):
            clone_permission_scheme(
                mock_jira_client,
                source_id=99999,
                new_name='Cloned Scheme'
            )

    def test_clone_with_modifications(self, mock_jira_client, permission_scheme_detail, created_permission_scheme):
        """Test cloning a scheme with added grants."""
        mock_jira_client.get_permission_scheme.return_value = permission_scheme_detail
        mock_jira_client.create_permission_scheme.return_value = created_permission_scheme

        from create_permission_scheme import clone_permission_scheme

        additional_grants = ['LINK_ISSUES:anyone']

        scheme = clone_permission_scheme(
            mock_jira_client,
            source_id=10000,
            new_name='Cloned Scheme',
            additional_grants=additional_grants
        )

        # Check that additional grants were included
        call_args = mock_jira_client.create_permission_scheme.call_args
        permissions = call_args[1]['permissions']

        # Should have original grants plus the new one
        assert len(permissions) > len(permission_scheme_detail['permissions'])


class TestDryRun:
    """Tests for dry-run mode."""

    def test_dry_run_does_not_create(self, mock_jira_client):
        """Test that dry-run mode doesn't actually create the scheme."""
        from create_permission_scheme import create_permission_scheme

        grants = ['BROWSE_PROJECTS:anyone']

        result = create_permission_scheme(
            mock_jira_client,
            name='Dry Run Scheme',
            grants=grants,
            dry_run=True
        )

        # Should not have called the API
        mock_jira_client.create_permission_scheme.assert_not_called()
        # Should return a preview
        assert result is not None
        assert result.get('name') == 'Dry Run Scheme'

    def test_dry_run_shows_grants(self, mock_jira_client):
        """Test that dry-run mode shows parsed grants."""
        from create_permission_scheme import create_permission_scheme

        grants = ['BROWSE_PROJECTS:anyone', 'CREATE_ISSUES:group:developers']

        result = create_permission_scheme(
            mock_jira_client,
            name='Dry Run Scheme',
            grants=grants,
            dry_run=True
        )

        assert 'permissions' in result
        assert len(result['permissions']) == 2


class TestValidation:
    """Tests for input validation."""

    def test_empty_name_rejected(self, mock_jira_client):
        """Test that empty name is rejected."""
        from create_permission_scheme import create_permission_scheme
        from assistant_skills_lib.error_handler import ValidationError

        with pytest.raises(ValidationError):
            create_permission_scheme(
                mock_jira_client,
                name=''
            )

    def test_invalid_grant_format(self, mock_jira_client):
        """Test that invalid grant format is rejected."""
        from create_permission_scheme import parse_grants
        from assistant_skills_lib.error_handler import ValidationError

        with pytest.raises(ValidationError):
            parse_grants(['INVALID_GRANT_FORMAT'])

    def test_invalid_holder_type(self, mock_jira_client):
        """Test that invalid holder type is rejected."""
        from create_permission_scheme import parse_grants
        from assistant_skills_lib.error_handler import ValidationError

        with pytest.raises(ValidationError):
            parse_grants(['BROWSE_PROJECTS:invalid_holder_type'])


class TestCreatePermissionSchemeCLI:
    """Tests for the CLI main() function."""

    def test_cli_basic_create(self, mock_jira_client, created_permission_scheme, capsys):
        """Test CLI basic create command."""
        mock_jira_client.create_permission_scheme.return_value = created_permission_scheme

        with patch('create_permission_scheme.get_jira_client', return_value=mock_jira_client):
            with patch('sys.argv', ['create_permission_scheme.py', '--name', 'New Scheme']):
                from create_permission_scheme import main
                main()

        captured = capsys.readouterr()
        assert 'Created' in captured.out or 'New Scheme' in captured.out

    def test_cli_with_grants(self, mock_jira_client, created_permission_scheme, capsys):
        """Test CLI with grants."""
        mock_jira_client.create_permission_scheme.return_value = created_permission_scheme

        with patch('create_permission_scheme.get_jira_client', return_value=mock_jira_client):
            with patch('sys.argv', ['create_permission_scheme.py', '--name', 'New Scheme',
                                   '--grant', 'BROWSE_PROJECTS:anyone',
                                   '--grant', 'CREATE_ISSUES:group:developers']):
                from create_permission_scheme import main
                main()

        mock_jira_client.create_permission_scheme.assert_called_once()

    def test_cli_json_output(self, mock_jira_client, created_permission_scheme, capsys):
        """Test CLI with JSON output format."""
        mock_jira_client.create_permission_scheme.return_value = created_permission_scheme

        with patch('create_permission_scheme.get_jira_client', return_value=mock_jira_client):
            with patch('sys.argv', ['create_permission_scheme.py', '--name', 'New Scheme',
                                   '--output', 'json']):
                from create_permission_scheme import main
                main()

        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert 'id' in parsed

    def test_cli_dry_run(self, mock_jira_client, capsys):
        """Test CLI dry-run mode."""
        with patch('create_permission_scheme.get_jira_client', return_value=mock_jira_client):
            with patch('sys.argv', ['create_permission_scheme.py', '--name', 'Test Scheme',
                                   '--grant', 'BROWSE_PROJECTS:anyone', '--dry-run']):
                from create_permission_scheme import main
                main()

        mock_jira_client.create_permission_scheme.assert_not_called()
        captured = capsys.readouterr()
        assert 'DRY RUN' in captured.out

    def test_cli_clone_scheme(self, mock_jira_client, permission_scheme_detail, created_permission_scheme, capsys):
        """Test CLI clone existing scheme."""
        mock_jira_client.get_permission_scheme.return_value = permission_scheme_detail
        mock_jira_client.create_permission_scheme.return_value = created_permission_scheme

        with patch('create_permission_scheme.get_jira_client', return_value=mock_jira_client):
            with patch('sys.argv', ['create_permission_scheme.py', '--name', 'Cloned',
                                   '--clone', '10000']):
                from create_permission_scheme import main
                main()

        # Should have fetched the source scheme
        mock_jira_client.get_permission_scheme.assert_called()

    def test_cli_error_handling(self, mock_jira_client, capsys):
        """Test CLI handles errors gracefully."""
        from jira_assistant_skills_lib import JiraError
        mock_jira_client.create_permission_scheme.side_effect = JiraError("API Error", status_code=500)

        with patch('create_permission_scheme.get_jira_client', return_value=mock_jira_client):
            with patch('sys.argv', ['create_permission_scheme.py', '--name', 'New Scheme']):
                from create_permission_scheme import main
                with pytest.raises(SystemExit) as exc_info:
                    main()

        assert exc_info.value.code == 1

    def test_cli_with_profile(self, mock_jira_client, created_permission_scheme):
        """Test CLI with profile argument."""
        mock_jira_client.create_permission_scheme.return_value = created_permission_scheme

        with patch('create_permission_scheme.get_jira_client', return_value=mock_jira_client) as mock_get_client:
            with patch('sys.argv', ['create_permission_scheme.py', '--name', 'New Scheme',
                                   '--profile', 'development']):
                from create_permission_scheme import main
                main()

        mock_get_client.assert_called_once_with(profile='development')