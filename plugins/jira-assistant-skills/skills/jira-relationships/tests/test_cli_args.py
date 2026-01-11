"""
CLI Argument Parsing Tests for jira-relationships skill.

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


@pytest.mark.relationships
@pytest.mark.unit
class TestLinkIssueCLI:
    """CLI argument tests for link_issue.py."""

    def test_required_args(self):
        """Test that issue_key and a link type are required."""
        import link_issue

        # Missing all required args
        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["link_issue.py"]):
                link_issue.main()
        assert exc_info.value.code == 2

        # Missing link type (semantic flag or --type with --to)
        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["link_issue.py", "PROJ-123"]):
                link_issue.main()
        assert exc_info.value.code == 1  # ValidationError, not argparse error

    def test_valid_positional_args(self):
        """Test valid positional argument with semantic flag."""
        import link_issue

        with patch("sys.argv", ["link_issue.py", "PROJ-123", "--blocks", "PROJ-456"]):
            with patch.object(link_issue, "get_jira_client") as mock_client:
                mock_client.return_value.get_link_types.return_value = [
                    {"name": "Blocks", "outward": "blocks"}
                ]
                mock_client.return_value.create_link = Mock()
                mock_client.return_value.close = Mock()
                try:
                    link_issue.main()
                except SystemExit as e:
                    if e.code == 2:
                        pytest.fail("Valid args should be accepted")

    def test_type_option(self):
        """Test --type option with --to."""
        import link_issue

        for link_type in ["Blocks", "Relates", "Cloners", "Duplicate"]:
            with (
                patch(
                    "sys.argv",
                    [
                        "link_issue.py",
                        "PROJ-123",
                        "--type",
                        link_type,
                        "--to",
                        "PROJ-456",
                    ],
                ),
                patch.object(link_issue, "get_jira_client") as mock_client,
            ):
                mock_client.return_value.get_link_types.return_value = [
                    {"name": link_type}
                ]
                mock_client.return_value.create_link = Mock()
                mock_client.return_value.close = Mock()
                try:
                    link_issue.main()
                except SystemExit as e:
                    if e.code == 2:
                        pytest.fail(f"--type {link_type} --to should be valid")


@pytest.mark.relationships
@pytest.mark.unit
class TestBulkLinkCLI:
    """CLI argument tests for bulk_link.py."""

    def test_requires_issues_or_jql(self):
        """Test that either --issues or --jql is required."""
        import bulk_link

        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["bulk_link.py", "--blocks", "PROJ-100"]):
                bulk_link.main()

        assert exc_info.value.code == 2

    def test_target_required(self):
        """Test that a link type with target is required."""
        import bulk_link

        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["bulk_link.py", "--issues", "PROJ-1"]):
                bulk_link.main()

        assert exc_info.value.code == 2

    def test_type_with_to_required(self):
        """Test that --type requires --to."""
        import bulk_link

        with (
            pytest.raises(SystemExit) as exc_info,
            patch(
                "sys.argv", ["bulk_link.py", "--issues", "PROJ-1", "--type", "Blocks"]
            ),
        ):
            bulk_link.main()

        assert exc_info.value.code == 2

    def test_valid_input(self):
        """Test valid input combination."""
        import bulk_link

        with (
            patch(
                "sys.argv",
                [
                    "bulk_link.py",
                    "--issues",
                    "PROJ-1,PROJ-2",
                    "--blocks",
                    "PROJ-100",
                    "--dry-run",
                ],
            ),
            patch.object(bulk_link, "get_jira_client") as mock_client,
        ):
            mock_client.return_value.close = Mock()
            try:
                bulk_link.main()
            except SystemExit as e:
                if e.code == 2:
                    pytest.fail("Valid input should be accepted")

    def test_skip_existing_option(self):
        """Test --skip-existing option."""
        import bulk_link

        with (
            patch(
                "sys.argv",
                [
                    "bulk_link.py",
                    "--issues",
                    "PROJ-1",
                    "--blocks",
                    "PROJ-100",
                    "--skip-existing",
                    "--dry-run",
                ],
            ),
            patch.object(bulk_link, "get_jira_client") as mock_client,
        ):
            mock_client.return_value.close = Mock()
            try:
                bulk_link.main()
            except SystemExit as e:
                if e.code == 2:
                    pytest.fail("--skip-existing should be valid")

    def test_jql_input(self):
        """Test --jql input."""
        import bulk_link

        with (
            patch(
                "sys.argv",
                [
                    "bulk_link.py",
                    "--jql",
                    "project = PROJ AND fixVersion = 1.0",
                    "--relates-to",
                    "PROJ-100",
                    "--dry-run",
                ],
            ),
            patch.object(bulk_link, "get_jira_client") as mock_client,
        ):
            mock_client.return_value.search_issues.return_value = {
                "issues": [],
                "total": 0,
            }
            mock_client.return_value.close = Mock()
            try:
                bulk_link.main()
            except SystemExit as e:
                if e.code == 2:
                    pytest.fail("--jql should be valid")
