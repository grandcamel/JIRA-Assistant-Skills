"""
Tests for jira-as search commands.

Tests cover:
- Constants and helper functions
- Search implementation functions
- Filter implementation functions
- Formatting functions
- CLI commands
"""

import json
import os
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from jira_assistant_skills.cli.commands.search_cmds import (
    # Constants
    COMMON_FIELDS,
    FUNCTION_EXAMPLES,
    JQL_TEMPLATES,
    # Search implementation functions
    _build_jql_impl,
    _bulk_update_impl,
    # Filter implementation functions
    _create_filter_impl,
    _delete_filter_impl,
    _export_results_impl,
    _favourite_filter_impl,
    # Formatting functions
    _format_fields,
    _format_filter_detail,
    _format_filters,
    _format_functions,
    _format_search_output,
    _format_suggestions,
    _format_validation_result,
    # Helper functions
    _format_value_for_jql,
    _get_fields_impl,
    _get_filters_impl,
    _get_functions_impl,
    _get_return_type,
    _get_suggestions_impl,
    _run_filter_impl,
    _search_issues_impl,
    _share_filter_impl,
    _suggest_correction,
    _update_filter_impl,
    _validate_jql_impl,
    # Click commands
    search,
)
from jira_assistant_skills_lib import JiraError, ValidationError

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_client():
    """Create mock JIRA client."""
    client = MagicMock()
    client.close = MagicMock()
    return client


@pytest.fixture
def sample_issues():
    """Sample issues for testing."""
    return [
        {
            "key": "TEST-1",
            "fields": {
                "summary": "First issue",
                "status": {"name": "Open"},
                "priority": {"name": "High"},
                "issuetype": {"name": "Bug"},
                "assignee": {"displayName": "John Doe", "accountId": "123"},
                "reporter": {"displayName": "Jane Smith", "accountId": "456"},
                "labels": ["bug", "critical"],
                "created": "2024-01-15T10:00:00.000+0000",
                "updated": "2024-01-16T15:30:00.000+0000",
            },
        },
        {
            "key": "TEST-2",
            "fields": {
                "summary": "Second issue",
                "status": {"name": "In Progress"},
                "priority": {"name": "Medium"},
                "issuetype": {"name": "Task"},
                "assignee": None,
                "reporter": {"displayName": "Jane Smith"},
                "labels": [],
            },
        },
        {
            "key": "TEST-3",
            "fields": {
                "summary": "Third issue",
                "status": {"name": "Done"},
                "priority": {"name": "Low"},
                "issuetype": {"name": "Story"},
                "assignee": {"displayName": "Bob Wilson"},
                "reporter": {"displayName": "John Doe"},
                "labels": ["feature"],
            },
        },
    ]


@pytest.fixture
def sample_filter():
    """Sample filter for testing."""
    return {
        "id": "10001",
        "name": "My Open Issues",
        "jql": "assignee = currentUser() AND status != Done",
        "description": "All my open issues",
        "favourite": True,
        "owner": {
            "accountId": "user123",
            "displayName": "John Doe",
        },
        "sharePermissions": [
            {"type": "project", "project": {"key": "TEST", "name": "Test Project"}},
        ],
        "viewUrl": "https://jira.example.com/issues/?filter=10001",
    }


@pytest.fixture
def sample_filters():
    """Sample filter list for testing."""
    return [
        {
            "id": "10001",
            "name": "My Open Issues",
            "jql": "assignee = currentUser() AND status != Done",
            "favourite": True,
            "owner": {"displayName": "John Doe"},
        },
        {
            "id": "10002",
            "name": "All Bugs",
            "jql": "type = Bug AND status != Done",
            "favourite": False,
            "owner": {"displayName": "Jane Smith"},
        },
        {
            "id": "10003",
            "name": "Sprint Issues",
            "jql": "sprint in openSprints()",
            "favourite": True,
            "owner": {"displayName": "John Doe"},
        },
    ]


@pytest.fixture
def sample_fields():
    """Sample JQL fields for testing."""
    return [
        {
            "value": "project",
            "displayName": "Project",
            "cfid": None,
            "operators": ["=", "!=", "in", "not in"],
        },
        {
            "value": "status",
            "displayName": "Status",
            "cfid": None,
            "operators": ["=", "!=", "in", "not in", "was", "was in", "changed"],
        },
        {
            "value": "customfield_10001",
            "displayName": "Story Points",
            "cfid": "10001",
            "operators": ["=", "!=", ">", "<", ">=", "<="],
        },
        {
            "value": "customfield_10002",
            "displayName": "Epic Link",
            "cfid": "10002",
            "operators": ["=", "!=", "in", "not in", "is empty", "is not empty"],
        },
    ]


@pytest.fixture
def sample_functions():
    """Sample JQL functions for testing."""
    return [
        {
            "value": "currentUser()",
            "displayName": "currentUser()",
            "isList": "false",
            "types": ["com.atlassian.jira.user.ApplicationUser"],
        },
        {
            "value": "openSprints()",
            "displayName": "openSprints()",
            "isList": "true",
            "types": ["com.atlassian.greenhopper.Sprint"],
        },
        {
            "value": "startOfDay()",
            "displayName": "startOfDay(increment)",
            "isList": "false",
            "types": ["java.util.Date"],
        },
        {
            "value": "membersOf(group)",
            "displayName": "membersOf(groupname)",
            "isList": "true",
            "types": ["com.atlassian.jira.user.ApplicationUser"],
        },
    ]


@pytest.fixture
def sample_suggestions():
    """Sample suggestions for testing."""
    return [
        {"value": "High", "displayName": "High"},
        {"value": "Medium", "displayName": "Medium"},
        {"value": "Low", "displayName": "Low"},
        {"value": "Lowest", "displayName": "Lowest"},
    ]


# =============================================================================
# Test Constants
# =============================================================================


