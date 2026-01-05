"""
Unit tests for get_permission_scheme.py

TDD: Write tests first before implementing the script.
Tests cover:
- Getting scheme by ID
- Getting scheme by name
- Permission grants display
- Export template functionality
- Error handling
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add script paths for imports
shared_lib_path = str(
    Path(__file__).parent.parent.parent.parent / "shared" / "scripts" / "lib"
)
scripts_path = str(Path(__file__).parent.parent.parent / "scripts")
if shared_lib_path not in sys.path:
    sys.path.insert(0, shared_lib_path)
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


class TestGetPermissionScheme:
    """Tests for getting a single permission scheme."""

    def test_get_scheme_by_id(self, mock_jira_client, permission_scheme_detail):
        """Test getting a scheme by numeric ID."""
        mock_jira_client.get_permission_scheme.return_value = permission_scheme_detail

        from get_permission_scheme import get_permission_scheme

        scheme = get_permission_scheme(mock_jira_client, 10000)

        assert scheme["id"] == 10000
        assert scheme["name"] == "Default Software Scheme"
        mock_jira_client.get_permission_scheme.assert_called_once_with(
            10000, expand="permissions,user,group,projectRole"
        )

    def test_get_scheme_by_string_id(self, mock_jira_client, permission_scheme_detail):
        """Test getting a scheme by string ID."""
        mock_jira_client.get_permission_scheme.return_value = permission_scheme_detail

        from get_permission_scheme import get_permission_scheme

        scheme = get_permission_scheme(mock_jira_client, "10000")

        assert scheme["id"] == 10000
        mock_jira_client.get_permission_scheme.assert_called_once()

    def test_get_scheme_by_name(
        self, mock_jira_client, permission_schemes_response, permission_scheme_detail
    ):
        """Test getting a scheme by name."""
        mock_jira_client.get_permission_schemes.return_value = (
            permission_schemes_response
        )
        mock_jira_client.get_permission_scheme.return_value = permission_scheme_detail

        from get_permission_scheme import get_permission_scheme

        scheme = get_permission_scheme(mock_jira_client, "Default Software Scheme")

        assert scheme["name"] == "Default Software Scheme"
        # Should have looked up schemes first
        mock_jira_client.get_permission_schemes.assert_called_once()

    def test_get_scheme_by_partial_name(
        self, mock_jira_client, permission_schemes_response, permission_scheme_detail
    ):
        """Test getting a scheme by partial name match."""
        mock_jira_client.get_permission_schemes.return_value = (
            permission_schemes_response
        )
        mock_jira_client.get_permission_scheme.return_value = permission_scheme_detail

        from get_permission_scheme import get_permission_scheme

        scheme = get_permission_scheme(mock_jira_client, "Software Scheme", fuzzy=True)

        assert scheme is not None
        assert "Software Scheme" in scheme["name"]

    def test_scheme_not_found_by_id(self, mock_jira_client):
        """Test error when scheme ID doesn't exist."""
        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.get_permission_scheme.side_effect = NotFoundError(
            "Permission scheme 99999 not found"
        )

        from get_permission_scheme import get_permission_scheme

        with pytest.raises(NotFoundError):
            get_permission_scheme(mock_jira_client, 99999)

    def test_scheme_not_found_by_name(
        self, mock_jira_client, permission_schemes_response
    ):
        """Test error when scheme name doesn't exist."""
        mock_jira_client.get_permission_schemes.return_value = (
            permission_schemes_response
        )

        from assistant_skills_lib.error_handler import ValidationError
        from get_permission_scheme import get_permission_scheme

        with pytest.raises(ValidationError):
            get_permission_scheme(mock_jira_client, "Nonexistent Scheme")

    def test_includes_permissions(self, mock_jira_client, permission_scheme_detail):
        """Test that scheme includes permission grants."""
        mock_jira_client.get_permission_scheme.return_value = permission_scheme_detail

        from get_permission_scheme import get_permission_scheme

        scheme = get_permission_scheme(mock_jira_client, 10000)

        assert "permissions" in scheme
        assert len(scheme["permissions"]) == 6


