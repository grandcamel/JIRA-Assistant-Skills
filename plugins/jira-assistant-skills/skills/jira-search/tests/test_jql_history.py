"""
Tests for jql_history.py - Manage JQL query history and cache.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add script path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


@pytest.fixture
def sample_history():
    """Sample history data."""
    return {
        'queries': [
            {
                'id': 1,
                'jql': 'project = PROJ',
                'name': 'my-project',
                'description': 'All issues in project',
                'created': '2024-01-15T10:00:00',
                'last_used': '2024-01-16T14:00:00',
                'use_count': 5
            },
            {
                'id': 2,
                'jql': 'assignee = currentUser()',
                'name': 'my-issues',
                'description': None,
                'created': '2024-01-14T09:00:00',
                'last_used': None,
                'use_count': 0
            },
            {
                'id': 3,
                'jql': 'status = Open',
                'name': None,
                'description': None,
                'created': '2024-01-13T08:00:00',
                'last_used': '2024-01-17T11:00:00',
                'use_count': 10
            }
        ],
        'version': 1
    }


@pytest.fixture
def temp_history_file(tmp_path, sample_history):
    """Create a temporary history file."""
    history_file = tmp_path / 'jql_history.json'
    with open(history_file, 'w') as f:
        json.dump(sample_history, f)
    return history_file


@pytest.mark.search
@pytest.mark.unit
class TestLoadHistory:
    """Tests for load_history function."""

    def test_load_existing_history(self, temp_history_file, sample_history):
        """Test loading existing history file."""
        with patch('jql_history.HISTORY_FILE', temp_history_file):
            from jql_history import load_history

            history = load_history()

            assert len(history['queries']) == 3
            assert history['queries'][0]['name'] == 'my-project'

    def test_load_nonexistent_file(self, tmp_path):
        """Test loading when file doesn't exist."""
        nonexistent = tmp_path / 'nonexistent.json'

        with patch('jql_history.HISTORY_FILE', nonexistent):
            from jql_history import load_history

            history = load_history()

            assert history == {'queries': [], 'version': 1}

    def test_load_corrupted_json(self, tmp_path):
        """Test loading corrupted JSON file."""
        corrupted_file = tmp_path / 'corrupted.json'
        with open(corrupted_file, 'w') as f:
            f.write('not valid json {{{')

        with patch('jql_history.HISTORY_FILE', corrupted_file):
            from jql_history import load_history

            history = load_history()

            assert history == {'queries': [], 'version': 1}


@pytest.mark.search
@pytest.mark.unit
class TestSaveHistory:
    """Tests for save_history function."""

    def test_save_history(self, tmp_path, sample_history):
        """Test saving history to file."""
        history_file = tmp_path / '.jira-skills' / 'jql_history.json'

        with patch('jql_history.HISTORY_FILE', history_file), \
             patch('jql_history.HISTORY_DIR', tmp_path / '.jira-skills'):
            from jql_history import save_history

            save_history(sample_history)

            assert history_file.exists()
            with open(history_file) as f:
                saved = json.load(f)
            assert len(saved['queries']) == 3


@pytest.mark.search
@pytest.mark.unit
class TestAddQuery:
    """Tests for add_query function."""

    def test_add_query_basic(self, tmp_path):
        """Test adding a basic query."""
        history_file = tmp_path / 'history.json'
        with open(history_file, 'w') as f:
            json.dump({'queries': [], 'version': 1}, f)

        with patch('jql_history.HISTORY_FILE', history_file), \
             patch('jql_history.HISTORY_DIR', tmp_path):
            from jql_history import add_query

            entry = add_query('project = PROJ', name='test-query', description='Test')

            assert entry['id'] == 1
            assert entry['jql'] == 'project = PROJ'
            assert entry['name'] == 'test-query'
            assert entry['use_count'] == 0

    def test_add_query_duplicate_name_error(self, temp_history_file, sample_history):
        """Test error on duplicate query name."""
        with patch('jql_history.HISTORY_FILE', temp_history_file), \
             patch('jql_history.HISTORY_DIR', temp_history_file.parent):
            from jql_history import add_query

            from jira_assistant_skills_lib import ValidationError

            with pytest.raises(ValidationError) as exc_info:
                add_query('status = Done', name='my-project')
            assert 'already exists' in str(exc_info.value)

    def test_add_query_without_name(self, tmp_path):
        """Test adding a query without a name."""
        history_file = tmp_path / 'history.json'
        with open(history_file, 'w') as f:
            json.dump({'queries': [], 'version': 1}, f)

        with patch('jql_history.HISTORY_FILE', history_file), \
             patch('jql_history.HISTORY_DIR', tmp_path):
            from jql_history import add_query

            entry = add_query('status = Open')

            assert entry['name'] is None


