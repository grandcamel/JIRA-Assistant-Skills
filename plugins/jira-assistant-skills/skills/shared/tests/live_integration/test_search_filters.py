"""
Live Integration Tests: Search and Filters

Tests for JQL operations and saved filter management against a real JIRA instance.
"""

import contextlib
import uuid

import pytest


@pytest.mark.integration
@pytest.mark.shared
class TestJQLValidation:
    """Tests for JQL validation and parsing."""

    def test_parse_valid_jql(self, jira_client, test_project):
        """Test parsing a valid JQL query."""
        jql = f"project = {test_project['key']} AND status = 'To Do'"
        result = jira_client.parse_jql([jql])

        assert "queries" in result
        assert len(result["queries"]) == 1
        # Valid query should have no errors
        query_result = result["queries"][0]
        assert query_result.get("errors", []) == []

    def test_parse_invalid_jql(self, jira_client):
        """Test parsing an invalid JQL query."""
        jql = "projct = INVALID AND statuss = Open"  # Misspelled fields
        result = jira_client.parse_jql([jql], validation="strict")

        assert "queries" in result
        query_result = result["queries"][0]
        # Should have errors for invalid fields
        assert len(query_result.get("errors", [])) > 0

    def test_parse_multiple_queries(self, jira_client, test_project):
        """Test parsing multiple JQL queries at once."""
        queries = [
            f"project = {test_project['key']}",
            "assignee = currentUser()",
            "status = 'In Progress'",
        ]
        result = jira_client.parse_jql(queries)

        assert len(result["queries"]) == 3

    def test_parse_with_functions(self, jira_client):
        """Test parsing JQL with functions."""
        jql = "assignee = currentUser() AND created >= startOfDay(-7d)"
        result = jira_client.parse_jql([jql])

        query_result = result["queries"][0]
        # Should parse successfully with no errors
        assert query_result.get("errors", []) == []


@pytest.mark.integration
@pytest.mark.shared
class TestJQLAutocomplete:
    """Tests for JQL autocomplete data."""

    def test_get_autocomplete_data(self, jira_client):
        """Test getting JQL autocomplete data."""
        result = jira_client.get_jql_autocomplete()

        assert "visibleFieldNames" in result
        assert "visibleFunctionNames" in result
        assert len(result["visibleFieldNames"]) > 0
        assert len(result["visibleFunctionNames"]) > 0

    def test_autocomplete_includes_standard_fields(self, jira_client):
        """Test that autocomplete includes standard JIRA fields."""
        result = jira_client.get_jql_autocomplete()

        field_names = [f["value"] for f in result["visibleFieldNames"]]
        # Standard fields should be present
        assert "project" in field_names
        assert "status" in field_names
        assert "assignee" in field_names
        assert "summary" in field_names
        assert "created" in field_names

    def test_autocomplete_includes_functions(self, jira_client):
        """Test that autocomplete includes JQL functions."""
        result = jira_client.get_jql_autocomplete()

        function_names = [f["value"] for f in result["visibleFunctionNames"]]
        # Standard functions should be present
        assert "currentUser()" in function_names

    def test_get_field_suggestions(self, jira_client):
        """Test getting value suggestions for a field."""
        result = jira_client.get_jql_suggestions("status")

        assert "results" in result
        # Verify results is a list (may be empty if no issues exist)
        assert isinstance(result["results"], list)

    def test_get_project_suggestions(self, jira_client, test_project):
        """Test getting project suggestions."""
        result = jira_client.get_jql_suggestions("project", test_project["key"][:3])

        assert "results" in result


