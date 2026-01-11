"""
Unit tests for update_permission_scheme.py

TDD: Write tests first before implementing the script.
Tests cover:
- Updating scheme name and description
- Adding permission grants
- Removing permission grants
- Error handling
"""

import copy
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


class TestUpdateSchemeMetadata:
    """Tests for updating scheme name and description."""

    def test_update_name(self, mock_jira_client, updated_permission_scheme):
        """Test updating scheme name."""
        mock_jira_client.update_permission_scheme.return_value = (
            updated_permission_scheme
        )

        from update_permission_scheme import update_permission_scheme

        scheme = update_permission_scheme(
            mock_jira_client, scheme_id=10000, name="Updated Scheme Name"
        )

        assert scheme["name"] == "Updated Scheme Name"
        mock_jira_client.update_permission_scheme.assert_called_once_with(
            10000, name="Updated Scheme Name", description=None
        )

    def test_update_description(self, mock_jira_client, updated_permission_scheme):
        """Test updating scheme description."""
        expected = copy.deepcopy(updated_permission_scheme)
        expected["description"] = "New description"
        mock_jira_client.update_permission_scheme.return_value = expected

        from update_permission_scheme import update_permission_scheme

        scheme = update_permission_scheme(
            mock_jira_client, scheme_id=10000, description="New description"
        )

        assert scheme["description"] == "New description"

    def test_update_both(self, mock_jira_client, updated_permission_scheme):
        """Test updating both name and description."""
        mock_jira_client.update_permission_scheme.return_value = (
            updated_permission_scheme
        )

        from update_permission_scheme import update_permission_scheme

        update_permission_scheme(
            mock_jira_client,
            scheme_id=10000,
            name="Updated Name",
            description="Updated description",
        )

        mock_jira_client.update_permission_scheme.assert_called_once_with(
            10000, name="Updated Name", description="Updated description"
        )

    def test_scheme_not_found(self, mock_jira_client):
        """Test error when scheme doesn't exist."""
        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.update_permission_scheme.side_effect = NotFoundError(
            "Scheme not found"
        )

        from update_permission_scheme import update_permission_scheme

        with pytest.raises(NotFoundError):
            update_permission_scheme(mock_jira_client, scheme_id=99999, name="New Name")


class TestAddGrants:
    """Tests for adding permission grants."""

    def test_add_single_grant(self, mock_jira_client, created_permission_grant):
        """Test adding a single grant."""
        mock_jira_client.create_permission_grant.return_value = created_permission_grant

        from update_permission_scheme import add_grants

        result = add_grants(
            mock_jira_client,
            scheme_id=10000,
            grants=["LINK_ISSUES:group:jira-developers"],
        )

        assert len(result) == 1
        mock_jira_client.create_permission_grant.assert_called_once()

    def test_add_multiple_grants(self, mock_jira_client, created_permission_grant):
        """Test adding multiple grants."""
        mock_jira_client.create_permission_grant.return_value = created_permission_grant

        from update_permission_scheme import add_grants

        grants = ["LINK_ISSUES:anyone", "MANAGE_WATCHERS:group:jira-developers"]

        result = add_grants(mock_jira_client, scheme_id=10000, grants=grants)

        assert len(result) == 2
        assert mock_jira_client.create_permission_grant.call_count == 2

    def test_add_grant_with_project_role(
        self, mock_jira_client, created_permission_grant
    ):
        """Test adding a grant for a project role."""
        mock_jira_client.create_permission_grant.return_value = created_permission_grant

        from update_permission_scheme import add_grants

        add_grants(
            mock_jira_client,
            scheme_id=10000,
            grants=["EDIT_ISSUES:projectRole:Developers"],
        )

        call_args = mock_jira_client.create_permission_grant.call_args
        assert call_args[1]["holder_type"] == "projectRole"
        assert call_args[1]["holder_parameter"] == "Developers"


class TestRemoveGrants:
    """Tests for removing permission grants."""

    def test_remove_grant_by_id(self, mock_jira_client):
        """Test removing a grant by its ID."""
        from update_permission_scheme import remove_grants

        remove_grants(mock_jira_client, scheme_id=10000, grant_ids=[10103])

        mock_jira_client.delete_permission_grant.assert_called_once_with(10000, 10103)

    def test_remove_multiple_grants(self, mock_jira_client):
        """Test removing multiple grants."""
        from update_permission_scheme import remove_grants

        remove_grants(
            mock_jira_client, scheme_id=10000, grant_ids=[10103, 10104, 10105]
        )

        assert mock_jira_client.delete_permission_grant.call_count == 3

    def test_remove_grant_by_spec(self, mock_jira_client, permission_scheme_detail):
        """Test removing a grant by permission and holder spec."""
        mock_jira_client.get_permission_scheme.return_value = permission_scheme_detail

        from update_permission_scheme import find_and_remove_grant

        result = find_and_remove_grant(
            mock_jira_client,
            scheme_id=10000,
            grant_spec="EDIT_ISSUES:group:jira-developers",
        )

        assert result is True
        mock_jira_client.delete_permission_grant.assert_called_once()

    def test_remove_grant_not_found(self, mock_jira_client, permission_scheme_detail):
        """Test error when grant to remove is not found."""
        mock_jira_client.get_permission_scheme.return_value = permission_scheme_detail

        from assistant_skills_lib.error_handler import ValidationError
        from update_permission_scheme import find_and_remove_grant

        with pytest.raises(ValidationError):
            find_and_remove_grant(
                mock_jira_client,
                scheme_id=10000,
                grant_spec="NONEXISTENT:group:developers",
            )