@pytest.mark.search
@pytest.mark.unit
class TestGetQuery:
    """Tests for get_query function."""

    def test_get_query_by_id(self, temp_history_file):
        """Test getting query by ID."""
        with patch('jql_history.HISTORY_FILE', temp_history_file):
            from jql_history import get_query

            query = get_query('1')

            assert query is not None
            assert query['jql'] == 'project = PROJ'

    def test_get_query_by_name(self, temp_history_file):
        """Test getting query by name."""
        with patch('jql_history.HISTORY_FILE', temp_history_file):
            from jql_history import get_query

            query = get_query('my-issues')

            assert query is not None
            assert query['jql'] == 'assignee = currentUser()'

    def test_get_query_not_found(self, temp_history_file):
        """Test getting non-existent query."""
        with patch('jql_history.HISTORY_FILE', temp_history_file):
            from jql_history import get_query

            query = get_query('999')

            assert query is None

    def test_get_query_by_invalid_name(self, temp_history_file):
        """Test getting query with non-existent name."""
        with patch('jql_history.HISTORY_FILE', temp_history_file):
            from jql_history import get_query

            query = get_query('nonexistent-name')

            assert query is None


@pytest.mark.search
@pytest.mark.unit
class TestUpdateQueryUsage:
    """Tests for update_query_usage function."""

    def test_update_usage(self, temp_history_file):
        """Test updating query usage statistics."""
        with patch('jql_history.HISTORY_FILE', temp_history_file), \
             patch('jql_history.HISTORY_DIR', temp_history_file.parent):
            from jql_history import load_history, update_query_usage

            update_query_usage(2)

            history = load_history()
            query = next(q for q in history['queries'] if q['id'] == 2)
            assert query['use_count'] == 1
            assert query['last_used'] is not None


@pytest.mark.search
@pytest.mark.unit
class TestDeleteQuery:
    """Tests for delete_query function."""

    def test_delete_by_id(self, temp_history_file):
        """Test deleting query by ID."""
        with patch('jql_history.HISTORY_FILE', temp_history_file), \
             patch('jql_history.HISTORY_DIR', temp_history_file.parent):
            from jql_history import delete_query, load_history

            result = delete_query('1')

            assert result is True
            history = load_history()
            assert len(history['queries']) == 2

    def test_delete_by_name(self, temp_history_file):
        """Test deleting query by name."""
        with patch('jql_history.HISTORY_FILE', temp_history_file), \
             patch('jql_history.HISTORY_DIR', temp_history_file.parent):
            from jql_history import delete_query, load_history

            result = delete_query('my-project')

            assert result is True
            history = load_history()
            assert len(history['queries']) == 2

    def test_delete_not_found(self, temp_history_file):
        """Test deleting non-existent query."""
        with patch('jql_history.HISTORY_FILE', temp_history_file):
            from jql_history import delete_query

            result = delete_query('999')

            assert result is False


@pytest.mark.search
@pytest.mark.unit
class TestClearHistory:
    """Tests for clear_history function."""

    def test_clear_all(self, temp_history_file):
        """Test clearing all history."""
        with patch('jql_history.HISTORY_FILE', temp_history_file), \
             patch('jql_history.HISTORY_DIR', temp_history_file.parent):
            from jql_history import clear_history, load_history

            count = clear_history()

            assert count == 3
            history = load_history()
            assert len(history['queries']) == 0


@pytest.mark.search
@pytest.mark.unit
class TestListQueries:
    """Tests for list_queries function."""

    def test_list_all(self, temp_history_file):
        """Test listing all queries."""
        with patch('jql_history.HISTORY_FILE', temp_history_file):
            from jql_history import list_queries

            queries = list_queries()

            assert len(queries) == 3

    def test_list_top_n(self, temp_history_file):
        """Test listing top N queries."""
        with patch('jql_history.HISTORY_FILE', temp_history_file):
            from jql_history import list_queries

            queries = list_queries(top=2)

            assert len(queries) == 2

    def test_list_sort_by_use_count(self, temp_history_file):
        """Test sorting by use count."""
        with patch('jql_history.HISTORY_FILE', temp_history_file):
            from jql_history import list_queries

            queries = list_queries(sort_by='use_count')

            assert queries[0]['use_count'] == 10  # ID 3 has highest use_count

    def test_list_sort_by_created(self, temp_history_file):
        """Test sorting by creation date."""
        with patch('jql_history.HISTORY_FILE', temp_history_file):
            from jql_history import list_queries

            queries = list_queries(sort_by='created')

            # Most recent first
            assert queries[0]['id'] == 1


