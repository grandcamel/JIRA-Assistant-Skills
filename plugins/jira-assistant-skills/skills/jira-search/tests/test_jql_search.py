"""
Tests for jql_search.py - Search for JIRA issues using JQL.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add script path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


@pytest.fixture
def sample_search_results():
    """Sample search results."""
    return {
        'issues': [
            {
                'key': 'PROJ-123',
                'fields': {
                    'summary': 'Test issue 1',
                    'status': {'name': 'Open'},
                    'priority': {'name': 'High'},
                    'issuetype': {'name': 'Bug'},
                    'assignee': {'displayName': 'John Smith'},
                    'reporter': {'displayName': 'Jane Doe'}
                }
            },
            {
                'key': 'PROJ-124',
                'fields': {
                    'summary': 'Test issue 2',
                    'status': {'name': 'In Progress'},
                    'priority': {'name': 'Medium'},
                    'issuetype': {'name': 'Task'},
                    'assignee': None,
                    'reporter': {'displayName': 'John Smith'}
                }
            }
        ],
        'total': 2,
        'isLast': True
    }


@pytest.fixture
def sample_search_results_paginated():
    """Sample search results with pagination."""
    return {
        'issues': [
            {
                'key': 'PROJ-123',
                'fields': {
                    'summary': 'Test issue 1',
                    'status': {'name': 'Open'},
                    'priority': {'name': 'High'},
                    'issuetype': {'name': 'Bug'},
                    'assignee': None,
                    'reporter': {'displayName': 'Jane Doe'}
                }
            }
        ],
        'isLast': False,
        'nextPageToken': 'abc123xyz'
    }


@pytest.mark.search
@pytest.mark.unit
class TestSearchIssues:
    """Tests for the search_issues function."""

    def test_search_basic(self, mock_jira_client, sample_search_results):
        """Test basic JQL search."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('jql_search.get_jira_client', return_value=mock_jira_client):
            from jql_search import search_issues

            result = search_issues('project = PROJ')

            assert len(result['issues']) == 2
            assert result['total'] == 2
            mock_jira_client.search_issues.assert_called_once()

    def test_search_with_custom_fields(self, mock_jira_client, sample_search_results):
        """Test search with custom field list."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('jql_search.get_jira_client', return_value=mock_jira_client):
            from jql_search import search_issues

            search_issues('project = PROJ', fields=['key', 'summary'])

            mock_jira_client.search_issues.assert_called_with(
                'project = PROJ',
                fields=['key', 'summary'],
                max_results=50,
                next_page_token=None
            )

    def test_search_with_agile_fields(self, mock_jira_client, sample_search_results):
        """Test search including agile fields."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('jql_search.get_jira_client', return_value=mock_jira_client):
            from jql_search import search_issues

            search_issues('project = PROJ', include_agile=True)

            call_args = mock_jira_client.search_issues.call_args
            fields = call_args[1]['fields']
            assert 'customfield_10014' in fields  # EPIC_LINK_FIELD
            assert 'customfield_10016' in fields  # STORY_POINTS_FIELD
            assert 'sprint' in fields

    def test_search_with_links(self, mock_jira_client, sample_search_results):
        """Test search including issue links."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('jql_search.get_jira_client', return_value=mock_jira_client):
            from jql_search import search_issues

            search_issues('project = PROJ', include_links=True)

            call_args = mock_jira_client.search_issues.call_args
            fields = call_args[1]['fields']
            assert 'issuelinks' in fields

    def test_search_with_time_tracking(self, mock_jira_client, sample_search_results):
        """Test search including time tracking fields."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('jql_search.get_jira_client', return_value=mock_jira_client):
            from jql_search import search_issues

            search_issues('project = PROJ', include_time=True)

            call_args = mock_jira_client.search_issues.call_args
            fields = call_args[1]['fields']
            assert 'timetracking' in fields

    def test_search_with_pagination(self, mock_jira_client, sample_search_results):
        """Test search with page token."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('jql_search.get_jira_client', return_value=mock_jira_client):
            from jql_search import search_issues

            search_issues('project = PROJ', next_page_token='abc123')

            mock_jira_client.search_issues.assert_called_with(
                'project = PROJ',
                fields=['key', 'summary', 'status', 'priority', 'issuetype', 'assignee', 'reporter'],
                max_results=50,
                next_page_token='abc123'
            )

    def test_search_with_profile(self, mock_jira_client, sample_search_results):
        """Test search with specific profile."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('jql_search.get_jira_client', return_value=mock_jira_client) as mock_get_client:
            from jql_search import search_issues

            search_issues('project = PROJ', profile='development')

            mock_get_client.assert_called_with('development')