class TestDryRun:
    """Tests for dry-run mode."""

    def test_dry_run_add_grant(self, mock_jira_client):
        """Test that dry-run doesn't add grants."""
        from update_permission_scheme import add_grants

        result = add_grants(
            mock_jira_client,
            scheme_id=10000,
            grants=["LINK_ISSUES:anyone"],
            dry_run=True,
        )

        mock_jira_client.create_permission_grant.assert_not_called()
        assert len(result) == 1

    def test_dry_run_remove_grant(self, mock_jira_client, permission_scheme_detail):
        """Test that dry-run doesn't remove grants."""
        mock_jira_client.get_permission_scheme.return_value = permission_scheme_detail

        from update_permission_scheme import find_and_remove_grant

        result = find_and_remove_grant(
            mock_jira_client,
            scheme_id=10000,
            grant_spec="EDIT_ISSUES:group:jira-developers",
            dry_run=True,
        )

        mock_jira_client.delete_permission_grant.assert_not_called()
        assert result is True


class TestUpdatePermissionSchemeCLI:
    """Tests for the CLI main() function."""

    def test_cli_update_name(self, mock_jira_client, updated_permission_scheme, capsys):
        """Test CLI update name command."""
        mock_jira_client.update_permission_scheme.return_value = (
            updated_permission_scheme
        )

        with (
            patch(
                "update_permission_scheme.get_jira_client",
                return_value=mock_jira_client,
            ),
            patch(
                "sys.argv",
                ["update_permission_scheme.py", "10000", "--name", "Updated Name"],
            ),
        ):
            from update_permission_scheme import main

            main()

        captured = capsys.readouterr()
        assert "Updated" in captured.out

    def test_cli_update_description(
        self, mock_jira_client, updated_permission_scheme, capsys
    ):
        """Test CLI update description."""
        mock_jira_client.update_permission_scheme.return_value = (
            updated_permission_scheme
        )

        with (
            patch(
                "update_permission_scheme.get_jira_client",
                return_value=mock_jira_client,
            ),
            patch(
                "sys.argv",
                [
                    "update_permission_scheme.py",
                    "10000",
                    "--description",
                    "New description",
                ],
            ),
        ):
            from update_permission_scheme import main

            main()

        mock_jira_client.update_permission_scheme.assert_called_once()

    def test_cli_add_grant(self, mock_jira_client, created_permission_grant, capsys):
        """Test CLI add grant."""
        mock_jira_client.create_permission_grant.return_value = created_permission_grant

        with (
            patch(
                "update_permission_scheme.get_jira_client",
                return_value=mock_jira_client,
            ),
            patch(
                "sys.argv",
                [
                    "update_permission_scheme.py",
                    "10000",
                    "--add-grant",
                    "LINK_ISSUES:group:developers",
                ],
            ),
        ):
            from update_permission_scheme import main

            main()

        mock_jira_client.create_permission_grant.assert_called_once()

    def test_cli_remove_grant_by_id(self, mock_jira_client, capsys):
        """Test CLI remove grant by ID."""
        with (
            patch(
                "update_permission_scheme.get_jira_client",
                return_value=mock_jira_client,
            ),
            patch(
                "sys.argv",
                ["update_permission_scheme.py", "10000", "--remove-grant", "10103"],
            ),
        ):
            from update_permission_scheme import main

            main()

        mock_jira_client.delete_permission_grant.assert_called_once_with(10000, 10103)

    def test_cli_dry_run(self, mock_jira_client, capsys):
        """Test CLI dry-run mode."""
        with (
            patch(
                "update_permission_scheme.get_jira_client",
                return_value=mock_jira_client,
            ),
            patch(
                "sys.argv",
                ["update_permission_scheme.py", "10000", "--name", "Test", "--dry-run"],
            ),
        ):
            from update_permission_scheme import main

            main()

        mock_jira_client.update_permission_scheme.assert_not_called()
        captured = capsys.readouterr()
        assert "DRY RUN" in captured.out

    def test_cli_error_handling(self, mock_jira_client, capsys):
        """Test CLI handles errors gracefully."""
        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.update_permission_scheme.side_effect = NotFoundError(
            "Scheme not found"
        )

        with (
            patch(
                "update_permission_scheme.get_jira_client",
                return_value=mock_jira_client,
            ),
            patch(
                "sys.argv", ["update_permission_scheme.py", "99999", "--name", "Test"]
            ),
        ):
            from update_permission_scheme import main

            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 1