@pytest.mark.search
@pytest.mark.unit
class TestExportHistory:
    """Tests for export_history function."""

    def test_export(self, temp_history_file, tmp_path):
        """Test exporting history."""
        output_file = tmp_path / 'export.json'

        with patch('jql_history.HISTORY_FILE', temp_history_file):
            from jql_history import export_history

            count = export_history(str(output_file))

            assert count == 3
            assert output_file.exists()
            with open(output_file) as f:
                data = json.load(f)
            assert len(data['queries']) == 3


@pytest.mark.search
@pytest.mark.unit
class TestImportHistory:
    """Tests for import_history function."""

    def test_import_merge(self, tmp_path, sample_history):
        """Test importing and merging history."""
        history_file = tmp_path / 'history.json'
        import_file = tmp_path / 'import.json'

        # Create existing history with 1 query
        existing = {'queries': [{'id': 1, 'jql': 'existing query', 'name': 'existing'}], 'version': 1}
        with open(history_file, 'w') as f:
            json.dump(existing, f)

        # Create import file
        with open(import_file, 'w') as f:
            json.dump(sample_history, f)

        with patch('jql_history.HISTORY_FILE', history_file), \
             patch('jql_history.HISTORY_DIR', tmp_path):
            from jql_history import import_history, load_history

            count = import_history(str(import_file), merge=True)

            assert count == 3
            history = load_history()
            assert len(history['queries']) == 4  # 1 existing + 3 imported

    def test_import_replace(self, tmp_path, sample_history):
        """Test importing and replacing history."""
        history_file = tmp_path / 'history.json'
        import_file = tmp_path / 'import.json'

        # Create existing history
        existing = {'queries': [{'id': 1, 'jql': 'existing query'}], 'version': 1}
        with open(history_file, 'w') as f:
            json.dump(existing, f)

        # Create import file
        with open(import_file, 'w') as f:
            json.dump(sample_history, f)

        with patch('jql_history.HISTORY_FILE', history_file), \
             patch('jql_history.HISTORY_DIR', tmp_path):
            from jql_history import import_history, load_history

            count = import_history(str(import_file), merge=False)

            assert count == 3
            history = load_history()
            assert len(history['queries']) == 3  # Only imported queries




@pytest.mark.search
@pytest.mark.unit
class TestFormatQueryList:
    """Tests for format_query_list function."""

    def test_format_list(self, sample_history):
        """Test formatting query list for display."""
        from jql_history import format_query_list

        output = format_query_list(sample_history['queries'])

        assert 'my-project' in output
        assert 'project = PROJ' in output


@pytest.mark.search
@pytest.mark.unit
class TestJqlHistoryMain:
    """Tests for main() function."""

    def test_main_list(self, temp_history_file, capsys):
        """Test main with --list."""
        with patch('jql_history.HISTORY_FILE', temp_history_file):
            from jql_history import main

            main(['--list'])

            captured = capsys.readouterr()
            assert 'my-project' in captured.out

    def test_main_add(self, tmp_path, capsys):
        """Test main with --add."""
        history_file = tmp_path / 'history.json'
        with open(history_file, 'w') as f:
            json.dump({'queries': [], 'version': 1}, f)

        with patch('jql_history.HISTORY_FILE', history_file), \
             patch('jql_history.HISTORY_DIR', tmp_path):
            from jql_history import main

            main(['--add', 'project = TEST', '--name', 'test-query'])

            captured = capsys.readouterr()
            assert 'Added' in captured.out or 'test-query' in captured.out

    def test_main_delete(self, temp_history_file, capsys):
        """Test main with --delete."""
        with patch('jql_history.HISTORY_FILE', temp_history_file), \
             patch('jql_history.HISTORY_DIR', temp_history_file.parent):
            from jql_history import main

            main(['--delete', '1'])

            captured = capsys.readouterr()
            assert 'Deleted' in captured.out

    def test_main_clear(self, temp_history_file, capsys):
        """Test main with --clear."""
        with patch('jql_history.HISTORY_FILE', temp_history_file), \
             patch('jql_history.HISTORY_DIR', temp_history_file.parent), \
             patch('builtins.input', return_value='yes'):
            from jql_history import main

            main(['--clear'])

            captured = capsys.readouterr()
            assert 'Cleared' in captured.out

    def test_main_run(self, temp_history_file, mock_jira_client, capsys):
        """Test main with --run."""
        mock_jira_client.search_issues.return_value = {
            'issues': [{'key': 'PROJ-1', 'fields': {'summary': 'Test'}}],
            'total': 1
        }

        with patch('jql_history.HISTORY_FILE', temp_history_file), \
             patch('jql_history.HISTORY_DIR', temp_history_file.parent), \
             patch('jql_history.get_jira_client', return_value=mock_jira_client):
            from jql_history import main

            main(['--run', '1'])

            captured = capsys.readouterr()
            assert 'Found' in captured.out or 'PROJ-1' in captured.out
