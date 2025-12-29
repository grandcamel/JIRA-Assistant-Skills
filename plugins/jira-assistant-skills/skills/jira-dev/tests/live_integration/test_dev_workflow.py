"""
Live Integration Tests: Developer Workflow

Tests for developer workflow integration against a real JIRA instance.
"""

import sys
import pytest
import uuid
from pathlib import Path
from typing import Dict, Any

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))

from create_branch_name import create_branch_name, sanitize_for_branch, get_prefix_for_issue_type
from create_pr_description import create_pr_description, extract_acceptance_criteria
from link_commit import link_commit
from link_pr import link_pr


class TestCreateBranchName:
    """Tests for branch name generation from JIRA issues."""

    def test_create_branch_name_task(self, jira_client, test_project, test_issue):
        """Test creating branch name from a task."""
        result = create_branch_name(
            issue_key=test_issue['key'],
            client=jira_client
        )

        assert result is not None
        assert 'branch_name' in result
        assert test_issue['key'].lower() in result['branch_name'].lower()

    def test_create_branch_name_with_auto_prefix(self, jira_client, test_project, test_bug):
        """Test auto-prefix based on issue type."""
        result = create_branch_name(
            issue_key=test_bug['key'],
            client=jira_client,
            auto_prefix=True
        )

        assert result is not None
        assert result['branch_name'].startswith('bugfix/')

    def test_create_branch_name_with_custom_prefix(self, jira_client, test_project, test_issue):
        """Test custom prefix."""
        result = create_branch_name(
            issue_key=test_issue['key'],
            client=jira_client,
            prefix='hotfix'
        )

        assert result is not None
        assert result['branch_name'].startswith('hotfix/')

    def test_create_branch_name_story(self, jira_client, test_project, test_story):
        """Test branch name from story with auto-prefix."""
        result = create_branch_name(
            issue_key=test_story['key'],
            client=jira_client,
            auto_prefix=True
        )

        assert result is not None
        assert result['branch_name'].startswith('feature/')

    def test_create_branch_name_json_output(self, jira_client, test_project, test_issue):
        """Test JSON output format."""
        result = create_branch_name(
            issue_key=test_issue['key'],
            client=jira_client,
            output_format='json'
        )

        assert result is not None
        assert 'issue_key' in result
        assert 'issue_type' in result
        assert 'branch_name' in result

    def test_create_branch_name_git_output(self, jira_client, test_project, test_issue):
        """Test git command output format."""
        result = create_branch_name(
            issue_key=test_issue['key'],
            client=jira_client,
            output_format='git'
        )

        assert result is not None
        assert 'git_command' in result
        assert result['git_command'].startswith('git checkout -b ')


class TestLinkCommit:
    """Tests for linking commits to JIRA issues."""

    def test_link_commit_github(self, jira_client, test_project, test_issue):
        """Test linking a GitHub commit."""
        commit_sha = 'abc123def456'
        repo_url = 'https://github.com/test-org/test-repo'

        result = link_commit(
            issue_key=test_issue['key'],
            commit=commit_sha,
            repo=repo_url,
            message='Test commit message',
            client=jira_client
        )

        assert result is not None
        assert result['success'] is True

        # Verify comment was added
        comments = jira_client.get_comments(test_issue['key'])
        assert comments['total'] >= 1

    def test_link_commit_gitlab(self, jira_client, test_project, test_issue):
        """Test linking a GitLab commit."""
        commit_sha = 'def789abc012'
        repo_url = 'https://gitlab.com/test-org/test-repo'

        result = link_commit(
            issue_key=test_issue['key'],
            commit=commit_sha,
            repo=repo_url,
            client=jira_client
        )

        assert result is not None
        assert result['success'] is True

    def test_link_commit_bitbucket(self, jira_client, test_project, test_issue):
        """Test linking a Bitbucket commit."""
        commit_sha = 'ghi345jkl678'
        repo_url = 'https://bitbucket.org/test-org/test-repo'

        result = link_commit(
            issue_key=test_issue['key'],
            commit=commit_sha,
            repo=repo_url,
            client=jira_client
        )

        assert result is not None
        assert result['success'] is True


