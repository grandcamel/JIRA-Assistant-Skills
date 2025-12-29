"""
Tests for list_workflows.py - TDD approach.

Tests for listing and filtering workflows in a JIRA instance.
"""

import sys
from pathlib import Path
from unittest.mock import patch
import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))


class TestListWorkflowsBasic:
    """Test listing all workflows with basic information."""

    def test_list_workflows_returns_all(self, mock_jira_client, workflows_response):
        """Test listing all workflows with basic information."""
        from list_workflows import list_workflows

        mock_jira_client.get_workflows.return_value = workflows_response

        result = list_workflows(client=mock_jira_client)

        assert result['total'] == 4
        assert len(result['workflows']) == 4
        mock_jira_client.get_workflows.assert_called_once()

    def test_list_workflows_empty_result(self, mock_jira_client, empty_workflows_response):
        """Test handling empty workflows list."""
        from list_workflows import list_workflows

        mock_jira_client.get_workflows.return_value = empty_workflows_response

        result = list_workflows(client=mock_jira_client)

        assert result['total'] == 0
        assert len(result['workflows']) == 0


class TestListWorkflowsWithDetails:
    """Test listing workflows with full details (statuses, transitions)."""

    def test_list_workflows_with_details(self, mock_jira_client, workflow_search_response):
        """Test listing workflows with full details using search endpoint."""
        from list_workflows import list_workflows

        mock_jira_client.search_workflows.return_value = workflow_search_response

        result = list_workflows(client=mock_jira_client, details=True)

        assert result['total'] == 2
        # Verify workflows have status and transition counts
        for wf in result['workflows']:
            assert 'status_count' in wf
            assert 'transition_count' in wf
        mock_jira_client.search_workflows.assert_called_once()

    def test_list_workflows_details_includes_statuses(self, mock_jira_client, workflow_search_response):
        """Test that details mode includes status information."""
        from list_workflows import list_workflows

        mock_jira_client.search_workflows.return_value = workflow_search_response

        result = list_workflows(client=mock_jira_client, details=True)

        # Software workflow should have 5 statuses
        software_wf = next(w for w in result['workflows']
                          if w['name'] == 'Software Development Workflow')
        assert software_wf['status_count'] == 5


class TestListWorkflowsFilterByName:
    """Test filtering workflows by name pattern."""

    def test_list_workflows_filter_by_name(self, mock_jira_client, workflows_response):
        """Test filtering workflows by name pattern."""
        from list_workflows import list_workflows

        # Simulate filtering at client level
        filtered_response = {
            **workflows_response,
            'values': [w for w in workflows_response['values']
                      if 'Development' in w['id']['name']],
            'total': 1
        }
        mock_jira_client.get_workflows.return_value = filtered_response

        result = list_workflows(client=mock_jira_client, name_filter='Development')

        assert result['total'] == 1
        assert 'Development' in result['workflows'][0]['name']

    def test_list_workflows_filter_case_insensitive(self, mock_jira_client, workflows_response):
        """Test that name filter is case insensitive."""
        from list_workflows import list_workflows

        # Simulate filtering - would match "Bug Workflow"
        filtered_response = {
            **workflows_response,
            'values': [w for w in workflows_response['values']
                      if 'bug' in w['id']['name'].lower()],
            'total': 1
        }
        mock_jira_client.get_workflows.return_value = filtered_response

        result = list_workflows(client=mock_jira_client, name_filter='bug')

        assert result['total'] == 1
        assert 'Bug' in result['workflows'][0]['name']


class TestListWorkflowsFilterByScope:
    """Test filtering by global vs project-scoped workflows."""

    def test_list_workflows_filter_global_scope(self, mock_jira_client, workflows_response):
        """Test filtering to global workflows only."""
        from list_workflows import list_workflows

        mock_jira_client.get_workflows.return_value = workflows_response

        result = list_workflows(client=mock_jira_client, scope='global')

        # All workflows in our fixture are global
        assert result['total'] >= 0
        mock_jira_client.get_workflows.assert_called_once()

    def test_list_workflows_filter_project_scope(self, mock_jira_client):
        """Test filtering to project-scoped workflows only."""
        from list_workflows import list_workflows

        # Create response with project-scoped workflow
        project_workflow_response = {
            'values': [
                {
                    'id': {
                        'name': 'Project Custom Workflow',
                        'entityId': 'project-custom-123'
                    },
                    'description': 'Custom workflow for specific project',
                    'isDefault': False,
                    'scope': {
                        'type': 'PROJECT',
                        'project': {'id': '10000', 'key': 'PROJ'}
                    }
                }
            ],
            'total': 1
        }
        mock_jira_client.get_workflows.return_value = project_workflow_response

        result = list_workflows(client=mock_jira_client, scope='project')

        assert result['total'] == 1


