"""
Unit tests for list_permission_schemes.py

TDD: Write tests first before implementing the script.
Tests cover:
- Basic listing of permission schemes
- Filtering by name
- JSON output format
- Table output format
- Show grants expansion
- Show projects association
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


class TestListPermissionSchemes:
    """Tests for listing permission schemes."""

    def test_list_all_schemes(self, mock_jira_client, permission_schemes_response):
        """Test listing all permission schemes."""
        mock_jira_client.get_permission_schemes.return_value = (
            permission_schemes_response
        )

        from list_permission_schemes import list_permission_schemes

        schemes = list_permission_schemes(mock_jira_client)

        assert len(schemes) == 3
        assert schemes[0]["name"] == "Default Software Scheme"
        mock_jira_client.get_permission_schemes.assert_called_once()

    def test_list_empty_schemes(self, mock_jira_client, empty_permission_schemes):
        """Test listing when no schemes exist."""
        mock_jira_client.get_permission_schemes.return_value = empty_permission_schemes

        from list_permission_schemes import list_permission_schemes

        schemes = list_permission_schemes(mock_jira_client)

        assert len(schemes) == 0

    def test_filter_by_name(self, mock_jira_client, permission_schemes_response):
        """Test filtering schemes by name."""
        mock_jira_client.get_permission_schemes.return_value = (
            permission_schemes_response
        )

        from list_permission_schemes import list_permission_schemes

        schemes = list_permission_schemes(mock_jira_client, name_filter="Development")

        assert len(schemes) == 1
        assert "Development" in schemes[0]["name"]

    def test_filter_by_name_case_insensitive(
        self, mock_jira_client, permission_schemes_response
    ):
        """Test filtering schemes by name is case-insensitive."""
        mock_jira_client.get_permission_schemes.return_value = (
            permission_schemes_response
        )

        from list_permission_schemes import list_permission_schemes

        schemes = list_permission_schemes(mock_jira_client, name_filter="development")

        assert len(schemes) == 1
        assert "Development" in schemes[0]["name"]

    def test_filter_no_matches(self, mock_jira_client, permission_schemes_response):
        """Test filtering with no matches returns empty list."""
        mock_jira_client.get_permission_schemes.return_value = (
            permission_schemes_response
        )

        from list_permission_schemes import list_permission_schemes

        schemes = list_permission_schemes(mock_jira_client, name_filter="nonexistent")

        assert len(schemes) == 0

    def test_show_grants_expands_permissions(
        self, mock_jira_client, permission_schemes_response
    ):
        """Test that show_grants requests permission expansion."""
        mock_jira_client.get_permission_schemes.return_value = (
            permission_schemes_response
        )

        from list_permission_schemes import list_permission_schemes

        list_permission_schemes(mock_jira_client, show_grants=True)

        mock_jira_client.get_permission_schemes.assert_called_once_with(
            expand="permissions"
        )

    def test_format_schemes_table(self, mock_jira_client, permission_schemes_response):
        """Test formatting schemes as a table."""
        mock_jira_client.get_permission_schemes.return_value = (
            permission_schemes_response
        )

        from list_permission_schemes import format_permission_schemes

        output = format_permission_schemes(
            permission_schemes_response["permissionSchemes"], output_format="table"
        )

        # Table should contain scheme names
        assert "Default Software Scheme" in output
        assert "Internal Projects Scheme" in output
        assert "Custom Development Scheme" in output

    def test_format_schemes_json(self, mock_jira_client, permission_schemes_response):
        """Test formatting schemes as JSON."""
        from list_permission_schemes import format_permission_schemes

        output = format_permission_schemes(
            permission_schemes_response["permissionSchemes"], output_format="json"
        )

        # Should be valid JSON
        parsed = json.loads(output)
        assert len(parsed) == 3
        assert parsed[0]["name"] == "Default Software Scheme"

    def test_scheme_has_expected_fields(
        self, mock_jira_client, permission_schemes_response
    ):
        """Test that scheme objects have expected fields."""
        mock_jira_client.get_permission_schemes.return_value = (
            permission_schemes_response
        )

        from list_permission_schemes import list_permission_schemes

        schemes = list_permission_schemes(mock_jira_client)

        for scheme in schemes:
            assert "id" in scheme
            assert "name" in scheme
            # Description may or may not be present

    def test_api_error_handling(self, mock_jira_client):
        """Test handling of API errors."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.get_permission_schemes.side_effect = JiraError(
            "API Error", status_code=500
        )

        from list_permission_schemes import list_permission_schemes

        with pytest.raises(JiraError):
            list_permission_schemes(mock_jira_client)

    def test_permission_denied_error(self, mock_jira_client):
        """Test handling of permission denied errors."""
        from jira_assistant_skills_lib import PermissionError

        mock_jira_client.get_permission_schemes.side_effect = PermissionError(
            "You do not have permission to view permission schemes"
        )

        from list_permission_schemes import list_permission_schemes

        with pytest.raises(PermissionError):
            list_permission_schemes(mock_jira_client)


