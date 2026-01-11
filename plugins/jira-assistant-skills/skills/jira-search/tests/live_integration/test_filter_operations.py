"""
Live Integration Tests for filter operations.

Tests create_filter.py, run_filter.py, update_filter.py, delete_filter.py
functionality against a real JIRA instance.

Usage:
    pytest plugins/jira-assistant-skills/skills/jira-search/tests/live_integration/test_filter_operations.py --profile development -v
"""

import pytest
import uuid
import sys
from pathlib import Path

# Add scripts to path
_this_dir = Path(__file__).parent
_scripts_path = _this_dir.parent.parent / 'scripts'
sys.path.insert(0, str(_scripts_path))

from create_filter import create_filter
from run_filter import run_filter
from update_filter import update_filter
from delete_filter import delete_filter
from get_filters import get_my_filters, get_favourite_filters


@pytest.mark.integration
@pytest.mark.search
class TestCreateFilter:
    """Tests for create_filter.py functionality."""

    def test_create_filter_basic(self, jira_client, test_project, jira_profile):
        """Test creating a basic filter."""
        filter_name = f"Test Filter {uuid.uuid4().hex[:8]}"
        jql = f"project = {test_project['key']}"

        result = create_filter(
            jira_client,
            name=filter_name,
            jql=jql
        )

        try:
            assert 'id' in result
            assert result['name'] == filter_name
            assert result['jql'] == jql
        finally:
            # Cleanup
            jira_client.delete_filter(result['id'])

    def test_create_filter_with_description(self, jira_client, test_project, jira_profile):
        """Test creating a filter with description."""
        filter_name = f"Test Filter {uuid.uuid4().hex[:8]}"
        jql = f"project = {test_project['key']}"
        description = "This is a test filter description"

        result = create_filter(
            jira_client,
            name=filter_name,
            jql=jql,
            description=description
        )

        try:
            assert result['description'] == description
        finally:
            jira_client.delete_filter(result['id'])

    def test_create_filter_as_favourite(self, jira_client, test_project, jira_profile):
        """Test creating a filter marked as favourite."""
        filter_name = f"Test Favourite Filter {uuid.uuid4().hex[:8]}"
        jql = f"project = {test_project['key']}"

        result = create_filter(
            jira_client,
            name=filter_name,
            jql=jql,
            favourite=True
        )

        try:
            assert result.get('favourite', False) == True
        finally:
            jira_client.delete_filter(result['id'])

    def test_create_filter_complex_jql(self, jira_client, test_project, jira_profile):
        """Test creating a filter with complex JQL."""
        filter_name = f"Complex Filter {uuid.uuid4().hex[:8]}"
        jql = f"project = {test_project['key']} AND type = Bug AND priority IN (High, Medium) ORDER BY created DESC"

        result = create_filter(
            jira_client,
            name=filter_name,
            jql=jql
        )

        try:
            assert 'id' in result
            assert jql in result['jql'] or result['jql'] == jql
        finally:
            jira_client.delete_filter(result['id'])


@pytest.mark.integration
@pytest.mark.search
class TestRunFilter:
    """Tests for run_filter.py functionality."""

    def test_run_filter_by_id(self, jira_client, test_project, test_filter, test_issues, jira_profile):
        """Test running a filter by ID."""
        result = run_filter(
            filter_id=test_filter['id'],
            profile=jira_profile
        )

        assert 'issues' in result
        # Filter queries the test project, so should find our test issues
        assert len(result['issues']) >= 1

    def test_run_filter_by_name(self, jira_client, test_project, test_filter, test_issues, jira_profile):
        """Test running a filter by name."""
        result = run_filter(
            filter_name=test_filter['name'],
            profile=jira_profile
        )

        assert 'issues' in result

    def test_run_filter_with_max_results(self, jira_client, test_project, test_filter, test_issues, jira_profile):
        """Test running a filter with max results limit."""
        result = run_filter(
            filter_id=test_filter['id'],
            max_results=2,
            profile=jira_profile
        )

        assert 'issues' in result
        assert len(result['issues']) <= 2

    def test_run_filter_not_found(self, jira_profile):
        """Test running a non-existent filter."""
        from jira_assistant_skills_lib import ValidationError

        with pytest.raises(ValidationError):
            run_filter(
                filter_name="NonExistent Filter 99999",
                profile=jira_profile
            )


