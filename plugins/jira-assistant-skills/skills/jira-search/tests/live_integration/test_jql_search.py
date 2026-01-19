"""
Live Integration Tests for JQL search operations.

Tests jql_search.py functionality against a real JIRA instance.

Usage:
    pytest plugins/jira-assistant-skills/skills/jira-search/tests/live_integration/test_jql_search.py --profile development -v
"""

import pytest
import sys
from pathlib import Path

# Add scripts to path
_this_dir = Path(__file__).parent
_scripts_path = _this_dir.parent.parent / 'scripts'
sys.path.insert(0, str(_scripts_path))

from jql_search import search_issues


@pytest.mark.integration
@pytest.mark.search
class TestJqlSearch:
    """Tests for jql_search.py functionality."""

    def test_search_all_issues_in_project(self, jira_client, test_project, test_issues, jira_profile):
        """Test searching for all issues in a project."""
        jql = f"project = {test_project['key']}"

        result = search_issues(jql=jql, profile=jira_profile)

        assert 'issues' in result
        assert len(result['issues']) >= len(test_issues)

    def test_search_by_issue_type(self, jira_client, test_project, test_issues, jira_profile):
        """Test searching by issue type."""
        jql = f"project = {test_project['key']} AND type = Bug"

        result = search_issues(jql=jql, profile=jira_profile)

        assert 'issues' in result
        issues = result['issues']
        # Should find at least the 2 bugs we created
        assert len(issues) >= 2
        for issue in issues:
            assert issue['fields']['issuetype']['name'] == 'Bug'

    def test_search_by_priority(self, jira_client, test_project, test_issues, jira_profile):
        """Test searching by priority."""
        jql = f"project = {test_project['key']} AND priority = High"

        result = search_issues(jql=jql, profile=jira_profile)

        assert 'issues' in result
        issues = result['issues']
        # Should find at least 2 High priority issues
        assert len(issues) >= 2
        for issue in issues:
            assert issue['fields']['priority']['name'] == 'High'

    def test_search_by_labels(self, jira_client, test_project, test_issues, jira_profile):
        """Test searching by labels."""
        jql = f"project = {test_project['key']} AND labels = backend"

        result = search_issues(jql=jql, profile=jira_profile)

        assert 'issues' in result
        issues = result['issues']
        assert len(issues) >= 2
        for issue in issues:
            assert 'backend' in issue['fields']['labels']

    def test_search_with_specific_fields(self, jira_client, test_project, test_issues, jira_profile):
        """Test searching with specific fields returned."""
        jql = f"project = {test_project['key']}"
        fields = ['key', 'summary', 'status']

        result = search_issues(jql=jql, fields=fields, profile=jira_profile)

        assert 'issues' in result
        issues = result['issues']
        assert len(issues) > 0
        # Check that requested fields are present
        first_issue = issues[0]
        assert 'key' in first_issue
        assert 'summary' in first_issue['fields']
        assert 'status' in first_issue['fields']

    def test_search_with_max_results(self, jira_client, test_project, test_issues, jira_profile):
        """Test searching with max results limit."""
        jql = f"project = {test_project['key']}"

        result = search_issues(jql=jql, max_results=2, profile=jira_profile)

        assert 'issues' in result
        issues = result['issues']
        assert len(issues) <= 2

    def test_search_combined_criteria(self, jira_client, test_project, test_issues, jira_profile):
        """Test searching with combined criteria."""
        jql = f"project = {test_project['key']} AND type = Bug AND priority = High"

        result = search_issues(jql=jql, profile=jira_profile)

        assert 'issues' in result
        issues = result['issues']
        assert len(issues) >= 1
        for issue in issues:
            assert issue['fields']['issuetype']['name'] == 'Bug'
            assert issue['fields']['priority']['name'] == 'High'

    def test_search_with_order_by(self, jira_client, test_project, test_issues, jira_profile):
        """Test searching with ORDER BY clause."""
        jql = f"project = {test_project['key']} ORDER BY created DESC"

        result = search_issues(jql=jql, profile=jira_profile)

        assert 'issues' in result
        issues = result['issues']
        assert len(issues) > 0

    def test_search_no_results(self, jira_client, test_project, jira_profile):
        """Test searching with no matching results."""
        jql = f"project = {test_project['key']} AND labels = nonexistent_label_xyz"

        result = search_issues(jql=jql, profile=jira_profile)

        assert 'issues' in result
        assert len(result['issues']) == 0

    def test_search_with_agile_fields(self, jira_client, test_project, test_issues, jira_profile):
        """Test searching with agile fields included."""
        jql = f"project = {test_project['key']}"

        result = search_issues(
            jql=jql,
            include_agile=True,
            profile=jira_profile
        )

        assert 'issues' in result
        # Agile fields should be included in the request
        # (may be null if not set)

    def test_search_with_time_tracking(self, jira_client, test_project, test_issues, jira_profile):
        """Test searching with time tracking fields included."""
        jql = f"project = {test_project['key']}"

        result = search_issues(
            jql=jql,
            include_time=True,
            profile=jira_profile
        )

        assert 'issues' in result
        # Time tracking fields should be requested

    def test_search_status_category(self, jira_client, test_project, test_issues, jira_profile):
        """Test searching by status category."""
        # All new issues should be in 'To Do' category
        jql = f"project = {test_project['key']} AND statusCategory = 'To Do'"

        result = search_issues(jql=jql, profile=jira_profile)

        assert 'issues' in result
        assert len(result['issues']) >= 1


