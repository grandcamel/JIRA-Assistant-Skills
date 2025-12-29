"""
Tests for get_workflow_for_issue.py - TDD approach.

Tests for getting workflow information for a specific issue.
"""

import sys
from pathlib import Path
from unittest.mock import patch
import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))


class TestGetWorkflowForIssueBasic:
    """Test getting workflow information for an issue."""

    def test_get_workflow_for_issue(self, mock_jira_client, issue_with_status, project_workflow_scheme, software_scheme_detail):
        """Test getting workflow info for an issue."""
        from get_workflow_for_issue import get_workflow_for_issue

        mock_jira_client.get_issue.return_value = issue_with_status
        mock_jira_client.get_workflow_scheme_for_project.return_value = project_workflow_scheme
        mock_jira_client.get_workflow_scheme.return_value = software_scheme_detail

        result = get_workflow_for_issue(client=mock_jira_client, issue_key='PROJ-123')

        assert result['issue_key'] == 'PROJ-123'
        assert 'current_status' in result
        assert 'workflow' in result or 'workflow_name' in result

    def test_get_workflow_for_issue_not_found(self, mock_jira_client):
        """Test error when issue not found."""
        from get_workflow_for_issue import get_workflow_for_issue
        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.get_issue.side_effect = NotFoundError("Issue not found")

        with pytest.raises(NotFoundError):
            get_workflow_for_issue(client=mock_jira_client, issue_key='NONEXISTENT-999')


class TestGetWorkflowForIssueWithStatus:
    """Test getting issue workflow with current status details."""

    def test_get_workflow_for_issue_current_status(self, mock_jira_client, issue_with_status, project_workflow_scheme, software_scheme_detail):
        """Test that current status is included."""
        from get_workflow_for_issue import get_workflow_for_issue

        mock_jira_client.get_issue.return_value = issue_with_status
        mock_jira_client.get_workflow_scheme_for_project.return_value = project_workflow_scheme
        mock_jira_client.get_workflow_scheme.return_value = software_scheme_detail

        result = get_workflow_for_issue(client=mock_jira_client, issue_key='PROJ-123')

        assert 'current_status' in result
        assert result['current_status']['name'] == 'To Do'


class TestGetWorkflowForIssueWithTransitions:
    """Test getting available transitions from current status."""

    def test_get_workflow_for_issue_show_transitions(self, mock_jira_client, issue_with_status, issue_transitions, project_workflow_scheme, software_scheme_detail):
        """Test showing available transitions."""
        from get_workflow_for_issue import get_workflow_for_issue

        mock_jira_client.get_issue.return_value = issue_with_status
        mock_jira_client.get_transitions.return_value = issue_transitions['transitions']
        mock_jira_client.get_workflow_scheme_for_project.return_value = project_workflow_scheme
        mock_jira_client.get_workflow_scheme.return_value = software_scheme_detail

        result = get_workflow_for_issue(
            client=mock_jira_client,
            issue_key='PROJ-123',
            show_transitions=True
        )

        assert 'available_transitions' in result
        assert len(result['available_transitions']) > 0
        transition_names = [t['name'] for t in result['available_transitions']]
        assert 'Start Progress' in transition_names


class TestGetWorkflowForIssueWithScheme:
    """Test showing workflow scheme information."""

    def test_get_workflow_for_issue_show_scheme(self, mock_jira_client, issue_with_status, project_workflow_scheme, software_scheme_detail):
        """Test showing workflow scheme information."""
        from get_workflow_for_issue import get_workflow_for_issue

        mock_jira_client.get_issue.return_value = issue_with_status
        mock_jira_client.get_workflow_scheme_for_project.return_value = project_workflow_scheme
        mock_jira_client.get_workflow_scheme.return_value = software_scheme_detail

        result = get_workflow_for_issue(
            client=mock_jira_client,
            issue_key='PROJ-123',
            show_scheme=True
        )

        assert 'workflow_scheme' in result
        assert result['workflow_scheme']['name'] == 'Software Development Scheme'


class TestGetWorkflowForIssueOutputFormats:
    """Test output format handling."""

    def test_get_workflow_for_issue_format_json(self, mock_jira_client, issue_with_status, project_workflow_scheme, software_scheme_detail):
        """Test JSON output format."""
        from get_workflow_for_issue import get_workflow_for_issue, format_issue_workflow_json
        import json

        mock_jira_client.get_issue.return_value = issue_with_status
        mock_jira_client.get_workflow_scheme_for_project.return_value = project_workflow_scheme
        mock_jira_client.get_workflow_scheme.return_value = software_scheme_detail

        result = get_workflow_for_issue(client=mock_jira_client, issue_key='PROJ-123')
        output = format_issue_workflow_json(result)

        parsed = json.loads(output)
        assert parsed['issue_key'] == 'PROJ-123'

    def test_get_workflow_for_issue_format_text(self, mock_jira_client, issue_with_status, issue_transitions, project_workflow_scheme, software_scheme_detail):
        """Test human-readable output format."""
        from get_workflow_for_issue import get_workflow_for_issue, format_issue_workflow

        mock_jira_client.get_issue.return_value = issue_with_status
        mock_jira_client.get_transitions.return_value = issue_transitions['transitions']
        mock_jira_client.get_workflow_scheme_for_project.return_value = project_workflow_scheme
        mock_jira_client.get_workflow_scheme.return_value = software_scheme_detail

        result = get_workflow_for_issue(
            client=mock_jira_client,
            issue_key='PROJ-123',
            show_transitions=True
        )
        output = format_issue_workflow(result)

        assert 'PROJ-123' in output
        assert 'To Do' in output or 'Status' in output


class TestGetWorkflowForIssueIssueType:
    """Test determining workflow by issue type."""

    def test_get_workflow_for_issue_by_issue_type(self, mock_jira_client, issue_with_status, project_workflow_scheme, software_scheme_detail):
        """Test that workflow is determined by issue type."""
        from get_workflow_for_issue import get_workflow_for_issue

        mock_jira_client.get_issue.return_value = issue_with_status
        mock_jira_client.get_workflow_scheme_for_project.return_value = project_workflow_scheme
        mock_jira_client.get_workflow_scheme.return_value = software_scheme_detail

        result = get_workflow_for_issue(client=mock_jira_client, issue_key='PROJ-123')

        # Should identify issue type and corresponding workflow
        assert 'issue_type' in result
        assert result['issue_type'] == 'Story'


class TestGetWorkflowForIssueErrorHandling:
    """Test error handling scenarios."""

    def test_get_workflow_for_issue_invalid_key(self, mock_jira_client):
        """Test error for invalid issue key format."""
        from get_workflow_for_issue import get_workflow_for_issue
        from jira_assistant_skills_lib import ValidationError

        with pytest.raises(ValidationError):
            get_workflow_for_issue(client=mock_jira_client, issue_key='invalid-key')

    def test_get_workflow_for_issue_no_permission(self, mock_jira_client):
        """Test error when user lacks permission."""
        from get_workflow_for_issue import get_workflow_for_issue
        from jira_assistant_skills_lib import PermissionError as JiraPermissionError

        mock_jira_client.get_issue.side_effect = JiraPermissionError("No access")

        with pytest.raises(JiraPermissionError):
            get_workflow_for_issue(client=mock_jira_client, issue_key='PROJ-123')