class TestFormatPermissionScheme:
    """Tests for formatting a single permission scheme."""

    def test_format_table_basic(self, permission_scheme_detail):
        """Test basic table formatting."""
        from get_permission_scheme import format_permission_scheme

        output = format_permission_scheme(
            permission_scheme_detail, output_format="table"
        )

        assert "Default Software Scheme" in output
        assert "10000" in output

    def test_format_table_with_grants(self, permission_scheme_detail):
        """Test table formatting includes grant information."""
        from get_permission_scheme import format_permission_scheme

        output = format_permission_scheme(
            permission_scheme_detail, output_format="table"
        )

        # Should list the permissions and their holders
        assert "BROWSE_PROJECTS" in output
        assert "CREATE_ISSUES" in output

    def test_format_json(self, permission_scheme_detail):
        """Test JSON formatting."""
        from get_permission_scheme import format_permission_scheme

        output = format_permission_scheme(
            permission_scheme_detail, output_format="json"
        )

        # Should be valid JSON
        parsed = json.loads(output)
        assert parsed["id"] == 10000
        assert len(parsed["permissions"]) == 6

    def test_format_shows_holder_types(self, permission_scheme_detail):
        """Test that different holder types are displayed."""
        from get_permission_scheme import format_permission_scheme

        output = format_permission_scheme(
            permission_scheme_detail, output_format="table"
        )

        # Should show various holder types
        assert "anyone" in output.lower() or "Anyone" in output
        assert "group" in output.lower()
        assert "projectRole" in output or "role" in output.lower()


class TestExportTemplate:
    """Tests for exporting scheme as a template."""

    def test_export_grants_as_template(self, permission_scheme_detail):
        """Test exporting grants as a JSON template."""
        from get_permission_scheme import export_grants_template

        template = export_grants_template(permission_scheme_detail)

        # Should be a list of grant strings
        assert isinstance(template, list)
        assert len(template) > 0

        # Should have format like PERMISSION:holder_type[:parameter]
        assert any("BROWSE_PROJECTS" in g for g in template)

    def test_export_template_format(self, permission_scheme_detail):
        """Test exported template has correct format."""
        from get_permission_scheme import export_grants_template

        template = export_grants_template(permission_scheme_detail)

        for grant in template:
            parts = grant.split(":")
            assert len(parts) >= 2  # PERMISSION:holder_type at minimum

    def test_export_template_includes_parameters(self, permission_scheme_detail):
        """Test that template includes holder parameters."""
        from get_permission_scheme import export_grants_template

        template = export_grants_template(permission_scheme_detail)

        # Should include group names in parameters
        has_parameter = any(":group:" in g or ":projectRole:" in g for g in template)
        assert has_parameter

    def test_export_to_file(self, mock_jira_client, permission_scheme_detail, tmp_path):
        """Test exporting template to a file."""
        mock_jira_client.get_permission_scheme.return_value = permission_scheme_detail

        from get_permission_scheme import export_grants_template, get_permission_scheme

        scheme = get_permission_scheme(mock_jira_client, 10000)
        template = export_grants_template(scheme)

        # Write to file
        output_file = tmp_path / "template.json"
        with open(output_file, "w") as f:
            json.dump(template, f)

        # Verify file contents
        with open(output_file) as f:
            loaded = json.load(f)

        assert len(loaded) == len(template)


class TestPermissionGrouping:
    """Tests for grouping and displaying permissions."""

    def test_group_by_permission(self, permission_scheme_detail):
        """Test grouping grants by permission."""
        from get_permission_scheme import group_grants_by_permission

        grouped = group_grants_by_permission(permission_scheme_detail["permissions"])

        # EDIT_ISSUES should have 2 holders (group and projectRole)
        assert "EDIT_ISSUES" in grouped
        assert len(grouped["EDIT_ISSUES"]) == 2

    def test_group_by_holder(self, permission_scheme_detail):
        """Test grouping grants by holder."""
        from get_permission_scheme import group_grants_by_holder

        grouped = group_grants_by_holder(permission_scheme_detail["permissions"])

        # jira-developers group should have multiple permissions
        assert any("jira-developers" in k for k in grouped)

    def test_format_grouped_table(self, permission_scheme_detail):
        """Test formatting grouped permissions as table."""
        from get_permission_scheme import format_permission_scheme

        output = format_permission_scheme(
            permission_scheme_detail, output_format="table", group_by="permission"
        )

        # Should show grouped output
        assert "EDIT_ISSUES" in output
        assert "BROWSE_PROJECTS" in output