class TestListPermissionSchemesWithGrants:
    """Tests for listing schemes with grant details."""

    def test_list_with_grants_included(
        self, mock_jira_client, permission_scheme_detail
    ):
        """Test listing schemes with grants expanded."""
        # When expanding permissions, each scheme has grants
        response = {"permissionSchemes": [permission_scheme_detail]}
        mock_jira_client.get_permission_schemes.return_value = response

        from list_permission_schemes import list_permission_schemes

        schemes = list_permission_schemes(mock_jira_client, show_grants=True)

        assert len(schemes) == 1
        assert "permissions" in schemes[0]
        assert len(schemes[0]["permissions"]) > 0

    def test_format_grants_in_table(self, permission_scheme_detail):
        """Test that grants are formatted correctly in table output."""
        from list_permission_schemes import format_permission_schemes

        output = format_permission_schemes(
            [permission_scheme_detail], output_format="table", show_grants=True
        )

        # Should show grant count column
        assert "Grants" in output or "grants" in output.lower()

    def test_count_grants_per_scheme(self, permission_scheme_detail):
        """Test that grant counts are shown."""
        from list_permission_schemes import format_permission_schemes

        output = format_permission_schemes(
            [permission_scheme_detail], output_format="table", show_grants=True
        )

        # Should show grant count
        assert "6" in output or "Grants: 6" in output or "6 grants" in output.lower()


class TestListPermissionSchemesCSV:
    """Tests for CSV output format."""

    def test_csv_output(self, permission_schemes_response):
        """Test CSV output format."""
        from list_permission_schemes import format_permission_schemes

        output = format_permission_schemes(
            permission_schemes_response["permissionSchemes"], output_format="csv"
        )

        # Should be valid CSV with headers
        lines = output.strip().split("\n")
        assert len(lines) == 4  # Header + 3 schemes
        assert "id" in lines[0].lower() or "ID" in lines[0]

    def test_csv_has_all_schemes(self, permission_schemes_response):
        """Test CSV contains all schemes."""
        from list_permission_schemes import format_permission_schemes

        output = format_permission_schemes(
            permission_schemes_response["permissionSchemes"], output_format="csv"
        )

        assert "Default Software Scheme" in output
        assert "Internal Projects Scheme" in output
        assert "Custom Development Scheme" in output


class TestListPermissionSchemesCLI:
    """Tests for the CLI main() function."""

    def test_cli_basic_list(
        self, mock_jira_client, permission_schemes_response, capsys
    ):
        """Test CLI basic list command."""
        mock_jira_client.get_permission_schemes.return_value = (
            permission_schemes_response
        )

        with (
            patch(
                "list_permission_schemes.get_jira_client", return_value=mock_jira_client
            ),
            patch("sys.argv", ["list_permission_schemes.py"]),
        ):
            from list_permission_schemes import main

            main()

        captured = capsys.readouterr()
        assert "Default Software Scheme" in captured.out

    def test_cli_json_output(
        self, mock_jira_client, permission_schemes_response, capsys
    ):
        """Test CLI with JSON output format."""
        mock_jira_client.get_permission_schemes.return_value = (
            permission_schemes_response
        )

        with (
            patch(
                "list_permission_schemes.get_jira_client", return_value=mock_jira_client
            ),
            patch("sys.argv", ["list_permission_schemes.py", "--output", "json"]),
        ):
            from list_permission_schemes import main

            main()

        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert len(parsed) == 3

    def test_cli_filter_by_name(
        self, mock_jira_client, permission_schemes_response, capsys
    ):
        """Test CLI filtering by name."""
        mock_jira_client.get_permission_schemes.return_value = (
            permission_schemes_response
        )

        with (
            patch(
                "list_permission_schemes.get_jira_client", return_value=mock_jira_client
            ),
            patch(
                "sys.argv", ["list_permission_schemes.py", "--filter", "Development"]
            ),
        ):
            from list_permission_schemes import main

            main()

        captured = capsys.readouterr()
        assert "Development" in captured.out
        # Should not show Internal scheme
        assert "Internal Projects Scheme" not in captured.out

    def test_cli_show_grants(self, mock_jira_client, permission_scheme_detail, capsys):
        """Test CLI with grants expansion."""
        response = {"permissionSchemes": [permission_scheme_detail]}
        mock_jira_client.get_permission_schemes.return_value = response

        with (
            patch(
                "list_permission_schemes.get_jira_client", return_value=mock_jira_client
            ),
            patch("sys.argv", ["list_permission_schemes.py", "--show-grants"]),
        ):
            from list_permission_schemes import main

            main()

        mock_jira_client.get_permission_schemes.assert_called_with(expand="permissions")

    def test_cli_error_handling(self, mock_jira_client, capsys):
        """Test CLI handles errors gracefully."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.get_permission_schemes.side_effect = JiraError(
            "API Error", status_code=500
        )

        with (
            patch(
                "list_permission_schemes.get_jira_client", return_value=mock_jira_client
            ),
            patch("sys.argv", ["list_permission_schemes.py"]),
        ):
            from list_permission_schemes import main

            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 1

    def test_cli_with_profile(self, mock_jira_client, permission_schemes_response):
        """Test CLI with profile argument."""
        mock_jira_client.get_permission_schemes.return_value = (
            permission_schemes_response
        )

        with (
            patch(
                "list_permission_schemes.get_jira_client", return_value=mock_jira_client
            ) as mock_get_client,
            patch(
                "sys.argv", ["list_permission_schemes.py", "--profile", "development"]
            ),
        ):
            from list_permission_schemes import main

            main()

        mock_get_client.assert_called_once_with(profile="development")