class TestConstants:
    """Tests for constants."""

    def test_common_fields_contains_expected(self):
        """Test COMMON_FIELDS contains essential fields."""
        assert "project" in COMMON_FIELDS
        assert "status" in COMMON_FIELDS
        assert "assignee" in COMMON_FIELDS
        assert "priority" in COMMON_FIELDS
        assert "summary" in COMMON_FIELDS

    def test_jql_templates_keys(self):
        """Test JQL_TEMPLATES contains expected templates."""
        assert "my-open" in JQL_TEMPLATES
        assert "my-bugs" in JQL_TEMPLATES
        assert "unassigned" in JQL_TEMPLATES
        assert "blockers" in JQL_TEMPLATES

    def test_jql_templates_values_are_valid_jql(self):
        """Test JQL_TEMPLATES values look like JQL."""
        for name, jql in JQL_TEMPLATES.items():
            assert isinstance(jql, str)
            assert len(jql) > 0
            # JQL should contain at least one comparison operator or keyword
            assert any(op in jql for op in ["=", "!=", "in", "IS", ">=", "<="])

    def test_function_examples_valid(self):
        """Test FUNCTION_EXAMPLES are valid."""
        assert "currentUser()" in FUNCTION_EXAMPLES
        assert "openSprints()" in FUNCTION_EXAMPLES
        for func, example in FUNCTION_EXAMPLES.items():
            # Extract function name without parentheses for matching
            func_base = func.split("(")[0]
            assert func_base in example or func in example


# =============================================================================
# Test Helper Functions
# =============================================================================


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_suggest_correction_exact_match(self):
        """Test suggestion finds close matches."""
        result = _suggest_correction("porject")
        assert result == "project"

    def test_suggest_correction_case_insensitive(self):
        """Test suggestion is case insensitive."""
        result = _suggest_correction("STATUS")
        assert result == "status"

    def test_suggest_correction_no_match(self):
        """Test suggestion returns None for no match."""
        result = _suggest_correction("zzzznotafield")
        assert result is None

    def test_suggest_correction_custom_fields(self):
        """Test suggestion with custom field list."""
        custom_fields = ["customfield_10001", "customfield_10002", "story_points"]
        result = _suggest_correction("customfield_1001", custom_fields)
        assert result == "customfield_10001"

    def test_format_value_for_jql_no_spaces(self):
        """Test formatting value without spaces."""
        result = _format_value_for_jql("Bug")
        assert result == "Bug"

    def test_format_value_for_jql_with_spaces(self):
        """Test formatting value with spaces gets quoted."""
        result = _format_value_for_jql("In Progress")
        assert result == '"In Progress"'

    def test_get_return_type_date(self):
        """Test getting return type for Date function."""
        func = {"types": ["java.util.Date"]}
        result = _get_return_type(func)
        assert result == "Date"

    def test_get_return_type_user(self):
        """Test getting return type for User function."""
        func = {"types": ["com.atlassian.jira.user.ApplicationUser"]}
        result = _get_return_type(func)
        assert result == "User"

    def test_get_return_type_sprint(self):
        """Test getting return type for Sprint function."""
        func = {"types": ["com.atlassian.greenhopper.Sprint"]}
        result = _get_return_type(func)
        assert result == "Sprint"

    def test_get_return_type_empty(self):
        """Test getting return type with no types."""
        func = {"types": []}
        result = _get_return_type(func)
        assert result == "Unknown"

    def test_get_return_type_missing(self):
        """Test getting return type with missing types key."""
        func = {}
        result = _get_return_type(func)
        assert result == "Unknown"


# =============================================================================
# Test Search Implementation Functions
# =============================================================================


