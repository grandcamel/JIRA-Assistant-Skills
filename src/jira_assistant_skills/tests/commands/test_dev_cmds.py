"""
Unit tests for dev CLI commands.

Tests cover:
- branch-name: Generate Git branch names from issues
- pr-description: Generate PR descriptions
- parse-commits: Parse JIRA issue keys from commit messages
- link-commit: Link commits to issues
- link-pr: Link pull requests to issues
- get-commits: Get commits linked to issues
"""

from copy import deepcopy
from unittest.mock import patch

import pytest

from jira_assistant_skills.cli.commands.dev_cmds import (
    DEFAULT_PREFIX,
    ISSUE_KEY_PATTERN,
    ISSUE_TYPE_PREFIXES,
    _build_commit_url,
    _create_branch_name_impl,
    _create_pr_description_impl,
    _detect_repo_type,
    _extract_acceptance_criteria,
    _get_commits_impl,
    _get_prefix_for_issue_type,
    _link_commit_impl,
    _link_pr_impl,
    _parse_commit_issues_impl,
    _parse_pr_url,
    _sanitize_for_branch,
    dev,
)

# =============================================================================
# Constants Tests
# =============================================================================


@pytest.mark.unit
class TestConstants:
    """Tests for module constants."""

    def test_issue_type_prefixes_defined(self):
        """Test that issue type prefixes are defined."""
        assert "bug" in ISSUE_TYPE_PREFIXES
        assert "story" in ISSUE_TYPE_PREFIXES
        assert ISSUE_TYPE_PREFIXES["bug"] == "bugfix"

    def test_default_prefix_is_feature(self):
        """Test that default prefix is feature."""
        assert DEFAULT_PREFIX == "feature"

    def test_issue_key_pattern_matches(self):
        """Test that issue key pattern matches expected formats."""
        assert ISSUE_KEY_PATTERN.findall("PROJ-123")
        assert ISSUE_KEY_PATTERN.findall("ABC-1")
        assert ISSUE_KEY_PATTERN.findall("TEST-99999")
        assert not ISSUE_KEY_PATTERN.findall("invalid")


# =============================================================================
# Helper Function Tests - Branch Name
# =============================================================================


@pytest.mark.unit
class TestSanitizeForBranch:
    """Tests for the _sanitize_for_branch helper function."""

    def test_sanitize_empty_string(self):
        """Test sanitizing empty string."""
        assert _sanitize_for_branch("") == ""

    def test_sanitize_converts_to_lowercase(self):
        """Test that text is converted to lowercase."""
        assert _sanitize_for_branch("Hello World") == "hello-world"

    def test_sanitize_replaces_special_chars(self):
        """Test that special characters are replaced with hyphens."""
        assert _sanitize_for_branch("Hello@World!") == "hello-world"

    def test_sanitize_removes_consecutive_hyphens(self):
        """Test that consecutive hyphens are removed."""
        assert _sanitize_for_branch("Hello---World") == "hello-world"

    def test_sanitize_removes_leading_trailing_hyphens(self):
        """Test that leading/trailing hyphens are removed."""
        assert _sanitize_for_branch("--Hello World--") == "hello-world"


@pytest.mark.unit
class TestGetPrefixForIssueType:
    """Tests for the _get_prefix_for_issue_type helper function."""

    def test_bug_returns_bugfix(self):
        """Test that bug type returns bugfix prefix."""
        assert _get_prefix_for_issue_type("bug") == "bugfix"
        assert _get_prefix_for_issue_type("Bug") == "bugfix"

    def test_story_returns_feature(self):
        """Test that story type returns feature prefix."""
        assert _get_prefix_for_issue_type("story") == "feature"

    def test_unknown_returns_default(self):
        """Test that unknown type returns default prefix."""
        assert _get_prefix_for_issue_type("unknown") == DEFAULT_PREFIX

    def test_empty_returns_default(self):
        """Test that empty type returns default prefix."""
        assert _get_prefix_for_issue_type("") == DEFAULT_PREFIX


# =============================================================================
# Helper Function Tests - PR Description
# =============================================================================