@pytest.mark.integration
@pytest.mark.search
class TestUpdateFilter:
    """Tests for update_filter.py functionality."""

    def test_update_filter_name(self, jira_client, test_project, jira_profile):
        """Test updating filter name."""
        # Create a filter to update
        original = jira_client.create_filter(
            name=f"Original Filter {uuid.uuid4().hex[:8]}",
            jql=f"project = {test_project['key']}"
        )

        try:
            new_name = f"Updated Filter {uuid.uuid4().hex[:8]}"
            result = update_filter(
                jira_client,
                filter_id=original['id'],
                name=new_name
            )

            assert result['name'] == new_name
        finally:
            jira_client.delete_filter(original['id'])

    def test_update_filter_jql(self, jira_client, test_project, jira_profile):
        """Test updating filter JQL."""
        original = jira_client.create_filter(
            name=f"JQL Update Filter {uuid.uuid4().hex[:8]}",
            jql=f"project = {test_project['key']}"
        )

        try:
            new_jql = f"project = {test_project['key']} AND type = Bug"
            result = update_filter(
                jira_client,
                filter_id=original['id'],
                jql=new_jql
            )

            assert result['jql'] == new_jql
        finally:
            jira_client.delete_filter(original['id'])

    def test_update_filter_description(self, jira_client, test_project, jira_profile):
        """Test updating filter description."""
        original = jira_client.create_filter(
            name=f"Desc Update Filter {uuid.uuid4().hex[:8]}",
            jql=f"project = {test_project['key']}"
        )

        try:
            new_desc = "Updated description"
            result = update_filter(
                jira_client,
                filter_id=original['id'],
                description=new_desc
            )

            assert result['description'] == new_desc
        finally:
            jira_client.delete_filter(original['id'])


@pytest.mark.integration
@pytest.mark.search
class TestDeleteFilter:
    """Tests for delete_filter.py functionality."""

    def test_delete_filter(self, jira_client, test_project, jira_profile):
        """Test deleting a filter."""
        # Create a filter to delete
        created = jira_client.create_filter(
            name=f"To Delete Filter {uuid.uuid4().hex[:8]}",
            jql=f"project = {test_project['key']}"
        )

        # Delete it
        delete_filter(jira_client, filter_id=created['id'])

        # Verify it's gone
        from jira_assistant_skills_lib import NotFoundError
        with pytest.raises((NotFoundError, Exception)):
            jira_client.get_filter(created['id'])

    def test_delete_filter_not_found(self, jira_client, jira_profile):
        """Test deleting a non-existent filter."""
        from jira_assistant_skills_lib import NotFoundError

        with pytest.raises((NotFoundError, Exception)):
            delete_filter(jira_client, filter_id="999999999")


@pytest.mark.integration
@pytest.mark.search
class TestGetFilters:
    """Tests for get_filters.py functionality."""

    def test_get_my_filters(self, jira_client, test_filter, jira_profile):
        """Test getting user's filters."""
        result = get_my_filters(jira_client)

        # Should return a list of filters
        assert isinstance(result, list)
        # Our test filter should be in the list
        filter_ids = [f['id'] for f in result]
        assert test_filter['id'] in filter_ids

    def test_get_favourite_filters(self, jira_client, test_project, jira_profile):
        """Test getting favourite filters."""
        # Create a favourite filter
        fav_filter = jira_client.create_filter(
            name=f"Fav Filter {uuid.uuid4().hex[:8]}",
            jql=f"project = {test_project['key']}",
            favourite=True
        )

        try:
            result = get_favourite_filters(jira_client)

            assert isinstance(result, list)
            # Our favourite filter should be in the list
            filter_ids = [f['id'] for f in result]
            assert fav_filter['id'] in filter_ids
        finally:
            jira_client.delete_filter(fav_filter['id'])


@pytest.mark.integration
@pytest.mark.search
class TestFilterLifecycle:
    """Tests for complete filter lifecycle."""

    def test_filter_lifecycle(self, jira_client, test_project, test_issues, jira_profile):
        """Test complete filter lifecycle: create -> run -> update -> delete."""
        # Create
        filter_name = f"Lifecycle Filter {uuid.uuid4().hex[:8]}"
        jql = f"project = {test_project['key']}"

        created = create_filter(
            jira_client,
            name=filter_name,
            jql=jql,
            description="Initial description"
        )

        filter_id = created['id']

        try:
            # Run
            results = run_filter(filter_id=filter_id, profile=jira_profile)
            assert 'issues' in results
            initial_count = len(results['issues'])

            # Update to narrow search
            new_jql = f"project = {test_project['key']} AND type = Bug"
            updated = update_filter(
                jira_client,
                filter_id=filter_id,
                jql=new_jql
            )
            assert updated['jql'] == new_jql

            # Run again with updated filter
            results_after = run_filter(filter_id=filter_id, profile=jira_profile)
            assert 'issues' in results_after
            # Should have fewer or equal results after narrowing
            assert len(results_after['issues']) <= initial_count

        finally:
            # Delete
            delete_filter(jira_client, filter_id=filter_id)

            # Verify deletion
            from jira_assistant_skills_lib import NotFoundError
            with pytest.raises((NotFoundError, Exception)):
                jira_client.get_filter(filter_id)