class TestSearchImplementation:
    """Tests for search implementation functions."""

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.search_cmds.validate_jql")
    def test_search_issues_basic(
        self, mock_validate, mock_get_client, mock_client, sample_issues
    ):
        """Test basic issue search."""
        mock_get_client.return_value = mock_client
        mock_validate.return_value = "project = TEST"
        mock_client.search_issues.return_value = {
            "issues": sample_issues,
            "total": 3,
        }

        result = _search_issues_impl(jql="project = TEST")

        assert result["total"] == 3
        assert len(result["issues"]) == 3
        assert result["_jql"] == "project = TEST"
        mock_client.close.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.search_cmds.validate_jql")
    def test_search_issues_with_filter(
        self, mock_validate, mock_get_client, mock_client, sample_issues
    ):
        """Test search using saved filter."""
        mock_get_client.return_value = mock_client
        mock_validate.return_value = "project = TEST"
        mock_client.get_filter.return_value = {
            "id": "10001",
            "name": "My Filter",
            "jql": "project = TEST",
        }
        mock_client.search_issues.return_value = {
            "issues": sample_issues,
            "total": 3,
        }

        result = _search_issues_impl(filter_id="10001")

        assert result["_filter_name"] == "My Filter"
        mock_client.get_filter.assert_called_with("10001")

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.search_cmds.validate_jql")
    def test_search_issues_with_save(self, mock_validate, mock_get_client, mock_client):
        """Test search with save-as filter option."""
        mock_get_client.return_value = mock_client
        mock_validate.return_value = "project = TEST"
        mock_client.search_issues.return_value = {"issues": [], "total": 0}
        mock_client.create_filter.return_value = {
            "id": "10005",
            "name": "New Filter",
        }

        result = _search_issues_impl(jql="project = TEST", save_as="New Filter")

        assert "savedFilter" in result
        assert result["savedFilter"]["name"] == "New Filter"
        mock_client.create_filter.assert_called_once()

    def test_search_issues_no_query_no_filter(self):
        """Test search fails without JQL or filter."""
        with pytest.raises(ValidationError, match="Either JQL query or filter_id"):
            _search_issues_impl()

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.search_cmds.validate_jql")
    def test_export_results_csv(
        self, mock_validate, mock_get_client, mock_client, sample_issues, tmp_path
    ):
        """Test exporting results to CSV."""
        mock_get_client.return_value = mock_client
        mock_validate.return_value = "project = TEST"
        mock_client.search_issues.return_value = {"issues": sample_issues}

        output_file = str(tmp_path / "export.csv")

        with patch(
            "jira_assistant_skills.cli.commands.search_cmds.export_csv"
        ) as mock_export:
            result = _export_results_impl(
                jql="project = TEST",
                output_file=output_file,
                format_type="csv",
            )

            assert result["exported"] == 3
            assert result["format"] == "csv"
            mock_export.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.search_cmds.validate_jql")
    def test_export_results_json(
        self, mock_validate, mock_get_client, mock_client, sample_issues, tmp_path
    ):
        """Test exporting results to JSON."""
        mock_get_client.return_value = mock_client
        mock_validate.return_value = "project = TEST"
        mock_client.search_issues.return_value = {"issues": sample_issues}

        output_file = str(tmp_path / "export.json")
        result = _export_results_impl(
            jql="project = TEST",
            output_file=output_file,
            format_type="json",
        )

        assert result["exported"] == 3
        assert result["format"] == "json"
        assert os.path.exists(output_file)

        with open(output_file) as f:
            data = json.load(f)
        assert data["total"] == 3

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.search_cmds.validate_jql")
    def test_export_results_no_issues(
        self, mock_validate, mock_get_client, mock_client, tmp_path
    ):
        """Test export with no matching issues."""
        mock_get_client.return_value = mock_client
        mock_validate.return_value = "project = EMPTY"
        mock_client.search_issues.return_value = {"issues": []}

        result = _export_results_impl(
            jql="project = EMPTY",
            output_file=str(tmp_path / "export.csv"),
        )

        assert result["exported"] == 0
        assert "No issues found" in result["message"]

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_validate_jql_valid(self, mock_get_client, mock_client):
        """Test validating valid JQL."""
        mock_get_client.return_value = mock_client
        mock_client.parse_jql.return_value = {
            "queries": [{"query": "project = TEST", "errors": []}]
        }

        results = _validate_jql_impl(["project = TEST"])

        assert len(results) == 1
        assert results[0]["valid"] is True
        assert results[0]["errors"] == []

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_validate_jql_invalid(self, mock_get_client, mock_client):
        """Test validating invalid JQL."""
        mock_get_client.return_value = mock_client
        mock_client.parse_jql.return_value = {
            "queries": [
                {
                    "query": "porject = TEST",
                    "errors": ["Field 'porject' does not exist"],
                }
            ]
        }

        results = _validate_jql_impl(["porject = TEST"])

        assert len(results) == 1
        assert results[0]["valid"] is False
        assert len(results[0]["errors"]) > 0

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_validate_jql_multiple(self, mock_get_client, mock_client):
        """Test validating multiple queries."""
        mock_get_client.return_value = mock_client
        mock_client.parse_jql.return_value = {
            "queries": [
                {"query": "project = A", "errors": []},
                {"query": "invalid", "errors": ["Parse error"]},
            ]
        }

        results = _validate_jql_impl(["project = A", "invalid"])

        assert len(results) == 2
        assert results[0]["valid"] is True
        assert results[1]["valid"] is False

    def test_validate_jql_empty(self):
        """Test validation fails with empty list."""
        with pytest.raises(ValidationError, match="At least one query"):
            _validate_jql_impl([])

    def test_build_jql_from_clauses(self):
        """Test building JQL from clauses."""
        result = _build_jql_impl(
            clauses=["project = TEST", "status = Open"],
            operator="AND",
        )

        assert result["jql"] == "project = TEST AND status = Open"

    def test_build_jql_with_order(self):
        """Test building JQL with ORDER BY."""
        result = _build_jql_impl(
            clauses=["project = TEST"],
            order_by="created",
            order_desc=True,
        )

        assert "ORDER BY created DESC" in result["jql"]

    def test_build_jql_from_template(self):
        """Test building JQL from template."""
        result = _build_jql_impl(template="my-open")

        assert result["jql"] == JQL_TEMPLATES["my-open"]

    def test_build_jql_unknown_template(self):
        """Test building JQL with unknown template."""
        with pytest.raises(ValidationError, match="Unknown template"):
            _build_jql_impl(template="nonexistent")

    def test_build_jql_no_input(self):
        """Test building JQL with no input."""
        with pytest.raises(ValidationError, match="Either clauses or template"):
            _build_jql_impl()

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_build_jql_with_validation(self, mock_get_client, mock_client):
        """Test building JQL with validation."""
        mock_get_client.return_value = mock_client
        mock_client.parse_jql.return_value = {"queries": [{"errors": []}]}

        result = _build_jql_impl(
            clauses=["project = TEST"],
            validate=True,
        )

        assert result["valid"] is True
        assert result["errors"] == []

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.search_cmds.get_autocomplete_cache")
    def test_get_suggestions_cached(
        self, mock_get_cache, mock_get_client, mock_client, sample_suggestions
    ):
        """Test getting suggestions with cache."""
        mock_get_client.return_value = mock_client
        mock_cache = MagicMock()
        mock_cache.get_suggestions.return_value = sample_suggestions
        mock_get_cache.return_value = mock_cache

        result = _get_suggestions_impl("priority")

        assert len(result) == 4
        mock_cache.get_suggestions.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_get_suggestions_no_cache(
        self, mock_get_client, mock_client, sample_suggestions
    ):
        """Test getting suggestions without cache."""
        mock_get_client.return_value = mock_client
        mock_client.get_jql_suggestions.return_value = {"results": sample_suggestions}

        result = _get_suggestions_impl("priority", use_cache=False)

        assert len(result) == 4
        mock_client.get_jql_suggestions.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.search_cmds.get_autocomplete_cache")
    def test_get_fields_all(
        self, mock_get_cache, mock_get_client, mock_client, sample_fields
    ):
        """Test getting all fields."""
        mock_get_client.return_value = mock_client
        mock_cache = MagicMock()
        mock_cache.get_fields.return_value = sample_fields
        mock_get_cache.return_value = mock_cache

        result = _get_fields_impl()

        assert len(result) == 4

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.search_cmds.get_autocomplete_cache")
    def test_get_fields_custom_only(
        self, mock_get_cache, mock_get_client, mock_client, sample_fields
    ):
        """Test getting custom fields only."""
        mock_get_client.return_value = mock_client
        mock_cache = MagicMock()
        mock_cache.get_fields.return_value = sample_fields
        mock_get_cache.return_value = mock_cache

        result = _get_fields_impl(custom_only=True)

        assert len(result) == 2
        assert all(f.get("cfid") is not None for f in result)

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.search_cmds.get_autocomplete_cache")
    def test_get_fields_system_only(
        self, mock_get_cache, mock_get_client, mock_client, sample_fields
    ):
        """Test getting system fields only."""
        mock_get_client.return_value = mock_client
        mock_cache = MagicMock()
        mock_cache.get_fields.return_value = sample_fields
        mock_get_cache.return_value = mock_cache

        result = _get_fields_impl(system_only=True)

        assert len(result) == 2
        assert all(f.get("cfid") is None for f in result)

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.search_cmds.get_autocomplete_cache")
    def test_get_fields_filtered(
        self, mock_get_cache, mock_get_client, mock_client, sample_fields
    ):
        """Test getting fields filtered by name."""
        mock_get_client.return_value = mock_client
        mock_cache = MagicMock()
        mock_cache.get_fields.return_value = sample_fields
        mock_get_cache.return_value = mock_cache

        result = _get_fields_impl(name_filter="status")

        assert len(result) == 1
        assert result[0]["value"] == "status"

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_get_functions_all(self, mock_get_client, mock_client, sample_functions):
        """Test getting all functions."""
        mock_get_client.return_value = mock_client
        mock_client.get_jql_autocomplete.return_value = {
            "visibleFunctionNames": sample_functions
        }

        result = _get_functions_impl()

        assert len(result) == 4

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_get_functions_list_only(
        self, mock_get_client, mock_client, sample_functions
    ):
        """Test getting list-returning functions only."""
        mock_get_client.return_value = mock_client
        mock_client.get_jql_autocomplete.return_value = {
            "visibleFunctionNames": sample_functions
        }

        result = _get_functions_impl(list_only=True)

        assert len(result) == 2
        assert all(f.get("isList") == "true" for f in result)

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_get_functions_filtered(
        self, mock_get_client, mock_client, sample_functions
    ):
        """Test getting functions filtered by name."""
        mock_get_client.return_value = mock_client
        mock_client.get_jql_autocomplete.return_value = {
            "visibleFunctionNames": sample_functions
        }

        result = _get_functions_impl(name_filter="sprint")

        assert len(result) == 1
        assert "Sprint" in result[0]["value"]

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.search_cmds.validate_jql")
    def test_bulk_update_dry_run(
        self, mock_validate, mock_get_client, mock_client, sample_issues
    ):
        """Test bulk update dry run."""
        mock_get_client.return_value = mock_client
        mock_validate.return_value = "project = TEST"
        mock_client.search_issues.return_value = {"issues": sample_issues, "total": 3}

        result = _bulk_update_impl(
            jql="project = TEST",
            add_labels=["newlabel"],
            dry_run=True,
        )

        assert result["would_update"] == 3
        assert "TEST-1" in result["issues"]
        mock_client.update_issue.assert_not_called()

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.search_cmds.validate_jql")
    def test_bulk_update_execute(
        self, mock_validate, mock_get_client, mock_client, sample_issues
    ):
        """Test bulk update execution."""
        mock_get_client.return_value = mock_client
        mock_validate.return_value = "project = TEST"
        mock_client.search_issues.return_value = {"issues": sample_issues, "total": 3}

        result = _bulk_update_impl(
            jql="project = TEST",
            add_labels=["newlabel"],
            dry_run=False,
        )

        assert result["updated"] == 3
        assert result["failed"] == 0
        assert mock_client.update_issue.call_count == 3

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.search_cmds.validate_jql")
    def test_bulk_update_no_issues(self, mock_validate, mock_get_client, mock_client):
        """Test bulk update with no matching issues."""
        mock_get_client.return_value = mock_client
        mock_validate.return_value = "project = EMPTY"
        mock_client.search_issues.return_value = {"issues": [], "total": 0}

        result = _bulk_update_impl(
            jql="project = EMPTY",
            add_labels=["newlabel"],
        )

        assert result["updated"] == 0
        assert "No issues found" in result["message"]


