"""
Tests for jql_build.py - Build JQL queries from components.
"""

import sys
from pathlib import Path

import pytest

# Add script path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


@pytest.mark.search
@pytest.mark.unit
class TestBuildJQL:
    """Tests for JQL query building."""

    def test_build_simple_query(self):
        """Test building a simple single-clause query."""
        from jql_build import build_jql

        jql = build_jql(clauses=["project = PROJ"])

        assert jql == "project = PROJ"

    def test_build_compound_query(self):
        """Test building AND/OR queries."""
        from jql_build import build_jql

        jql = build_jql(clauses=["project = PROJ", "status != Done"])

        assert "project = PROJ" in jql
        assert "status != Done" in jql
        assert "AND" in jql

    def test_build_from_template(self):
        """Test using predefined templates."""
        from jql_build import TEMPLATES, build_from_template

        assert "my-open" in TEMPLATES
        jql = build_from_template("my-open")

        assert "assignee = currentUser()" in jql
        assert "status != Done" in jql

    def test_add_order_by(self):
        """Test adding ORDER BY clause."""
        from jql_build import build_jql

        jql = build_jql(clauses=["project = PROJ"], order_by="created", order_desc=True)

        assert "project = PROJ" in jql
        assert "ORDER BY created DESC" in jql

    def test_validate_during_build(self, mock_jira_client):
        """Test that built queries can be validated."""
        mock_jira_client.parse_jql.return_value = {
            "queries": [{"query": "project = PROJ", "errors": []}]
        }

        from jql_build import build_and_validate

        result = build_and_validate(mock_jira_client, clauses=["project = PROJ"])

        assert result["valid"] is True
        assert result["jql"] == "project = PROJ"

    def test_output_for_copy(self):
        """Test clean output for copy/paste."""
        from jql_build import build_jql, format_for_copy

        jql = build_jql(clauses=["project = PROJ", "type = Bug"], order_by="priority")
        output = format_for_copy(jql)

        # Should be a clean JQL string without extra formatting
        assert "project = PROJ" in output
        assert "type = Bug" in output
        assert "ORDER BY priority" in output
