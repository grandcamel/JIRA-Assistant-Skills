"""
Tests for PR Management (Phase 2) - jira-dev skill.

TDD tests for:
- link_pr.py
- create_pr_description.py
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch
import json

# Add scripts path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


# =============================================================================
# Tests for link_pr.py
# =============================================================================

@pytest.mark.dev
@pytest.mark.unit
class TestLinkPR:
    """Tests for link_pr functionality."""

    def test_link_pr_github(self, mock_jira_client):
        """Test linking GitHub PR to issue."""
        from link_pr import link_pr, parse_pr_url

        mock_jira_client.post.return_value = {'id': '10001'}

        with patch('link_pr.get_jira_client', return_value=mock_jira_client):
            result = link_pr(
                issue_key='PROJ-123',
                pr_url='https://github.com/org/repo/pull/456'
            )

        assert result['success'] is True
        assert result['pr_number'] == 456
        mock_jira_client.post.assert_called_once()

    def test_link_pr_gitlab(self, mock_jira_client):
        """Test linking GitLab MR to issue."""
        from link_pr import link_pr, parse_pr_url

        mock_jira_client.post.return_value = {'id': '10001'}

        with patch('link_pr.get_jira_client', return_value=mock_jira_client):
            result = link_pr(
                issue_key='PROJ-123',
                pr_url='https://gitlab.com/org/repo/-/merge_requests/789'
            )

        assert result['success'] is True
        assert result['pr_number'] == 789

    def test_link_pr_bitbucket(self, mock_jira_client):
        """Test linking Bitbucket PR to issue."""
        from link_pr import link_pr, parse_pr_url

        mock_jira_client.post.return_value = {'id': '10001'}

        with patch('link_pr.get_jira_client', return_value=mock_jira_client):
            result = link_pr(
                issue_key='PROJ-123',
                pr_url='https://bitbucket.org/org/repo/pull-requests/101'
            )

        assert result['success'] is True
        assert result['pr_number'] == 101

    def test_link_pr_with_status(self, mock_jira_client):
        """Test including PR status (open, merged, closed)."""
        from link_pr import link_pr, build_pr_comment

        comment = build_pr_comment(
            pr_url='https://github.com/org/repo/pull/456',
            pr_number=456,
            status='merged',
            title='Fix login bug'
        )

        assert 'merged' in comment.lower()
        assert '456' in comment

    def test_parse_github_pr_url(self):
        """Test parsing GitHub PR URL."""
        from link_pr import parse_pr_url

        result = parse_pr_url('https://github.com/org/repo/pull/456')

        assert result['provider'] == 'github'
        assert result['owner'] == 'org'
        assert result['repo'] == 'repo'
        assert result['pr_number'] == 456

    def test_parse_gitlab_mr_url(self):
        """Test parsing GitLab MR URL."""
        from link_pr import parse_pr_url

        result = parse_pr_url('https://gitlab.com/org/repo/-/merge_requests/789')

        assert result['provider'] == 'gitlab'
        assert result['owner'] == 'org'
        assert result['repo'] == 'repo'
        assert result['pr_number'] == 789

    def test_parse_bitbucket_pr_url(self):
        """Test parsing Bitbucket PR URL."""
        from link_pr import parse_pr_url

        result = parse_pr_url('https://bitbucket.org/org/repo/pull-requests/101')

        assert result['provider'] == 'bitbucket'
        assert result['owner'] == 'org'
        assert result['repo'] == 'repo'
        assert result['pr_number'] == 101


# =============================================================================
# Tests for create_pr_description.py
# =============================================================================

@pytest.mark.dev
@pytest.mark.unit
class TestCreatePRDescription:
    """Tests for create_pr_description functionality."""

    def test_create_pr_description_basic(self, mock_jira_client, sample_issue):
        """Test generating PR description from issue."""
        from create_pr_description import create_pr_description

        mock_jira_client.get_issue.return_value = sample_issue

        with patch('create_pr_description.get_jira_client', return_value=mock_jira_client):
            result = create_pr_description('PROJ-123')

        # Result is now a dict with 'markdown' key
        markdown = result['markdown']
        # Should contain key elements
        assert 'PROJ-123' in markdown
        assert 'Fix login button not responding' in markdown
        mock_jira_client.close.assert_called_once()

    def test_create_pr_description_includes_jira_link(self, mock_jira_client, sample_issue):
        """Test PR description includes link to JIRA issue."""
        from create_pr_description import create_pr_description

        mock_jira_client.get_issue.return_value = sample_issue

        with patch('create_pr_description.get_jira_client', return_value=mock_jira_client):
            with patch('create_pr_description.get_jira_base_url', return_value='https://jira.example.com'):
                result = create_pr_description('PROJ-123')

        # Should have link to JIRA
        assert 'PROJ-123' in result['markdown']

    def test_create_pr_description_includes_checklist(self, mock_jira_client, sample_issue):
        """Test including checklist items."""
        from create_pr_description import create_pr_description

        mock_jira_client.get_issue.return_value = sample_issue

        with patch('create_pr_description.get_jira_client', return_value=mock_jira_client):
            result = create_pr_description('PROJ-123', include_checklist=True)

        # Should have checklist markers with standard markdown format
        assert '- [ ]' in result['markdown'], "Checklist should use '- [ ]' format"

    def test_create_pr_description_markdown_format(self, mock_jira_client, sample_issue):
        """Test Markdown output format."""
        from create_pr_description import create_pr_description

        mock_jira_client.get_issue.return_value = sample_issue

        with patch('create_pr_description.get_jira_client', return_value=mock_jira_client):
            result = create_pr_description('PROJ-123')

        # Should be valid markdown with h2 headers
        assert '## ' in result['markdown'], "PR description should have markdown h2 headers (## )"

    def test_create_pr_description_with_labels(self, mock_jira_client, sample_issue):
        """Test including labels from issue."""
        from create_pr_description import create_pr_description

        mock_jira_client.get_issue.return_value = sample_issue

        with patch('create_pr_description.get_jira_client', return_value=mock_jira_client):
            result = create_pr_description('PROJ-123', include_labels=True)

        # Labels from sample_issue: ['mobile', 'ui'] - should have Labels section
        result_lower = result['markdown'].lower()
        assert 'mobile' in result_lower, "Label 'mobile' should be in output"
        assert 'ui' in result_lower, "Label 'ui' should be in output"

    def test_create_pr_description_json_output(self, mock_jira_client, sample_issue):
        """Test JSON output format."""
        from create_pr_description import create_pr_description, format_output

        mock_jira_client.get_issue.return_value = sample_issue

        with patch('create_pr_description.get_jira_client', return_value=mock_jira_client):
            result = create_pr_description('PROJ-123')
            # format_output now expects the result dict directly
            output = format_output(result, output_format='json')

        data = json.loads(output)
        assert 'description' in data
        assert 'issue_key' in data


# =============================================================================
# Error Handling Tests
# =============================================================================

@pytest.mark.dev
@pytest.mark.unit
class TestLinkPRErrors:
    """Error handling tests for link_pr."""

    def test_link_pr_auth_error(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from link_pr import link_pr
        from jira_assistant_skills_lib import AuthenticationError

        mock_jira_client.post.side_effect = AuthenticationError("Invalid token")

        with patch('link_pr.get_jira_client', return_value=mock_jira_client):
            with pytest.raises(AuthenticationError):
                link_pr(
                    issue_key='PROJ-123',
                    pr_url='https://github.com/org/repo/pull/456'
                )

    def test_link_pr_permission_error(self, mock_jira_client):
        """Test handling of 403 permission denied."""
        from link_pr import link_pr
        from jira_assistant_skills_lib import PermissionError

        mock_jira_client.post.side_effect = PermissionError("Access denied")

        with patch('link_pr.get_jira_client', return_value=mock_jira_client):
            with pytest.raises(PermissionError):
                link_pr(
                    issue_key='PROJ-123',
                    pr_url='https://github.com/org/repo/pull/456'
                )

    def test_link_pr_not_found_error(self, mock_jira_client):
        """Test handling of 404 issue not found."""
        from link_pr import link_pr
        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.post.side_effect = NotFoundError("Issue", "PROJ-999")

        with patch('link_pr.get_jira_client', return_value=mock_jira_client):
            with pytest.raises(NotFoundError):
                link_pr(
                    issue_key='PROJ-999',
                    pr_url='https://github.com/org/repo/pull/456'
                )

    def test_link_pr_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from link_pr import link_pr
        from jira_assistant_skills_lib import RateLimitError

        mock_jira_client.post.side_effect = RateLimitError(retry_after=60)

        with patch('link_pr.get_jira_client', return_value=mock_jira_client):
            with pytest.raises(RateLimitError):
                link_pr(
                    issue_key='PROJ-123',
                    pr_url='https://github.com/org/repo/pull/456'
                )

    def test_link_pr_server_error(self, mock_jira_client):
        """Test handling of 500 server error."""
        from link_pr import link_pr
        from jira_assistant_skills_lib import ServerError

        mock_jira_client.post.side_effect = ServerError("Internal server error")

        with patch('link_pr.get_jira_client', return_value=mock_jira_client):
            with pytest.raises(ServerError):
                link_pr(
                    issue_key='PROJ-123',
                    pr_url='https://github.com/org/repo/pull/456'
                )


@pytest.mark.dev
@pytest.mark.unit
class TestCreatePRDescriptionErrors:
    """Error handling tests for create_pr_description."""

    def test_create_pr_description_auth_error(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from create_pr_description import create_pr_description
        from jira_assistant_skills_lib import AuthenticationError

        mock_jira_client.get_issue.side_effect = AuthenticationError("Invalid token")

        with patch('create_pr_description.get_jira_client', return_value=mock_jira_client):
            with pytest.raises(AuthenticationError):
                create_pr_description('PROJ-123')

    def test_create_pr_description_permission_error(self, mock_jira_client):
        """Test handling of 403 permission denied."""
        from create_pr_description import create_pr_description
        from jira_assistant_skills_lib import PermissionError

        mock_jira_client.get_issue.side_effect = PermissionError("Access denied")

        with patch('create_pr_description.get_jira_client', return_value=mock_jira_client):
            with pytest.raises(PermissionError):
                create_pr_description('PROJ-123')

    def test_create_pr_description_not_found_error(self, mock_jira_client):
        """Test handling of 404 issue not found."""
        from create_pr_description import create_pr_description
        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.get_issue.side_effect = NotFoundError("Issue", "PROJ-999")

        with patch('create_pr_description.get_jira_client', return_value=mock_jira_client):
            with pytest.raises(NotFoundError):
                create_pr_description('PROJ-999')

    def test_create_pr_description_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from create_pr_description import create_pr_description
        from jira_assistant_skills_lib import RateLimitError

        mock_jira_client.get_issue.side_effect = RateLimitError(retry_after=60)

        with patch('create_pr_description.get_jira_client', return_value=mock_jira_client):
            with pytest.raises(RateLimitError):
                create_pr_description('PROJ-123')

    def test_create_pr_description_server_error(self, mock_jira_client):
        """Test handling of 500 server error."""
        from create_pr_description import create_pr_description
        from jira_assistant_skills_lib import ServerError

        mock_jira_client.get_issue.side_effect = ServerError("Internal server error")

        with patch('create_pr_description.get_jira_client', return_value=mock_jira_client):
            with pytest.raises(ServerError):
                create_pr_description('PROJ-123')