@pytest.mark.unit
class TestExtractAcceptanceCriteria:
    """Tests for the _extract_acceptance_criteria helper function."""

    def test_extract_empty_description(self):
        """Test extracting from empty description."""
        assert _extract_acceptance_criteria("") == []

    def test_extract_acceptance_criteria_section(self):
        """Test extracting AC from labeled section."""
        desc = """Some description

Acceptance Criteria:
- First item
- Second item

Other section:
"""
        result = _extract_acceptance_criteria(desc)
        assert "First item" in result
        assert "Second item" in result

    def test_extract_given_when_then(self):
        """Test extracting Given/When/Then patterns."""
        desc = """Given a user is logged in
When they click logout
Then they should be redirected"""
        result = _extract_acceptance_criteria(desc)
        assert len(result) == 3


# =============================================================================
# Helper Function Tests - Link Commit/PR
# =============================================================================


@pytest.mark.unit
class TestDetectRepoType:
    """Tests for the _detect_repo_type helper function."""

    def test_github_url(self):
        """Test detecting GitHub URL."""
        assert _detect_repo_type("https://github.com/org/repo") == "github"

    def test_gitlab_url(self):
        """Test detecting GitLab URL."""
        assert _detect_repo_type("https://gitlab.com/org/repo") == "gitlab"

    def test_bitbucket_url(self):
        """Test detecting Bitbucket URL."""
        assert _detect_repo_type("https://bitbucket.org/org/repo") == "bitbucket"

    def test_generic_url(self):
        """Test detecting generic URL."""
        assert _detect_repo_type("https://git.example.com/org/repo") == "generic"

    def test_empty_url(self):
        """Test detecting empty URL."""
        assert _detect_repo_type("") == "generic"


@pytest.mark.unit
class TestBuildCommitUrl:
    """Tests for the _build_commit_url helper function."""

    def test_github_commit_url(self):
        """Test building GitHub commit URL."""
        url = _build_commit_url("abc123", "https://github.com/org/repo")
        assert url == "https://github.com/org/repo/commit/abc123"

    def test_gitlab_commit_url(self):
        """Test building GitLab commit URL."""
        url = _build_commit_url("abc123", "https://gitlab.com/org/repo")
        assert url == "https://gitlab.com/org/repo/-/commit/abc123"

    def test_bitbucket_commit_url(self):
        """Test building Bitbucket commit URL."""
        url = _build_commit_url("abc123", "https://bitbucket.org/org/repo")
        assert url == "https://bitbucket.org/org/repo/commits/abc123"

    def test_no_repo_returns_none(self):
        """Test that no repo returns None."""
        assert _build_commit_url("abc123", None) is None


@pytest.mark.unit
class TestParsePrUrl:
    """Tests for the _parse_pr_url helper function."""

    def test_github_pr_url(self):
        """Test parsing GitHub PR URL."""
        result = _parse_pr_url("https://github.com/org/repo/pull/123")
        assert result["provider"] == "github"
        assert result["owner"] == "org"
        assert result["repo"] == "repo"
        assert result["pr_number"] == 123

    def test_gitlab_mr_url(self):
        """Test parsing GitLab MR URL."""
        result = _parse_pr_url("https://gitlab.com/org/repo/-/merge_requests/456")
        assert result["provider"] == "gitlab"
        assert result["pr_number"] == 456

    def test_bitbucket_pr_url(self):
        """Test parsing Bitbucket PR URL."""
        result = _parse_pr_url("https://bitbucket.org/org/repo/pull-requests/789")
        assert result["provider"] == "bitbucket"
        assert result["pr_number"] == 789

    def test_invalid_url_raises_error(self):
        """Test that invalid URL raises ValidationError."""
        from jira_assistant_skills_lib import ValidationError

        with pytest.raises(ValidationError, match="Unrecognized PR URL"):
            _parse_pr_url("https://invalid.com/pr/123")


# =============================================================================
# Implementation Function Tests - Branch Name
# =============================================================================