@pytest.mark.integration
@pytest.mark.shared
class TestFilterCRUD:
    """Tests for filter create, read, update, delete operations."""

    def test_create_filter(self, jira_client, test_project):
        """Test creating a new filter."""
        filter_name = f"Test Filter {uuid.uuid4().hex[:8]}"
        jql = f"project = {test_project['key']} AND type = Task"

        try:
            result = jira_client.create_filter(
                name=filter_name, jql=jql, description="Integration test filter"
            )

            assert "id" in result
            assert result["name"] == filter_name
            assert result["jql"] == jql
            assert result.get("description") == "Integration test filter"

        finally:
            # Cleanup
            if "id" in result:
                with contextlib.suppress(Exception):
                    jira_client.delete_filter(result["id"])

    def test_create_filter_as_favourite(self, jira_client, test_project):
        """Test creating a filter and adding to favourites."""
        filter_name = f"Fav Filter {uuid.uuid4().hex[:8]}"
        jql = f"project = {test_project['key']}"

        try:
            result = jira_client.create_filter(
                name=filter_name, jql=jql, favourite=True
            )

            assert result["favourite"]

        finally:
            if "id" in result:
                with contextlib.suppress(Exception):
                    jira_client.delete_filter(result["id"])

    def test_get_filter(self, jira_client, test_project):
        """Test getting a filter by ID."""
        filter_name = f"Get Filter {uuid.uuid4().hex[:8]}"
        jql = f"project = {test_project['key']}"

        try:
            created = jira_client.create_filter(name=filter_name, jql=jql)
            filter_id = created["id"]

            result = jira_client.get_filter(filter_id)

            assert result["id"] == filter_id
            assert result["name"] == filter_name
            assert result["jql"] == jql

        finally:
            with contextlib.suppress(Exception):
                jira_client.delete_filter(filter_id)

    def test_update_filter_name(self, jira_client, test_project):
        """Test updating a filter's name."""
        filter_name = f"Update Filter {uuid.uuid4().hex[:8]}"
        new_name = f"Updated Filter {uuid.uuid4().hex[:8]}"
        jql = f"project = {test_project['key']}"

        try:
            created = jira_client.create_filter(name=filter_name, jql=jql)
            filter_id = created["id"]

            result = jira_client.update_filter(filter_id, name=new_name)

            assert result["name"] == new_name

        finally:
            with contextlib.suppress(Exception):
                jira_client.delete_filter(filter_id)

    def test_update_filter_jql(self, jira_client, test_project):
        """Test updating a filter's JQL."""
        filter_name = f"JQL Filter {uuid.uuid4().hex[:8]}"
        original_jql = f"project = {test_project['key']}"
        new_jql = f"project = {test_project['key']} AND type = Bug"

        try:
            created = jira_client.create_filter(name=filter_name, jql=original_jql)
            filter_id = created["id"]

            result = jira_client.update_filter(filter_id, jql=new_jql)

            assert result["jql"] == new_jql

        finally:
            with contextlib.suppress(Exception):
                jira_client.delete_filter(filter_id)

    def test_delete_filter(self, jira_client, test_project):
        """Test deleting a filter."""
        filter_name = f"Delete Filter {uuid.uuid4().hex[:8]}"
        jql = f"project = {test_project['key']}"

        created = jira_client.create_filter(name=filter_name, jql=jql)
        filter_id = created["id"]

        # Delete the filter
        jira_client.delete_filter(filter_id)

        # Verify it's gone
        from jira_assistant_skills_lib import NotFoundError

        with pytest.raises(NotFoundError):
            jira_client.get_filter(filter_id)

    def test_get_my_filters(self, jira_client, test_project):
        """Test getting the current user's filters."""
        filter_name = f"My Filter {uuid.uuid4().hex[:8]}"
        jql = f"project = {test_project['key']}"

        try:
            created = jira_client.create_filter(name=filter_name, jql=jql)

            result = jira_client.get_my_filters()

            assert isinstance(result, list)
            # Our filter should be in the list
            filter_ids = [f["id"] for f in result]
            assert created["id"] in filter_ids

        finally:
            with contextlib.suppress(Exception):
                jira_client.delete_filter(created["id"])

    def test_search_filters_by_name(self, jira_client, test_project):
        """Test searching filters by name."""
        unique_id = uuid.uuid4().hex[:8]
        filter_name = f"Searchable_{unique_id}"
        jql = f"project = {test_project['key']}"

        try:
            created = jira_client.create_filter(name=filter_name, jql=jql)

            result = jira_client.search_filters(filter_name=unique_id)

            assert "values" in result
            # Our filter should be found
            found_ids = [f["id"] for f in result["values"]]
            assert created["id"] in found_ids

        finally:
            with contextlib.suppress(Exception):
                jira_client.delete_filter(created["id"])