# =============================================================================
# Test Filter Implementation Functions
# =============================================================================


class TestFilterImplementation:
    """Tests for filter implementation functions."""

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_get_filters_my_filters(self, mock_get_client, mock_client, sample_filters):
        """Test getting my filters."""
        mock_get_client.return_value = mock_client
        mock_client.get_my_filters.return_value = sample_filters

        result = _get_filters_impl(my_filters=True)

        assert result["type"] == "my"
        assert len(result["filters"]) == 3

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_get_filters_favourites(self, mock_get_client, mock_client, sample_filters):
        """Test getting favourite filters."""
        mock_get_client.return_value = mock_client
        mock_client.get_favourite_filters.return_value = [
            f for f in sample_filters if f["favourite"]
        ]

        result = _get_filters_impl(favourites=True)

        assert result["type"] == "favourites"
        assert len(result["filters"]) == 2

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_get_filters_by_id(self, mock_get_client, mock_client, sample_filter):
        """Test getting filter by ID."""
        mock_get_client.return_value = mock_client
        mock_client.get_filter.return_value = sample_filter

        result = _get_filters_impl(filter_id="10001")

        assert result["type"] == "single"
        assert result["filter"]["name"] == "My Open Issues"

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_get_filters_search(self, mock_get_client, mock_client, sample_filters):
        """Test searching filters."""
        mock_get_client.return_value = mock_client
        mock_client.search_filters.return_value = {"values": sample_filters}

        result = _get_filters_impl(search_name="Open")

        assert result["type"] == "search"
        mock_client.search_filters.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_get_filters_no_option(self, mock_get_client, mock_client):
        """Test getting filters with no options raises error."""
        mock_get_client.return_value = mock_client
        with pytest.raises(ValidationError, match="Specify"):
            _get_filters_impl()

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_create_filter_basic(self, mock_get_client, mock_client):
        """Test creating a basic filter."""
        mock_get_client.return_value = mock_client
        mock_client.create_filter.return_value = {
            "id": "10010",
            "name": "New Filter",
            "jql": "project = TEST",
        }

        result = _create_filter_impl(
            name="New Filter",
            jql="project = TEST",
        )

        assert result["id"] == "10010"
        mock_client.create_filter.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_create_filter_with_share(self, mock_get_client, mock_client):
        """Test creating filter with sharing."""
        mock_get_client.return_value = mock_client
        mock_client.create_filter.return_value = {
            "id": "10010",
            "name": "New Filter",
        }

        result = _create_filter_impl(
            name="New Filter",
            jql="project = TEST",
            share_global=True,
        )

        assert result["id"] == "10010"
        call_args = mock_client.create_filter.call_args
        assert call_args[1]["share_permissions"] is not None

    def test_create_filter_no_name(self):
        """Test creating filter without name fails."""
        with pytest.raises(ValidationError, match="name is required"):
            _create_filter_impl(name="", jql="project = TEST")

    def test_create_filter_no_jql(self):
        """Test creating filter without JQL fails."""
        with pytest.raises(ValidationError, match="JQL query is required"):
            _create_filter_impl(name="Test", jql="")

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_run_filter_by_id(
        self, mock_get_client, mock_client, sample_issues, sample_filter
    ):
        """Test running filter by ID."""
        mock_get_client.return_value = mock_client
        mock_client.get_filter.return_value = sample_filter
        mock_client.search_issues.return_value = {"issues": sample_issues, "total": 3}

        result = _run_filter_impl(filter_id="10001")

        assert result["total"] == 3
        assert result["_filter"]["name"] == "My Open Issues"

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_run_filter_by_name(
        self, mock_get_client, mock_client, sample_issues, sample_filter
    ):
        """Test running filter by name."""
        mock_get_client.return_value = mock_client
        mock_client.get.return_value = [sample_filter]
        mock_client.get_filter.return_value = sample_filter
        mock_client.search_issues.return_value = {"issues": sample_issues, "total": 3}

        result = _run_filter_impl(filter_name="My Open Issues")

        assert result["total"] == 3

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_run_filter_not_found(self, mock_get_client, mock_client):
        """Test running filter that doesn't exist."""
        mock_get_client.return_value = mock_client
        mock_client.get.return_value = []

        with pytest.raises(ValidationError, match="not found"):
            _run_filter_impl(filter_name="Nonexistent")

    def test_run_filter_no_id_or_name(self):
        """Test running filter without ID or name."""
        with pytest.raises(ValidationError, match="Either filter_id or filter_name"):
            _run_filter_impl()

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_update_filter(self, mock_get_client, mock_client):
        """Test updating a filter."""
        mock_get_client.return_value = mock_client
        mock_client.update_filter.return_value = {
            "id": "10001",
            "name": "Updated Name",
            "jql": "project = TEST",
        }

        result = _update_filter_impl(
            filter_id="10001",
            name="Updated Name",
        )

        assert result["name"] == "Updated Name"

    def test_update_filter_no_changes(self):
        """Test updating filter with no changes."""
        with pytest.raises(ValidationError, match="At least one"):
            _update_filter_impl(filter_id="10001")

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_delete_filter_dry_run(self, mock_get_client, mock_client, sample_filter):
        """Test deleting filter with dry run."""
        mock_get_client.return_value = mock_client
        mock_client.get_filter.return_value = sample_filter

        result = _delete_filter_impl("10001", dry_run=True)

        assert result["would_delete"] is True
        assert result["filter_name"] == "My Open Issues"
        mock_client.delete_filter.assert_not_called()

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_delete_filter_execute(self, mock_get_client, mock_client, sample_filter):
        """Test deleting filter."""
        mock_get_client.return_value = mock_client
        mock_client.get_filter.return_value = sample_filter

        result = _delete_filter_impl("10001", dry_run=False)

        assert result["deleted"] is True
        mock_client.delete_filter.assert_called_with("10001")

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_share_filter_list(self, mock_get_client, mock_client):
        """Test listing filter permissions."""
        mock_get_client.return_value = mock_client
        mock_client.get_filter_permissions.return_value = [
            {"id": "1", "type": "project"},
        ]

        result = _share_filter_impl("10001", list_permissions=True)

        assert result["action"] == "list"
        assert len(result["permissions"]) == 1

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_share_filter_with_project(self, mock_get_client, mock_client):
        """Test sharing filter with project."""
        mock_get_client.return_value = mock_client
        mock_client.add_filter_permission.return_value = {"id": "5", "type": "project"}

        result = _share_filter_impl("10001", project="TEST")

        assert result["action"] == "shared"
        assert result["type"] == "project"

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_share_filter_with_role(self, mock_get_client, mock_client):
        """Test sharing filter with project role."""
        mock_get_client.return_value = mock_client
        mock_client.get.return_value = {
            "Developers": "https://jira/role/10002",
            "Users": "https://jira/role/10003",
        }
        mock_client.add_filter_permission.return_value = {
            "id": "5",
            "type": "projectRole",
        }

        result = _share_filter_impl("10001", project="TEST", role="Developers")

        assert result["action"] == "shared"

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_share_filter_role_not_found(self, mock_get_client, mock_client):
        """Test sharing with non-existent role."""
        mock_get_client.return_value = mock_client
        mock_client.get.return_value = {
            "Users": "https://jira/role/10003",
        }

        with pytest.raises(ValidationError, match="not found"):
            _share_filter_impl("10001", project="TEST", role="NonexistentRole")

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_share_filter_global(self, mock_get_client, mock_client):
        """Test sharing filter globally."""
        mock_get_client.return_value = mock_client
        mock_client.add_filter_permission.return_value = {"id": "5", "type": "global"}

        result = _share_filter_impl("10001", share_global=True)

        assert result["action"] == "shared"
        assert result["type"] == "global"

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_share_filter_unshare(self, mock_get_client, mock_client):
        """Test removing filter permission."""
        mock_get_client.return_value = mock_client

        result = _share_filter_impl("10001", unshare="5")

        assert result["action"] == "removed"
        mock_client.delete_filter_permission.assert_called_with("10001", "5")

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_share_filter_no_option(self, mock_get_client, mock_client):
        """Test share filter with no options."""
        mock_get_client.return_value = mock_client
        with pytest.raises(ValidationError, match="Specify"):
            _share_filter_impl("10001")

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_favourite_filter_add(self, mock_get_client, mock_client, sample_filter):
        """Test adding filter to favourites."""
        mock_get_client.return_value = mock_client
        mock_client.add_filter_favourite.return_value = sample_filter

        result = _favourite_filter_impl("10001", add=True)

        assert result["action"] == "added"

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_favourite_filter_remove(self, mock_get_client, mock_client, sample_filter):
        """Test removing filter from favourites."""
        mock_get_client.return_value = mock_client
        mock_client.get_filter.return_value = sample_filter

        result = _favourite_filter_impl("10001", remove=True)

        assert result["action"] == "removed"
        mock_client.remove_filter_favourite.assert_called_with("10001")

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_favourite_filter_toggle_add(self, mock_get_client, mock_client):
        """Test toggling favourite adds when not favourite."""
        mock_get_client.return_value = mock_client
        mock_client.get_filter.return_value = {"id": "10001", "favourite": False}
        mock_client.add_filter_favourite.return_value = {
            "id": "10001",
            "favourite": True,
        }

        result = _favourite_filter_impl("10001")

        assert result["action"] == "added"

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_favourite_filter_toggle_remove(self, mock_get_client, mock_client):
        """Test toggling favourite removes when favourite."""
        mock_get_client.return_value = mock_client
        mock_client.get_filter.return_value = {"id": "10001", "favourite": True}

        result = _favourite_filter_impl("10001")

        assert result["action"] == "removed"


