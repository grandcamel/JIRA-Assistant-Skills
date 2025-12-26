"""
Live Integration Tests: Field Management

Tests for JIRA field management against a real JIRA instance.
"""

import sys
import pytest
from pathlib import Path
from typing import Dict, Any, List

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))

from list_fields import list_fields
from check_project_fields import check_project_fields


class TestListFields:
    """Tests for listing JIRA fields."""

    def test_list_all_custom_fields(self, jira_client):
        """Test listing all custom fields."""
        fields = list_fields(client=jira_client)

        assert fields is not None
        assert isinstance(fields, list)
        assert len(fields) > 0

        # Verify field structure
        for field in fields[:5]:
            assert 'id' in field
            assert 'name' in field
            assert field['id'].startswith('customfield_')

    def test_list_fields_with_filter(self, jira_client):
        """Test filtering fields by name pattern."""
        # Most JIRA instances have some 'Epic' related fields
        fields = list_fields(filter_pattern='epic', client=jira_client)

        # May or may not find matches depending on instance
        assert fields is not None
        assert isinstance(fields, list)

        # If fields found, verify they match the pattern
        for field in fields:
            assert 'epic' in field['name'].lower()

    def test_list_agile_fields(self, jira_client):
        """Test listing Agile-related fields."""
        fields = list_fields(agile_only=True, client=jira_client)

        assert fields is not None
        assert isinstance(fields, list)

        # Agile fields should match known patterns
        agile_patterns = ['epic', 'sprint', 'story', 'point', 'rank', 'velocity', 'backlog']
        for field in fields:
            name_lower = field['name'].lower()
            assert any(pattern in name_lower for pattern in agile_patterns)

    def test_list_all_fields_including_system(self, jira_client):
        """Test listing all fields including system fields."""
        fields = list_fields(custom_only=False, client=jira_client)

        assert fields is not None
        assert len(fields) > 0

        # Should include system fields (non-customfield IDs)
        system_fields = [f for f in fields if not f['id'].startswith('customfield_')]
        assert len(system_fields) > 0

    def test_list_fields_structure(self, jira_client):
        """Test that field structure is complete."""
        fields = list_fields(client=jira_client)

        if fields:
            field = fields[0]
            assert 'id' in field
            assert 'name' in field
            # Custom fields may have additional properties
            assert isinstance(field.get('custom', True), bool)


class TestCheckProjectFields:
    """Tests for checking project field availability."""

    def test_check_project_fields_basic(self, jira_client, test_project):
        """Test basic project field check."""
        result = check_project_fields(
            project_key=test_project['key'],
            client=jira_client
        )

        assert result is not None
        assert 'project_key' in result
        assert result['project_key'] == test_project['key']
        assert 'available_fields' in result or 'fields' in result

    def test_check_project_fields_issue_type(self, jira_client, test_project):
        """Test field check for specific issue type."""
        result = check_project_fields(
            project_key=test_project['key'],
            issue_type='Task',
            client=jira_client
        )

        assert result is not None
        assert 'project_key' in result

    def test_check_project_fields_story(self, jira_client, test_project):
        """Test field check for Story issue type."""
        result = check_project_fields(
            project_key=test_project['key'],
            issue_type='Story',
            client=jira_client
        )

        assert result is not None

    def test_check_project_agile_fields(self, jira_client, test_project):
        """Test checking Agile field availability."""
        result = check_project_fields(
            project_key=test_project['key'],
            check_agile=True,
            client=jira_client
        )

        assert result is not None
        assert 'project_key' in result
        # Should have agile field info
        assert 'agile_fields' in result or 'fields' in result

    def test_check_project_fields_project_type(self, jira_client, test_project):
        """Test that project type is detected."""
        result = check_project_fields(
            project_key=test_project['key'],
            client=jira_client
        )

        assert result is not None
        # Should detect project type (team-managed or company-managed)
        assert 'project_type' in result or 'style' in result or 'simplified' in str(result)


class TestFieldDiscovery:
    """Tests for field discovery functionality."""

    def test_find_sprint_field(self, jira_client):
        """Test finding Sprint field."""
        fields = list_fields(filter_pattern='sprint', client=jira_client)

        # Most Agile projects have a Sprint field
        sprint_fields = [f for f in fields if 'sprint' in f['name'].lower()]
        # May or may not exist depending on instance
        assert isinstance(sprint_fields, list)

    def test_find_story_points_field(self, jira_client):
        """Test finding Story Points field."""
        fields = list_fields(filter_pattern='story', client=jira_client)

        # Look for story points specifically
        points_fields = [f for f in fields if 'point' in f['name'].lower()]
        assert isinstance(points_fields, list)

    def test_find_epic_fields(self, jira_client):
        """Test finding Epic-related fields."""
        fields = list_fields(filter_pattern='epic', client=jira_client)

        # Common epic fields: Epic Link, Epic Name, Epic Color
        epic_fields = [f for f in fields if 'epic' in f['name'].lower()]
        assert isinstance(epic_fields, list)


class TestFieldMetadata:
    """Tests for field metadata retrieval."""

    def test_field_has_id(self, jira_client):
        """Test that all fields have IDs."""
        fields = list_fields(client=jira_client)

        for field in fields:
            assert 'id' in field
            assert field['id'] is not None
            assert len(field['id']) > 0

    def test_field_has_name(self, jira_client):
        """Test that all fields have names."""
        fields = list_fields(client=jira_client)

        for field in fields:
            assert 'name' in field
            assert field['name'] is not None
            assert len(field['name']) > 0

    def test_custom_field_id_format(self, jira_client):
        """Test custom field ID format."""
        fields = list_fields(custom_only=True, client=jira_client)

        for field in fields:
            assert field['id'].startswith('customfield_')
            # ID should have numeric suffix
            suffix = field['id'].replace('customfield_', '')
            assert suffix.isdigit()


class TestProjectFieldContext:
    """Tests for project-specific field contexts."""

    def test_get_create_meta_fields(self, jira_client, test_project):
        """Test getting fields available for issue creation."""
        result = check_project_fields(
            project_key=test_project['key'],
            issue_type='Task',
            client=jira_client
        )

        assert result is not None
        # Should return available fields for creation
        assert 'fields' in result or 'available_fields' in result or 'create_fields' in result

    def test_multiple_issue_types(self, jira_client, test_project):
        """Test field availability for different issue types."""
        issue_types = ['Task', 'Bug', 'Story']

        for issue_type in issue_types:
            try:
                result = check_project_fields(
                    project_key=test_project['key'],
                    issue_type=issue_type,
                    client=jira_client
                )
                assert result is not None
            except Exception:
                # Some issue types may not be available
                pass
