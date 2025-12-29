"""
Live Integration Tests: Bulk Time Logging

Tests for bulk time logging operations against a real JIRA instance.
"""

import pytest
import uuid
import sys
from pathlib import Path

# Add scripts to path for testing
skills_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(skills_dir / 'scripts'))

from bulk_log_time import bulk_log_time


@pytest.mark.integration
@pytest.mark.time
@pytest.mark.bulk
class TestBulkLogTime:
    """Tests for bulk time logging."""

    def test_bulk_log_time_multiple_issues(self, jira_client, multiple_issues):
        """Test logging time to multiple issues at once."""
        issue_keys = [i['key'] for i in multiple_issues]

        result = bulk_log_time(
            jira_client,
            issues=issue_keys,
            time_spent='30m'
        )

        assert result['success_count'] == 3
        assert result['failure_count'] == 0
        assert result['total_seconds'] == 1800 * 3  # 30m * 3 issues

    def test_bulk_log_time_with_comment(self, jira_client, multiple_issues):
        """Test bulk logging with comment."""
        issue_keys = [i['key'] for i in multiple_issues]

        result = bulk_log_time(
            jira_client,
            issues=issue_keys,
            time_spent='15m',
            comment='Sprint planning meeting'
        )

        assert result['success_count'] == 3

        # Verify comments were added
        for entry in result['entries']:
            worklogs = jira_client.get_worklogs(entry['issue'])
            latest_worklog = worklogs['worklogs'][-1]
            assert 'comment' in latest_worklog

    def test_bulk_log_time_dry_run(self, jira_client, multiple_issues):
        """Test bulk logging in dry run mode."""
        issue_keys = [i['key'] for i in multiple_issues]

        result = bulk_log_time(
            jira_client,
            issues=issue_keys,
            time_spent='1h',
            dry_run=True
        )

        assert result['dry_run'] is True
        assert result['would_log_count'] == 3
        assert result['would_log_seconds'] == 3600 * 3
        assert 'preview' in result
        assert len(result['preview']) == 3

    def test_bulk_log_time_partial_failure(self, jira_client, multiple_issues, test_project):
        """Test bulk logging with some invalid issues."""
        issue_keys = [i['key'] for i in multiple_issues]
        # Add invalid issue key
        issue_keys.append('INVALID-999999')

        result = bulk_log_time(
            jira_client,
            issues=issue_keys,
            time_spent='30m'
        )

        assert result['success_count'] == 3
        assert result['failure_count'] == 1
        assert len(result['failures']) == 1

    def test_bulk_log_time_empty_list(self, jira_client):
        """Test bulk logging with empty issue list."""
        result = bulk_log_time(
            jira_client,
            issues=[],
            time_spent='30m'
        )

        assert result['success_count'] == 0
        assert result['failure_count'] == 0
        assert result['total_seconds'] == 0


@pytest.mark.integration
@pytest.mark.time
@pytest.mark.bulk
class TestBulkLogTimeJQL:
    """Tests for bulk time logging using JQL queries."""

    def test_bulk_log_time_with_jql(self, jira_client, multiple_issues, test_project):
        """Test logging time to issues found via JQL."""
        # Wait for issues to be indexed with retry loop
        import time
        issue_keys = [i['key'] for i in multiple_issues]
        jql = f'project = {test_project["key"]} AND type = Task'

        # Retry loop for eventual consistency
        max_retries = 10
        for attempt in range(max_retries):
            search_result = jira_client.search_issues(jql, fields=['key'], max_results=100)
            found_keys = [i['key'] for i in search_result.get('issues', [])]
            if all(key in found_keys for key in issue_keys):
                break
            time.sleep(1)

        result = bulk_log_time(
            jira_client,
            jql=jql,
            time_spent='15m'
        )

        # Should find at least the 3 test issues
        assert result['success_count'] >= 3

    def test_bulk_log_time_jql_dry_run(self, jira_client, multiple_issues, test_project):
        """Test dry run with JQL query."""
        # Wait for issues to be indexed with retry loop
        import time
        issue_keys = [i['key'] for i in multiple_issues]
        jql = f'project = {test_project["key"]} AND type = Task'

        # Retry loop for eventual consistency
        max_retries = 10
        for attempt in range(max_retries):
            search_result = jira_client.search_issues(jql, fields=['key'], max_results=100)
            found_keys = [i['key'] for i in search_result.get('issues', [])]
            if all(key in found_keys for key in issue_keys):
                break
            time.sleep(1)

        result = bulk_log_time(
            jira_client,
            jql=jql,
            time_spent='30m',
            dry_run=True
        )

        assert result['dry_run'] is True
        assert result['would_log_count'] >= 3

    def test_bulk_log_time_jql_no_results(self, jira_client, test_project):
        """Test JQL query that returns no results."""
        jql = f'project = {test_project["key"]} AND summary ~ "NONEXISTENT_STRING_12345"'

        result = bulk_log_time(
            jira_client,
            jql=jql,
            time_spent='30m'
        )

        assert result['success_count'] == 0
        assert result['failure_count'] == 0


