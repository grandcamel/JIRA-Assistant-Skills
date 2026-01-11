"""
Live Integration Tests for JQL validation.

Tests jql_validate.py functionality against a real JIRA instance.

Usage:
    pytest plugins/jira-assistant-skills/skills/jira-search/tests/live_integration/test_jql_validation.py --profile development -v
"""

import pytest
import sys
from pathlib import Path

# Add scripts to path
_this_dir = Path(__file__).parent
_scripts_path = _this_dir.parent.parent / 'scripts'
sys.path.insert(0, str(_scripts_path))

from jql_validate import validate_jql, validate_multiple, suggest_correction


@pytest.mark.integration
@pytest.mark.search
class TestJqlValidate:
    """Tests for jql_validate.py functionality."""

    def test_validate_simple_valid_jql(self, jira_client, test_project):
        """Test validating a simple valid JQL query."""
        jql = f"project = {test_project['key']}"

        result = validate_jql(jira_client, jql)

        assert result['valid'] == True
        assert result['query'] == jql
        assert len(result['errors']) == 0

    def test_validate_complex_valid_jql(self, jira_client, test_project):
        """Test validating a complex valid JQL query."""
        jql = f"project = {test_project['key']} AND type = Bug AND priority IN (High, Medium) ORDER BY created DESC"

        result = validate_jql(jira_client, jql)

        assert result['valid'] == True
        assert len(result['errors']) == 0

    def test_validate_jql_with_functions(self, jira_client, test_project):
        """Test validating JQL with functions."""
        jql = f"project = {test_project['key']} AND created >= startOfDay(-7d)"

        result = validate_jql(jira_client, jql)

        assert result['valid'] == True

    def test_validate_jql_with_current_user(self, jira_client, test_project):
        """Test validating JQL with currentUser()."""
        jql = "assignee = currentUser()"

        result = validate_jql(jira_client, jql)

        assert result['valid'] == True

    def test_validate_invalid_field(self, jira_client, test_project):
        """Test validating JQL with invalid field."""
        jql = "invalidfield = something"

        result = validate_jql(jira_client, jql)

        assert result['valid'] == False
        assert len(result['errors']) > 0

    def test_validate_invalid_syntax(self, jira_client, test_project):
        """Test validating JQL with invalid syntax."""
        jql = "project = AND type = Bug"

        result = validate_jql(jira_client, jql)

        assert result['valid'] == False
        assert len(result['errors']) > 0

    def test_validate_missing_value(self, jira_client, test_project):
        """Test validating JQL with missing value."""
        jql = "project ="

        result = validate_jql(jira_client, jql)

        assert result['valid'] == False
        assert len(result['errors']) > 0

    def test_validate_structure_returned(self, jira_client, test_project):
        """Test that parsed structure is returned for valid JQL."""
        jql = f"project = {test_project['key']} AND type = Bug"

        result = validate_jql(jira_client, jql)

        assert result['valid'] == True
        assert 'structure' in result
        # Structure should have parsed information
        if result['structure']:
            assert 'where' in result['structure'] or result['structure'] is not None


@pytest.mark.integration
@pytest.mark.search
class TestJqlValidateMultiple:
    """Tests for validating multiple JQL queries."""

    def test_validate_multiple_all_valid(self, jira_client, test_project):
        """Test validating multiple valid queries."""
        queries = [
            f"project = {test_project['key']}",
            f"project = {test_project['key']} AND type = Bug",
            "assignee = currentUser()"
        ]

        results = validate_multiple(jira_client, queries)

        assert len(results) == 3
        for result in results:
            assert result['valid'] == True

    def test_validate_multiple_mixed(self, jira_client, test_project):
        """Test validating a mix of valid and invalid queries."""
        queries = [
            f"project = {test_project['key']}",  # Valid
            "invalidfield = something",  # Invalid
            "assignee = currentUser()"  # Valid
        ]

        results = validate_multiple(jira_client, queries)

        assert len(results) == 3
        assert results[0]['valid'] == True
        assert results[1]['valid'] == False
        assert results[2]['valid'] == True

    def test_validate_multiple_all_invalid(self, jira_client):
        """Test validating multiple invalid queries."""
        queries = [
            "badfield = x",
            "project = AND",
            "= something"
        ]

        results = validate_multiple(jira_client, queries)

        assert len(results) == 3
        for result in results:
            assert result['valid'] == False


@pytest.mark.integration
@pytest.mark.search
class TestJqlSuggestions:
    """Tests for JQL field suggestions."""

    def test_suggest_correction_typo(self):
        """Test suggesting correction for typo."""
        suggestion = suggest_correction("projct")

        assert suggestion == "project"

    def test_suggest_correction_case(self):
        """Test suggesting correction for case issues."""
        suggestion = suggest_correction("PROJECT")

        # Should suggest the correct casing
        assert suggestion is not None
        assert suggestion.lower() == "project"

    def test_suggest_correction_similar(self):
        """Test suggesting correction for similar field."""
        suggestion = suggest_correction("issutype")

        # Should suggest issuetype
        assert suggestion in ["issuetype", "type"]

    def test_suggest_correction_no_match(self):
        """Test no suggestion for completely different string."""
        suggestion = suggest_correction("xyzabc123")

        assert suggestion is None

    def test_suggest_correction_status(self):
        """Test suggesting status field."""
        suggestion = suggest_correction("statu")

        assert suggestion == "status"

    def test_suggest_correction_assignee(self):
        """Test suggesting assignee field."""
        suggestion = suggest_correction("asignee")

        assert suggestion == "assignee"


@pytest.mark.integration
@pytest.mark.search
class TestJqlValidationEdgeCases:
    """Edge case tests for JQL validation."""

    def test_validate_empty_jql(self, jira_client):
        """Test validating empty JQL."""
        result = validate_jql(jira_client, "")

        # Empty JQL is technically valid (returns all issues)
        # or may be invalid depending on JIRA config
        assert 'valid' in result

    def test_validate_jql_with_quotes(self, jira_client, test_project):
        """Test validating JQL with quoted strings."""
        jql = f'project = "{test_project["key"]}" AND summary ~ "test"'

        result = validate_jql(jira_client, jql)

        # Should be valid
        assert result['valid'] == True

    def test_validate_jql_with_special_operators(self, jira_client, test_project):
        """Test validating JQL with special operators."""
        jql = f"project = {test_project['key']} AND summary ~ 'test*'"

        result = validate_jql(jira_client, jql)

        assert result['valid'] == True

    def test_validate_jql_is_empty(self, jira_client, test_project):
        """Test validating JQL with IS EMPTY operator."""
        jql = f"project = {test_project['key']} AND assignee IS EMPTY"

        result = validate_jql(jira_client, jql)

        assert result['valid'] == True

    def test_validate_jql_is_not_empty(self, jira_client, test_project):
        """Test validating JQL with IS NOT EMPTY operator."""
        jql = f"project = {test_project['key']} AND assignee IS NOT EMPTY"

        result = validate_jql(jira_client, jql)

        assert result['valid'] == True

    def test_validate_jql_changed_function(self, jira_client, test_project):
        """Test validating JQL with CHANGED function."""
        jql = f"project = {test_project['key']} AND status CHANGED"

        result = validate_jql(jira_client, jql)

        assert result['valid'] == True

    def test_validate_jql_was_function(self, jira_client, test_project):
        """Test validating JQL with WAS function."""
        jql = f"project = {test_project['key']} AND status WAS 'Open'"

        result = validate_jql(jira_client, jql)

        assert result['valid'] == True