class TestGetPermissionSchemeCLI:
    """Tests for the CLI main() function."""

    def test_cli_basic_get(self, mock_jira_client, permission_scheme_detail, capsys):
        """Test CLI basic get command."""
        mock_jira_client.get_permission_scheme.return_value = permission_scheme_detail

        with (
            patch(
                "get_permission_scheme.get_jira_client", return_value=mock_jira_client
            ),
            patch("sys.argv", ["get_permission_scheme.py", "10000"]),
        ):
            from get_permission_scheme import main

            main()

        captured = capsys.readouterr()
        assert "Default Software Scheme" in captured.out

    def test_cli_json_output(self, mock_jira_client, permission_scheme_detail, capsys):
        """Test CLI with JSON output format."""
        mock_jira_client.get_permission_scheme.return_value = permission_scheme_detail

        with (
            patch(
                "get_permission_scheme.get_jira_client", return_value=mock_jira_client
            ),
            patch(
                "sys.argv", ["get_permission_scheme.py", "10000", "--output", "json"]
            ),
        ):
            from get_permission_scheme import main

            main()

        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert parsed["name"] == "Default Software Scheme"

    def test_cli_group_by_permission(
        self, mock_jira_client, permission_scheme_detail, capsys
    ):
        """Test CLI with group by permission."""
        mock_jira_client.get_permission_scheme.return_value = permission_scheme_detail

        with (
            patch(
                "get_permission_scheme.get_jira_client", return_value=mock_jira_client
            ),
            patch(
                "sys.argv",
                ["get_permission_scheme.py", "10000", "--group-by", "permission"],
            ),
        ):
            from get_permission_scheme import main

            main()

        captured = capsys.readouterr()
        assert "BROWSE_PROJECTS" in captured.out or "EDIT_ISSUES" in captured.out

    def test_cli_export_template(
        self, mock_jira_client, permission_scheme_detail, capsys, tmp_path
    ):
        """Test CLI export template to file."""
        mock_jira_client.get_permission_scheme.return_value = permission_scheme_detail

        template_file = tmp_path / "template.json"
        with (
            patch(
                "get_permission_scheme.get_jira_client", return_value=mock_jira_client
            ),
            patch(
                "sys.argv",
                [
                    "get_permission_scheme.py",
                    "10000",
                    "--export-template",
                    str(template_file),
                ],
            ),
        ):
            from get_permission_scheme import main

            main()

        # Template should be written to file
        assert template_file.exists()
        with open(template_file) as f:
            parsed = json.load(f)
        assert isinstance(parsed, list)

    def test_cli_error_handling(self, mock_jira_client, capsys):
        """Test CLI handles errors gracefully."""
        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.get_permission_scheme.side_effect = NotFoundError(
            "Scheme not found"
        )

        with (
            patch(
                "get_permission_scheme.get_jira_client", return_value=mock_jira_client
            ),
            patch("sys.argv", ["get_permission_scheme.py", "99999"]),
        ):
            from get_permission_scheme import main

            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 1

    def test_cli_with_profile(self, mock_jira_client, permission_scheme_detail):
        """Test CLI with profile argument."""
        mock_jira_client.get_permission_scheme.return_value = permission_scheme_detail

        with (
            patch(
                "get_permission_scheme.get_jira_client", return_value=mock_jira_client
            ) as mock_get_client,
            patch(
                "sys.argv",
                ["get_permission_scheme.py", "10000", "--profile", "development"],
            ),
        ):
            from get_permission_scheme import main

            main()

        mock_get_client.assert_called_once_with(profile="development")