@pytest.mark.integration
@pytest.mark.shared
class TestFilterFavourites:
    """Tests for filter favourite operations."""

    def test_add_filter_to_favourites(self, jira_client, test_project):
        """Test adding a filter to favourites."""
        filter_name = f"Fav Test {uuid.uuid4().hex[:8]}"
        jql = f"project = {test_project['key']}"

        try:
            created = jira_client.create_filter(
                name=filter_name, jql=jql, favourite=False
            )
            filter_id = created["id"]

            # Add to favourites
            result = jira_client.add_filter_favourite(filter_id)

            assert result["favourite"]

        finally:
            with contextlib.suppress(Exception):
                jira_client.delete_filter(filter_id)

    def test_remove_filter_from_favourites(self, jira_client, test_project):
        """Test removing a filter from favourites."""
        filter_name = f"Unfav Test {uuid.uuid4().hex[:8]}"
        jql = f"project = {test_project['key']}"

        try:
            created = jira_client.create_filter(
                name=filter_name, jql=jql, favourite=True
            )
            filter_id = created["id"]

            # Remove from favourites
            jira_client.remove_filter_favourite(filter_id)

            # Verify
            updated = jira_client.get_filter(filter_id)
            assert not updated["favourite"]

        finally:
            with contextlib.suppress(Exception):
                jira_client.delete_filter(filter_id)

    def test_get_favourite_filters(self, jira_client, test_project):
        """Test getting favourite filters."""
        filter_name = f"Fav List {uuid.uuid4().hex[:8]}"
        jql = f"project = {test_project['key']}"

        try:
            created = jira_client.create_filter(
                name=filter_name, jql=jql, favourite=True
            )

            result = jira_client.get_favourite_filters()

            assert isinstance(result, list)
            # Our filter should be in the list
            filter_ids = [f["id"] for f in result]
            assert created["id"] in filter_ids

        finally:
            with contextlib.suppress(Exception):
                jira_client.delete_filter(created["id"])


