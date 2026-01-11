"""
CLI Argument Parsing Tests for jira-fields skill.

Tests verify that argparse configurations are correct and handle
various input combinations properly.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add scripts path
scripts_path = str(Path(__file__).parent.parent / "scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


@pytest.mark.fields
@pytest.mark.unit
class TestListFieldsCLI:
    """CLI argument tests for list_fields.py."""

    def test_no_required_args(self):
        """Test list_fields works with no arguments."""
        import list_fields

        with patch("sys.argv", ["list_fields.py"]):
            with patch.object(list_fields, "get_jira_client") as mock_client:
                mock_client.return_value.get.return_value = []
                mock_client.return_value.close = Mock()
                try:
                    list_fields.main()
                except SystemExit as e:
                    if e.code == 2:
                        pytest.fail("Should work with no arguments")

    def test_type_filter(self):
        """Test --all flag for showing all field types."""
        import list_fields

        # Test with --all flag (shows all fields including system)
        with patch("sys.argv", ["list_fields.py", "--all"]):
            with patch.object(list_fields, "get_jira_client") as mock_client:
                mock_client.return_value.get.return_value = []
                mock_client.return_value.close = Mock()
                try:
                    list_fields.main()
                except SystemExit as e:
                    if e.code == 2:
                        pytest.fail("--all flag should be valid")

    def test_search_filter(self):
        """Test --filter option for searching fields by name."""
        import list_fields

        with patch("sys.argv", ["list_fields.py", "--filter", "story"]):
            with patch.object(list_fields, "get_jira_client") as mock_client:
                mock_client.return_value.get.return_value = []
                mock_client.return_value.close = Mock()
                try:
                    list_fields.main()
                except SystemExit as e:
                    if e.code == 2:
                        pytest.fail("--filter should be valid")

    def test_output_format(self):
        """Test output format options."""
        import list_fields

        for fmt in ["text", "json"]:
            with patch("sys.argv", ["list_fields.py", "--output", fmt]):
                with patch.object(list_fields, "get_jira_client") as mock_client:
                    mock_client.return_value.get.return_value = []
                    mock_client.return_value.close = Mock()
                    try:
                        list_fields.main()
                    except SystemExit as e:
                        if e.code == 2:
                            pytest.fail(f"--output {fmt} should be valid")


@pytest.mark.fields
@pytest.mark.unit
class TestCreateFieldCLI:
    """CLI argument tests for create_field.py."""

    def test_name_required(self):
        """Test that name is required."""
        import create_field

        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["create_field.py", "--type", "text"]):
                create_field.main()

        assert exc_info.value.code == 2

    def test_type_required(self):
        """Test that --type is required."""
        import create_field

        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["create_field.py", "MyField"]):
                create_field.main()

        assert exc_info.value.code == 2

    def test_valid_field_types(self):
        """Test valid field type choices."""
        import create_field

        valid_types = [
            "text",
            "textarea",
            "number",
            "date",
            "datetime",
            "select",
            "multiselect",
            "checkbox",
        ]

        for field_type in valid_types:
            with (
                patch(
                    "sys.argv",
                    ["create_field.py", "--name", "MyField", "--type", field_type],
                ),
                patch.object(create_field, "get_jira_client") as mock_client,
            ):
                mock_client.return_value.post.return_value = {"id": "customfield_10100"}
                mock_client.return_value.close = Mock()
                try:
                    create_field.main()
                except SystemExit as e:
                    if e.code == 2:
                        pytest.fail(f"Field type '{field_type}' should be valid")

    def test_optional_description(self):
        """Test --description option."""
        import create_field

        with (
            patch(
                "sys.argv",
                [
                    "create_field.py",
                    "--name",
                    "MyField",
                    "--type",
                    "text",
                    "--description",
                    "A custom field for testing",
                ],
            ),
            patch.object(create_field, "get_jira_client") as mock_client,
        ):
            mock_client.return_value.post.return_value = {"id": "customfield_10100"}
            mock_client.return_value.close = Mock()
            try:
                create_field.main()
            except SystemExit as e:
                if e.code == 2:
                    pytest.fail("--description should be valid")


@pytest.mark.fields
@pytest.mark.unit
class TestConfigureAgileFieldsCLI:
    """CLI argument tests for configure_agile_fields.py."""

    def test_project_required(self):
        """Test that --project is required."""
        import configure_agile_fields

        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["configure_agile_fields.py"]):
                configure_agile_fields.main()

        assert exc_info.value.code == 2

    def test_valid_project(self):
        """Test valid positional project argument."""
        import configure_agile_fields

        with patch("sys.argv", ["configure_agile_fields.py", "PROJ"]):
            with patch.object(configure_agile_fields, "get_jira_client") as mock_client:
                mock_client.return_value.get.return_value = []
                mock_client.return_value.close = Mock()
                try:
                    configure_agile_fields.main()
                except SystemExit as e:
                    if e.code == 2:
                        pytest.fail("positional project argument should be valid")

    def test_discover_flag(self):
        """Test that discovery is automatic with positional project."""
        import configure_agile_fields

        # Discovery is automatic in this script - no --discover flag needed
        with patch("sys.argv", ["configure_agile_fields.py", "PROJ"]):
            with patch.object(configure_agile_fields, "get_jira_client") as mock_client:
                mock_client.return_value.get.return_value = []
                mock_client.return_value.close = Mock()
                try:
                    configure_agile_fields.main()
                except SystemExit as e:
                    if e.code == 2:
                        pytest.fail(
                            "positional project with auto-discovery should be valid"
                        )
