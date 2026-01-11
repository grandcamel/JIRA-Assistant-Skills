"""
Unit tests for fields CLI commands.

Tests cover:
- list: List fields with filters
- create: Create custom fields
- check-project: Check field availability for a project
- configure-agile: Configure Agile field mappings
"""

from copy import deepcopy
from unittest.mock import patch

import pytest

from jira_assistant_skills.cli.commands.fields_cmds import (
    AGILE_FIELDS,
    AGILE_PATTERNS,
    FIELD_TYPES,
    _add_field_to_screen,
    _check_project_fields_impl,
    _configure_agile_fields_impl,
    _create_field_impl,
    _find_agile_fields,
    _find_project_screens,
    _format_agile_config,
    _format_created_field,
    _format_fields_list,
    _format_project_fields,
    _list_fields_impl,
    fields,
)

# =============================================================================
# Constants Tests
# =============================================================================


@pytest.mark.unit
class TestConstants:
    """Tests for module constants."""

    def test_agile_patterns_defined(self):
        """Test that AGILE_PATTERNS is defined."""
        assert len(AGILE_PATTERNS) > 0
        assert "epic" in AGILE_PATTERNS
        assert "sprint" in AGILE_PATTERNS
        assert "story" in AGILE_PATTERNS

    def test_agile_fields_defined(self):
        """Test that AGILE_FIELDS is defined."""
        assert "sprint" in AGILE_FIELDS
        assert "story_points" in AGILE_FIELDS
        assert "epic_link" in AGILE_FIELDS

    def test_field_types_defined(self):
        """Test that FIELD_TYPES is defined with valid types."""
        assert "text" in FIELD_TYPES
        assert "number" in FIELD_TYPES
        assert "select" in FIELD_TYPES
        assert "date" in FIELD_TYPES

        # Each type should have 'type' and 'searcher' keys
        for field_type, config in FIELD_TYPES.items():
            assert "type" in config, f"Missing 'type' for {field_type}"
            assert "searcher" in config, f"Missing 'searcher' for {field_type}"


# =============================================================================
# Helper Function Tests
# =============================================================================


@pytest.mark.unit
class TestFindAgileFields:
    """Tests for the _find_agile_fields helper function."""

    def test_find_agile_fields_all_found(self, mock_jira_client, sample_fields):
        """Test finding all Agile fields."""
        mock_jira_client.get.return_value = deepcopy(sample_fields)

        result = _find_agile_fields(mock_jira_client)

        assert result["story_points"] == "customfield_10001"
        assert result["sprint"] == "customfield_10003"
        mock_jira_client.get.assert_called_once_with("/rest/api/3/field")

    def test_find_agile_fields_none_found(self, mock_jira_client):
        """Test when no Agile fields are found."""
        mock_jira_client.get.return_value = [
            {"id": "customfield_99999", "name": "Some Other Field"}
        ]

        result = _find_agile_fields(mock_jira_client)

        assert result["story_points"] is None
        assert result["epic_link"] is None
        assert result["sprint"] is None


@pytest.mark.unit
class TestFindProjectScreens:
    """Tests for the _find_project_screens helper function."""

    def test_find_project_screens_default(
        self, mock_jira_client, sample_project_classic, sample_screens
    ):
        """Test finding screens when no scheme mappings exist."""
        mock_jira_client.get.side_effect = [
            deepcopy(sample_project_classic),  # Project info
            {"values": []},  # No scheme mappings
            deepcopy(sample_screens),  # All screens
        ]

        result = _find_project_screens(mock_jira_client, "PROJ")

        assert len(result) == 1
        assert result[0]["name"] == "Default Screen"