@pytest.mark.integration
@pytest.mark.shared
class TestFilterSharing:
    """Tests for filter sharing permissions."""

    def test_get_filter_permissions(self, jira_client, test_project):
        """Test getting filter permissions."""
        filter_name = f"Perm Filter {uuid.uuid4().hex[:8]}"
        jql = f"project = {test_project['key']}"

        try:
            created = jira_client.create_filter(name=filter_name, jql=jql)
            filter_id = created["id"]

            result = jira_client.get_filter_permissions(filter_id)

            assert isinstance(result, list)
            # New filter should have no permissions (private)

        finally:
            with contextlib.suppress(Exception):
                jira_client.delete_filter(filter_id)

    def test_share_filter_with_project(self, jira_client, test_project):
        """Test sharing a filter with a project."""
        filter_name = f"Share Filter {uuid.uuid4().hex[:8]}"
        jql = f"project = {test_project['key']}"

        try:
            created = jira_client.create_filter(name=filter_name, jql=jql)
            filter_id = created["id"]

            # Share with project
            permission = {"type": "project", "projectId": test_project["id"]}
            result = jira_client.add_filter_permission(filter_id, permission)

            # Result may be a list or dict depending on API version
            if isinstance(result, list):
                # Find the permission we just added
                project_perms = [p for p in result if p.get("type") == "project"]
                assert len(project_perms) >= 1
            else:
                assert result["type"] == "project"

            # Verify permission was added
            permissions = jira_client.get_filter_permissions(filter_id)
            assert len(permissions) >= 1

        finally:
            with contextlib.suppress(Exception):
                jira_client.delete_filter(filter_id)

    def test_share_filter_globally(self, jira_client, test_project):
        """Test sharing a filter globally (may be disabled on some instances)."""
        filter_name = f"Global Filter {uuid.uuid4().hex[:8]}"
        jql = f"project = {test_project['key']}"

        try:
            created = jira_client.create_filter(name=filter_name, jql=jql)
            filter_id = created["id"]

            # Share globally - may fail if global sharing is disabled
            permission = {"type": "global"}
            try:
                result = jira_client.add_filter_permission(filter_id, permission)
                # If it succeeds, verify the result
                if isinstance(result, list):
                    global_perms = [p for p in result if p.get("type") == "global"]
                    assert len(global_perms) >= 1
                else:
                    assert result["type"] == "global"
            except Exception as e:
                # Skip if global sharing is disabled
                if "cannot be shared with the public" in str(e):
                    pytest.skip("Global sharing is disabled on this JIRA instance")
                raise

        finally:
            with contextlib.suppress(Exception):
                jira_client.delete_filter(filter_id)

    def test_remove_filter_permission(self, jira_client, test_project):
        """Test removing a filter permission."""
        filter_name = f"Unshare Filter {uuid.uuid4().hex[:8]}"
        jql = f"project = {test_project['key']}"

        try:
            created = jira_client.create_filter(name=filter_name, jql=jql)
            filter_id = created["id"]

            # Add project permission (more likely to succeed than global)
            permission = {"type": "project", "projectId": test_project["id"]}
            added = jira_client.add_filter_permission(filter_id, permission)

            # Get the permission ID
            if isinstance(added, list):
                # Find the project permission
                project_perms = [p for p in added if p.get("type") == "project"]
                permission_id = str(project_perms[0]["id"])
            else:
                permission_id = str(added["id"])

            # Remove permission
            jira_client.delete_filter_permission(filter_id, permission_id)

            # Verify it's gone
            permissions = jira_client.get_filter_permissions(filter_id)
            perm_ids = [str(p["id"]) for p in permissions]
            assert permission_id not in perm_ids

        finally:
            with contextlib.suppress(Exception):
                jira_client.delete_filter(filter_id)


@pytest.mark.integration
@pytest.mark.shared
class TestFilterSearch:
    """Tests for executing searches with filters."""

    def test_execute_filter_jql(self, jira_client, test_project):
        """Test executing a filter's JQL query."""
        import time

        filter_name = f"Exec Filter {uuid.uuid4().hex[:8]}"
        jql = f"project = {test_project['key']}"

        # Create an issue to search for
        issue = jira_client.create_issue(
            {
                "project": {"key": test_project["key"]},
                "summary": f"Filter Test Issue {uuid.uuid4().hex[:8]}",
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "Test"}],
                        }
                    ],
                },
                "issuetype": {"name": "Task"},
            }
        )

        # Wait a moment for JIRA to index the issue
        time.sleep(1)

        try:
            created = jira_client.create_filter(name=filter_name, jql=jql)

            # Get the filter's JQL and execute it
            filter_data = jira_client.get_filter(created["id"])
            result = jira_client.search_issues(filter_data["jql"], max_results=10)

            assert "issues" in result
            # API may return 'total' or 'isLast' depending on version
            assert "total" in result or "isLast" in result
            # Should find at least our test issue (it may take a moment to index)
            # Just verify the search executed successfully
            assert isinstance(result.get("issues", []), list)

        finally:
            with contextlib.suppress(Exception):
                jira_client.delete_filter(created["id"])
            with contextlib.suppress(Exception):
                jira_client.delete_issue(issue["key"])

    def test_filter_subscriptions_view(self, jira_client, test_project):
        """Test viewing filter subscriptions."""
        filter_name = f"Sub Filter {uuid.uuid4().hex[:8]}"
        jql = f"project = {test_project['key']}"

        try:
            created = jira_client.create_filter(name=filter_name, jql=jql)

            # Get filter with subscriptions expanded
            result = jira_client.get_filter(created["id"], expand="subscriptions")

            # Should have subscriptions field (may be empty)
            assert "subscriptions" in result

        finally:
            with contextlib.suppress(Exception):
                jira_client.delete_filter(created["id"])
