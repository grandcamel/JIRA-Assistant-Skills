from unittest.mock import patch

import pytest
from click.testing import CliRunner

# Import the main cli group from your application
from jira_assistant_skills.cli.main import cli
from jira_assistant_skills.utils import SKILLS_ROOT_DIR


# Define common fixture for CliRunner
@pytest.fixture
def runner():
    return CliRunner()


# Helper to construct expected script path for mocking
def get_script_path(skill_name, script_name):
    return (SKILLS_ROOT_DIR / skill_name / "scripts" / f"{script_name}.py").resolve()


# Common global options context for tests
DEFAULT_CLI_OBJ = {
    "PROFILE": None,
    "OUTPUT": "text",
    "VERBOSE": False,
    "QUIET": False,
}


# --- Tests for `jira issue` commands ---
class TestIssueCommands:
    """Test issue command group."""

    def test_issue_help(self, runner):
        """Test issue group shows help."""
        result = runner.invoke(cli, ["issue", "--help"])
        assert result.exit_code == 0
        assert "get" in result.output
        assert "create" in result.output
        assert "update" in result.output
        assert "delete" in result.output

    def test_issue_get_requires_key(self, runner):
        """Test issue get requires issue key argument."""
        result = runner.invoke(cli, ["issue", "get"])
        assert result.exit_code != 0
        assert "Missing argument" in result.output

    def test_issue_get_help(self, runner):
        """Test issue get shows help with options."""
        result = runner.invoke(cli, ["issue", "get", "--help"])
        assert result.exit_code == 0
        assert "--fields" in result.output
        assert "--detailed" in result.output
        assert "--show-links" in result.output
        assert "--show-time" in result.output

    def test_issue_create_requires_options(self, runner):
        """Test issue create requires project, type, and summary."""
        result = runner.invoke(cli, ["issue", "create"])
        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

    def test_issue_create_help(self, runner):
        """Test issue create shows help with options."""
        result = runner.invoke(cli, ["issue", "create", "--help"])
        assert result.exit_code == 0
        assert "--project" in result.output
        assert "--type" in result.output
        assert "--summary" in result.output

    def test_issue_update_requires_key(self, runner):
        """Test issue update requires issue key argument."""
        result = runner.invoke(cli, ["issue", "update"])
        assert result.exit_code != 0
        assert "Missing argument" in result.output

    def test_issue_delete_requires_key(self, runner):
        """Test issue delete requires issue key argument."""
        result = runner.invoke(cli, ["issue", "delete"])
        assert result.exit_code != 0
        assert "Missing argument" in result.output


