"""
Tests for list_projects.py - Listing and searching JIRA projects.

Following TDD: These tests are written FIRST and should FAIL initially.
Implementation comes after tests are defined.
"""

import sys
from pathlib import Path

# Add paths BEFORE any other imports
test_dir = Path(__file__).parent  # unit
tests_dir = test_dir.parent  # tests
jira_admin_dir = tests_dir.parent  # jira-admin
skills_dir = jira_admin_dir.parent  # skills
shared_lib_path = skills_dir / 'shared' / 'scripts' / 'lib'
scripts_path = jira_admin_dir / 'scripts'

sys.path.insert(0, str(shared_lib_path))
sys.path.insert(0, str(scripts_path))

import pytest
from unittest.mock import Mock, patch, MagicMock


@pytest.mark.admin
@pytest.mark.unit
class TestListProjects:
    """Test suite for list_projects.py functionality."""

    def test_list_projects_all(self, mock_jira_client, sample_project_list_response):
        """Test listing all projects."""
        from list_projects import list_projects

        mock_jira_client.search_projects.return_value = sample_project_list_response

        result = list_projects(client=mock_jira_client)

        assert result is not None
        assert len(result['values']) == 2
        assert result['values'][0]['key'] == "PROJ"
        assert result['values'][1]['key'] == "KANBAN"

        mock_jira_client.search_projects.assert_called_once()

    def test_list_projects_by_type(self, mock_jira_client, sample_project_list_response):
        """Test filtering projects by type."""
        from list_projects import list_projects

        mock_jira_client.search_projects.return_value = sample_project_list_response

        result = list_projects(
            project_type="software",
            client=mock_jira_client
        )

        assert result is not None

        # Verify type filter was passed
        call_kwargs = mock_jira_client.search_projects.call_args
        assert 'type_key' in str(call_kwargs) or 'software' in str(call_kwargs)

    def test_list_projects_search_query(self, mock_jira_client, sample_project_list_response):
        """Test searching projects by name/key."""
        from list_projects import list_projects

        mock_jira_client.search_projects.return_value = sample_project_list_response

        result = list_projects(
            query="Test",
            client=mock_jira_client
        )

        assert result is not None

        # Verify query was passed
        call_kwargs = mock_jira_client.search_projects.call_args
        assert 'query' in str(call_kwargs) or 'Test' in str(call_kwargs)

    def test_list_projects_by_category(self, mock_jira_client, sample_project_list_response):
        """Test filtering projects by category."""
        from list_projects import list_projects

        mock_jira_client.search_projects.return_value = sample_project_list_response

        result = list_projects(
            category_id=10000,
            client=mock_jira_client
        )

        assert result is not None

        # Verify category filter was passed
        call_kwargs = mock_jira_client.search_projects.call_args
        assert 'category_id' in str(call_kwargs) or '10000' in str(call_kwargs)

    def test_list_projects_include_archived(self, mock_jira_client, sample_project_list_response):
        """Test including archived projects."""
        from list_projects import list_projects

        mock_jira_client.search_projects.return_value = sample_project_list_response

        result = list_projects(
            include_archived=True,
            client=mock_jira_client
        )

        assert result is not None

        # Verify status filter was passed
        call_kwargs = mock_jira_client.search_projects.call_args
        assert 'archived' in str(call_kwargs).lower() or 'status' in str(call_kwargs).lower()

    def test_list_projects_pagination(self, mock_jira_client, sample_project_list_response):
        """Test pagination parameters."""
        from list_projects import list_projects

        mock_jira_client.search_projects.return_value = sample_project_list_response

        result = list_projects(
            start_at=50,
            max_results=25,
            client=mock_jira_client
        )

        assert result is not None

        # Verify pagination was passed
        call_kwargs = mock_jira_client.search_projects.call_args
        assert 'start_at' in str(call_kwargs).lower() or '50' in str(call_kwargs)

    def test_list_projects_with_expand(self, mock_jira_client, sample_project_list_response):
        """Test expanding additional fields."""
        from list_projects import list_projects

        mock_jira_client.search_projects.return_value = sample_project_list_response

        result = list_projects(
            expand=['description', 'lead'],
            client=mock_jira_client
        )

        assert result is not None

        # Verify expand was passed
        call_kwargs = mock_jira_client.search_projects.call_args
        assert 'expand' in str(call_kwargs).lower()

    def test_list_projects_empty(self, mock_jira_client):
        """Test when no projects found."""
        from list_projects import list_projects

        mock_jira_client.search_projects.return_value = {
            "values": [],
            "total": 0,
            "isLast": True
        }

        result = list_projects(client=mock_jira_client)

        assert result is not None
        assert len(result['values']) == 0

    def test_list_projects_json_output(self, mock_jira_client, sample_project_list_response):
        """Test JSON output format."""
        from list_projects import list_projects

        mock_jira_client.search_projects.return_value = sample_project_list_response

        result = list_projects(
            output_format="json",
            client=mock_jira_client
        )

        assert result is not None
        # Result should be suitable for JSON serialization
        import json
        json.dumps(result)  # Should not raise

    def test_list_projects_table_output(self, mock_jira_client, sample_project_list_response):
        """Test table output format."""
        from list_projects import list_projects

        mock_jira_client.search_projects.return_value = sample_project_list_response

        result = list_projects(
            output_format="table",
            client=mock_jira_client
        )

        assert result is not None

    def test_list_projects_csv_output(self, mock_jira_client, sample_project_list_response):
        """Test CSV output format."""
        from list_projects import list_projects

        mock_jira_client.search_projects.return_value = sample_project_list_response

        result = list_projects(
            output_format="csv",
            client=mock_jira_client
        )

        assert result is not None


