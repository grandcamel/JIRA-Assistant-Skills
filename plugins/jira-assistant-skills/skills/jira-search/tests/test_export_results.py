"""
Tests for export_results.py - Export JQL search results to file.
"""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add script path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


@pytest.fixture
def sample_search_results():
    """Sample search results for export."""
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
                    'reporter': {'displayName': 'Jane Doe'},
                    'created': '2024-01-15T10:30:00.000+0000',
                    'updated': '2024-01-16T14:00:00.000+0000'
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
                    'reporter': {'displayName': 'John Smith'},
                    'created': '2024-01-14T09:00:00.000+0000',
                    'updated': '2024-01-17T11:00:00.000+0000'
                }
            }
        ],
        'total': 2
    }


@pytest.fixture
def sample_search_results_with_lists():
    """Sample search results with list fields."""
    return {
        'issues': [
            {
                'key': 'PROJ-125',
                'fields': {
                    'summary': 'Issue with labels',
                    'status': {'name': 'Open'},
                    'labels': ['urgent', 'needs-review', 'bug'],
                    'components': [{'name': 'Backend'}, {'name': 'API'}]
                }
            }
        ],
        'total': 1
    }


@pytest.mark.search
@pytest.mark.unit
class TestExportResults:
    """Tests for export_results function."""

    def test_export_csv_basic(self, mock_jira_client, sample_search_results):
        """Test basic CSV export."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('export_results.get_jira_client', return_value=mock_jira_client), \
             patch('export_results.export_csv') as mock_export_csv:
            from export_results import export_results

            export_results('project = PROJ', '/tmp/test.csv')

            mock_export_csv.assert_called_once()
            call_args = mock_export_csv.call_args
            data = call_args[0][0]
            assert len(data) == 2
            assert data[0]['key'] == 'PROJ-123'

    def test_export_json_basic(self, mock_jira_client, sample_search_results):
        """Test basic JSON export."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name

        try:
            with patch('export_results.get_jira_client', return_value=mock_jira_client):
                from export_results import export_results

                export_results('project = PROJ', output_path, format_type='json')

                with open(output_path) as f:
                    data = json.load(f)
                    assert data['total'] == 2
                    assert len(data['issues']) == 2
        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_export_with_custom_fields(self, mock_jira_client, sample_search_results):
        """Test export with custom field list."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('export_results.get_jira_client', return_value=mock_jira_client), \
             patch('export_results.export_csv'):
            from export_results import export_results

            export_results('project = PROJ', '/tmp/test.csv', fields=['key', 'summary', 'status'])

            mock_jira_client.search_issues.assert_called_with(
                'project = PROJ',
                fields=['key', 'summary', 'status'],
                max_results=1000,
                start_at=0
            )

    def test_export_with_max_results(self, mock_jira_client, sample_search_results):
        """Test export with custom max results."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('export_results.get_jira_client', return_value=mock_jira_client), \
             patch('export_results.export_csv'):
            from export_results import export_results

            export_results('project = PROJ', '/tmp/test.csv', max_results=500)

            call_args = mock_jira_client.search_issues.call_args
            assert call_args[1]['max_results'] == 500

    def test_export_no_results(self, mock_jira_client, capsys):
        """Test export when no issues found."""
        mock_jira_client.search_issues.return_value = {'issues': [], 'total': 0}

        with patch('export_results.get_jira_client', return_value=mock_jira_client):
            from export_results import export_results

            export_results('project = NONEXISTENT', '/tmp/test.csv')

            captured = capsys.readouterr()
            assert 'No issues found' in captured.out

    def test_export_extracts_display_name(self, mock_jira_client, sample_search_results):
        """Test that displayName is extracted from nested objects."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('export_results.get_jira_client', return_value=mock_jira_client), \
             patch('export_results.export_csv') as mock_export_csv:
            from export_results import export_results

            export_results('project = PROJ', '/tmp/test.csv')

            call_args = mock_export_csv.call_args
            data = call_args[0][0]
            assert data[0]['assignee'] == 'John Smith'

    def test_export_extracts_name(self, mock_jira_client, sample_search_results):
        """Test that name is extracted from nested objects."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('export_results.get_jira_client', return_value=mock_jira_client), \
             patch('export_results.export_csv') as mock_export_csv:
            from export_results import export_results

            export_results('project = PROJ', '/tmp/test.csv')

            call_args = mock_export_csv.call_args
            data = call_args[0][0]
            assert data[0]['status'] == 'Open'
            assert data[0]['priority'] == 'High'

    def test_export_handles_list_fields(self, mock_jira_client, sample_search_results_with_lists):
        """Test that list fields are joined with commas."""
        mock_jira_client.search_issues.return_value = sample_search_results_with_lists

        with patch('export_results.get_jira_client', return_value=mock_jira_client), \
             patch('export_results.export_csv') as mock_export_csv:
            from export_results import export_results

            export_results('project = PROJ', '/tmp/test.csv', fields=['key', 'summary', 'labels', 'components'])

            call_args = mock_export_csv.call_args
            data = call_args[0][0]
            assert 'urgent' in data[0]['labels']
            assert 'Backend' in data[0]['components']

    def test_export_handles_null_assignee(self, mock_jira_client, sample_search_results):
        """Test that null assignee is handled."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('export_results.get_jira_client', return_value=mock_jira_client), \
             patch('export_results.export_csv') as mock_export_csv:
            from export_results import export_results

            export_results('project = PROJ', '/tmp/test.csv')

            call_args = mock_export_csv.call_args
            data = call_args[0][0]
            # Second issue has None assignee
            assert data[1]['assignee'] is None or data[1]['assignee'] == ''

    def test_export_with_profile(self, mock_jira_client, sample_search_results):
        """Test export with profile parameter."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('export_results.get_jira_client', return_value=mock_jira_client) as mock_get_client, \
             patch('export_results.export_csv'):
            from export_results import export_results

            export_results('project = PROJ', '/tmp/test.csv', profile='development')

            mock_get_client.assert_called_with('development')