# --- Tests for `jira search` commands ---
class TestSearchCommands:
    """Test search command group."""

    def test_search_help(self, runner):
        """Test search group shows help."""
        result = runner.invoke(cli, ["search", "--help"])
        assert result.exit_code == 0
        assert "query" in result.output
        assert "export" in result.output
        assert "filter" in result.output

    def test_search_query(self, runner):
        """Test search query command."""
        with patch(
            "jira_assistant_skills.cli.commands.search_cmds.run_skill_script_subprocess"
        ) as mock:
            runner.invoke(
                cli, ["search", "query", "project = PROJ"], obj=DEFAULT_CLI_OBJ.copy()
            )
            mock.assert_called_once()

    def test_search_filter_list(self, runner):
        """Test search filter list command."""
        result = runner.invoke(cli, ["search", "filter", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output
        assert "create" in result.output


# --- Tests for `jira lifecycle` commands ---
class TestLifecycleCommands:
    """Test lifecycle command group."""

    def test_lifecycle_help(self, runner):
        """Test lifecycle group shows help."""
        result = runner.invoke(cli, ["lifecycle", "--help"])
        assert result.exit_code == 0
        assert "transition" in result.output
        assert "assign" in result.output
        assert "version" in result.output
        assert "component" in result.output

    def test_lifecycle_transition(self, runner):
        """Test lifecycle transition command."""
        with patch(
            "jira_assistant_skills.cli.commands.lifecycle_cmds.run_skill_script_subprocess"
        ) as mock:
            runner.invoke(
                cli,
                ["lifecycle", "transition", "PROJ-123", "Done"],
                obj=DEFAULT_CLI_OBJ.copy(),
            )
            mock.assert_called_once()

    def test_lifecycle_version_subgroup(self, runner):
        """Test lifecycle version subgroup."""
        result = runner.invoke(cli, ["lifecycle", "version", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output
        assert "create" in result.output
        assert "release" in result.output


# --- Tests for `jira bulk` commands ---
class TestBulkCommands:
    """Test bulk command group."""

    def test_bulk_help(self, runner):
        """Test bulk group shows help."""
        result = runner.invoke(cli, ["bulk", "--help"])
        assert result.exit_code == 0
        assert "transition" in result.output
        assert "assign" in result.output
        assert "clone" in result.output

    def test_bulk_transition(self, runner):
        """Test bulk transition command."""
        with patch(
            "jira_assistant_skills.cli.commands.bulk_cmds.run_skill_script_subprocess"
        ) as mock:
            runner.invoke(
                cli,
                ["bulk", "transition", "project = PROJ", "Done", "--dry-run"],
                obj=DEFAULT_CLI_OBJ.copy(),
            )
            mock.assert_called_once()
            call_args = mock.call_args[0][1]
            assert "--dry-run" in call_args


# --- Tests for `jira agile` commands ---
class TestAgileCommands:
    """Test agile command group."""

    def test_agile_help(self, runner):
        """Test agile group shows help."""
        result = runner.invoke(cli, ["agile", "--help"])
        assert result.exit_code == 0
        assert "epic" in result.output
        assert "sprint" in result.output
        assert "backlog" in result.output

    def test_agile_epic_subgroup(self, runner):
        """Test agile epic subgroup."""
        result = runner.invoke(cli, ["agile", "epic", "--help"])
        assert result.exit_code == 0
        assert "create" in result.output
        assert "get" in result.output

    def test_agile_sprint_subgroup(self, runner):
        """Test agile sprint subgroup."""
        result = runner.invoke(cli, ["agile", "sprint", "--help"])
        assert result.exit_code == 0
        assert "create" in result.output
        assert "manage" in result.output


# --- Tests for `jira collaborate` commands ---
class TestCollaborateCommands:
    """Test collaborate command group."""

    def test_collaborate_help(self, runner):
        """Test collaborate group shows help."""
        result = runner.invoke(cli, ["collaborate", "--help"])
        assert result.exit_code == 0
        assert "comment" in result.output
        assert "attachment" in result.output
        assert "watchers" in result.output

    def test_collaborate_comment_subgroup(self, runner):
        """Test collaborate comment subgroup."""
        result = runner.invoke(cli, ["collaborate", "comment", "--help"])
        assert result.exit_code == 0
        assert "add" in result.output
        assert "list" in result.output


# --- Tests for `jira time` commands ---
class TestTimeCommands:
    """Test time command group."""

    def test_time_help(self, runner):
        """Test time group shows help."""
        result = runner.invoke(cli, ["time", "--help"])
        assert result.exit_code == 0
        assert "log" in result.output
        assert "worklogs" in result.output
        assert "report" in result.output

    def test_time_log(self, runner):
        """Test time log command."""
        with patch(
            "jira_assistant_skills.cli.commands.time_cmds.run_skill_script_subprocess"
        ) as mock:
            runner.invoke(
                cli, ["time", "log", "PROJ-123", "2h"], obj=DEFAULT_CLI_OBJ.copy()
            )
            mock.assert_called_once()


# --- Tests for `jira relationships` commands ---
class TestRelationshipsCommands:
    """Test relationships command group."""

    def test_relationships_help(self, runner):
        """Test relationships group shows help."""
        result = runner.invoke(cli, ["relationships", "--help"])
        assert result.exit_code == 0
        assert "link" in result.output
        assert "unlink" in result.output
        assert "get-blockers" in result.output

    def test_relationships_link(self, runner):
        """Test relationships link command."""
        with patch(
            "jira_assistant_skills.cli.commands.relationships_cmds.run_skill_script_subprocess"
        ) as mock:
            runner.invoke(
                cli,
                ["relationships", "link", "PROJ-123", "PROJ-456"],
                obj=DEFAULT_CLI_OBJ.copy(),
            )
            mock.assert_called_once()


# --- Tests for `jira dev` commands ---
class TestDevCommands:
    """Test dev command group."""

    def test_dev_help(self, runner):
        """Test dev group shows help."""
        result = runner.invoke(cli, ["dev", "--help"])
        assert result.exit_code == 0
        assert "branch-name" in result.output
        assert "pr-description" in result.output

    def test_dev_branch_name(self, runner):
        """Test dev branch-name command."""
        with patch(
            "jira_assistant_skills.cli.commands.dev_cmds.run_skill_script_subprocess"
        ) as mock:
            runner.invoke(
                cli, ["dev", "branch-name", "PROJ-123"], obj=DEFAULT_CLI_OBJ.copy()
            )
            mock.assert_called_once()


# --- Tests for `jira fields` commands ---
class TestFieldsCommands:
    """Test fields command group."""

    def test_fields_help(self, runner):
        """Test fields group shows help."""
        result = runner.invoke(cli, ["fields", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output
        assert "create" in result.output

    def test_fields_list(self, runner):
        """Test fields list command."""
        with patch(
            "jira_assistant_skills.cli.commands.fields_cmds.run_skill_script_subprocess"
        ) as mock:
            runner.invoke(cli, ["fields", "list"], obj=DEFAULT_CLI_OBJ.copy())
            mock.assert_called_once()


# --- Tests for `jira ops` commands ---
class TestOpsCommands:
    """Test ops command group."""

    def test_ops_help(self, runner):
        """Test ops group shows help."""
        result = runner.invoke(cli, ["ops", "--help"])
        assert result.exit_code == 0
        assert "cache-status" in result.output
        assert "cache-clear" in result.output
        assert "cache-warm" in result.output

    def test_ops_cache_status(self, runner):
        """Test ops cache-status command."""
        with patch(
            "jira_assistant_skills.cli.commands.ops_cmds.run_skill_script_subprocess"
        ) as mock:
            runner.invoke(cli, ["ops", "cache-status"], obj=DEFAULT_CLI_OBJ.copy())
            mock.assert_called_once()


# --- Tests for `jira jsm` commands ---
class TestJSMCommands:
    """Test JSM command group."""

    def test_jsm_help(self, runner):
        """Test jsm group shows help."""
        result = runner.invoke(cli, ["jsm", "--help"])
        assert result.exit_code == 0
        assert "service-desk" in result.output
        assert "request" in result.output
        assert "customer" in result.output
        assert "sla" in result.output

    def test_jsm_service_desk_subgroup(self, runner):
        """Test jsm service-desk subgroup."""
        result = runner.invoke(cli, ["jsm", "service-desk", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output
        assert "get" in result.output

    def test_jsm_request_subgroup(self, runner):
        """Test jsm request subgroup."""
        result = runner.invoke(cli, ["jsm", "request", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output
        assert "create" in result.output
        assert "transition" in result.output

    def test_jsm_approval_subgroup(self, runner):
        """Test jsm approval subgroup."""
        result = runner.invoke(cli, ["jsm", "approval", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output
        assert "approve" in result.output
        assert "decline" in result.output

    def test_jsm_service_desk_list(self, runner):
        """Test jsm service-desk list command."""
        with patch(
            "jira_assistant_skills.cli.commands.jsm_cmds.run_skill_script_subprocess"
        ) as mock:
            runner.invoke(
                cli, ["jsm", "service-desk", "list"], obj=DEFAULT_CLI_OBJ.copy()
            )
            mock.assert_called_once()


# --- Tests for global options ---
class TestGlobalOptions:
    """Test global CLI options."""

    def test_profile_option(self, runner):
        """Test --profile option is recognized."""
        result = runner.invoke(cli, ["--profile", "development", "--help"])
        assert result.exit_code == 0

    def test_output_option(self, runner):
        """Test --output option is recognized."""
        result = runner.invoke(cli, ["--output", "json", "--help"])
        assert result.exit_code == 0

    def test_verbose_option(self, runner):
        """Test --verbose option is recognized."""
        result = runner.invoke(cli, ["--verbose", "--help"])
        assert result.exit_code == 0

    def test_quiet_option(self, runner):
        """Test --quiet option is recognized."""
        result = runner.invoke(cli, ["--quiet", "--help"])
        assert result.exit_code == 0

    def test_version_option(self, runner):
        """Test --version option is recognized."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "1.0.0" in result.output