class TestLinkPR:
    """Tests for linking pull requests to JIRA issues."""

    def test_link_pr_github(self, jira_client, test_project, test_issue):
        """Test linking a GitHub PR."""
        pr_url = 'https://github.com/test-org/test-repo/pull/123'

        result = link_pr(
            issue_key=test_issue['key'],
            pr_url=pr_url,
            client=jira_client
        )

        assert result is not None
        assert result['success'] is True

        # Verify comment was added
        comments = jira_client.get_comments(test_issue['key'])
        assert comments['total'] >= 1

    def test_link_pr_gitlab(self, jira_client, test_project, test_issue):
        """Test linking a GitLab merge request."""
        pr_url = 'https://gitlab.com/test-org/test-repo/-/merge_requests/456'

        result = link_pr(
            issue_key=test_issue['key'],
            pr_url=pr_url,
            client=jira_client
        )

        assert result is not None
        assert result['success'] is True

    def test_link_pr_bitbucket(self, jira_client, test_project, test_issue):
        """Test linking a Bitbucket pull request."""
        pr_url = 'https://bitbucket.org/test-org/test-repo/pull-requests/789'

        result = link_pr(
            issue_key=test_issue['key'],
            pr_url=pr_url,
            client=jira_client
        )

        assert result is not None
        assert result['success'] is True

    def test_link_pr_with_status(self, jira_client, test_project, test_issue):
        """Test linking PR with status."""
        pr_url = 'https://github.com/test-org/test-repo/pull/101'

        result = link_pr(
            issue_key=test_issue['key'],
            pr_url=pr_url,
            status='merged',
            title='Fix authentication bug',
            client=jira_client
        )

        assert result is not None
        assert result['success'] is True


class TestCreatePRDescription:
    """Tests for generating PR descriptions from JIRA issues."""

    def test_create_pr_description_basic(self, jira_client, test_project, test_issue, jira_profile):
        """Test basic PR description generation."""
        result = create_pr_description(
            issue_key=test_issue['key'],
            client=jira_client,
            profile=jira_profile
        )

        assert result is not None
        assert 'markdown' in result
        assert test_issue['key'] in result['markdown']

    def test_create_pr_description_with_checklist(self, jira_client, test_project, test_issue, jira_profile):
        """Test PR description with testing checklist."""
        result = create_pr_description(
            issue_key=test_issue['key'],
            client=jira_client,
            include_checklist=True,
            profile=jira_profile
        )

        assert result is not None
        assert 'Testing Checklist' in result['markdown'] or 'checklist' in result['markdown'].lower()

    def test_create_pr_description_story_with_ac(self, jira_client, test_project, test_story, jira_profile):
        """Test PR description for story with acceptance criteria."""
        result = create_pr_description(
            issue_key=test_story['key'],
            client=jira_client,
            profile=jira_profile
        )

        assert result is not None
        assert 'markdown' in result
        # Story type should be reflected
        assert test_story['key'] in result['markdown']

    def test_create_pr_description_json_output(self, jira_client, test_project, test_issue, jira_profile):
        """Test JSON output format."""
        result = create_pr_description(
            issue_key=test_issue['key'],
            client=jira_client,
            output_format='json',
            profile=jira_profile
        )

        assert result is not None
        assert 'issue_key' in result
        assert 'issue_type' in result
        assert 'priority' in result

    def test_create_pr_description_bug(self, jira_client, test_project, test_bug, jira_profile):
        """Test PR description for bug issue."""
        result = create_pr_description(
            issue_key=test_bug['key'],
            client=jira_client,
            profile=jira_profile
        )

        assert result is not None
        assert 'Bug' in result['markdown'] or 'bug' in result.get('issue_type', '').lower()


class TestSanitizeForBranch:
    """Tests for branch name sanitization (local utility function)."""

    def test_sanitize_lowercase(self):
        """Test lowercase conversion."""
        assert sanitize_for_branch("Hello World") == "hello-world"

    def test_sanitize_special_chars(self):
        """Test special character replacement."""
        assert sanitize_for_branch("Feature: Add login!") == "feature-add-login"

    def test_sanitize_consecutive_hyphens(self):
        """Test consecutive hyphen removal."""
        assert sanitize_for_branch("Test--Multiple---Hyphens") == "test-multiple-hyphens"

    def test_sanitize_empty(self):
        """Test empty string."""
        assert sanitize_for_branch("") == ""


class TestExtractAcceptanceCriteria:
    """Tests for acceptance criteria extraction."""

    def test_extract_ac_section(self):
        """Test extracting AC section."""
        description = """
        Some description here.

        Acceptance Criteria:
        - Criteria 1
        - Criteria 2
        """
        criteria = extract_acceptance_criteria(description)
        assert len(criteria) >= 1

    def test_extract_empty_description(self):
        """Test with empty description."""
        criteria = extract_acceptance_criteria("")
        assert criteria == []

    def test_extract_no_ac(self):
        """Test description without AC."""
        description = "Just a regular description."
        criteria = extract_acceptance_criteria(description)
        assert criteria == []