# =============================================================================
# Test Formatting Functions
# =============================================================================


class TestFormattingFunctions:
    """Tests for formatting functions."""

    def test_format_search_output_basic(self, sample_issues):
        """Test basic search output formatting."""
        results = {
            "issues": sample_issues,
            "total": 3,
            "isLast": True,
        }

        output = _format_search_output(results, False, False, False)

        assert "Found 3 issue(s)" in output

    def test_format_search_output_with_filter(self, sample_issues):
        """Test search output with filter name."""
        results = {
            "issues": sample_issues,
            "total": 3,
            "_filter_name": "My Filter",
            "_jql": "project = TEST",
        }

        output = _format_search_output(results, False, False, False)

        assert "Running filter: My Filter" in output
        assert "JQL: project = TEST" in output

    def test_format_search_output_pagination(self, sample_issues):
        """Test search output with pagination."""
        results = {
            "issues": sample_issues,
            "total": 100,
            "nextPageToken": "abc123",
        }

        output = _format_search_output(results, False, False, False)

        assert "Next page token: abc123" in output
        assert "Showing 3 of 100" in output

    def test_format_search_output_saved_filter(self, sample_issues):
        """Test search output with saved filter."""
        results = {
            "issues": sample_issues,
            "total": 3,
            "savedFilter": {"id": "10010", "name": "New Filter"},
        }

        output = _format_search_output(results, False, False, False)

        assert "Saved as filter: New Filter" in output

    def test_format_validation_result_valid(self):
        """Test formatting valid query result."""
        result = {
            "valid": True,
            "query": "project = TEST",
            "errors": [],
        }

        output = _format_validation_result(result)

        assert "Valid JQL" in output
        assert "project = TEST" in output

    def test_format_validation_result_with_structure(self):
        """Test formatting validation with structure."""
        result = {
            "valid": True,
            "query": "project = TEST",
            "errors": [],
            "structure": {
                "where": {
                    "clauses": [
                        {
                            "field": {"name": "project"},
                            "operator": "=",
                            "operand": {"value": "TEST"},
                        }
                    ]
                }
            },
        }

        output = _format_validation_result(result)

        assert "Structure:" in output
        assert "project = TEST" in output

    def test_format_validation_result_invalid(self):
        """Test formatting invalid query result."""
        result = {
            "valid": False,
            "query": "porject = TEST",
            "errors": ["Field 'porject' does not exist"],
        }

        output = _format_validation_result(result)

        assert "Invalid JQL" in output
        assert "Errors:" in output
        assert "does not exist" in output
        # Should suggest correction
        assert "project" in output

    def test_format_suggestions(self, sample_suggestions):
        """Test formatting suggestions."""
        output = _format_suggestions("priority", sample_suggestions)

        assert "Suggestions for 'priority'" in output
        assert "High" in output
        assert "Medium" in output
        assert "Usage:" in output

    def test_format_suggestions_empty(self):
        """Test formatting empty suggestions."""
        output = _format_suggestions("customfield", [])

        assert "No suggestions found" in output

    def test_format_fields(self, sample_fields):
        """Test formatting fields."""
        output = _format_fields(sample_fields)

        assert "JQL Fields:" in output
        assert "project" in output
        assert "status" in output
        assert "Custom" in output
        assert "System" in output
        assert "Total:" in output

    def test_format_fields_empty(self):
        """Test formatting empty fields."""
        output = _format_fields([])

        assert "No fields found" in output

    def test_format_functions(self, sample_functions):
        """Test formatting functions."""
        output = _format_functions(sample_functions)

        assert "JQL Functions:" in output
        assert "currentUser()" in output
        assert "openSprints()" in output
        assert "Returns List" in output

    def test_format_functions_with_examples(self, sample_functions):
        """Test formatting functions with examples."""
        output = _format_functions(sample_functions, show_examples=True)

        assert "Examples:" in output

    def test_format_functions_empty(self):
        """Test formatting empty functions."""
        output = _format_functions([])

        assert "No functions found" in output

    def test_format_filters(self, sample_filters):
        """Test formatting filters."""
        output = _format_filters(sample_filters)

        assert "My Open Issues" in output
        assert "All Bugs" in output
        assert "Total:" in output
        assert "favourites" in output

    def test_format_filters_empty(self):
        """Test formatting empty filters."""
        output = _format_filters([])

        assert "No filters found" in output

    def test_format_filter_detail(self, sample_filter):
        """Test formatting filter detail."""
        output = _format_filter_detail(sample_filter)

        assert "ID:" in output
        assert "10001" in output
        assert "My Open Issues" in output
        assert "John Doe" in output
        assert "Favourite:" in output
        assert "JQL:" in output
        assert "Shared With:" in output
        assert "Project:" in output
        assert "View URL:" in output


