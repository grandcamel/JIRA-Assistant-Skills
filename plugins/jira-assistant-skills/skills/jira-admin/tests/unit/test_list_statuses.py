"""
Tests for list_statuses.py - TDD approach.

Tests for listing and filtering statuses.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'shared' / 'scripts' / 'lib'))


@pytest.mark.admin
@pytest.mark.unit
class TestListStatusesBasic:
    """Test listing all statuses."""

    def test_list_statuses_returns_all(self, mock_jira_client, all_statuses_response):
        """Test listing all statuses in the instance."""
        from list_statuses import list_statuses

        mock_jira_client.get_all_statuses.return_value = all_statuses_response

        result = list_statuses(client=mock_jira_client)

        assert len(result['statuses']) == len(all_statuses_response)
        mock_jira_client.get_all_statuses.assert_called_once()

    def test_list_statuses_empty(self, mock_jira_client, empty_statuses_response):
        """Test handling empty statuses list."""
        from list_statuses import list_statuses

        mock_jira_client.get_all_statuses.return_value = empty_statuses_response

        result = list_statuses(client=mock_jira_client)

        assert len(result['statuses']) == 0


@pytest.mark.admin
@pytest.mark.unit
class TestListStatusesFilterByCategory:
    """Test filtering statuses by category."""

    def test_list_statuses_filter_todo(self, mock_jira_client, all_statuses_response):
        """Test filtering to TODO category statuses."""
        from list_statuses import list_statuses

        mock_jira_client.get_all_statuses.return_value = all_statuses_response

        result = list_statuses(client=mock_jira_client, category='TODO')

        assert len(result['statuses']) > 0
        for status in result['statuses']:
            # Parsed status has category_key and category_name
            assert status.get('category_key') == 'new' or status.get('category_name') == 'To Do'

    def test_list_statuses_filter_in_progress(self, mock_jira_client, all_statuses_response):
        """Test filtering to IN_PROGRESS category statuses."""
        from list_statuses import list_statuses

        mock_jira_client.get_all_statuses.return_value = all_statuses_response

        result = list_statuses(client=mock_jira_client, category='IN_PROGRESS')

        assert len(result['statuses']) > 0
        for status in result['statuses']:
            # Parsed status has category_key and category_name
            assert status.get('category_key') == 'indeterminate' or status.get('category_name') == 'In Progress'

    def test_list_statuses_filter_done(self, mock_jira_client, all_statuses_response):
        """Test filtering to DONE category statuses."""
        from list_statuses import list_statuses

        mock_jira_client.get_all_statuses.return_value = all_statuses_response

        result = list_statuses(client=mock_jira_client, category='DONE')

        assert len(result['statuses']) > 0
        for status in result['statuses']:
            # Parsed status has category_key and category_name
            assert status.get('category_key') == 'done' or status.get('category_name') == 'Done'


@pytest.mark.admin
@pytest.mark.unit
class TestListStatusesFilterByWorkflow:
    """Test filtering statuses by workflow."""

    def test_list_statuses_filter_by_workflow(self, mock_jira_client, all_statuses_response, software_workflow):
        """Test filtering statuses to those in a specific workflow."""
        from list_statuses import list_statuses

        mock_jira_client.get_all_statuses.return_value = all_statuses_response
        mock_jira_client.search_workflows.return_value = {
            'values': [software_workflow],
            'total': 1
        }

        result = list_statuses(
            client=mock_jira_client,
            workflow='Software Development Workflow'
        )

        # Should filter to statuses in the workflow
        assert len(result['statuses']) > 0


@pytest.mark.admin
@pytest.mark.unit
class TestListStatusesGroupByCategory:
    """Test grouping statuses by category."""

    def test_list_statuses_group_by_category(self, mock_jira_client, all_statuses_response):
        """Test grouping statuses by category."""
        from list_statuses import list_statuses

        mock_jira_client.get_all_statuses.return_value = all_statuses_response

        result = list_statuses(client=mock_jira_client, group_by='category')

        assert 'groups' in result
        # Should have groups for TODO, IN_PROGRESS, DONE
        assert len(result['groups']) > 0


@pytest.mark.admin
@pytest.mark.unit
class TestListStatusesShowUsage:
    """Test showing status usage across workflows."""

    def test_list_statuses_show_usage(self, mock_jira_client, all_statuses_response, workflow_search_response):
        """Test showing how many workflows use each status."""
        from list_statuses import list_statuses

        mock_jira_client.get_all_statuses.return_value = all_statuses_response
        mock_jira_client.search_workflows.return_value = workflow_search_response

        result = list_statuses(client=mock_jira_client, show_usage=True)

        # Each status should have usage info
        for status in result['statuses']:
            assert 'workflow_count' in status or 'workflows' in status


@pytest.mark.admin
@pytest.mark.unit
class TestListStatusesOutputFormats:
    """Test output format handling."""

    def test_list_statuses_format_table(self, mock_jira_client, all_statuses_response):
        """Test table output format."""
        from list_statuses import list_statuses, format_statuses_table

        mock_jira_client.get_all_statuses.return_value = all_statuses_response

        result = list_statuses(client=mock_jira_client)
        output = format_statuses_table(result['statuses'])

        assert 'To Do' in output
        assert 'In Progress' in output
        assert 'Done' in output

    def test_list_statuses_format_json(self, mock_jira_client, all_statuses_response):
        """Test JSON output format."""
        from list_statuses import list_statuses, format_statuses_json
        import json

        mock_jira_client.get_all_statuses.return_value = all_statuses_response

        result = list_statuses(client=mock_jira_client)
        output = format_statuses_json(result['statuses'])

        parsed = json.loads(output)
        assert len(parsed) > 0


@pytest.mark.admin
@pytest.mark.unit
class TestListStatusesSearch:
    """Test using search endpoint for filtering."""

    def test_list_statuses_search_by_name(self, mock_jira_client, status_search_response):
        """Test searching statuses by name."""
        from list_statuses import list_statuses

        mock_jira_client.search_statuses.return_value = status_search_response

        result = list_statuses(client=mock_jira_client, search='Progress', use_search=True)

        mock_jira_client.search_statuses.assert_called_once()
        call_kwargs = mock_jira_client.search_statuses.call_args[1]
        assert call_kwargs.get('search_string') == 'Progress'


@pytest.mark.admin
@pytest.mark.unit
class TestListStatusesErrorHandling:
    """Test error handling scenarios."""

    def test_list_statuses_api_error(self, mock_jira_client):
        """Test handling of API errors."""
        from list_statuses import list_statuses
        from error_handler import JiraError

        mock_jira_client.get_all_statuses.side_effect = JiraError("API Error")

        with pytest.raises(JiraError):
            list_statuses(client=mock_jira_client)
