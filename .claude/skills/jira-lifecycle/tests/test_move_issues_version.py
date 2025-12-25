"""
Tests for move_issues_version.py - Move issues between versions.
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add script path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


class TestMoveIssuesVersion:
    """Tests for moving issues between versions."""

    @patch('move_issues_version.get_jira_client')
    def test_move_issues_by_jql(self, mock_get_client, mock_jira_client, sample_issue_list):
        """Test moving issues found by JQL to a version."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.search_issues.return_value = sample_issue_list
        mock_jira_client.update_issue.return_value = None

        from move_issues_version import move_issues_to_version

        result = move_issues_to_version(
            jql='fixVersion = "v1.0.0"',
            target_version='v2.0.0',
            profile=None
        )

        # Should have updated both issues
        assert result['moved'] == 2
        assert mock_jira_client.update_issue.call_count == 2

    @patch('move_issues_version.get_jira_client')
    def test_move_issues_by_version_name(self, mock_get_client, mock_jira_client, sample_issue_list):
        """Test moving issues from one version to another."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.search_issues.return_value = sample_issue_list
        mock_jira_client.update_issue.return_value = None

        from move_issues_version import move_issues_between_versions

        result = move_issues_between_versions(
            project='PROJ',
            source_version='v1.0.0',
            target_version='v1.2.0',
            profile=None
        )

        # Should have moved the issues found by JQL
        assert result['moved'] == 2
        assert mock_jira_client.update_issue.call_count == 2

    @patch('move_issues_version.get_jira_client')
    def test_move_specific_issues(self, mock_get_client, mock_jira_client):
        """Test moving specific issues by key."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.update_issue.return_value = None

        from move_issues_version import move_specific_issues

        result = move_specific_issues(
            issue_keys=['PROJ-1', 'PROJ-2'],
            target_version='v2.0.0',
            profile=None
        )

        assert result['moved'] == 2
        assert mock_jira_client.update_issue.call_count == 2

    @patch('move_issues_version.get_jira_client')
    def test_move_issues_field_type(self, mock_get_client, mock_jira_client):
        """Test moving issues with different version field types (fixVersions vs versions)."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.update_issue.return_value = None

        from move_issues_version import move_specific_issues

        # Test with fixVersions field
        result = move_specific_issues(
            issue_keys=['PROJ-1'],
            target_version='v2.0.0',
            field='fixVersions',
            profile=None
        )

        assert result['moved'] == 1
        call_args = mock_jira_client.update_issue.call_args
        assert 'fixVersions' in call_args[1]['fields']

    @patch('move_issues_version.get_jira_client')
    def test_move_issues_dry_run(self, mock_get_client, mock_jira_client, sample_issue_list):
        """Test dry-run mode shows what would be moved."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.search_issues.return_value = sample_issue_list

        from move_issues_version import move_issues_dry_run

        result = move_issues_dry_run(
            jql='project = PROJ',
            target_version='v2.0.0',
            profile=None
        )

        # Should return issue count without updating
        assert result['would_move'] == 2
        assert 'issues' in result
        mock_jira_client.update_issue.assert_not_called()

    @patch('move_issues_version.get_jira_client')
    def test_move_issues_with_confirmation(self, mock_get_client, mock_jira_client, sample_issue_list, monkeypatch):
        """Test confirmation prompt before moving."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.search_issues.return_value = sample_issue_list
        mock_jira_client.update_issue.return_value = None

        # Simulate user confirming with 'yes'
        monkeypatch.setattr('builtins.input', lambda _: 'yes')

        from move_issues_version import move_issues_with_confirmation

        result = move_issues_with_confirmation(
            jql='project = PROJ',
            target_version='v2.0.0',
            profile=None
        )

        # Should have moved issues after confirmation
        assert result['moved'] == 2