@pytest.mark.search
@pytest.mark.unit
class TestGetJqlFromFilter:
    """Tests for get_jql_from_filter function."""

    def test_get_jql_from_filter(self, mock_jira_client, sample_filter):
        """Test getting JQL from a saved filter."""
        mock_jira_client.get_filter.return_value = sample_filter

        from jql_search import get_jql_from_filter

        jql, name = get_jql_from_filter(mock_jira_client, '10042')

        assert jql == sample_filter['jql']
        assert name == sample_filter['name']
        mock_jira_client.get_filter.assert_called_with('10042')


@pytest.mark.search
@pytest.mark.unit
class TestSaveSearchAsFilter:
    """Tests for save_search_as_filter function."""

    def test_save_filter(self, mock_jira_client):
        """Test saving a search as a filter."""
        mock_jira_client.create_filter.return_value = {
            'id': '10050',
            'name': 'New Filter',
            'jql': 'project = PROJ'
        }

        from jql_search import save_search_as_filter

        result = save_search_as_filter(mock_jira_client, 'project = PROJ', 'New Filter')

        assert result['id'] == '10050'
        mock_jira_client.create_filter.assert_called_with(
            'New Filter', 'project = PROJ', description=None, favourite=False
        )

    def test_save_filter_with_options(self, mock_jira_client):
        """Test saving a filter with description and favourite."""
        mock_jira_client.create_filter.return_value = {
            'id': '10050',
            'name': 'New Filter',
            'jql': 'project = PROJ',
            'favourite': True
        }

        from jql_search import save_search_as_filter

        save_search_as_filter(
            mock_jira_client, 'project = PROJ', 'New Filter',
            description='My description', favourite=True
        )

        mock_jira_client.create_filter.assert_called_with(
            'New Filter', 'project = PROJ',
            description='My description', favourite=True
        )