@pytest.mark.integration
@pytest.mark.time
@pytest.mark.bulk
class TestBulkLogTimeValidation:
    """Tests for bulk time logging input validation."""

    def test_bulk_log_time_invalid_format(self, jira_client, multiple_issues):
        """Test bulk logging with invalid time format."""
        from jira_assistant_skills_lib import ValidationError

        issue_keys = [i['key'] for i in multiple_issues]

        with pytest.raises(ValidationError):
            bulk_log_time(
                jira_client,
                issues=issue_keys,
                time_spent='invalid'
            )

    def test_bulk_log_time_various_formats(self, jira_client, test_project):
        """Test bulk logging with various valid time formats."""
        test_cases = [
            ('30m', 1800),
            ('1h', 3600),
            ('1h 30m', 5400),
            ('2h', 7200),
        ]

        for time_format, expected_seconds in test_cases:
            issue = jira_client.create_issue({
                'project': {'key': test_project['key']},
                'summary': f'Format Test {time_format} {uuid.uuid4().hex[:8]}',
                'issuetype': {'name': 'Task'}
            })

            try:
                result = bulk_log_time(
                    jira_client,
                    issues=[issue['key']],
                    time_spent=time_format
                )

                assert result['success_count'] == 1
                assert result['total_seconds'] == expected_seconds
            finally:
                jira_client.delete_issue(issue['key'])


@pytest.mark.integration
@pytest.mark.time
@pytest.mark.bulk
class TestBulkLogTimeResults:
    """Tests for bulk time logging result structure."""

    def test_result_structure(self, jira_client, multiple_issues):
        """Test that result has expected structure."""
        issue_keys = [i['key'] for i in multiple_issues]

        result = bulk_log_time(
            jira_client,
            issues=issue_keys,
            time_spent='30m'
        )

        assert 'success_count' in result
        assert 'failure_count' in result
        assert 'total_seconds' in result
        assert 'total_formatted' in result
        assert 'entries' in result
        assert 'failures' in result
        assert 'dry_run' in result

    def test_entry_structure(self, jira_client, multiple_issues):
        """Test that each entry has expected structure."""
        issue_keys = [i['key'] for i in multiple_issues]

        result = bulk_log_time(
            jira_client,
            issues=issue_keys,
            time_spent='30m'
        )

        for entry in result['entries']:
            assert 'issue' in entry
            assert 'worklog_id' in entry
            assert 'time_spent' in entry

    def test_dry_run_preview_structure(self, jira_client, multiple_issues):
        """Test that dry run preview has expected structure."""
        issue_keys = [i['key'] for i in multiple_issues]

        result = bulk_log_time(
            jira_client,
            issues=issue_keys,
            time_spent='30m',
            dry_run=True
        )

        for preview in result['preview']:
            assert 'issue' in preview
            assert 'summary' in preview
            assert 'time_to_log' in preview

    def test_total_formatted(self, jira_client, multiple_issues):
        """Test that total_formatted is human-readable."""
        issue_keys = [i['key'] for i in multiple_issues]

        result = bulk_log_time(
            jira_client,
            issues=issue_keys,
            time_spent='1h'
        )

        # 3 issues * 1h = 3h
        assert '3h' in result['total_formatted']