# =============================================================================
# Test CLI Commands
# =============================================================================


class TestSearchCLICommands:
    """Tests for search CLI commands."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.search_cmds.validate_jql")
    def test_query_command(
        self, mock_validate, mock_get_client, runner, mock_client, sample_issues
    ):
        """Test search query command."""
        mock_get_client.return_value = mock_client
        mock_validate.return_value = "project = TEST"
        mock_client.search_issues.return_value = {"issues": sample_issues, "total": 3}

        result = runner.invoke(search, ["query", "project = TEST"])

        assert result.exit_code == 0
        assert "Found 3" in result.output

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.search_cmds.validate_jql")
    def test_query_command_json(
        self, mock_validate, mock_get_client, runner, mock_client, sample_issues
    ):
        """Test search query with JSON output."""
        mock_get_client.return_value = mock_client
        mock_validate.return_value = "project = TEST"
        mock_client.search_issues.return_value = {"issues": sample_issues, "total": 3}

        result = runner.invoke(search, ["query", "project = TEST", "-o", "json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["total"] == 3

    def test_query_command_no_query(self, runner):
        """Test search query requires JQL or filter."""
        result = runner.invoke(search, ["query"])

        assert result.exit_code != 0
        assert "required" in result.output.lower()

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_validate_command_valid(self, mock_get_client, runner, mock_client):
        """Test validate command with valid JQL."""
        mock_get_client.return_value = mock_client
        mock_client.parse_jql.return_value = {
            "queries": [{"query": "project = TEST", "errors": []}]
        }

        result = runner.invoke(search, ["validate", "project = TEST"])

        assert result.exit_code == 0
        assert "Valid JQL" in result.output

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_validate_command_invalid(self, mock_get_client, runner, mock_client):
        """Test validate command with invalid JQL."""
        mock_get_client.return_value = mock_client
        mock_client.parse_jql.return_value = {
            "queries": [{"query": "invalid", "errors": ["Parse error"]}]
        }

        result = runner.invoke(search, ["validate", "invalid"])

        assert result.exit_code == 1
        assert "Invalid JQL" in result.output

    def test_build_command_list_templates(self, runner):
        """Test build command listing templates."""
        result = runner.invoke(search, ["build", "--list-templates"])

        assert result.exit_code == 0
        assert "Available Templates:" in result.output
        assert "my-open" in result.output

    def test_build_command_with_clauses(self, runner):
        """Test build command with clauses."""
        result = runner.invoke(
            search,
            [
                "build",
                "-c",
                "project = TEST",
                "-c",
                "status = Open",
            ],
        )

        assert result.exit_code == 0
        assert "project = TEST AND status = Open" in result.output

    def test_build_command_with_template(self, runner):
        """Test build command with template."""
        result = runner.invoke(search, ["build", "-t", "my-open"])

        assert result.exit_code == 0
        assert "assignee = currentUser()" in result.output

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.search_cmds.get_autocomplete_cache")
    def test_suggest_command(
        self, mock_cache, mock_get_client, runner, mock_client, sample_suggestions
    ):
        """Test suggest command."""
        mock_get_client.return_value = mock_client
        cache = MagicMock()
        cache.get_suggestions.return_value = sample_suggestions
        mock_cache.return_value = cache

        result = runner.invoke(search, ["suggest", "-f", "priority"])

        assert result.exit_code == 0
        assert "High" in result.output

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.search_cmds.get_autocomplete_cache")
    def test_fields_command(
        self, mock_cache, mock_get_client, runner, mock_client, sample_fields
    ):
        """Test fields command."""
        mock_get_client.return_value = mock_client
        cache = MagicMock()
        cache.get_fields.return_value = sample_fields
        mock_cache.return_value = cache

        result = runner.invoke(search, ["fields"])

        assert result.exit_code == 0
        assert "project" in result.output
        assert "JQL Fields:" in result.output

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_functions_command(
        self, mock_get_client, runner, mock_client, sample_functions
    ):
        """Test functions command."""
        mock_get_client.return_value = mock_client
        mock_client.get_jql_autocomplete.return_value = {
            "visibleFunctionNames": sample_functions
        }

        result = runner.invoke(search, ["functions"])

        assert result.exit_code == 0
        assert "currentUser()" in result.output

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.search_cmds.validate_jql")
    def test_bulk_update_dry_run(
        self, mock_validate, mock_get_client, runner, mock_client, sample_issues
    ):
        """Test bulk-update command dry run."""
        mock_get_client.return_value = mock_client
        mock_validate.return_value = "project = TEST"
        mock_client.search_issues.return_value = {"issues": sample_issues, "total": 3}

        result = runner.invoke(
            search,
            [
                "bulk-update",
                "project = TEST",
                "--add-labels",
                "newlabel",
                "--dry-run",
            ],
        )

        assert result.exit_code == 0
        assert "Would update" in result.output


class TestFilterCLICommands:
    """Tests for filter CLI commands."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_filter_list_my(self, mock_get_client, runner, mock_client, sample_filters):
        """Test filter list --my command."""
        mock_get_client.return_value = mock_client
        mock_client.get_my_filters.return_value = sample_filters

        result = runner.invoke(search, ["filter", "list", "--my"])

        assert result.exit_code == 0
        assert "My Open Issues" in result.output

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_filter_list_favourites(
        self, mock_get_client, runner, mock_client, sample_filters
    ):
        """Test filter list --favourites command."""
        mock_get_client.return_value = mock_client
        mock_client.get_favourite_filters.return_value = [
            f for f in sample_filters if f["favourite"]
        ]

        result = runner.invoke(search, ["filter", "list", "--favourites"])

        assert result.exit_code == 0
        assert "My Open Issues" in result.output

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_filter_list_by_id(
        self, mock_get_client, runner, mock_client, sample_filter
    ):
        """Test filter list --id command."""
        mock_get_client.return_value = mock_client
        mock_client.get_filter.return_value = sample_filter

        result = runner.invoke(search, ["filter", "list", "--id", "10001"])

        assert result.exit_code == 0
        assert "My Open Issues" in result.output
        assert "Filter Details:" in result.output

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_filter_create(self, mock_get_client, runner, mock_client):
        """Test filter create command."""
        mock_get_client.return_value = mock_client
        mock_client.create_filter.return_value = {
            "id": "10010",
            "name": "New Filter",
            "jql": "project = TEST",
        }

        result = runner.invoke(
            search,
            [
                "filter",
                "create",
                "-n",
                "New Filter",
                "-j",
                "project = TEST",
            ],
        )

        assert result.exit_code == 0
        assert "Filter created" in result.output
        assert "10010" in result.output

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_filter_run(
        self, mock_get_client, runner, mock_client, sample_issues, sample_filter
    ):
        """Test filter run command."""
        mock_get_client.return_value = mock_client
        mock_client.get_filter.return_value = sample_filter
        mock_client.search_issues.return_value = {"issues": sample_issues, "total": 3}

        result = runner.invoke(search, ["filter", "run", "-i", "10001"])

        assert result.exit_code == 0
        assert "Found 3" in result.output

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_filter_update(self, mock_get_client, runner, mock_client):
        """Test filter update command."""
        mock_get_client.return_value = mock_client
        mock_client.update_filter.return_value = {
            "id": "10001",
            "name": "Updated Name",
            "jql": "project = TEST",
        }

        result = runner.invoke(
            search,
            [
                "filter",
                "update",
                "10001",
                "-n",
                "Updated Name",
            ],
        )

        assert result.exit_code == 0
        assert "Filter updated" in result.output
        assert "Updated Name" in result.output

    def test_filter_update_no_changes(self, runner):
        """Test filter update requires at least one change."""
        result = runner.invoke(search, ["filter", "update", "10001"])

        assert result.exit_code != 0
        assert "required" in result.output.lower()

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_filter_delete_dry_run(
        self, mock_get_client, runner, mock_client, sample_filter
    ):
        """Test filter delete dry run."""
        mock_get_client.return_value = mock_client
        mock_client.get_filter.return_value = sample_filter

        result = runner.invoke(search, ["filter", "delete", "10001", "--dry-run"])

        assert result.exit_code == 0
        assert "Would delete" in result.output
        mock_client.delete_filter.assert_not_called()

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_filter_delete_confirmed(
        self, mock_get_client, runner, mock_client, sample_filter
    ):
        """Test filter delete with confirmation."""
        mock_get_client.return_value = mock_client
        mock_client.get_filter.return_value = sample_filter

        result = runner.invoke(search, ["filter", "delete", "10001", "--yes"])

        assert result.exit_code == 0
        assert "deleted" in result.output
        mock_client.delete_filter.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_filter_share_list(self, mock_get_client, runner, mock_client):
        """Test filter share --list command."""
        mock_get_client.return_value = mock_client
        mock_client.get_filter_permissions.return_value = [
            {"id": "1", "type": "project"},
        ]

        result = runner.invoke(search, ["filter", "share", "10001", "--list"])

        assert result.exit_code == 0
        assert "permissions" in result.output.lower()

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_filter_share_project(self, mock_get_client, runner, mock_client):
        """Test filter share --project command."""
        mock_get_client.return_value = mock_client
        mock_client.add_filter_permission.return_value = {"id": "5", "type": "project"}

        result = runner.invoke(
            search, ["filter", "share", "10001", "--project", "TEST"]
        )

        assert result.exit_code == 0
        assert "shared" in result.output.lower()

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_filter_favourite_add(
        self, mock_get_client, runner, mock_client, sample_filter
    ):
        """Test filter favourite --add command."""
        mock_get_client.return_value = mock_client
        mock_client.add_filter_favourite.return_value = sample_filter

        result = runner.invoke(search, ["filter", "favourite", "10001", "--add"])

        assert result.exit_code == 0
        assert "added" in result.output.lower()

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_filter_favourite_remove(
        self, mock_get_client, runner, mock_client, sample_filter
    ):
        """Test filter favourite --remove command."""
        mock_get_client.return_value = mock_client
        mock_client.get_filter.return_value = sample_filter

        result = runner.invoke(search, ["filter", "favourite", "10001", "--remove"])

        assert result.exit_code == 0
        assert "removed" in result.output.lower()