@pytest.mark.unit
class TestAddFieldToScreen:
    """Tests for the _add_field_to_screen helper function."""

    def test_add_field_to_screen_dry_run(self, mock_jira_client):
        """Test dry-run mode returns True without making changes."""
        result = _add_field_to_screen(
            mock_jira_client, screen_id=1, field_id="customfield_10001", dry_run=True
        )

        assert result is True
        mock_jira_client.get.assert_not_called()
        mock_jira_client.post.assert_not_called()

    def test_add_field_to_screen_already_present(
        self, mock_jira_client, sample_screen_tabs, sample_screen_fields
    ):
        """Test when field is already on screen."""
        mock_jira_client.get.side_effect = [
            deepcopy(sample_screen_tabs),
            [{"id": "customfield_10001", "name": "Story Points"}],  # Field exists
        ]

        result = _add_field_to_screen(
            mock_jira_client, screen_id=1, field_id="customfield_10001"
        )

        assert result is True
        mock_jira_client.post.assert_not_called()

    def test_add_field_to_screen_success(
        self, mock_jira_client, sample_screen_tabs, sample_screen_fields
    ):
        """Test successfully adding a field to screen."""
        mock_jira_client.get.side_effect = [
            deepcopy(sample_screen_tabs),
            deepcopy(sample_screen_fields),  # Field not present
        ]

        result = _add_field_to_screen(
            mock_jira_client, screen_id=1, field_id="customfield_10001"
        )

        assert result is True
        mock_jira_client.post.assert_called_once()

    def test_add_field_to_screen_no_tabs(self, mock_jira_client):
        """Test when screen has no tabs."""
        mock_jira_client.get.return_value = []

        result = _add_field_to_screen(
            mock_jira_client, screen_id=1, field_id="customfield_10001"
        )

        assert result is False


# =============================================================================
# List Fields Implementation Tests
# =============================================================================