@pytest.mark.search
@pytest.mark.unit
class TestExportResultsMain:
    """Tests for main() function."""

    def test_main_csv_export(self, mock_jira_client, sample_search_results, capsys):
        """Test main function with CSV export."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('export_results.get_jira_client', return_value=mock_jira_client), \
             patch('export_results.export_csv'):
            from export_results import main

            main(['project = PROJ', '--output', '/tmp/test.csv'])

            captured = capsys.readouterr()
            assert 'Exported' in captured.out

    def test_main_json_export(self, mock_jira_client, sample_search_results, capsys):
        """Test main function with JSON export."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name

        try:
            with patch('export_results.get_jira_client', return_value=mock_jira_client):
                from export_results import main

                main(['project = PROJ', '--output', output_path, '--format', 'json'])

                captured = capsys.readouterr()
                assert 'Exported' in captured.out
        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_main_with_fields(self, mock_jira_client, sample_search_results):
        """Test main function with custom fields."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('export_results.get_jira_client', return_value=mock_jira_client), \
             patch('export_results.export_csv'):
            from export_results import main

            main(['project = PROJ', '--output', '/tmp/test.csv', '--fields', 'key,summary,status'])

            call_args = mock_jira_client.search_issues.call_args
            assert call_args[1]['fields'] == ['key', 'summary', 'status']

    def test_main_with_max_results(self, mock_jira_client, sample_search_results):
        """Test main function with max results."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('export_results.get_jira_client', return_value=mock_jira_client), \
             patch('export_results.export_csv'):
            from export_results import main

            main(['project = PROJ', '--output', '/tmp/test.csv', '--max-results', '250'])

            call_args = mock_jira_client.search_issues.call_args
            assert call_args[1]['max_results'] == 250


@pytest.mark.search
@pytest.mark.unit
class TestExportResultsErrors:
    """Tests for error handling."""

    def test_jira_error_handling(self, mock_jira_client):
        """Test handling of JIRA API errors."""
        from jira_assistant_skills_lib import JiraError
        mock_jira_client.search_issues.side_effect = JiraError("API Error", status_code=500)

        with patch('export_results.get_jira_client', return_value=mock_jira_client):
            from export_results import main

            with pytest.raises(SystemExit) as exc_info:
                main(['project = PROJ', '--output', '/tmp/test.csv'])
            assert exc_info.value.code == 1

    def test_validation_error_handling(self, mock_jira_client):
        """Test handling of validation errors."""
        from jira_assistant_skills_lib import ValidationError
        mock_jira_client.search_issues.side_effect = ValidationError("Invalid JQL")

        with patch('export_results.get_jira_client', return_value=mock_jira_client):
            from export_results import main

            with pytest.raises(SystemExit) as exc_info:
                main(['invalid query', '--output', '/tmp/test.csv'])
            assert exc_info.value.code == 1
