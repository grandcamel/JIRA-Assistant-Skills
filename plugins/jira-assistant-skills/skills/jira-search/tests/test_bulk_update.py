"""
Tests for bulk_update.py - Bulk update issues from JQL search results.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add script path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


@pytest.fixture
def sample_search_results():
    """Sample search results for bulk update."""
    return {
        'issues': [
            {
                'key': 'PROJ-123',
                'fields': {
                    'summary': 'Test issue 1',
                    'labels': ['existing-label']
                }
            },
            {
                'key': 'PROJ-124',
                'fields': {
                    'summary': 'Test issue 2',
                    'labels': ['old-label', 'another-label']
                }
            }
        ],
        'total': 2
    }


@pytest.fixture
def sample_search_results_large():
    """Sample search results exceeding max limit."""
    return {
        'issues': [
            {
                'key': f'PROJ-{i}',
                'fields': {
                    'summary': f'Test issue {i}',
                    'labels': []
                }
            }
            for i in range(10)
        ],
        'total': 150  # More than default max
    }


@pytest.mark.search
@pytest.mark.unit
class TestBulkUpdateDryRun:
    """Tests for dry run mode."""

    def test_dry_run_shows_issues(self, mock_jira_client, sample_search_results, capsys):
        """Test that dry run shows issues without updating."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('bulk_update.get_jira_client', return_value=mock_jira_client):
            from bulk_update import bulk_update

            bulk_update('project = PROJ', add_labels=['new-label'], dry_run=True)

            captured = capsys.readouterr()
            assert 'DRY RUN' in captured.out
            assert 'PROJ-123' in captured.out
            assert 'PROJ-124' in captured.out
            mock_jira_client.update_issue.assert_not_called()

    def test_dry_run_no_confirmation_needed(self, mock_jira_client, sample_search_results):
        """Test that dry run doesn't ask for confirmation."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('bulk_update.get_jira_client', return_value=mock_jira_client), \
             patch('builtins.input') as mock_input:
            from bulk_update import bulk_update

            bulk_update('project = PROJ', priority='High', dry_run=True)

            mock_input.assert_not_called()


@pytest.mark.search
@pytest.mark.unit
class TestBulkUpdateLabels:
    """Tests for label operations."""

    def test_add_labels(self, mock_jira_client, sample_search_results):
        """Test adding labels to issues."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('bulk_update.get_jira_client', return_value=mock_jira_client), \
             patch('builtins.input', return_value='yes'):
            from bulk_update import bulk_update

            bulk_update('project = PROJ', add_labels=['new-label', 'another-new'])

            assert mock_jira_client.update_issue.call_count == 2
            # Check first issue call
            first_call = mock_jira_client.update_issue.call_args_list[0]
            labels = first_call[0][1]['labels']
            assert 'new-label' in labels
            assert 'another-new' in labels
            assert 'existing-label' in labels

    def test_remove_labels(self, mock_jira_client, sample_search_results):
        """Test removing labels from issues."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('bulk_update.get_jira_client', return_value=mock_jira_client), \
             patch('builtins.input', return_value='yes'):
            from bulk_update import bulk_update

            bulk_update('project = PROJ', remove_labels=['old-label'])

            second_call = mock_jira_client.update_issue.call_args_list[1]
            labels = second_call[0][1]['labels']
            assert 'old-label' not in labels
            assert 'another-label' in labels

    def test_add_and_remove_labels(self, mock_jira_client, sample_search_results):
        """Test adding and removing labels simultaneously."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('bulk_update.get_jira_client', return_value=mock_jira_client), \
             patch('builtins.input', return_value='yes'):
            from bulk_update import bulk_update

            bulk_update('project = PROJ', add_labels=['new'], remove_labels=['old-label'])

            second_call = mock_jira_client.update_issue.call_args_list[1]
            labels = second_call[0][1]['labels']
            assert 'new' in labels
            assert 'old-label' not in labels


@pytest.mark.search
@pytest.mark.unit
class TestBulkUpdatePriority:
    """Tests for priority updates."""

    def test_set_priority(self, mock_jira_client, sample_search_results):
        """Test setting priority on issues."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('bulk_update.get_jira_client', return_value=mock_jira_client), \
             patch('builtins.input', return_value='yes'):
            from bulk_update import bulk_update

            bulk_update('project = PROJ', priority='High')

            assert mock_jira_client.update_issue.call_count == 2
            first_call = mock_jira_client.update_issue.call_args_list[0]
            assert first_call[0][1]['priority'] == {'name': 'High'}


@pytest.mark.search
@pytest.mark.unit
class TestBulkUpdateConfirmation:
    """Tests for confirmation handling."""

    def test_cancelled_on_no(self, mock_jira_client, sample_search_results, capsys):
        """Test that update is cancelled when user says no."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('bulk_update.get_jira_client', return_value=mock_jira_client), \
             patch('builtins.input', return_value='no'):
            from bulk_update import bulk_update

            bulk_update('project = PROJ', priority='High')

            captured = capsys.readouterr()
            assert 'cancelled' in captured.out.lower()
            mock_jira_client.update_issue.assert_not_called()

    def test_proceeds_on_yes(self, mock_jira_client, sample_search_results):
        """Test that update proceeds when user says yes."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('bulk_update.get_jira_client', return_value=mock_jira_client), \
             patch('builtins.input', return_value='yes'):
            from bulk_update import bulk_update

            bulk_update('project = PROJ', priority='High')

            assert mock_jira_client.update_issue.call_count == 2

    def test_proceeds_on_y(self, mock_jira_client, sample_search_results):
        """Test that update proceeds when user says y."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('bulk_update.get_jira_client', return_value=mock_jira_client), \
             patch('builtins.input', return_value='y'):
            from bulk_update import bulk_update

            bulk_update('project = PROJ', priority='Medium')

            assert mock_jira_client.update_issue.call_count == 2