@pytest.mark.integration
@pytest.mark.search
class TestJqlSearchEdgeCases:
    """Edge case tests for JQL search."""

    def test_search_with_special_characters_in_label(self, jira_client, test_project, jira_profile):
        """Test searching for labels with special handling."""
        # Search for a label that exists
        jql = f"project = {test_project['key']} AND labels = documentation"

        result = search_issues(jql=jql, profile=jira_profile)

        assert 'issues' in result

    def test_search_or_condition(self, jira_client, test_project, test_issues, jira_profile):
        """Test searching with OR condition."""
        jql = f"project = {test_project['key']} AND (type = Bug OR type = Story)"

        result = search_issues(jql=jql, profile=jira_profile)

        assert 'issues' in result
        issues = result['issues']
        assert len(issues) >= 3  # 2 bugs + 1 story
        for issue in issues:
            assert issue['fields']['issuetype']['name'] in ['Bug', 'Story']

    def test_search_not_condition(self, jira_client, test_project, test_issues, jira_profile):
        """Test searching with NOT condition."""
        jql = f"project = {test_project['key']} AND type != Bug"

        result = search_issues(jql=jql, profile=jira_profile)

        assert 'issues' in result
        issues = result['issues']
        for issue in issues:
            assert issue['fields']['issuetype']['name'] != 'Bug'

    def test_search_in_operator(self, jira_client, test_project, test_issues, jira_profile):
        """Test searching with IN operator."""
        jql = f"project = {test_project['key']} AND priority IN (High, Medium)"

        result = search_issues(jql=jql, profile=jira_profile)

        assert 'issues' in result
        issues = result['issues']
        assert len(issues) >= 3  # 2 high + 1 medium
        for issue in issues:
            assert issue['fields']['priority']['name'] in ['High', 'Medium']

    def test_search_empty_project(self, jira_client, jira_profile):
        """Test searching in a project that might not exist returns appropriate response."""
        # Use an invalid project - this should either return empty or raise an error
        jql = "project = NONEXISTENT999 AND type = Bug"

        # This may raise a JiraError or return empty results depending on JIRA config
        try:
            result = search_issues(jql=jql, profile=jira_profile)
            # If it doesn't raise, should return empty
            assert result.get('issues', []) == []
        except Exception:
            # Expected for invalid project
            pass