@pytest.mark.search
@pytest.mark.unit
class TestJqlSearchMain:
    """Tests for main() function."""

    def test_main_basic_search(self, mock_jira_client, sample_search_results, capsys):
        """Test main function with basic search."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('jql_search.get_jira_client', return_value=mock_jira_client):
            from jql_search import main

            main(['project = PROJ'])

            captured = capsys.readouterr()
            assert 'Found 2 issue' in captured.out

    def test_main_with_filter(self, mock_jira_client, sample_filter, sample_search_results, capsys):
        """Test main function using a saved filter."""
        mock_jira_client.get_filter.return_value = sample_filter
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('jql_search.get_jira_client', return_value=mock_jira_client):
            from jql_search import main

            main(['--filter', '10042'])

            captured = capsys.readouterr()
            assert 'Running filter' in captured.out
            assert sample_filter['name'] in captured.out

    def test_main_save_as_filter(self, mock_jira_client, sample_search_results, capsys):
        """Test main function saving search as filter."""
        mock_jira_client.search_issues.return_value = sample_search_results
        mock_jira_client.create_filter.return_value = {
            'id': '10050',
            'name': 'Saved Filter'
        }

        with patch('jql_search.get_jira_client', return_value=mock_jira_client):
            from jql_search import main

            main(['project = PROJ', '--save-as', 'Saved Filter'])

            captured = capsys.readouterr()
            assert 'Saved as filter' in captured.out
            mock_jira_client.create_filter.assert_called_once()

    def test_main_json_output(self, mock_jira_client, sample_search_results, capsys):
        """Test main function with JSON output."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('jql_search.get_jira_client', return_value=mock_jira_client):
            from jql_search import main

            main(['project = PROJ', '--output', 'json'])

            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert 'issues' in output
            assert len(output['issues']) == 2

    def test_main_with_fields(self, mock_jira_client, sample_search_results):
        """Test main function with custom fields."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('jql_search.get_jira_client', return_value=mock_jira_client):
            from jql_search import main

            main(['project = PROJ', '--fields', 'key,summary,status'])

            call_args = mock_jira_client.search_issues.call_args
            fields = call_args[1]['fields']
            assert fields == ['key', 'summary', 'status']

    def test_main_with_agile_flags(self, mock_jira_client, sample_search_results):
        """Test main function with agile display flags."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('jql_search.get_jira_client', return_value=mock_jira_client):
            from jql_search import main

            main(['project = PROJ', '--show-agile', '--show-links', '--show-time'])

            call_args = mock_jira_client.search_issues.call_args
            fields = call_args[1]['fields']
            assert 'customfield_10014' in fields
            assert 'issuelinks' in fields
            assert 'timetracking' in fields

    def test_main_with_pagination(self, mock_jira_client, sample_search_results_paginated, capsys):
        """Test main function with pagination info."""
        mock_jira_client.search_issues.return_value = sample_search_results_paginated

        with patch('jql_search.get_jira_client', return_value=mock_jira_client):
            from jql_search import main

            main(['project = PROJ'])

            captured = capsys.readouterr()
            assert 'more available' in captured.out
            assert 'abc123xyz' in captured.out
            assert '--page-token' in captured.out

    def test_main_with_page_token(self, mock_jira_client, sample_search_results):
        """Test main function using page token."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('jql_search.get_jira_client', return_value=mock_jira_client):
            from jql_search import main

            main(['project = PROJ', '--page-token', 'abc123'])

            call_args = mock_jira_client.search_issues.call_args
            assert call_args[1]['next_page_token'] == 'abc123'

    def test_main_no_jql_or_filter_error(self, capsys):
        """Test that error is raised when neither JQL nor filter provided."""
        with patch('jql_search.get_jira_client'):
            from jql_search import main

            with pytest.raises(SystemExit):
                main([])


@pytest.mark.search
@pytest.mark.unit
class TestJqlSearchErrors:
    """Tests for error handling."""

    def test_jira_error_handling(self, mock_jira_client):
        """Test handling of JIRA API errors."""
        from jira_assistant_skills_lib import JiraError
        mock_jira_client.search_issues.side_effect = JiraError("API Error", status_code=500)

        with patch('jql_search.get_jira_client', return_value=mock_jira_client):
            from jql_search import main

            with pytest.raises(SystemExit) as exc_info:
                main(['project = PROJ'])
            assert exc_info.value.code == 1

    def test_validation_error_handling(self, mock_jira_client):
        """Test handling of validation errors."""
        from jira_assistant_skills_lib import ValidationError
        mock_jira_client.search_issues.side_effect = ValidationError("Invalid JQL")

        with patch('jql_search.get_jira_client', return_value=mock_jira_client):
            from jql_search import main

            with pytest.raises(SystemExit) as exc_info:
                main(['invalid jql query'])
            assert exc_info.value.code == 1

    def test_save_filter_in_json_output(self, mock_jira_client, sample_search_results, capsys):
        """Test that saved filter info is included in JSON output."""
        mock_jira_client.search_issues.return_value = sample_search_results
        saved_filter = {'id': '10050', 'name': 'My Filter'}
        mock_jira_client.create_filter.return_value = saved_filter

        with patch('jql_search.get_jira_client', return_value=mock_jira_client):
            from jql_search import main

            main(['project = PROJ', '--save-as', 'My Filter', '--output', 'json'])

            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert 'savedFilter' in output
            assert output['savedFilter']['id'] == '10050'