@pytest.mark.unit
class TestCreateBranchNameImpl:
    """Tests for the _create_branch_name_impl implementation function."""

    def test_create_branch_name_basic(self, mock_jira_client, sample_issue):
        """Test creating a basic branch name."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)

        with patch(
            "jira_assistant_skills.cli.commands.dev_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _create_branch_name_impl(issue_key="PROJ-123")

        assert "branch_name" in result
        assert "feature/" in result["branch_name"]
        assert "proj-123" in result["branch_name"]
        mock_jira_client.close.assert_called_once()

    def test_create_branch_name_with_prefix(self, mock_jira_client, sample_issue):
        """Test creating branch name with explicit prefix."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)

        with patch(
            "jira_assistant_skills.cli.commands.dev_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _create_branch_name_impl(issue_key="PROJ-123", prefix="bugfix")

        assert "bugfix/" in result["branch_name"]

    def test_create_branch_name_auto_prefix_bug(self, mock_jira_client, sample_issue):
        """Test auto-prefix for bug issue type."""
        issue = deepcopy(sample_issue)
        issue["fields"]["issuetype"]["name"] = "Bug"
        mock_jira_client.get_issue.return_value = issue

        with patch(
            "jira_assistant_skills.cli.commands.dev_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _create_branch_name_impl(issue_key="PROJ-123", auto_prefix=True)

        assert "bugfix/" in result["branch_name"]

    def test_create_branch_name_includes_git_command(
        self, mock_jira_client, sample_issue
    ):
        """Test that git command is included in result."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)

        with patch(
            "jira_assistant_skills.cli.commands.dev_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _create_branch_name_impl(issue_key="PROJ-123")

        assert "git_command" in result
        assert "git checkout -b" in result["git_command"]


# =============================================================================
# Implementation Function Tests - PR Description
# =============================================================================


@pytest.mark.unit
class TestCreatePrDescriptionImpl:
    """Tests for the _create_pr_description_impl implementation function."""

    def test_create_pr_description_basic(self, mock_jira_client, sample_issue):
        """Test creating a basic PR description."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)

        with patch(
            "jira_assistant_skills.cli.commands.dev_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _create_pr_description_impl(issue_key="PROJ-123")

        assert "markdown" in result
        assert "## Summary" in result["markdown"]
        assert "## JIRA Issue" in result["markdown"]
        assert "PROJ-123" in result["markdown"]

    def test_create_pr_description_with_checklist(self, mock_jira_client, sample_issue):
        """Test creating PR description with testing checklist."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)

        with patch(
            "jira_assistant_skills.cli.commands.dev_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _create_pr_description_impl(
                issue_key="PROJ-123",
                include_checklist=True,
            )

        assert "## Testing Checklist" in result["markdown"]
        assert "Unit tests" in result["markdown"]

    def test_create_pr_description_with_labels(self, mock_jira_client, sample_issue):
        """Test creating PR description with labels."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)

        with patch(
            "jira_assistant_skills.cli.commands.dev_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _create_pr_description_impl(
                issue_key="PROJ-123",
                include_labels=True,
            )

        assert "## Labels" in result["markdown"]


# =============================================================================
# Implementation Function Tests - Parse Commits
# =============================================================================


@pytest.mark.unit
class TestParseCommitIssuesImpl:
    """Tests for the _parse_commit_issues_impl implementation function."""

    def test_parse_single_issue(self):
        """Test parsing single issue key."""
        result = _parse_commit_issues_impl(message="PROJ-123: Fix bug")
        assert result["issue_keys"] == ["PROJ-123"]
        assert result["count"] == 1

    def test_parse_multiple_issues(self):
        """Test parsing multiple issue keys."""
        result = _parse_commit_issues_impl(message="Fix PROJ-123 and PROJ-456")
        assert "PROJ-123" in result["issue_keys"]
        assert "PROJ-456" in result["issue_keys"]
        assert result["count"] == 2

    def test_parse_with_project_filter(self):
        """Test parsing with project filter."""
        result = _parse_commit_issues_impl(
            message="Fix PROJ-123 and OTHER-456",
            project_filter="PROJ",
        )
        assert result["issue_keys"] == ["PROJ-123"]
        assert result["count"] == 1

    def test_parse_empty_message(self):
        """Test parsing empty message."""
        result = _parse_commit_issues_impl(message=None)
        assert result["issue_keys"] == []
        assert result["count"] == 0

    def test_parse_no_issues(self):
        """Test parsing message with no issues."""
        result = _parse_commit_issues_impl(message="Fixed a bug")
        assert result["issue_keys"] == []
        assert result["count"] == 0


# =============================================================================
# Implementation Function Tests - Link Commit
# =============================================================================


@pytest.mark.unit
class TestLinkCommitImpl:
    """Tests for the _link_commit_impl implementation function."""

    def test_link_commit_basic(self, mock_jira_client):
        """Test linking a basic commit."""
        mock_jira_client.post.return_value = {"id": "10001"}

        with patch(
            "jira_assistant_skills.cli.commands.dev_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _link_commit_impl(
                issue_key="PROJ-123",
                commit="abc123def",
            )

        assert result["success"] is True
        assert result["issue_key"] == "PROJ-123"
        assert result["commit_sha"] == "abc123def"
        mock_jira_client.post.assert_called_once()

    def test_link_commit_with_repo(self, mock_jira_client):
        """Test linking commit with repository URL."""
        mock_jira_client.post.return_value = {"id": "10001"}

        with patch(
            "jira_assistant_skills.cli.commands.dev_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _link_commit_impl(
                issue_key="PROJ-123",
                commit="abc123def",
                repo="https://github.com/org/repo",
            )

        assert result["success"] is True


# =============================================================================
# Implementation Function Tests - Link PR
# =============================================================================


@pytest.mark.unit
class TestLinkPrImpl:
    """Tests for the _link_pr_impl implementation function."""

    def test_link_pr_github(self, mock_jira_client):
        """Test linking a GitHub PR."""
        mock_jira_client.post.return_value = {"id": "10001"}

        with patch(
            "jira_assistant_skills.cli.commands.dev_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _link_pr_impl(
                issue_key="PROJ-123",
                pr_url="https://github.com/org/repo/pull/456",
            )

        assert result["success"] is True
        assert result["pr_number"] == 456
        assert result["provider"] == "github"

    def test_link_pr_gitlab(self, mock_jira_client):
        """Test linking a GitLab MR."""
        mock_jira_client.post.return_value = {"id": "10001"}

        with patch(
            "jira_assistant_skills.cli.commands.dev_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _link_pr_impl(
                issue_key="PROJ-123",
                pr_url="https://gitlab.com/org/repo/-/merge_requests/789",
            )

        assert result["success"] is True
        assert result["provider"] == "gitlab"


# =============================================================================
# Implementation Function Tests - Get Commits
# =============================================================================


@pytest.mark.unit
class TestGetCommitsImpl:
    """Tests for the _get_commits_impl implementation function."""

    def test_get_commits_basic(self, mock_jira_client, sample_issue):
        """Test getting commits linked to an issue."""
        mock_jira_client.get_issue.return_value = {"id": "10001"}
        mock_jira_client.get.return_value = {
            "detail": [
                {
                    "repositories": [
                        {
                            "name": "org/repo",
                            "commits": [
                                {
                                    "id": "abc123def456",
                                    "displayId": "abc123d",
                                    "url": "https://github.com/org/repo/commit/abc123def456",
                                    "message": "Fix bug",
                                    "author": {
                                        "name": "John Doe",
                                        "email": "john@example.com",
                                    },
                                }
                            ],
                        }
                    ]
                }
            ]
        }

        with patch(
            "jira_assistant_skills.cli.commands.dev_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            commits = _get_commits_impl(issue_key="PROJ-123")

        assert len(commits) == 1
        assert commits[0]["display_id"] == "abc123d"
        assert commits[0]["repository"] == "org/repo"

    def test_get_commits_detailed(self, mock_jira_client):
        """Test getting detailed commits."""
        mock_jira_client.get_issue.return_value = {"id": "10001"}
        mock_jira_client.get.return_value = {
            "detail": [
                {
                    "repositories": [
                        {
                            "name": "org/repo",
                            "commits": [
                                {
                                    "id": "abc123",
                                    "message": "Fix bug",
                                    "author": {
                                        "name": "John Doe",
                                        "email": "john@example.com",
                                    },
                                    "authorTimestamp": "2025-01-15T10:30:00Z",
                                }
                            ],
                        }
                    ]
                }
            ]
        }

        with patch(
            "jira_assistant_skills.cli.commands.dev_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            commits = _get_commits_impl(issue_key="PROJ-123", detailed=True)

        assert commits[0]["message"] == "Fix bug"
        assert commits[0]["author"] == "John Doe"

    def test_get_commits_no_results(self, mock_jira_client):
        """Test getting commits when none linked."""
        mock_jira_client.get_issue.return_value = {"id": "10001"}
        mock_jira_client.get.return_value = {"detail": []}

        with patch(
            "jira_assistant_skills.cli.commands.dev_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            commits = _get_commits_impl(issue_key="PROJ-123")

        assert commits == []


# =============================================================================
# CLI Command Tests
# =============================================================================


@pytest.mark.unit
class TestBranchNameCommand:
    """Tests for the branch-name CLI command."""

    def test_branch_name_cli(self, cli_runner, mock_jira_client, sample_issue):
        """Test CLI branch-name command."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)

        with patch(
            "jira_assistant_skills.cli.commands.dev_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = cli_runner.invoke(dev, ["branch-name", "PROJ-123"])

        assert result.exit_code == 0
        assert "feature/" in result.output

    def test_branch_name_cli_json(self, cli_runner, mock_jira_client, sample_issue):
        """Test CLI branch-name with JSON output."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)

        with patch(
            "jira_assistant_skills.cli.commands.dev_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = cli_runner.invoke(dev, ["branch-name", "PROJ-123", "-o", "json"])

        assert result.exit_code == 0
        assert "{" in result.output

    def test_branch_name_cli_git_output(
        self, cli_runner, mock_jira_client, sample_issue
    ):
        """Test CLI branch-name with git output format."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)

        with patch(
            "jira_assistant_skills.cli.commands.dev_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = cli_runner.invoke(dev, ["branch-name", "PROJ-123", "-o", "git"])

        assert result.exit_code == 0
        assert "git checkout -b" in result.output


@pytest.mark.unit
class TestPrDescriptionCommand:
    """Tests for the pr-description CLI command."""

    def test_pr_description_cli(self, cli_runner, mock_jira_client, sample_issue):
        """Test CLI pr-description command."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)

        with patch(
            "jira_assistant_skills.cli.commands.dev_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = cli_runner.invoke(dev, ["pr-description", "PROJ-123"])

        assert result.exit_code == 0
        assert "## Summary" in result.output


@pytest.mark.unit
class TestParseCommitsCommand:
    """Tests for the parse-commits CLI command."""

    def test_parse_commits_cli(self, cli_runner):
        """Test CLI parse-commits command."""
        result = cli_runner.invoke(dev, ["parse-commits", "PROJ-123: Fix bug"])

        assert result.exit_code == 0
        assert "PROJ-123" in result.output

    def test_parse_commits_cli_json(self, cli_runner):
        """Test CLI parse-commits with JSON output."""
        result = cli_runner.invoke(
            dev, ["parse-commits", "PROJ-123: Fix bug", "-o", "json"]
        )

        assert result.exit_code == 0
        assert "{" in result.output

    def test_parse_commits_cli_no_message_error(self, cli_runner):
        """Test CLI parse-commits fails without message."""
        result = cli_runner.invoke(dev, ["parse-commits"])

        assert result.exit_code != 0


@pytest.mark.unit
class TestLinkCommitCommand:
    """Tests for the link-commit CLI command."""

    def test_link_commit_cli(self, cli_runner, mock_jira_client):
        """Test CLI link-commit command."""
        mock_jira_client.post.return_value = {"id": "10001"}

        with patch(
            "jira_assistant_skills.cli.commands.dev_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = cli_runner.invoke(
                dev, ["link-commit", "PROJ-123", "-c", "abc123def"]
            )

        assert result.exit_code == 0
        assert "Linked commit" in result.output


@pytest.mark.unit
class TestLinkPrCommand:
    """Tests for the link-pr CLI command."""

    def test_link_pr_cli(self, cli_runner, mock_jira_client):
        """Test CLI link-pr command."""
        mock_jira_client.post.return_value = {"id": "10001"}

        with patch(
            "jira_assistant_skills.cli.commands.dev_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = cli_runner.invoke(
                dev,
                ["link-pr", "PROJ-123", "-p", "https://github.com/org/repo/pull/456"],
            )

        assert result.exit_code == 0
        assert "Linked PR" in result.output


@pytest.mark.unit
class TestGetCommitsCommand:
    """Tests for the get-commits CLI command."""

    def test_get_commits_cli(self, cli_runner, mock_jira_client):
        """Test CLI get-commits command."""
        mock_jira_client.get_issue.return_value = {"id": "10001"}
        mock_jira_client.get.return_value = {"detail": []}

        with patch(
            "jira_assistant_skills.cli.commands.dev_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = cli_runner.invoke(dev, ["get-commits", "PROJ-123"])

        assert result.exit_code == 0
        assert "No commits" in result.output

    def test_get_commits_cli_with_commits(self, cli_runner, mock_jira_client):
        """Test CLI get-commits with commits found."""
        mock_jira_client.get_issue.return_value = {"id": "10001"}
        mock_jira_client.get.return_value = {
            "detail": [
                {
                    "repositories": [
                        {
                            "name": "org/repo",
                            "commits": [
                                {"id": "abc123", "displayId": "abc123d", "url": ""}
                            ],
                        }
                    ]
                }
            ]
        }

        with patch(
            "jira_assistant_skills.cli.commands.dev_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = cli_runner.invoke(dev, ["get-commits", "PROJ-123"])

        assert result.exit_code == 0
        assert "Found 1 commit" in result.output