@pytest.mark.search
@pytest.mark.unit
class TestBulkUpdateNoIssues:
    """Tests for empty results."""

    def test_no_issues_found(self, mock_jira_client, capsys):
        """Test handling when no issues found."""
        mock_jira_client.search_issues.return_value = {'issues': [], 'total': 0}

        with patch('bulk_update.get_jira_client', return_value=mock_jira_client):
            from bulk_update import bulk_update

            bulk_update('project = NONEXISTENT', priority='High')

            captured = capsys.readouterr()
            assert 'No issues found' in captured.out
            mock_jira_client.update_issue.assert_not_called()


@pytest.mark.search
@pytest.mark.unit
class TestBulkUpdateLimits:
    """Tests for max issue limits."""

    def test_warns_on_exceeding_max(self, mock_jira_client, sample_search_results_large, capsys):
        """Test warning when total exceeds max."""
        mock_jira_client.search_issues.return_value = sample_search_results_large

        with patch('bulk_update.get_jira_client', return_value=mock_jira_client), \
             patch('builtins.input', return_value='no'):
            from bulk_update import bulk_update

            bulk_update('project = PROJ', priority='High', max_issues=10)

            captured = capsys.readouterr()
            assert 'Found 150 issues' in captured.out
            assert 'limiting to first 10' in captured.out

    def test_custom_max_issues(self, mock_jira_client, sample_search_results):
        """Test custom max issues parameter."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('bulk_update.get_jira_client', return_value=mock_jira_client), \
             patch('builtins.input', return_value='no'):
            from bulk_update import bulk_update

            bulk_update('project = PROJ', priority='High', max_issues=50)

            call_args = mock_jira_client.search_issues.call_args
            assert call_args[1]['max_results'] == 50


@pytest.mark.search
@pytest.mark.unit
class TestBulkUpdateErrors:
    """Tests for error handling."""

    def test_partial_failure(self, mock_jira_client, sample_search_results, capsys):
        """Test handling of partial failures."""
        mock_jira_client.search_issues.return_value = sample_search_results
        # First update succeeds, second fails
        mock_jira_client.update_issue.side_effect = [None, Exception("Update failed")]

        with patch('bulk_update.get_jira_client', return_value=mock_jira_client), \
             patch('builtins.input', return_value='yes'):
            from bulk_update import bulk_update

            bulk_update('project = PROJ', priority='High')

            captured = capsys.readouterr()
            assert 'Updated 1' in captured.out
            assert 'Failed: 1' in captured.out

    def test_all_fail(self, mock_jira_client, sample_search_results, capsys):
        """Test handling when all updates fail."""
        mock_jira_client.search_issues.return_value = sample_search_results
        mock_jira_client.update_issue.side_effect = Exception("Update failed")

        with patch('bulk_update.get_jira_client', return_value=mock_jira_client), \
             patch('builtins.input', return_value='yes'):
            from bulk_update import bulk_update

            bulk_update('project = PROJ', priority='High')

            captured = capsys.readouterr()
            assert 'Updated 0' in captured.out
            assert 'Failed: 2' in captured.out


@pytest.mark.search
@pytest.mark.unit
class TestBulkUpdateMain:
    """Tests for main() function."""

    def test_main_with_add_labels(self, mock_jira_client, sample_search_results):
        """Test main with add-labels argument."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('bulk_update.get_jira_client', return_value=mock_jira_client), \
             patch('builtins.input', return_value='yes'):
            from bulk_update import main

            main(['project = PROJ', '--add-labels', 'label1,label2', '--dry-run'])

    def test_main_with_remove_labels(self, mock_jira_client, sample_search_results):
        """Test main with remove-labels argument."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('bulk_update.get_jira_client', return_value=mock_jira_client), \
             patch('builtins.input', return_value='yes'):
            from bulk_update import main

            main(['project = PROJ', '--remove-labels', 'old-label', '--dry-run'])

    def test_main_with_priority(self, mock_jira_client, sample_search_results):
        """Test main with priority argument."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('bulk_update.get_jira_client', return_value=mock_jira_client), \
             patch('builtins.input', return_value='yes'):
            from bulk_update import main

            main(['project = PROJ', '--priority', 'High', '--dry-run'])

    def test_main_jira_error(self, mock_jira_client):
        """Test main function error handling."""
        from jira_assistant_skills_lib import JiraError
        mock_jira_client.search_issues.side_effect = JiraError("API Error", status_code=500)

        with patch('bulk_update.get_jira_client', return_value=mock_jira_client):
            from bulk_update import main

            with pytest.raises(SystemExit) as exc_info:
                main(['project = PROJ', '--priority', 'High'])
            assert exc_info.value.code == 1

    def test_main_keyboard_interrupt(self, mock_jira_client, sample_search_results):
        """Test main function handles keyboard interrupt."""
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch('bulk_update.get_jira_client', return_value=mock_jira_client), \
             patch('builtins.input', side_effect=KeyboardInterrupt):
            from bulk_update import main

            with pytest.raises(SystemExit) as exc_info:
                main(['project = PROJ', '--priority', 'High'])
            assert exc_info.value.code == 0