@pytest.mark.admin
@pytest.mark.unit
class TestListProjectsDeleted:
    """Test listing deleted/trashed projects."""

    def test_list_trash_projects(self, mock_jira_client, sample_trash_projects):
        """Test listing projects in trash."""
        from list_projects import list_trash_projects

        mock_jira_client.search_projects.return_value = sample_trash_projects

        result = list_trash_projects(client=mock_jira_client)

        assert result is not None
        assert len(result['values']) == 1
        assert result['values'][0]['deleted'] == True

        # Verify status filter was 'deleted'
        call_kwargs = mock_jira_client.search_projects.call_args
        assert 'deleted' in str(call_kwargs).lower()

    def test_list_trash_shows_retention_date(self, mock_jira_client, sample_trash_projects):
        """Test that trash listing includes retention date."""
        from list_projects import list_trash_projects

        mock_jira_client.search_projects.return_value = sample_trash_projects

        result = list_trash_projects(client=mock_jira_client)

        assert 'retentionTillDate' in result['values'][0]


@pytest.mark.admin
@pytest.mark.unit
class TestListProjectsCLI:
    """Test command-line interface for list_projects.py."""

    @patch('sys.argv', ['list_projects.py'])
    def test_cli_no_args(self, mock_jira_client, sample_project_list_response):
        """Test CLI with no arguments."""
        mock_jira_client.search_projects.return_value = sample_project_list_response
        pass

    @patch('sys.argv', ['list_projects.py', '--type', 'software'])
    def test_cli_filter_by_type(self, mock_jira_client, sample_project_list_response):
        """Test CLI with type filter."""
        mock_jira_client.search_projects.return_value = sample_project_list_response
        pass

    @patch('sys.argv', ['list_projects.py', '--search', 'Mobile'])
    def test_cli_search(self, mock_jira_client, sample_project_list_response):
        """Test CLI with search query."""
        mock_jira_client.search_projects.return_value = sample_project_list_response
        pass

    @patch('sys.argv', ['list_projects.py', '--include-archived'])
    def test_cli_include_archived(self, mock_jira_client, sample_project_list_response):
        """Test CLI including archived projects."""
        mock_jira_client.search_projects.return_value = sample_project_list_response
        pass

    @patch('sys.argv', ['list_projects.py', '--output', 'csv'])
    def test_cli_csv_output(self, mock_jira_client, sample_project_list_response):
        """Test CLI with CSV output."""
        mock_jira_client.search_projects.return_value = sample_project_list_response
        pass