@pytest.mark.unit
class TestListFieldsImpl:
    """Tests for the _list_fields_impl implementation function."""

    def test_list_fields_custom_only(self, mock_jira_client, sample_fields):
        """Test listing only custom fields (default)."""
        mock_jira_client.get.return_value = deepcopy(sample_fields)

        with patch(
            "jira_assistant_skills.cli.commands.fields_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _list_fields_impl()

        # Should exclude 'summary' which has custom=False
        assert len(result) == 4
        assert all(f["custom"] for f in result)
        mock_jira_client.close.assert_called_once()

    def test_list_fields_all(self, mock_jira_client, sample_fields):
        """Test listing all fields including system fields."""
        mock_jira_client.get.return_value = deepcopy(sample_fields)

        with patch(
            "jira_assistant_skills.cli.commands.fields_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _list_fields_impl(custom_only=False)

        assert len(result) == 5

    def test_list_fields_with_filter(self, mock_jira_client, sample_fields):
        """Test listing fields with name filter."""
        mock_jira_client.get.return_value = deepcopy(sample_fields)

        with patch(
            "jira_assistant_skills.cli.commands.fields_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _list_fields_impl(filter_pattern="sprint")

        assert len(result) == 1
        assert result[0]["name"] == "Sprint"

    def test_list_fields_agile_only(self, mock_jira_client, sample_fields):
        """Test listing only Agile-related fields."""
        mock_jira_client.get.return_value = deepcopy(sample_fields)

        with patch(
            "jira_assistant_skills.cli.commands.fields_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _list_fields_impl(agile_only=True)

        # Story Points, Epic Link, Sprint match agile patterns
        assert len(result) == 3
        names = [f["name"] for f in result]
        assert "Story Points" in names
        assert "Epic Link" in names
        assert "Sprint" in names

    def test_list_fields_empty(self, mock_jira_client):
        """Test listing fields when none match criteria."""
        mock_jira_client.get.return_value = []

        with patch(
            "jira_assistant_skills.cli.commands.fields_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _list_fields_impl()

        assert result == []


# =============================================================================
# Create Field Implementation Tests
# =============================================================================


@pytest.mark.unit
class TestCreateFieldImpl:
    """Tests for the _create_field_impl implementation function."""

    def test_create_field_text(self, mock_jira_client, sample_created_field):
        """Test creating a text field."""
        mock_jira_client.post.return_value = deepcopy(sample_created_field)

        with patch(
            "jira_assistant_skills.cli.commands.fields_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _create_field_impl(name="Custom Text Field", field_type="text")

        assert result["id"] == "customfield_10005"
        mock_jira_client.post.assert_called_once()
        call_args = mock_jira_client.post.call_args
        assert call_args[1]["data"]["name"] == "Custom Text Field"
        mock_jira_client.close.assert_called_once()

    def test_create_field_with_description(
        self, mock_jira_client, sample_created_field
    ):
        """Test creating a field with description."""
        mock_jira_client.post.return_value = deepcopy(sample_created_field)

        with patch(
            "jira_assistant_skills.cli.commands.fields_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            _create_field_impl(
                name="Custom Text Field",
                field_type="text",
                description="A custom text field",
            )

        call_args = mock_jira_client.post.call_args
        assert "description" in call_args[1]["data"]
        assert call_args[1]["data"]["description"] == "A custom text field"

    def test_create_field_invalid_type(self, mock_jira_client):
        """Test that invalid field type raises ValidationError."""
        from jira_assistant_skills_lib import ValidationError

        with (
            patch(
                "jira_assistant_skills.cli.commands.fields_cmds.get_jira_client",
                return_value=mock_jira_client,
            ),
            pytest.raises(ValidationError, match="Invalid field type"),
        ):
            _create_field_impl(name="Test Field", field_type="invalid_type")

        mock_jira_client.post.assert_not_called()


# =============================================================================
# Check Project Fields Implementation Tests
# =============================================================================


@pytest.mark.unit
class TestCheckProjectFieldsImpl:
    """Tests for the _check_project_fields_impl implementation function."""

    def test_check_project_fields_basic(
        self, mock_jira_client, sample_project_classic, sample_project_meta
    ):
        """Test checking project fields."""
        mock_jira_client.get.side_effect = [
            deepcopy(sample_project_classic),
            deepcopy(sample_project_meta),
        ]

        with patch(
            "jira_assistant_skills.cli.commands.fields_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _check_project_fields_impl(project_key="PROJ")

        assert result["project_key"] == "PROJ"
        assert result["project"]["key"] == "PROJ"
        assert result["is_team_managed"] is False
        assert len(result["issue_types"]) == 2
        mock_jira_client.close.assert_called_once()

    def test_check_project_fields_team_managed(
        self, mock_jira_client, sample_project_nextgen, sample_project_meta
    ):
        """Test checking team-managed project fields."""
        mock_jira_client.get.side_effect = [
            deepcopy(sample_project_nextgen),
            deepcopy(sample_project_meta),
        ]

        with patch(
            "jira_assistant_skills.cli.commands.fields_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _check_project_fields_impl(project_key="TEAM")

        assert result["is_team_managed"] is True

    def test_check_project_fields_with_agile(
        self, mock_jira_client, sample_project_classic, sample_project_meta
    ):
        """Test checking project fields with Agile check."""
        mock_jira_client.get.side_effect = [
            deepcopy(sample_project_classic),
            deepcopy(sample_project_meta),
        ]

        with patch(
            "jira_assistant_skills.cli.commands.fields_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _check_project_fields_impl(project_key="PROJ", check_agile=True)

        assert "agile_fields" in result
        # Story Points should be found
        assert result["agile_fields"]["story_points"] is not None

    def test_check_project_fields_specific_issue_type(
        self, mock_jira_client, sample_project_classic, sample_project_meta
    ):
        """Test checking fields for specific issue type."""
        mock_jira_client.get.side_effect = [
            deepcopy(sample_project_classic),
            deepcopy(sample_project_meta),
        ]

        with patch(
            "jira_assistant_skills.cli.commands.fields_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _check_project_fields_impl(project_key="PROJ", issue_type="Task")

        # Should still work but pass issue type to API
        assert result["project_key"] == "PROJ"


# =============================================================================
# Configure Agile Fields Implementation Tests
# =============================================================================


@pytest.mark.unit
class TestConfigureAgileFieldsImpl:
    """Tests for the _configure_agile_fields_impl implementation function."""

    def test_configure_agile_fields_dry_run(
        self,
        mock_jira_client,
        sample_project_classic,
        sample_fields,
        sample_screens,
    ):
        """Test configure Agile fields with dry-run."""
        mock_jira_client.get.side_effect = [
            deepcopy(sample_project_classic),
            deepcopy(sample_fields),  # For finding agile fields
            deepcopy(sample_project_classic),  # For finding screens
            {"values": []},  # No scheme mappings
            deepcopy(sample_screens),
        ]

        with patch(
            "jira_assistant_skills.cli.commands.fields_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _configure_agile_fields_impl(project_key="PROJ", dry_run=True)

        assert result["dry_run"] is True
        assert result["project"] == "PROJ"
        assert "fields_found" in result
        mock_jira_client.close.assert_called_once()

    def test_configure_agile_fields_team_managed_error(
        self, mock_jira_client, sample_project_nextgen
    ):
        """Test that team-managed project raises ValidationError."""
        from jira_assistant_skills_lib import ValidationError

        mock_jira_client.get.return_value = deepcopy(sample_project_nextgen)

        with (
            patch(
                "jira_assistant_skills.cli.commands.fields_cmds.get_jira_client",
                return_value=mock_jira_client,
            ),
            pytest.raises(ValidationError, match="team-managed"),
        ):
            _configure_agile_fields_impl(project_key="TEAM")

    def test_configure_agile_fields_no_agile_fields_error(
        self, mock_jira_client, sample_project_classic
    ):
        """Test error when no Agile fields found."""
        from jira_assistant_skills_lib import ValidationError

        mock_jira_client.get.side_effect = [
            deepcopy(sample_project_classic),
            [],  # No fields
        ]

        with (
            patch(
                "jira_assistant_skills.cli.commands.fields_cmds.get_jira_client",
                return_value=mock_jira_client,
            ),
            pytest.raises(ValidationError, match="No Agile fields found"),
        ):
            _configure_agile_fields_impl(project_key="PROJ")

    def test_configure_agile_fields_with_explicit_ids(
        self,
        mock_jira_client,
        sample_project_classic,
        sample_fields,
        sample_screens,
        sample_screen_tabs,
        sample_screen_fields,
    ):
        """Test configure with explicit field IDs."""
        mock_jira_client.get.side_effect = [
            deepcopy(sample_project_classic),
            deepcopy(sample_fields),
            deepcopy(sample_project_classic),
            {"values": []},
            deepcopy(sample_screens),
            deepcopy(sample_screen_tabs),
            deepcopy(sample_screen_fields),
        ]

        with patch(
            "jira_assistant_skills.cli.commands.fields_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _configure_agile_fields_impl(
                project_key="PROJ",
                story_points_id="customfield_99999",
                dry_run=True,
            )

        assert result["fields_found"]["story_points"] == "customfield_99999"


# =============================================================================
# Formatting Function Tests
# =============================================================================


@pytest.mark.unit
class TestFormatFieldsList:
    """Tests for the _format_fields_list formatting function."""

    def test_format_fields_list_empty(self):
        """Test formatting empty field list."""
        result = _format_fields_list([])
        assert "No fields found" in result

    def test_format_fields_list_with_fields(self):
        """Test formatting field list with data."""
        fields = [
            {"id": "customfield_10001", "name": "Story Points", "type": "number"},
            {"id": "customfield_10002", "name": "Epic Link", "type": "string"},
        ]

        result = _format_fields_list(fields)

        assert "Found 2 field(s)" in result
        assert "Story Points" in result
        assert "Epic Link" in result
        assert "customfield_10001" in result


@pytest.mark.unit
class TestFormatCreatedField:
    """Tests for the _format_created_field formatting function."""

    def test_format_created_field(self, sample_created_field):
        """Test formatting created field."""
        result = _format_created_field(sample_created_field)

        assert "Created field" in result
        assert "Custom Text Field" in result
        assert "customfield_10005" in result


@pytest.mark.unit
class TestFormatProjectFields:
    """Tests for the _format_project_fields formatting function."""

    def test_format_project_fields_basic(self):
        """Test formatting project fields without Agile check."""
        data = {
            "project": {
                "key": "PROJ",
                "name": "Test Project",
                "project_type": "software",
            },
            "is_team_managed": False,
            "issue_types": [
                {"name": "Task", "fields": [{"id": "summary"}]},
                {"name": "Bug", "fields": [{"id": "summary"}, {"id": "priority"}]},
            ],
        }

        result = _format_project_fields(data, check_agile=False)

        assert "Project: PROJ" in result
        assert "Test Project" in result
        assert "Issue Types: 2" in result

    def test_format_project_fields_with_agile(self):
        """Test formatting project fields with Agile check."""
        data = {
            "project": {
                "key": "PROJ",
                "name": "Test Project",
                "project_type": "software",
            },
            "is_team_managed": False,
            "issue_types": [],
            "agile_fields": {
                "story_points": {"id": "customfield_10001", "name": "Story Points"},
                "epic_link": None,
            },
        }

        result = _format_project_fields(data, check_agile=True)

        assert "Agile Field Availability" in result
        assert "story_points" in result


@pytest.mark.unit
class TestFormatAgileConfig:
    """Tests for the _format_agile_config formatting function."""

    def test_format_agile_config_dry_run(self):
        """Test formatting Agile config in dry-run mode."""
        data = {
            "project": "PROJ",
            "dry_run": True,
            "fields_found": {"story_points": "customfield_10001"},
            "screens_found": ["Default Screen"],
            "fields_added": [
                {
                    "field": "story_points",
                    "field_id": "customfield_10001",
                    "screen": "Default Screen",
                }
            ],
        }

        result = _format_agile_config(data)

        assert "[DRY RUN]" in result
        assert "Project: PROJ" in result
        assert "Would add" in result

    def test_format_agile_config_applied(self):
        """Test formatting Agile config when changes are applied."""
        data = {
            "project": "PROJ",
            "dry_run": False,
            "fields_found": {"story_points": "customfield_10001"},
            "screens_found": ["Default Screen"],
            "fields_added": [
                {
                    "field": "story_points",
                    "field_id": "customfield_10001",
                    "screen": "Default Screen",
                }
            ],
        }

        result = _format_agile_config(data)

        assert "[DRY RUN]" not in result
        assert "Added fields:" in result
        assert "configured successfully" in result


# =============================================================================
# CLI Command Tests
# =============================================================================


@pytest.mark.unit
class TestFieldsListCommand:
    """Tests for the fields list CLI command."""

    def test_fields_list_cli(self, cli_runner, mock_jira_client, sample_fields):
        """Test CLI fields list command."""
        mock_jira_client.get.return_value = deepcopy(sample_fields)

        with patch(
            "jira_assistant_skills.cli.commands.fields_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = cli_runner.invoke(fields, ["list"])

        assert result.exit_code == 0
        assert "Found" in result.output

    def test_fields_list_cli_json(self, cli_runner, mock_jira_client, sample_fields):
        """Test CLI fields list with JSON output."""
        mock_jira_client.get.return_value = deepcopy(sample_fields)

        with patch(
            "jira_assistant_skills.cli.commands.fields_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = cli_runner.invoke(fields, ["list", "--output", "json"])

        assert result.exit_code == 0
        assert "[" in result.output  # JSON array

    def test_fields_list_cli_agile(self, cli_runner, mock_jira_client, sample_fields):
        """Test CLI fields list with --agile flag."""
        mock_jira_client.get.return_value = deepcopy(sample_fields)

        with patch(
            "jira_assistant_skills.cli.commands.fields_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = cli_runner.invoke(fields, ["list", "--agile"])

        assert result.exit_code == 0


@pytest.mark.unit
class TestFieldsCreateCommand:
    """Tests for the fields create CLI command."""

    def test_fields_create_cli(
        self, cli_runner, mock_jira_client, sample_created_field
    ):
        """Test CLI fields create command."""
        mock_jira_client.post.return_value = deepcopy(sample_created_field)

        with patch(
            "jira_assistant_skills.cli.commands.fields_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = cli_runner.invoke(
                fields, ["create", "--name", "Test Field", "--type", "text"]
            )

        assert result.exit_code == 0
        assert "Created field" in result.output

    def test_fields_create_cli_json(
        self, cli_runner, mock_jira_client, sample_created_field
    ):
        """Test CLI fields create with JSON output."""
        mock_jira_client.post.return_value = deepcopy(sample_created_field)

        with patch(
            "jira_assistant_skills.cli.commands.fields_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = cli_runner.invoke(
                fields,
                [
                    "create",
                    "--name",
                    "Test Field",
                    "--type",
                    "text",
                    "--output",
                    "json",
                ],
            )

        assert result.exit_code == 0
        assert "{" in result.output  # JSON object


@pytest.mark.unit
class TestFieldsCheckProjectCommand:
    """Tests for the fields check-project CLI command."""

    def test_fields_check_project_cli(
        self, cli_runner, mock_jira_client, sample_project_classic, sample_project_meta
    ):
        """Test CLI fields check-project command."""
        mock_jira_client.get.side_effect = [
            deepcopy(sample_project_classic),
            deepcopy(sample_project_meta),
        ]

        with patch(
            "jira_assistant_skills.cli.commands.fields_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = cli_runner.invoke(fields, ["check-project", "PROJ"])

        assert result.exit_code == 0
        assert "Project: PROJ" in result.output

    def test_fields_check_project_cli_with_agile(
        self, cli_runner, mock_jira_client, sample_project_classic, sample_project_meta
    ):
        """Test CLI fields check-project with --check-agile flag."""
        mock_jira_client.get.side_effect = [
            deepcopy(sample_project_classic),
            deepcopy(sample_project_meta),
        ]

        with patch(
            "jira_assistant_skills.cli.commands.fields_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = cli_runner.invoke(
                fields, ["check-project", "PROJ", "--check-agile"]
            )

        assert result.exit_code == 0
        assert "Agile Field Availability" in result.output


@pytest.mark.unit
class TestFieldsConfigureAgileCommand:
    """Tests for the fields configure-agile CLI command."""

    def test_fields_configure_agile_cli_dry_run(
        self,
        cli_runner,
        mock_jira_client,
        sample_project_classic,
        sample_fields,
        sample_screens,
    ):
        """Test CLI fields configure-agile with dry-run."""
        mock_jira_client.get.side_effect = [
            deepcopy(sample_project_classic),
            deepcopy(sample_fields),
            deepcopy(sample_project_classic),
            {"values": []},
            deepcopy(sample_screens),
        ]

        with patch(
            "jira_assistant_skills.cli.commands.fields_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = cli_runner.invoke(fields, ["configure-agile", "PROJ", "--dry-run"])

        assert result.exit_code == 0
        assert "[DRY RUN]" in result.output

    def test_fields_configure_agile_cli_json(
        self,
        cli_runner,
        mock_jira_client,
        sample_project_classic,
        sample_fields,
        sample_screens,
    ):
        """Test CLI fields configure-agile with JSON output."""
        mock_jira_client.get.side_effect = [
            deepcopy(sample_project_classic),
            deepcopy(sample_fields),
            deepcopy(sample_project_classic),
            {"values": []},
            deepcopy(sample_screens),
        ]

        with patch(
            "jira_assistant_skills.cli.commands.fields_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = cli_runner.invoke(
                fields, ["configure-agile", "PROJ", "--dry-run", "--output", "json"]
            )

        assert result.exit_code == 0
        assert "{" in result.output
