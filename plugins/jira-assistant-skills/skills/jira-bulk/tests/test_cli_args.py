"""
CLI Argument Parsing Tests for jira-bulk skill.

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


@pytest.mark.bulk
@pytest.mark.unit
class TestBulkTransitionCLI:
    """CLI argument tests for bulk_transition.py."""

    def test_requires_issues_or_jql(self):
        """Test that either --issues or --jql is required."""
        import bulk_transition

        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["bulk_transition.py", "--to", "Done"]):
                bulk_transition.main()

        assert exc_info.value.code == 2

    def test_issues_and_jql_mutually_exclusive(self):
        """Test that --issues and --jql are mutually exclusive."""
        import bulk_transition

        with (
            pytest.raises(SystemExit) as exc_info,
            patch(
                "sys.argv",
                [
                    "bulk_transition.py",
                    "--issues",
                    "PROJ-1,PROJ-2",
                    "--jql",
                    "project = PROJ",
                    "--to",
                    "Done",
                ],
            ),
        ):
            bulk_transition.main()

        assert exc_info.value.code == 2

    def test_target_status_required(self):
        """Test that --to is required."""
        import bulk_transition

        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["bulk_transition.py", "--issues", "PROJ-1"]):
                bulk_transition.main()

        assert exc_info.value.code == 2

    def test_valid_issues_input(self):
        """Test valid --issues input."""
        import bulk_transition

        with (
            patch(
                "sys.argv",
                [
                    "bulk_transition.py",
                    "--issues",
                    "PROJ-1,PROJ-2,PROJ-3",
                    "--to",
                    "Done",
                    "--dry-run",
                ],
            ),
            patch.object(bulk_transition, "get_jira_client") as mock_client,
        ):
            mock_client.return_value.close = Mock()
            try:
                bulk_transition.main()
            except SystemExit as e:
                if e.code == 2:
                    pytest.fail("Valid --issues input should be accepted")

    def test_valid_jql_input(self):
        """Test valid --jql input."""
        import bulk_transition

        with (
            patch(
                "sys.argv",
                [
                    "bulk_transition.py",
                    "--jql",
                    'project = PROJ AND status = "In Progress"',
                    "--to",
                    "Done",
                    "--dry-run",
                ],
            ),
            patch.object(bulk_transition, "get_jira_client") as mock_client,
        ):
            mock_client.return_value.search_issues.return_value = {
                "issues": [],
                "total": 0,
            }
            mock_client.return_value.close = Mock()
            try:
                bulk_transition.main()
            except SystemExit as e:
                if e.code == 2:
                    pytest.fail("Valid --jql input should be accepted")

    def test_optional_resolution(self):
        """Test optional --resolution option."""
        import bulk_transition

        with (
            patch(
                "sys.argv",
                [
                    "bulk_transition.py",
                    "--issues",
                    "PROJ-1",
                    "--to",
                    "Done",
                    "--resolution",
                    "Fixed",
                    "--dry-run",
                ],
            ),
            patch.object(bulk_transition, "get_jira_client") as mock_client,
        ):
            mock_client.return_value.close = Mock()
            try:
                bulk_transition.main()
            except SystemExit as e:
                if e.code == 2:
                    pytest.fail("--resolution should be accepted")

    def test_optional_comment(self):
        """Test optional --comment option."""
        import bulk_transition

        with (
            patch(
                "sys.argv",
                [
                    "bulk_transition.py",
                    "--issues",
                    "PROJ-1",
                    "--to",
                    "Done",
                    "--comment",
                    "Closing as fixed",
                    "--dry-run",
                ],
            ),
            patch.object(bulk_transition, "get_jira_client") as mock_client,
        ):
            mock_client.return_value.close = Mock()
            try:
                bulk_transition.main()
            except SystemExit as e:
                if e.code == 2:
                    pytest.fail("--comment should be accepted")

    def test_max_issues_integer(self):
        """Test --max-issues accepts integer."""
        import bulk_transition

        with (
            patch(
                "sys.argv",
                [
                    "bulk_transition.py",
                    "--issues",
                    "PROJ-1",
                    "--to",
                    "Done",
                    "--max-issues",
                    "50",
                    "--dry-run",
                ],
            ),
            patch.object(bulk_transition, "get_jira_client") as mock_client,
        ):
            mock_client.return_value.close = Mock()
            try:
                bulk_transition.main()
            except SystemExit as e:
                if e.code == 2:
                    pytest.fail("--max-issues should accept integer")

    def test_short_options(self):
        """Test short option forms."""
        import bulk_transition

        with (
            patch(
                "sys.argv",
                [
                    "bulk_transition.py",
                    "-i",
                    "PROJ-1,PROJ-2",
                    "-t",
                    "Done",
                    "-r",
                    "Fixed",
                    "-c",
                    "Done",
                ],
            ),
            patch.object(bulk_transition, "get_jira_client") as mock_client,
        ):
            mock_client.return_value.get_transitions.return_value = [
                {"id": "1", "name": "Done", "to": {"name": "Done"}}
            ]
            mock_client.return_value.transition_issue = Mock()
            mock_client.return_value.add_comment = Mock()
            mock_client.return_value.close = Mock()
            try:
                bulk_transition.main()
            except SystemExit as e:
                if e.code == 2:
                    pytest.fail("Short options should be valid")


@pytest.mark.bulk
@pytest.mark.unit
class TestBulkAssignCLI:
    """CLI argument tests for bulk_assign.py."""

    def test_requires_issues_or_jql(self):
        """Test that either --issues or --jql is required."""
        import bulk_assign

        with (
            pytest.raises(SystemExit) as exc_info,
            patch("sys.argv", ["bulk_assign.py", "--assignee", "user@example.com"]),
        ):
            bulk_assign.main()

        assert exc_info.value.code == 2

    def test_assignee_required(self):
        """Test that --assignee is required."""
        import bulk_assign

        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["bulk_assign.py", "--issues", "PROJ-1"]):
                bulk_assign.main()

        assert exc_info.value.code == 2

    def test_valid_input(self):
        """Test valid input combination."""
        import bulk_assign

        with (
            patch(
                "sys.argv",
                [
                    "bulk_assign.py",
                    "--issues",
                    "PROJ-1,PROJ-2",
                    "--assignee",
                    "user@example.com",
                    "--dry-run",
                ],
            ),
            patch.object(bulk_assign, "get_jira_client") as mock_client,
        ):
            mock_client.return_value.close = Mock()
            try:
                bulk_assign.main()
            except SystemExit as e:
                if e.code == 2:
                    pytest.fail("Valid input should be accepted")

    def test_self_assignee(self):
        """Test --assignee self option."""
        import bulk_assign

        with (
            patch(
                "sys.argv",
                [
                    "bulk_assign.py",
                    "--issues",
                    "PROJ-1",
                    "--assignee",
                    "self",
                    "--dry-run",
                ],
            ),
            patch.object(bulk_assign, "get_jira_client") as mock_client,
        ):
            mock_client.return_value.get_current_user_id.return_value = "123456"
            mock_client.return_value.close = Mock()
            try:
                bulk_assign.main()
            except SystemExit as e:
                if e.code == 2:
                    pytest.fail("--assignee self should be accepted")


@pytest.mark.bulk
@pytest.mark.unit
class TestBulkSetPriorityCLI:
    """CLI argument tests for bulk_set_priority.py."""

    def test_requires_issues_or_jql(self):
        """Test that either --issues or --jql is required."""
        import bulk_set_priority

        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["bulk_set_priority.py", "--priority", "High"]):
                bulk_set_priority.main()

        assert exc_info.value.code == 2

    def test_priority_required(self):
        """Test that --priority is required."""
        import bulk_set_priority

        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["bulk_set_priority.py", "--issues", "PROJ-1"]):
                bulk_set_priority.main()

        assert exc_info.value.code == 2

    def test_valid_input(self):
        """Test valid input combination."""
        import bulk_set_priority

        with (
            patch(
                "sys.argv",
                [
                    "bulk_set_priority.py",
                    "--issues",
                    "PROJ-1,PROJ-2",
                    "--priority",
                    "High",
                    "--dry-run",
                ],
            ),
            patch.object(bulk_set_priority, "get_jira_client") as mock_client,
        ):
            mock_client.return_value.close = Mock()
            try:
                bulk_set_priority.main()
            except SystemExit as e:
                if e.code == 2:
                    pytest.fail("Valid input should be accepted")


@pytest.mark.bulk
@pytest.mark.unit
class TestBulkCloneCLI:
    """CLI argument tests for bulk_clone.py."""

    def test_requires_issues_or_jql(self):
        """Test that either --issues or --jql is required."""
        import bulk_clone

        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["bulk_clone.py", "--target-project", "OTHER"]):
                bulk_clone.main()

        assert exc_info.value.code == 2

    def test_valid_input(self):
        """Test valid input combination."""
        import bulk_clone

        with (
            patch(
                "sys.argv", ["bulk_clone.py", "--issues", "PROJ-1,PROJ-2", "--dry-run"]
            ),
            patch.object(bulk_clone, "get_jira_client") as mock_client,
        ):
            mock_client.return_value.close = Mock()
            try:
                bulk_clone.main()
            except SystemExit as e:
                if e.code == 2:
                    pytest.fail("Valid input should be accepted")

    def test_target_project_optional(self):
        """Test --target-project is optional."""
        import bulk_clone

        with (
            patch(
                "sys.argv",
                [
                    "bulk_clone.py",
                    "--issues",
                    "PROJ-1",
                    "--target-project",
                    "OTHER",
                    "--dry-run",
                ],
            ),
            patch.object(bulk_clone, "get_jira_client") as mock_client,
        ):
            mock_client.return_value.close = Mock()
            try:
                bulk_clone.main()
            except SystemExit as e:
                if e.code == 2:
                    pytest.fail("--target-project should be accepted")

    def test_clone_options(self):
        """Test --include-subtasks and --include-links options."""
        import bulk_clone

        with (
            patch(
                "sys.argv",
                [
                    "bulk_clone.py",
                    "--issues",
                    "PROJ-1",
                    "--include-subtasks",
                    "--include-links",
                    "--dry-run",
                ],
            ),
            patch.object(bulk_clone, "get_jira_client") as mock_client,
        ):
            mock_client.return_value.close = Mock()
            try:
                bulk_clone.main()
            except SystemExit as e:
                if e.code == 2:
                    pytest.fail("Clone options should be accepted")
