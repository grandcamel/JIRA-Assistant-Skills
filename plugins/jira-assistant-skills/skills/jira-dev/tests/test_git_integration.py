"""
Tests for Git Integration (Phase 1) - jira-dev skill.

TDD tests for:
- create_branch_name.py
- parse_commit_issues.py
- link_commit.py
- get_issue_commits.py
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch
import json

# Add scripts path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


# =============================================================================
# Tests for create_branch_name.py
# =============================================================================

@pytest.mark.dev
@pytest.mark.unit
class TestCreateBranchName:
    """Tests for create_branch_name functionality."""

    def test_create_branch_name_basic(self, mock_jira_client, sample_issue):
        """Test creating branch name from issue - basic case."""
        from create_branch_name import create_branch_name, sanitize_for_branch

        mock_jira_client.get_issue.return_value = sample_issue

        with patch('create_branch_name.get_jira_client', return_value=mock_jira_client):
            result = create_branch_name('PROJ-123')

        # Result is now a dict with 'branch_name' key
        branch_name = result['branch_name']
        # Should produce: feature/proj-123-fix-login-button-not-responding
        assert branch_name.startswith('feature/')
        assert 'proj-123' in branch_name  # Lowercase
        assert 'fix-login' in branch_name
        assert branch_name == branch_name.lower()  # Should be lowercase
        mock_jira_client.close.assert_called_once()

    def test_create_branch_name_with_custom_prefix(self, mock_jira_client, sample_issue):
        """Test creating branch name with custom prefix (bugfix, hotfix)."""
        from create_branch_name import create_branch_name

        mock_jira_client.get_issue.return_value = sample_issue

        with patch('create_branch_name.get_jira_client', return_value=mock_jira_client):
            result = create_branch_name('PROJ-123', prefix='bugfix')

        branch_name = result['branch_name']
        assert branch_name.startswith('bugfix/')
        assert 'proj-123' in branch_name  # Already lowercase

    def test_create_branch_name_sanitizes_special_chars(self):
        """Test removing special characters from summary."""
        from create_branch_name import sanitize_for_branch

        # Test various special characters
        assert sanitize_for_branch("Fix bug: login (v2)") == "fix-bug-login-v2"
        assert sanitize_for_branch("Add feature!") == "add-feature"
        assert sanitize_for_branch("Test@user#auth") == "test-user-auth"
        # Apostrophe becomes hyphen, then consecutive hyphens are collapsed
        assert sanitize_for_branch("What's new?") == "what-s-new"
        assert sanitize_for_branch("Multiple   spaces") == "multiple-spaces"
        assert sanitize_for_branch("--leading-dashes--") == "leading-dashes"

    def test_create_branch_name_max_length(self, mock_jira_client):
        """Test truncating long summaries."""
        from create_branch_name import create_branch_name, MAX_BRANCH_LENGTH

        long_summary_issue = {
            'key': 'PROJ-123',
            'fields': {
                'summary': 'This is a very long summary that exceeds the maximum allowed length for a branch name and should be truncated properly',
                'issuetype': {'name': 'Story'}
            }
        }
        mock_jira_client.get_issue.return_value = long_summary_issue

        with patch('create_branch_name.get_jira_client', return_value=mock_jira_client):
            result = create_branch_name('PROJ-123')

        branch_name = result['branch_name']
        # Total branch name should respect max length
        assert len(branch_name) <= MAX_BRANCH_LENGTH

    def test_create_branch_name_lowercase(self, mock_jira_client):
        """Test converting to lowercase."""
        from create_branch_name import create_branch_name

        mixed_case_issue = {
            'key': 'PROJ-123',
            'fields': {
                'summary': 'Fix UPPERCASE and MixedCase Words',
                'issuetype': {'name': 'Bug'}
            }
        }
        mock_jira_client.get_issue.return_value = mixed_case_issue

        with patch('create_branch_name.get_jira_client', return_value=mock_jira_client):
            result = create_branch_name('PROJ-123')

        branch_name = result['branch_name']
        assert branch_name == branch_name.lower()
        assert 'proj-123' in branch_name

    def test_create_branch_name_auto_prefix_bug(self, mock_jira_client, sample_issue):
        """Test auto-prefix based on Bug issue type."""
        from create_branch_name import create_branch_name

        # sample_issue has issuetype 'Bug'
        mock_jira_client.get_issue.return_value = sample_issue

        with patch('create_branch_name.get_jira_client', return_value=mock_jira_client):
            result = create_branch_name('PROJ-123', auto_prefix=True)

        assert result['branch_name'].startswith('bugfix/')

    def test_create_branch_name_auto_prefix_story(self, mock_jira_client, sample_story_issue):
        """Test auto-prefix based on Story issue type."""
        from create_branch_name import create_branch_name

        mock_jira_client.get_issue.return_value = sample_story_issue

        with patch('create_branch_name.get_jira_client', return_value=mock_jira_client):
            result = create_branch_name('PROJ-456', auto_prefix=True)

        assert result['branch_name'].startswith('feature/')

    def test_create_branch_name_auto_prefix_task(self, mock_jira_client, sample_task_issue):
        """Test auto-prefix based on Task issue type."""
        from create_branch_name import create_branch_name

        mock_jira_client.get_issue.return_value = sample_task_issue

        with patch('create_branch_name.get_jira_client', return_value=mock_jira_client):
            result = create_branch_name('PROJ-789', auto_prefix=True)

        assert result['branch_name'].startswith('task/')

    def test_create_branch_name_output_json(self, mock_jira_client, sample_issue):
        """Test JSON output format."""
        from create_branch_name import create_branch_name, format_output

        mock_jira_client.get_issue.return_value = sample_issue

        with patch('create_branch_name.get_jira_client', return_value=mock_jira_client):
            result = create_branch_name('PROJ-123')
            # format_output expects a string branch_name, not the result dict
            output = format_output(result['branch_name'], 'PROJ-123', sample_issue, output_format='json')

        data = json.loads(output)
        assert 'branch_name' in data
        assert 'issue_key' in data
        assert data['issue_key'] == 'PROJ-123'

    def test_create_branch_name_output_git_command(self, mock_jira_client, sample_issue):
        """Test git command output format."""
        from create_branch_name import create_branch_name, format_output

        mock_jira_client.get_issue.return_value = sample_issue

        with patch('create_branch_name.get_jira_client', return_value=mock_jira_client):
            result = create_branch_name('PROJ-123')
            branch_name = result['branch_name']
            # format_output expects a string branch_name, not the result dict
            output = format_output(branch_name, 'PROJ-123', sample_issue, output_format='git')

        assert output.startswith('git checkout -b ')
        assert branch_name in output


# =============================================================================
# Tests for parse_commit_issues.py
# =============================================================================

@pytest.mark.dev
@pytest.mark.unit
class TestParseCommitIssues:
    """Tests for parse_commit_issues functionality."""

    def test_parse_single_issue(self):
        """Test extracting single issue key."""
        from parse_commit_issues import parse_issue_keys

        result = parse_issue_keys("PROJ-123: Fix bug")
        assert result == ["PROJ-123"]

    def test_parse_multiple_issues(self):
        """Test extracting multiple issue keys."""
        from parse_commit_issues import parse_issue_keys

        result = parse_issue_keys("Fix PROJ-123 and PROJ-456")
        assert "PROJ-123" in result
        assert "PROJ-456" in result
        assert len(result) == 2

    def test_parse_with_prefixes(self):
        """Test various prefixes (fixes, closes, refs)."""
        from parse_commit_issues import parse_issue_keys

        assert parse_issue_keys("Fixes PROJ-123") == ["PROJ-123"]
        assert parse_issue_keys("Closes PROJ-456") == ["PROJ-456"]
        assert parse_issue_keys("Refs PROJ-789") == ["PROJ-789"]
        assert parse_issue_keys("resolves PROJ-101") == ["PROJ-101"]

    def test_parse_case_insensitive(self):
        """Test case-insensitive matching."""
        from parse_commit_issues import parse_issue_keys

        result1 = parse_issue_keys("proj-123: fix bug")
        result2 = parse_issue_keys("PROJ-123: fix bug")
        result3 = parse_issue_keys("Proj-123: fix bug")

        assert result1 == ["PROJ-123"]
        assert result2 == ["PROJ-123"]
        assert result3 == ["PROJ-123"]

    def test_parse_filter_by_project(self):
        """Test filtering by project key."""
        from parse_commit_issues import parse_issue_keys

        message = "Fix PROJ-123 and OTHER-456 issues"
        result = parse_issue_keys(message, project_filter="PROJ")

        assert result == ["PROJ-123"]
        assert "OTHER-456" not in result

    def test_parse_no_issues(self):
        """Test handling messages with no issue keys."""
        from parse_commit_issues import parse_issue_keys

        result = parse_issue_keys("Update README with examples")
        assert result == []

    def test_parse_duplicate_issues(self):
        """Test deduplication of issue keys."""
        from parse_commit_issues import parse_issue_keys

        result = parse_issue_keys("PROJ-123: Fix bug, related to PROJ-123")
        assert result == ["PROJ-123"]

    def test_parse_various_formats(self):
        """Test various commit message formats."""
        from parse_commit_issues import parse_issue_keys

        # Conventional commit
        assert parse_issue_keys("feat(PROJ-123): add feature") == ["PROJ-123"]

        # Square brackets
        assert parse_issue_keys("[PROJ-456] Fix issue") == ["PROJ-456"]

        # Parentheses
        assert parse_issue_keys("Fix something (PROJ-789)") == ["PROJ-789"]

        # At end of message
        assert parse_issue_keys("Add tests PROJ-101") == ["PROJ-101"]


# =============================================================================
# Tests for link_commit.py
# =============================================================================

@pytest.mark.dev
@pytest.mark.unit
class TestLinkCommit:
    """Tests for link_commit functionality."""

    def test_link_commit_basic(self, mock_jira_client):
        """Test linking commit to issue via comment."""
        from link_commit import link_commit

        mock_jira_client.post.return_value = {'id': '10001'}

        with patch('link_commit.get_jira_client', return_value=mock_jira_client):
            result = link_commit(
                issue_key='PROJ-123',
                commit_sha='abc123def456',
                message='Fix login bug'
            )

        assert result['success'] is True
        mock_jira_client.post.assert_called_once()
        call_args = mock_jira_client.post.call_args
        assert '/rest/api/3/issue/PROJ-123/comment' in call_args[0][0]

    def test_link_commit_with_repo(self, mock_jira_client):
        """Test including repository URL."""
        from link_commit import link_commit, build_commit_comment

        mock_jira_client.post.return_value = {'id': '10001'}

        comment = build_commit_comment(
            commit_sha='abc123def456',
            message='Fix login bug',
            repo_url='https://github.com/org/repo'
        )

        assert 'github.com/org/repo' in comment
        assert 'abc123def456' in comment

    def test_link_commit_with_github_link(self, mock_jira_client):
        """Test creating GitHub commit link."""
        from link_commit import build_commit_url

        url = build_commit_url(
            commit_sha='abc123def456',
            repo_url='https://github.com/org/repo'
        )

        assert url == 'https://github.com/org/repo/commit/abc123def456'

    def test_link_commit_with_gitlab_link(self, mock_jira_client):
        """Test creating GitLab commit link."""
        from link_commit import build_commit_url

        url = build_commit_url(
            commit_sha='abc123def456',
            repo_url='https://gitlab.com/org/repo'
        )

        assert url == 'https://gitlab.com/org/repo/-/commit/abc123def456'

    def test_link_commit_with_bitbucket_link(self, mock_jira_client):
        """Test creating Bitbucket commit link."""
        from link_commit import build_commit_url

        url = build_commit_url(
            commit_sha='abc123def456',
            repo_url='https://bitbucket.org/org/repo'
        )

        assert url == 'https://bitbucket.org/org/repo/commits/abc123def456'

    def test_link_commit_multiple_issues(self, mock_jira_client):
        """Test linking same commit to multiple issues."""
        from link_commit import link_commit_to_issues

        mock_jira_client.post.return_value = {'id': '10001'}

        with patch('link_commit.get_jira_client', return_value=mock_jira_client):
            results = link_commit_to_issues(
                issue_keys=['PROJ-123', 'PROJ-456'],
                commit_sha='abc123def456',
                message='Fix bugs'
            )

        assert len(results) == 2
        assert all(r['success'] for r in results)
        assert mock_jira_client.post.call_count == 2


# =============================================================================
# Tests for get_issue_commits.py
# =============================================================================

@pytest.mark.dev
@pytest.mark.unit
class TestGetIssueCommits:
    """Tests for get_issue_commits functionality."""

    def test_get_commits_basic(self, mock_jira_client, sample_dev_info):
        """Test retrieving commits for issue."""
        from get_issue_commits import get_issue_commits

        mock_jira_client.get.return_value = sample_dev_info

        with patch('get_issue_commits.get_jira_client', return_value=mock_jira_client):
            result = get_issue_commits('PROJ-123')

        assert len(result) == 2, "Expected 2 commits from sample_dev_info"
        assert 'id' in result[0], "Commit should have 'id' field"

    def test_get_commits_with_details(self, mock_jira_client, sample_dev_info):
        """Test including commit message and author."""
        from get_issue_commits import get_issue_commits

        mock_jira_client.get.return_value = sample_dev_info

        with patch('get_issue_commits.get_jira_client', return_value=mock_jira_client):
            result = get_issue_commits('PROJ-123', detailed=True)

        assert len(result) == 2, "Expected 2 commits from sample_dev_info"
        commit = result[0]
        assert 'message' in commit, "Detailed commit should have 'message' field"
        assert 'author' in commit, "Detailed commit should have 'author' field"

    def test_get_commits_by_repo(self, mock_jira_client, sample_dev_info):
        """Test filtering by repository."""
        from get_issue_commits import get_issue_commits

        mock_jira_client.get.return_value = sample_dev_info

        with patch('get_issue_commits.get_jira_client', return_value=mock_jira_client):
            result = get_issue_commits('PROJ-123', repo_filter='org/repo')

        # Should only return commits from org/repo
        assert len(result) == 2, "Expected 2 commits from org/repo repository"

    def test_get_commits_no_development_info(self, mock_jira_client):
        """Test handling when no dev info available."""
        from get_issue_commits import get_issue_commits

        # Empty response
        mock_jira_client.get.return_value = {'detail': []}

        with patch('get_issue_commits.get_jira_client', return_value=mock_jira_client):
            result = get_issue_commits('PROJ-123')

        assert result == []

    def test_get_commits_handles_api_error(self, mock_jira_client):
        """Test graceful handling of API errors."""
        from get_issue_commits import get_issue_commits
        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.get.side_effect = NotFoundError("Issue", "PROJ-999")

        with patch('get_issue_commits.get_jira_client', return_value=mock_jira_client):
            with pytest.raises(NotFoundError):
                get_issue_commits('PROJ-999')


# =============================================================================
# Error Handling Tests
# =============================================================================

@pytest.mark.dev
@pytest.mark.unit
class TestCreateBranchNameErrors:
    """Error handling tests for create_branch_name."""

    def test_create_branch_name_auth_error(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from create_branch_name import create_branch_name
        from jira_assistant_skills_lib import AuthenticationError

        mock_jira_client.get_issue.side_effect = AuthenticationError("Invalid token")

        with patch('create_branch_name.get_jira_client', return_value=mock_jira_client):
            with pytest.raises(AuthenticationError):
                create_branch_name('PROJ-123')

    def test_create_branch_name_permission_error(self, mock_jira_client):
        """Test handling of 403 permission denied."""
        from create_branch_name import create_branch_name
        from jira_assistant_skills_lib import PermissionError

        mock_jira_client.get_issue.side_effect = PermissionError("Access denied")

        with patch('create_branch_name.get_jira_client', return_value=mock_jira_client):
            with pytest.raises(PermissionError):
                create_branch_name('PROJ-123')

    def test_create_branch_name_not_found_error(self, mock_jira_client):
        """Test handling of 404 issue not found."""
        from create_branch_name import create_branch_name
        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.get_issue.side_effect = NotFoundError("Issue", "PROJ-999")

        with patch('create_branch_name.get_jira_client', return_value=mock_jira_client):
            with pytest.raises(NotFoundError):
                create_branch_name('PROJ-999')

    def test_create_branch_name_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from create_branch_name import create_branch_name
        from jira_assistant_skills_lib import RateLimitError

        mock_jira_client.get_issue.side_effect = RateLimitError(retry_after=60)

        with patch('create_branch_name.get_jira_client', return_value=mock_jira_client):
            with pytest.raises(RateLimitError):
                create_branch_name('PROJ-123')

    def test_create_branch_name_server_error(self, mock_jira_client):
        """Test handling of 500 server error."""
        from create_branch_name import create_branch_name
        from jira_assistant_skills_lib import ServerError

        mock_jira_client.get_issue.side_effect = ServerError("Internal server error")

        with patch('create_branch_name.get_jira_client', return_value=mock_jira_client):
            with pytest.raises(ServerError):
                create_branch_name('PROJ-123')


@pytest.mark.dev
@pytest.mark.unit
class TestLinkCommitErrors:
    """Error handling tests for link_commit."""

    def test_link_commit_auth_error(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from link_commit import link_commit
        from jira_assistant_skills_lib import AuthenticationError

        mock_jira_client.post.side_effect = AuthenticationError("Invalid token")

        with patch('link_commit.get_jira_client', return_value=mock_jira_client):
            with pytest.raises(AuthenticationError):
                link_commit(
                    issue_key='PROJ-123',
                    commit_sha='abc123',
                    message='Test commit'
                )

    def test_link_commit_permission_error(self, mock_jira_client):
        """Test handling of 403 permission denied."""
        from link_commit import link_commit
        from jira_assistant_skills_lib import PermissionError

        mock_jira_client.post.side_effect = PermissionError("Access denied")

        with patch('link_commit.get_jira_client', return_value=mock_jira_client):
            with pytest.raises(PermissionError):
                link_commit(
                    issue_key='PROJ-123',
                    commit_sha='abc123',
                    message='Test commit'
                )

    def test_link_commit_not_found_error(self, mock_jira_client):
        """Test handling of 404 issue not found."""
        from link_commit import link_commit
        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.post.side_effect = NotFoundError("Issue", "PROJ-999")

        with patch('link_commit.get_jira_client', return_value=mock_jira_client):
            with pytest.raises(NotFoundError):
                link_commit(
                    issue_key='PROJ-999',
                    commit_sha='abc123',
                    message='Test commit'
                )

    def test_link_commit_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from link_commit import link_commit
        from jira_assistant_skills_lib import RateLimitError

        mock_jira_client.post.side_effect = RateLimitError(retry_after=60)

        with patch('link_commit.get_jira_client', return_value=mock_jira_client):
            with pytest.raises(RateLimitError):
                link_commit(
                    issue_key='PROJ-123',
                    commit_sha='abc123',
                    message='Test commit'
                )

    def test_link_commit_server_error(self, mock_jira_client):
        """Test handling of 500 server error."""
        from link_commit import link_commit
        from jira_assistant_skills_lib import ServerError

        mock_jira_client.post.side_effect = ServerError("Internal server error")

        with patch('link_commit.get_jira_client', return_value=mock_jira_client):
            with pytest.raises(ServerError):
                link_commit(
                    issue_key='PROJ-123',
                    commit_sha='abc123',
                    message='Test commit'
                )


@pytest.mark.dev
@pytest.mark.unit
class TestGetIssueCommitsErrors:
    """Error handling tests for get_issue_commits."""

    def test_get_commits_auth_error(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from get_issue_commits import get_issue_commits
        from jira_assistant_skills_lib import AuthenticationError

        mock_jira_client.get.side_effect = AuthenticationError("Invalid token")

        with patch('get_issue_commits.get_jira_client', return_value=mock_jira_client):
            with pytest.raises(AuthenticationError):
                get_issue_commits('PROJ-123')

    def test_get_commits_permission_error(self, mock_jira_client):
        """Test handling of 403 permission denied."""
        from get_issue_commits import get_issue_commits
        from jira_assistant_skills_lib import PermissionError

        mock_jira_client.get.side_effect = PermissionError("Access denied")

        with patch('get_issue_commits.get_jira_client', return_value=mock_jira_client):
            with pytest.raises(PermissionError):
                get_issue_commits('PROJ-123')

    def test_get_commits_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from get_issue_commits import get_issue_commits
        from jira_assistant_skills_lib import RateLimitError

        mock_jira_client.get.side_effect = RateLimitError(retry_after=60)

        with patch('get_issue_commits.get_jira_client', return_value=mock_jira_client):
            with pytest.raises(RateLimitError):
                get_issue_commits('PROJ-123')

    def test_get_commits_server_error(self, mock_jira_client):
        """Test handling of 500 server error."""
        from get_issue_commits import get_issue_commits
        from jira_assistant_skills_lib import ServerError

        mock_jira_client.get.side_effect = ServerError("Internal server error")

        with patch('get_issue_commits.get_jira_client', return_value=mock_jira_client):
            with pytest.raises(ServerError):
                get_issue_commits('PROJ-123')