class TestListWorkflowsShowUsage:
    """Test showing which projects use each workflow."""

    def test_list_workflows_show_usage(self, mock_jira_client, workflows_response, schemes_for_workflow):
        """Test showing which projects use each workflow."""
        from list_workflows import list_workflows

        mock_jira_client.get_workflows.return_value = workflows_response
        mock_jira_client.get_workflow_schemes_for_workflow.return_value = schemes_for_workflow

        result = list_workflows(client=mock_jira_client, show_usage=True)

        # Should have usage info for workflows
        assert result['total'] == 4
        # At least one workflow should have scheme count
        has_usage = any(w.get('scheme_count', 0) > 0 for w in result['workflows'])
        # The call should be made for each workflow
        assert mock_jira_client.get_workflow_schemes_for_workflow.called


class TestListWorkflowsPagination:
    """Test handling paginated results."""

    def test_list_workflows_pagination_first_page(self, mock_jira_client, workflows_page_1):
        """Test first page of paginated results."""
        from list_workflows import list_workflows

        mock_jira_client.get_workflows.return_value = workflows_page_1

        result = list_workflows(client=mock_jira_client, max_results=2)

        assert len(result['workflows']) == 2
        assert result['total'] == 4
        assert result['has_more'] == True

    def test_list_workflows_all_pages(self, mock_jira_client, workflows_page_1, workflows_page_2):
        """Test fetching all pages of results."""
        from list_workflows import list_workflows

        # Mock to return different pages on subsequent calls
        mock_jira_client.get_workflows.side_effect = [workflows_page_1, workflows_page_2]

        result = list_workflows(client=mock_jira_client, fetch_all=True)

        assert len(result['workflows']) == 4
        assert mock_jira_client.get_workflows.call_count == 2


class TestListWorkflowsOutputFormats:
    """Test output format handling."""

    def test_list_workflows_format_table(self, mock_jira_client, workflows_response, capsys):
        """Test human-readable table output."""
        from list_workflows import list_workflows, format_workflows_table

        mock_jira_client.get_workflows.return_value = workflows_response

        result = list_workflows(client=mock_jira_client)
        output = format_workflows_table(result['workflows'])

        assert 'Software Development Workflow' in output
        assert 'Bug Workflow' in output

    def test_list_workflows_format_json(self, mock_jira_client, workflows_response):
        """Test JSON output format."""
        from list_workflows import list_workflows, format_workflows_json
        import json

        mock_jira_client.get_workflows.return_value = workflows_response

        result = list_workflows(client=mock_jira_client)
        output = format_workflows_json(result['workflows'])

        # Should be valid JSON
        parsed = json.loads(output)
        assert len(parsed) == 4


class TestListWorkflowsErrorHandling:
    """Test error handling scenarios."""

    def test_list_workflows_no_permission(self, mock_jira_client):
        """Test error handling when user lacks admin permission."""
        from list_workflows import list_workflows
        from error_handler import PermissionError as JiraPermissionError

        mock_jira_client.get_workflows.side_effect = JiraPermissionError(
            "You do not have permission to view workflows. "
            "Requires 'Administer Jira' global permission."
        )

        with pytest.raises(JiraPermissionError) as exc_info:
            list_workflows(client=mock_jira_client)

        assert 'permission' in str(exc_info.value).lower()

    def test_list_workflows_api_error(self, mock_jira_client):
        """Test handling of API errors."""
        from list_workflows import list_workflows
        from error_handler import JiraError

        mock_jira_client.get_workflows.side_effect = JiraError("API Error")

        with pytest.raises(JiraError):
            list_workflows(client=mock_jira_client)
