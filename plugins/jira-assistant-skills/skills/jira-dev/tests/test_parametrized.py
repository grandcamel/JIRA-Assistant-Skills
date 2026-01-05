"""
Parametrized Tests for jira-dev skill.

Uses pytest.mark.parametrize for DRYer test code, consolidating
related test cases into single parametrized test functions.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add scripts path
scripts_path = str(Path(__file__).parent.parent / "scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


# =============================================================================
# Parametrized tests for create_branch_name.py
# =============================================================================


@pytest.mark.dev
@pytest.mark.unit
class TestSanitizeForBranchParametrized:
    """Parametrized tests for branch name sanitization."""

    @pytest.mark.parametrize(
        "input_text,expected",
        [
            # Basic transformations
            ("Fix bug: login (v2)", "fix-bug-login-v2"),
            ("Add feature!", "add-feature"),
            ("Test@user#auth", "test-user-auth"),
            # Apostrophe handling
            ("What's new?", "what-s-new"),
            ("User's profile", "user-s-profile"),
            # Multiple spaces
            ("Multiple   spaces", "multiple-spaces"),
            ("  leading  trailing  ", "leading-trailing"),
            # Leading/trailing special chars
            ("--leading-dashes--", "leading-dashes"),
            ("...dots...", "dots"),
            # Case conversion
            ("MixedCase Words", "mixedcase-words"),
            ("ALLCAPS", "allcaps"),
            # Numbers preserved
            ("Version 2.0", "version-2-0"),
            ("Bug #123", "bug-123"),
            # Empty and whitespace
            ("", ""),
            ("   ", ""),
        ],
    )
    def test_sanitize_for_branch(self, input_text, expected):
        """Test branch name sanitization with various inputs."""
        from create_branch_name import sanitize_for_branch

        assert sanitize_for_branch(input_text) == expected


@pytest.mark.dev
@pytest.mark.unit
class TestIssueTypePrefixParametrized:
    """Parametrized tests for issue type to prefix mapping."""

    @pytest.mark.parametrize(
        "issue_type,expected_prefix",
        [
            # Bug types -> bugfix
            ("Bug", "bugfix"),
            ("bug", "bugfix"),
            ("Defect", "bugfix"),
            ("defect", "bugfix"),
            # Hotfix
            ("Hotfix", "hotfix"),
            ("hotfix", "hotfix"),
            # Story/Feature types -> feature
            ("Story", "feature"),
            ("story", "feature"),
            ("Feature", "feature"),
            ("New Feature", "feature"),
            ("Improvement", "feature"),
            ("Enhancement", "feature"),
            # Task types -> task
            ("Task", "task"),
            ("Sub-task", "task"),
            ("Subtask", "task"),
            # Epic
            ("Epic", "epic"),
            # Spike/Research
            ("Spike", "spike"),
            ("Research", "spike"),
            # Chore/Maintenance
            ("Chore", "chore"),
            ("Maintenance", "chore"),
            # Documentation
            ("Documentation", "docs"),
            ("Doc", "docs"),
            # Unknown -> default
            ("Unknown", "feature"),
            ("Custom Type", "feature"),
            ("", "feature"),
        ],
    )
    def test_issue_type_to_prefix(self, issue_type, expected_prefix):
        """Test issue type to prefix mapping."""
        from create_branch_name import get_prefix_for_issue_type

        assert get_prefix_for_issue_type(issue_type) == expected_prefix


# =============================================================================
# Parametrized tests for parse_commit_issues.py
# =============================================================================


@pytest.mark.dev
@pytest.mark.unit
class TestParseIssueKeysParametrized:
    """Parametrized tests for commit message parsing."""

    @pytest.mark.parametrize(
        "message,expected_keys",
        [
            # Single issue key formats
            ("PROJ-123: Fix bug", ["PROJ-123"]),
            ("[PROJ-456] Fix issue", ["PROJ-456"]),
            ("Fix something (PROJ-789)", ["PROJ-789"]),
            ("Add tests PROJ-101", ["PROJ-101"]),
            # Prefix formats
            ("Fixes PROJ-123", ["PROJ-123"]),
            ("fixes PROJ-123", ["PROJ-123"]),
            ("Closes PROJ-456", ["PROJ-456"]),
            ("closes PROJ-456", ["PROJ-456"]),
            ("Refs PROJ-789", ["PROJ-789"]),
            ("refs PROJ-789", ["PROJ-789"]),
            ("Resolves PROJ-101", ["PROJ-101"]),
            ("resolves PROJ-101", ["PROJ-101"]),
            # Conventional commit format
            ("feat(PROJ-123): add feature", ["PROJ-123"]),
            ("fix(PROJ-456): fix bug", ["PROJ-456"]),
            # Multiple issue keys
            ("Fix PROJ-123 and PROJ-456", ["PROJ-123", "PROJ-456"]),
            ("PROJ-1, PROJ-2, PROJ-3", ["PROJ-1", "PROJ-2", "PROJ-3"]),
            # Case insensitive matching (returns uppercase)
            ("proj-123: fix bug", ["PROJ-123"]),
            ("Proj-456: update", ["PROJ-456"]),
            # No issue keys
            ("Update README with examples", []),
            ("Fix typo in documentation", []),
            # Deduplication
            ("PROJ-123: Fix bug, related to PROJ-123", ["PROJ-123"]),
        ],
    )
    def test_parse_issue_keys(self, message, expected_keys):
        """Test parsing issue keys from commit messages."""
        from parse_commit_issues import parse_issue_keys

        result = parse_issue_keys(message)
        assert sorted(result) == sorted(expected_keys)


# =============================================================================
# Parametrized tests for link_commit.py
# =============================================================================


@pytest.mark.dev
@pytest.mark.unit
class TestBuildCommitUrlParametrized:
    """Parametrized tests for commit URL building."""

    @pytest.mark.parametrize(
        "repo_url,commit_sha,expected_url",
        [
            # GitHub
            (
                "https://github.com/org/repo",
                "abc123def456",
                "https://github.com/org/repo/commit/abc123def456",
            ),
            (
                "https://github.com/myorg/myrepo",
                "1234567890ab",
                "https://github.com/myorg/myrepo/commit/1234567890ab",
            ),
            # GitLab
            (
                "https://gitlab.com/org/repo",
                "abc123def456",
                "https://gitlab.com/org/repo/-/commit/abc123def456",
            ),
            (
                "https://gitlab.com/group/subgroup/repo",
                "fedcba987654",
                "https://gitlab.com/group/subgroup/repo/-/commit/fedcba987654",
            ),
            # Bitbucket
            (
                "https://bitbucket.org/org/repo",
                "abc123def456",
                "https://bitbucket.org/org/repo/commits/abc123def456",
            ),
            (
                "https://bitbucket.org/myteam/myproject",
                "deadbeef1234",
                "https://bitbucket.org/myteam/myproject/commits/deadbeef1234",
            ),
        ],
    )
    def test_build_commit_url(self, repo_url, commit_sha, expected_url):
        """Test building commit URLs for different providers."""
        from link_commit import build_commit_url

        result = build_commit_url(commit_sha, repo_url)
        assert result == expected_url


# =============================================================================
# Parametrized tests for link_pr.py
# =============================================================================


@pytest.mark.dev
@pytest.mark.unit
class TestParsePRUrlParametrized:
    """Parametrized tests for PR URL parsing."""

    @pytest.mark.parametrize(
        "pr_url,expected_provider,expected_owner,expected_repo,expected_number",
        [
            # GitHub PRs
            ("https://github.com/org/repo/pull/123", "github", "org", "repo", 123),
            (
                "https://github.com/myorg/my-repo/pull/456",
                "github",
                "myorg",
                "my-repo",
                456,
            ),
            (
                "https://github.com/company/project-name/pull/1",
                "github",
                "company",
                "project-name",
                1,
            ),
            # GitLab MRs
            (
                "https://gitlab.com/org/repo/-/merge_requests/789",
                "gitlab",
                "org",
                "repo",
                789,
            ),
            (
                "https://gitlab.com/group/project/-/merge_requests/100",
                "gitlab",
                "group",
                "project",
                100,
            ),
            # Bitbucket PRs
            (
                "https://bitbucket.org/org/repo/pull-requests/101",
                "bitbucket",
                "org",
                "repo",
                101,
            ),
            (
                "https://bitbucket.org/myteam/myrepo/pull-requests/999",
                "bitbucket",
                "myteam",
                "myrepo",
                999,
            ),
        ],
    )
    def test_parse_pr_url(
        self, pr_url, expected_provider, expected_owner, expected_repo, expected_number
    ):
        """Test parsing PR URLs from different providers."""
        from link_pr import parse_pr_url

        result = parse_pr_url(pr_url)
        assert result["provider"] == expected_provider
        assert result["owner"] == expected_owner
        assert result["repo"] == expected_repo
        assert result["pr_number"] == expected_number


@pytest.mark.dev
@pytest.mark.unit
class TestPRStatusParametrized:
    """Parametrized tests for PR status handling."""

    @pytest.mark.parametrize(
        "status,expected_in_comment",
        [
            ("open", "open"),
            ("merged", "merged"),
            ("closed", "closed"),
        ],
    )
    def test_pr_status_in_comment(self, status, expected_in_comment):
        """Test PR status appears in generated comment."""
        from link_pr import build_pr_comment

        comment = build_pr_comment(
            pr_url="https://github.com/org/repo/pull/123",
            pr_number=123,
            status=status,
            title="Fix login bug",
        )

        assert expected_in_comment in comment.lower()


# =============================================================================
# Parametrized tests for create_pr_description.py
# =============================================================================


@pytest.mark.dev
@pytest.mark.unit
class TestPRDescriptionFormatParametrized:
    """Parametrized tests for PR description formatting."""

    @pytest.mark.parametrize(
        "include_checklist,include_labels,expected_sections",
        [
            (True, True, ["checklist", "labels"]),
            (True, False, ["checklist"]),
            (False, True, ["labels"]),
            (False, False, []),
        ],
    )
    def test_pr_description_sections(
        self,
        mock_jira_client,
        sample_issue,
        include_checklist,
        include_labels,
        expected_sections,
    ):
        """Test PR description includes correct sections based on flags."""
        from create_pr_description import create_pr_description

        mock_jira_client.get_issue.return_value = sample_issue

        with patch(
            "create_pr_description.get_jira_client", return_value=mock_jira_client
        ):
            result = create_pr_description(
                "PROJ-123",
                include_checklist=include_checklist,
                include_labels=include_labels,
            )

        # Result is now a dict with 'markdown' key
        markdown = result["markdown"]
        result_lower = markdown.lower()

        for section in expected_sections:
            if section == "checklist":
                assert "- [ ]" in markdown, "Expected checklist markers"
            elif section == "labels":
                # Labels from sample_issue
                assert "mobile" in result_lower or "ui" in result_lower


# =============================================================================
# Parametrized error handling tests
# =============================================================================


@pytest.mark.dev
@pytest.mark.unit
class TestErrorHandlingParametrized:
    """Parametrized tests for error handling across scripts."""

    @pytest.mark.parametrize(
        "error_type,error_class_name",
        [
            ("authentication", "AuthenticationError"),
            ("permission", "PermissionError"),
            ("not_found", "NotFoundError"),
            ("rate_limit", "RateLimitError"),
            ("server", "ServerError"),
        ],
    )
    def test_create_branch_name_errors(
        self, mock_jira_client, error_type, error_class_name
    ):
        """Test error handling in create_branch_name."""
        import error_handler
        from create_branch_name import create_branch_name

        # Get the actual error class
        error_class = getattr(error_handler, error_class_name)

        # Create appropriate error instance
        if error_class_name == "NotFoundError":
            error = error_class("Issue", "PROJ-999")
        elif error_class_name == "RateLimitError":
            error = error_class(retry_after=60)
        else:
            error = error_class("Test error")

        mock_jira_client.get_issue.side_effect = error

        with patch("create_branch_name.get_jira_client", return_value=mock_jira_client):
            with pytest.raises(error_class):
                create_branch_name("PROJ-123")