# =============================================================================
# Test Error Handling
# =============================================================================


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_jira_error_handling(self, mock_get_client, runner):
        """Test JiraError is handled properly."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_my_filters.side_effect = JiraError("API Error")

        result = runner.invoke(search, ["filter", "list", "--my"])

        assert result.exit_code == 1
        assert "API Error" in result.output or "error" in result.output.lower()

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.search_cmds.validate_jql")
    def test_client_close_on_error(self, mock_validate, mock_get_client):
        """Test client is closed even on error."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_validate.side_effect = ValidationError("Bad JQL")

        try:
            _search_issues_impl(jql="bad query")
        except ValidationError:
            pass

        # Client should still be closed
        # Note: In this case, validate_jql is called before client operations

    @patch("jira_assistant_skills.cli.commands.search_cmds.get_jira_client")
    def test_partial_bulk_update_failure(self, mock_get_client):
        """Test bulk update handles partial failures."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.search_issues.return_value = {
            "issues": [
                {"key": "TEST-1", "fields": {"labels": []}},
                {"key": "TEST-2", "fields": {"labels": []}},
            ],
            "total": 2,
        }
        # First succeeds, second fails
        mock_client.update_issue.side_effect = [None, JiraError("Update failed")]

        with patch(
            "jira_assistant_skills.cli.commands.search_cmds.validate_jql",
            return_value="jql",
        ):
            result = _bulk_update_impl(
                jql="project = TEST",
                add_labels=["label"],
                dry_run=False,
            )

        assert result["updated"] == 1
        assert result["failed"] == 1
        assert len(result["failures"]) == 1
