# Test Remediation Plan: jira-fields Skill

**Created:** 2025-12-26
**Status:** Draft
**Test Files Reviewed:** 3 (live integration only)
**Scripts Analyzed:** 4
**Total Issues Identified:** ~45+

---

## Executive Summary

This plan addresses test quality issues discovered during a comprehensive review of the `jira-fields` skill test suite. The most critical finding is that **no unit tests exist** - only live integration tests are present. This creates several problems:
1. Tests require a live JIRA instance to run
2. CI/CD pipelines cannot run tests without credentials
3. Edge cases and error scenarios are difficult to test
4. Test execution is slow and unpredictable

**Issue Summary by Category:**
| Category | Count |
|----------|-------|
| Scripts completely untested (no unit tests) | 4 |
| Missing pytest markers on test classes | 6 |
| Weak assertions | 8 |
| Missing error handling tests | 16 |
| Missing dry-run tests | 1 |
| Fixture mutations (need deepcopy) | 2 |
| Unused imports | 3 |
| Missing conftest.py for unit tests | 1 |

**Estimated Effort:**
- Phase 1 (Critical - Create Unit Tests): 8-12 hours
- Phase 2 (High Priority - Error Handling): 4-6 hours
- Phase 3 (Medium Priority - Edge Cases): 3-4 hours
- Phase 4 (Low Priority - Code Quality): 1-2 hours

---

## Phase 1: Critical Issues (Must Fix)

### 1.1 No Unit Tests Exist - Scripts Completely Untested

**Impact:** Cannot run tests without live JIRA instance, no fast feedback loop
**Scripts Affected:** 4 scripts (100% of skill)

| Script | Functions | Complexity | Priority |
|--------|-----------|------------|----------|
| `scripts/list_fields.py` | `list_fields()` | Low | High |
| `scripts/check_project_fields.py` | `check_project_fields()` | Medium | High |
| `scripts/configure_agile_fields.py` | `configure_agile_fields()`, `find_agile_fields()`, `find_project_screens()`, `add_field_to_screen()` | High | High |
| `scripts/create_field.py` | `create_field()` | Low | High |

**Required Actions:**

1. Create `tests/unit/` directory structure
2. Create `tests/unit/__init__.py`
3. Create `tests/unit/conftest.py` with mock fixtures
4. Create unit test files for each script

**Directory Structure to Create:**

```
.claude/skills/jira-fields/tests/
├── __init__.py (new)
├── conftest.py (new - shared fixtures)
├── unit/
│   ├── __init__.py (new)
│   ├── conftest.py (new - unit-specific fixtures)
│   ├── test_list_fields.py (new)
│   ├── test_check_project_fields.py (new)
│   ├── test_configure_agile_fields.py (new)
│   └── test_create_field.py (new)
└── live_integration/
    ├── __init__.py (exists)
    ├── conftest.py (exists)
    └── test_field_management.py (exists)
```

**1.1.1 Create tests/unit/conftest.py:**

```python
"""
Unit Test Configuration for jira-fields skill.

Usage:
    pytest .claude/skills/jira-fields/tests/unit/ -v
"""

import sys
import copy
import pytest
from pathlib import Path
from unittest.mock import MagicMock, Mock

# Add paths
test_dir = Path(__file__).parent  # unit
tests_dir = test_dir.parent  # tests
jira_fields_dir = tests_dir.parent  # jira-fields
scripts_dir = jira_fields_dir / 'scripts'
shared_lib_dir = jira_fields_dir.parent / 'shared' / 'scripts' / 'lib'

sys.path.insert(0, str(scripts_dir))
sys.path.insert(0, str(shared_lib_dir))


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "fields: mark test as fields skill test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")


@pytest.fixture
def mock_jira_client():
    """Create a mock JIRA client."""
    client = MagicMock()
    client.close = MagicMock()
    return client


# Sample API responses
SAMPLE_FIELDS_RESPONSE = [
    {
        'id': 'customfield_10001',
        'name': 'Sprint',
        'custom': True,
        'searchable': True,
        'navigable': True,
        'schema': {'type': 'array', 'items': 'string'}
    },
    {
        'id': 'customfield_10002',
        'name': 'Story Points',
        'custom': True,
        'searchable': True,
        'navigable': True,
        'schema': {'type': 'number'}
    },
    {
        'id': 'customfield_10003',
        'name': 'Epic Link',
        'custom': True,
        'searchable': True,
        'navigable': True,
        'schema': {'type': 'any'}
    },
    {
        'id': 'customfield_10004',
        'name': 'Epic Name',
        'custom': True,
        'searchable': True,
        'navigable': True,
        'schema': {'type': 'string'}
    },
    {
        'id': 'customfield_10005',
        'name': 'Rank',
        'custom': True,
        'searchable': True,
        'navigable': True,
        'schema': {'type': 'any'}
    },
    {
        'id': 'summary',
        'name': 'Summary',
        'custom': False,
        'searchable': True,
        'navigable': True,
        'schema': {'type': 'string'}
    },
    {
        'id': 'description',
        'name': 'Description',
        'custom': False,
        'searchable': True,
        'navigable': True,
        'schema': {'type': 'string'}
    }
]


SAMPLE_PROJECT_RESPONSE = {
    'id': '10001',
    'key': 'TEST',
    'name': 'Test Project',
    'style': 'classic',
    'simplified': False,
    'projectTypeKey': 'software'
}


SAMPLE_PROJECT_TEAM_MANAGED = {
    'id': '10002',
    'key': 'TEAM',
    'name': 'Team Managed Project',
    'style': 'next-gen',
    'simplified': True,
    'projectTypeKey': 'software'
}


SAMPLE_CREATE_META_RESPONSE = {
    'projects': [{
        'id': '10001',
        'key': 'TEST',
        'issuetypes': [
            {
                'id': '10001',
                'name': 'Task',
                'fields': {
                    'summary': {'name': 'Summary', 'required': True},
                    'description': {'name': 'Description', 'required': False},
                    'customfield_10001': {'name': 'Sprint', 'required': False},
                    'customfield_10002': {'name': 'Story Points', 'required': False}
                }
            },
            {
                'id': '10002',
                'name': 'Story',
                'fields': {
                    'summary': {'name': 'Summary', 'required': True},
                    'description': {'name': 'Description', 'required': False},
                    'customfield_10001': {'name': 'Sprint', 'required': False},
                    'customfield_10002': {'name': 'Story Points', 'required': False},
                    'customfield_10003': {'name': 'Epic Link', 'required': False}
                }
            }
        ]
    }]
}


SAMPLE_SCREEN_SCHEMES_RESPONSE = {
    'values': [{
        'issueTypeScreenScheme': {
            'id': '10001',
            'name': 'Default Screen Scheme'
        }
    }]
}


SAMPLE_SCREEN_SCHEME_MAPPING = {
    'values': [{
        'screenSchemeId': '10001'
    }]
}


SAMPLE_SCREEN_SCHEME = {
    'id': '10001',
    'name': 'Default Screen Scheme',
    'screens': {
        'default': 10001,
        'create': 10002,
        'edit': 10003
    }
}


SAMPLE_SCREEN = {
    'id': 10001,
    'name': 'Default Screen'
}


SAMPLE_SCREEN_TABS = [{
    'id': 10001,
    'name': 'Field Tab'
}]


SAMPLE_SCREEN_FIELDS = [{
    'id': 'summary',
    'name': 'Summary'
}]


SAMPLE_CREATED_FIELD = {
    'id': 'customfield_10100',
    'name': 'Test Field',
    'schema': {'type': 'number'},
    'custom': True
}


@pytest.fixture
def sample_fields_response():
    """Sample fields API response."""
    return copy.deepcopy(SAMPLE_FIELDS_RESPONSE)


@pytest.fixture
def sample_project_response():
    """Sample project API response."""
    return copy.deepcopy(SAMPLE_PROJECT_RESPONSE)


@pytest.fixture
def sample_project_team_managed():
    """Sample team-managed project response."""
    return copy.deepcopy(SAMPLE_PROJECT_TEAM_MANAGED)


@pytest.fixture
def sample_create_meta_response():
    """Sample create meta API response."""
    return copy.deepcopy(SAMPLE_CREATE_META_RESPONSE)


@pytest.fixture
def sample_screen_schemes_response():
    """Sample screen schemes response."""
    return copy.deepcopy(SAMPLE_SCREEN_SCHEMES_RESPONSE)


@pytest.fixture
def sample_screen_scheme_mapping():
    """Sample screen scheme mapping."""
    return copy.deepcopy(SAMPLE_SCREEN_SCHEME_MAPPING)


@pytest.fixture
def sample_screen_scheme():
    """Sample screen scheme."""
    return copy.deepcopy(SAMPLE_SCREEN_SCHEME)


@pytest.fixture
def sample_screen():
    """Sample screen."""
    return copy.deepcopy(SAMPLE_SCREEN)


@pytest.fixture
def sample_screen_tabs():
    """Sample screen tabs."""
    return copy.deepcopy(SAMPLE_SCREEN_TABS)


@pytest.fixture
def sample_screen_fields():
    """Sample screen fields."""
    return copy.deepcopy(SAMPLE_SCREEN_FIELDS)


@pytest.fixture
def sample_created_field():
    """Sample created field response."""
    return copy.deepcopy(SAMPLE_CREATED_FIELD)
```

**1.1.2 Create tests/unit/test_list_fields.py:**

```python
"""
Unit Tests: list_fields.py

Tests for listing JIRA custom fields.
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Path setup
test_dir = Path(__file__).parent
tests_dir = test_dir.parent
jira_fields_dir = tests_dir.parent
scripts_dir = jira_fields_dir / 'scripts'
shared_lib_dir = jira_fields_dir.parent / 'shared' / 'scripts' / 'lib'

sys.path.insert(0, str(scripts_dir))
sys.path.insert(0, str(shared_lib_dir))

from list_fields import list_fields, AGILE_PATTERNS


@pytest.mark.fields
@pytest.mark.unit
class TestListFieldsBasic:
    """Test basic list_fields functionality."""

    def test_list_all_custom_fields(self, mock_jira_client, sample_fields_response):
        """Test listing all custom fields."""
        mock_jira_client.get.return_value = sample_fields_response

        result = list_fields(client=mock_jira_client)

        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 5  # Only custom fields
        mock_jira_client.get.assert_called_once_with('/rest/api/3/field')

    def test_list_includes_system_fields(self, mock_jira_client, sample_fields_response):
        """Test listing all fields including system fields."""
        mock_jira_client.get.return_value = sample_fields_response

        result = list_fields(custom_only=False, client=mock_jira_client)

        assert result is not None
        assert len(result) == 7  # All fields
        system_fields = [f for f in result if not f['id'].startswith('customfield_')]
        assert len(system_fields) == 2

    def test_list_fields_structure(self, mock_jira_client, sample_fields_response):
        """Test that returned fields have correct structure."""
        mock_jira_client.get.return_value = sample_fields_response

        result = list_fields(client=mock_jira_client)

        for field in result:
            assert 'id' in field
            assert 'name' in field
            assert 'type' in field
            assert 'custom' in field
            assert 'searchable' in field
            assert 'navigable' in field

    def test_list_fields_sorted_by_name(self, mock_jira_client, sample_fields_response):
        """Test that fields are sorted alphabetically by name."""
        mock_jira_client.get.return_value = sample_fields_response

        result = list_fields(client=mock_jira_client)

        names = [f['name'] for f in result]
        assert names == sorted(names, key=str.lower)


@pytest.mark.fields
@pytest.mark.unit
class TestListFieldsFiltering:
    """Test list_fields filtering options."""

    def test_filter_by_pattern(self, mock_jira_client, sample_fields_response):
        """Test filtering fields by name pattern."""
        mock_jira_client.get.return_value = sample_fields_response

        result = list_fields(filter_pattern='epic', client=mock_jira_client)

        assert len(result) == 2  # Epic Link and Epic Name
        for field in result:
            assert 'epic' in field['name'].lower()

    def test_filter_case_insensitive(self, mock_jira_client, sample_fields_response):
        """Test that filtering is case-insensitive."""
        mock_jira_client.get.return_value = sample_fields_response

        result = list_fields(filter_pattern='SPRINT', client=mock_jira_client)

        assert len(result) == 1
        assert result[0]['name'] == 'Sprint'

    def test_filter_no_matches(self, mock_jira_client, sample_fields_response):
        """Test filtering with no matches returns empty list."""
        mock_jira_client.get.return_value = sample_fields_response

        result = list_fields(filter_pattern='nonexistent', client=mock_jira_client)

        assert result == []

    def test_agile_only_filter(self, mock_jira_client, sample_fields_response):
        """Test filtering for Agile-related fields only."""
        mock_jira_client.get.return_value = sample_fields_response

        result = list_fields(agile_only=True, client=mock_jira_client)

        assert len(result) == 5  # Sprint, Story Points, Epic Link, Epic Name, Rank
        for field in result:
            name_lower = field['name'].lower()
            assert any(pattern in name_lower for pattern in AGILE_PATTERNS)


@pytest.mark.fields
@pytest.mark.unit
class TestListFieldsEmptyResults:
    """Test list_fields with empty or no results."""

    def test_empty_fields_response(self, mock_jira_client):
        """Test handling of empty fields response."""
        mock_jira_client.get.return_value = []

        result = list_fields(client=mock_jira_client)

        assert result == []

    def test_no_custom_fields(self, mock_jira_client):
        """Test when no custom fields exist."""
        mock_jira_client.get.return_value = [
            {'id': 'summary', 'name': 'Summary', 'custom': False, 'schema': {}}
        ]

        result = list_fields(custom_only=True, client=mock_jira_client)

        assert result == []


@pytest.mark.fields
@pytest.mark.unit
class TestListFieldsErrorHandling:
    """Test error handling in list_fields."""

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 authentication error."""
        from error_handler import AuthenticationError
        mock_jira_client.get.side_effect = AuthenticationError("Invalid token")

        with pytest.raises(AuthenticationError):
            list_fields(client=mock_jira_client)

    def test_permission_denied_error(self, mock_jira_client):
        """Test handling of 403 permission denied."""
        from error_handler import JiraError
        mock_jira_client.get.side_effect = JiraError("Permission denied", status_code=403)

        with pytest.raises(JiraError) as exc_info:
            list_fields(client=mock_jira_client)
        assert exc_info.value.status_code == 403

    def test_not_found_error(self, mock_jira_client):
        """Test handling of 404 not found."""
        from error_handler import JiraError
        mock_jira_client.get.side_effect = JiraError("Not found", status_code=404)

        with pytest.raises(JiraError) as exc_info:
            list_fields(client=mock_jira_client)
        assert exc_info.value.status_code == 404

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from error_handler import JiraError
        mock_jira_client.get.side_effect = JiraError("Rate limit exceeded", status_code=429)

        with pytest.raises(JiraError) as exc_info:
            list_fields(client=mock_jira_client)
        assert exc_info.value.status_code == 429

    def test_server_error(self, mock_jira_client):
        """Test handling of 500 server error."""
        from error_handler import JiraError
        mock_jira_client.get.side_effect = JiraError("Server error", status_code=500)

        with pytest.raises(JiraError) as exc_info:
            list_fields(client=mock_jira_client)
        assert exc_info.value.status_code == 500


@pytest.mark.fields
@pytest.mark.unit
class TestListFieldsClientManagement:
    """Test client lifecycle management."""

    def test_closes_client_on_success(self, sample_fields_response):
        """Test that client is closed after successful operation."""
        mock_client = MagicMock()
        mock_client.get.return_value = sample_fields_response

        with patch('list_fields.get_jira_client', return_value=mock_client):
            list_fields()

        mock_client.close.assert_called_once()

    def test_closes_client_on_error(self):
        """Test that client is closed even when operation fails."""
        from error_handler import JiraError
        mock_client = MagicMock()
        mock_client.get.side_effect = JiraError("Test error")

        with patch('list_fields.get_jira_client', return_value=mock_client):
            with pytest.raises(JiraError):
                list_fields()

        mock_client.close.assert_called_once()

    def test_does_not_close_provided_client(self, mock_jira_client, sample_fields_response):
        """Test that provided client is not closed."""
        mock_jira_client.get.return_value = sample_fields_response

        list_fields(client=mock_jira_client)

        mock_jira_client.close.assert_not_called()
```

**1.1.3 Create tests/unit/test_check_project_fields.py:**

```python
"""
Unit Tests: check_project_fields.py

Tests for checking project field availability.
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Path setup
test_dir = Path(__file__).parent
tests_dir = test_dir.parent
jira_fields_dir = tests_dir.parent
scripts_dir = jira_fields_dir / 'scripts'
shared_lib_dir = jira_fields_dir.parent / 'shared' / 'scripts' / 'lib'

sys.path.insert(0, str(scripts_dir))
sys.path.insert(0, str(shared_lib_dir))

from check_project_fields import check_project_fields, AGILE_FIELDS


@pytest.mark.fields
@pytest.mark.unit
class TestCheckProjectFieldsBasic:
    """Test basic check_project_fields functionality."""

    def test_check_project_fields_basic(self, mock_jira_client, sample_project_response, sample_create_meta_response):
        """Test basic project field check."""
        mock_jira_client.get.side_effect = [sample_project_response, sample_create_meta_response]

        result = check_project_fields(project_key='TEST', client=mock_jira_client)

        assert result is not None
        assert 'project' in result
        assert result['project']['key'] == 'TEST'
        assert result['project']['name'] == 'Test Project'
        assert 'fields' in result
        assert 'issue_types' in result

    def test_check_project_detects_classic_style(self, mock_jira_client, sample_project_response, sample_create_meta_response):
        """Test detection of company-managed (classic) project style."""
        mock_jira_client.get.side_effect = [sample_project_response, sample_create_meta_response]

        result = check_project_fields(project_key='TEST', client=mock_jira_client)

        assert result['is_team_managed'] is False
        assert result['project']['style'] == 'classic'

    def test_check_project_detects_team_managed_style(self, mock_jira_client, sample_project_team_managed, sample_create_meta_response):
        """Test detection of team-managed (next-gen) project style."""
        mock_jira_client.get.side_effect = [sample_project_team_managed, sample_create_meta_response]

        result = check_project_fields(project_key='TEAM', client=mock_jira_client)

        assert result['is_team_managed'] is True
        assert result['project']['style'] == 'next-gen'


@pytest.mark.fields
@pytest.mark.unit
class TestCheckProjectFieldsIssueTypes:
    """Test issue type filtering."""

    def test_check_specific_issue_type(self, mock_jira_client, sample_project_response, sample_create_meta_response):
        """Test checking fields for specific issue type."""
        mock_jira_client.get.side_effect = [sample_project_response, sample_create_meta_response]

        result = check_project_fields(
            project_key='TEST',
            issue_type='Task',
            client=mock_jira_client
        )

        assert result is not None
        # Verify API was called with issuetypeNames param
        calls = mock_jira_client.get.call_args_list
        assert len(calls) == 2
        second_call = calls[1]
        assert 'issuetypeNames' in str(second_call)

    def test_issue_types_in_result(self, mock_jira_client, sample_project_response, sample_create_meta_response):
        """Test that issue types are properly populated."""
        mock_jira_client.get.side_effect = [sample_project_response, sample_create_meta_response]

        result = check_project_fields(project_key='TEST', client=mock_jira_client)

        assert len(result['issue_types']) == 2
        type_names = [t['name'] for t in result['issue_types']]
        assert 'Task' in type_names
        assert 'Story' in type_names


@pytest.mark.fields
@pytest.mark.unit
class TestCheckProjectFieldsAgile:
    """Test Agile field checking."""

    def test_check_agile_fields(self, mock_jira_client, sample_project_response, sample_create_meta_response):
        """Test checking Agile field availability."""
        mock_jira_client.get.side_effect = [sample_project_response, sample_create_meta_response]

        result = check_project_fields(
            project_key='TEST',
            check_agile=True,
            client=mock_jira_client
        )

        assert 'agile_fields' in result
        # Should find Sprint and Story Points from the create meta
        agile = result['agile_fields']
        assert 'sprint' in agile
        assert 'story_points' in agile

    def test_agile_fields_not_found(self, mock_jira_client, sample_project_response):
        """Test when no Agile fields are available."""
        # Create meta with no agile fields
        meta = {
            'projects': [{
                'id': '10001',
                'key': 'TEST',
                'issuetypes': [{
                    'id': '10001',
                    'name': 'Task',
                    'fields': {
                        'summary': {'name': 'Summary', 'required': True}
                    }
                }]
            }]
        }
        mock_jira_client.get.side_effect = [sample_project_response, meta]

        result = check_project_fields(
            project_key='TEST',
            check_agile=True,
            client=mock_jira_client
        )

        assert 'agile_fields' in result
        # All agile fields should be None
        for field_type in AGILE_FIELDS:
            assert result['agile_fields'].get(field_type) is None


@pytest.mark.fields
@pytest.mark.unit
class TestCheckProjectFieldsErrorHandling:
    """Test error handling in check_project_fields."""

    def test_project_not_found(self, mock_jira_client):
        """Test handling of non-existent project."""
        from error_handler import JiraError
        mock_jira_client.get.side_effect = JiraError("Project not found", status_code=404)

        with pytest.raises(JiraError) as exc_info:
            check_project_fields(project_key='NOTEXIST', client=mock_jira_client)
        assert exc_info.value.status_code == 404

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 authentication error."""
        from error_handler import AuthenticationError
        mock_jira_client.get.side_effect = AuthenticationError("Invalid token")

        with pytest.raises(AuthenticationError):
            check_project_fields(project_key='TEST', client=mock_jira_client)

    def test_permission_denied_error(self, mock_jira_client):
        """Test handling of 403 permission denied."""
        from error_handler import JiraError
        mock_jira_client.get.side_effect = JiraError("Permission denied", status_code=403)

        with pytest.raises(JiraError) as exc_info:
            check_project_fields(project_key='TEST', client=mock_jira_client)
        assert exc_info.value.status_code == 403

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from error_handler import JiraError
        mock_jira_client.get.side_effect = JiraError("Rate limit exceeded", status_code=429)

        with pytest.raises(JiraError) as exc_info:
            check_project_fields(project_key='TEST', client=mock_jira_client)
        assert exc_info.value.status_code == 429

    def test_server_error(self, mock_jira_client):
        """Test handling of 500 server error."""
        from error_handler import JiraError
        mock_jira_client.get.side_effect = JiraError("Server error", status_code=500)

        with pytest.raises(JiraError) as exc_info:
            check_project_fields(project_key='TEST', client=mock_jira_client)
        assert exc_info.value.status_code == 500


@pytest.mark.fields
@pytest.mark.unit
class TestCheckProjectFieldsClientManagement:
    """Test client lifecycle management."""

    def test_closes_client_on_success(self, sample_project_response, sample_create_meta_response):
        """Test that client is closed after successful operation."""
        mock_client = MagicMock()
        mock_client.get.side_effect = [sample_project_response, sample_create_meta_response]

        with patch('check_project_fields.get_jira_client', return_value=mock_client):
            check_project_fields(project_key='TEST')

        mock_client.close.assert_called_once()

    def test_does_not_close_provided_client(self, mock_jira_client, sample_project_response, sample_create_meta_response):
        """Test that provided client is not closed."""
        mock_jira_client.get.side_effect = [sample_project_response, sample_create_meta_response]

        check_project_fields(project_key='TEST', client=mock_jira_client)

        mock_jira_client.close.assert_not_called()
```

**1.1.4 Create tests/unit/test_configure_agile_fields.py:**

```python
"""
Unit Tests: configure_agile_fields.py

Tests for configuring Agile fields for projects.
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, call

# Path setup
test_dir = Path(__file__).parent
tests_dir = test_dir.parent
jira_fields_dir = tests_dir.parent
scripts_dir = jira_fields_dir / 'scripts'
shared_lib_dir = jira_fields_dir.parent / 'shared' / 'scripts' / 'lib'

sys.path.insert(0, str(scripts_dir))
sys.path.insert(0, str(shared_lib_dir))

from configure_agile_fields import (
    configure_agile_fields,
    find_agile_fields,
    find_project_screens,
    add_field_to_screen
)


@pytest.mark.fields
@pytest.mark.unit
class TestFindAgileFields:
    """Test find_agile_fields helper function."""

    def test_find_all_agile_fields(self, mock_jira_client, sample_fields_response):
        """Test finding all Agile fields."""
        mock_jira_client.get.return_value = sample_fields_response

        result = find_agile_fields(mock_jira_client)

        assert result['story_points'] == 'customfield_10002'
        assert result['epic_link'] == 'customfield_10003'
        assert result['sprint'] == 'customfield_10001'
        assert result['epic_name'] == 'customfield_10004'

    def test_find_no_agile_fields(self, mock_jira_client):
        """Test when no Agile fields exist."""
        mock_jira_client.get.return_value = [
            {'id': 'summary', 'name': 'Summary', 'custom': False}
        ]

        result = find_agile_fields(mock_jira_client)

        assert result['story_points'] is None
        assert result['epic_link'] is None
        assert result['sprint'] is None
        assert result['epic_name'] is None

    def test_find_partial_agile_fields(self, mock_jira_client):
        """Test finding only some Agile fields."""
        mock_jira_client.get.return_value = [
            {'id': 'customfield_10001', 'name': 'Sprint', 'custom': True}
        ]

        result = find_agile_fields(mock_jira_client)

        assert result['sprint'] == 'customfield_10001'
        assert result['story_points'] is None


@pytest.mark.fields
@pytest.mark.unit
class TestFindProjectScreens:
    """Test find_project_screens helper function."""

    def test_find_screens_with_scheme(
        self,
        mock_jira_client,
        sample_project_response,
        sample_screen_schemes_response,
        sample_screen_scheme_mapping,
        sample_screen_scheme,
        sample_screen
    ):
        """Test finding screens when project has screen scheme."""
        mock_jira_client.get.side_effect = [
            sample_project_response,
            sample_screen_schemes_response,
            sample_screen_scheme_mapping,
            sample_screen_scheme,
            sample_screen,
            sample_screen,
            sample_screen
        ]

        result = find_project_screens(mock_jira_client, 'TEST')

        assert isinstance(result, list)
        assert len(result) > 0

    def test_find_screens_no_scheme_uses_default(self, mock_jira_client, sample_project_response):
        """Test fallback to default screen when no scheme found."""
        mock_jira_client.get.side_effect = [
            sample_project_response,
            {'values': []},  # No screen schemes
            {'values': [{'id': 1, 'name': 'Default Screen'}]}  # All screens
        ]

        result = find_project_screens(mock_jira_client, 'TEST')

        assert isinstance(result, list)


@pytest.mark.fields
@pytest.mark.unit
class TestAddFieldToScreen:
    """Test add_field_to_screen helper function."""

    def test_add_field_success(self, mock_jira_client, sample_screen_tabs, sample_screen_fields):
        """Test successfully adding a field to a screen."""
        mock_jira_client.get.side_effect = [sample_screen_tabs, sample_screen_fields]
        mock_jira_client.post.return_value = {}

        result = add_field_to_screen(mock_jira_client, 10001, 'customfield_10002')

        assert result is True
        mock_jira_client.post.assert_called_once()

    def test_add_field_already_exists(self, mock_jira_client, sample_screen_tabs):
        """Test adding a field that already exists on screen."""
        fields_with_target = [{'id': 'customfield_10002', 'name': 'Story Points'}]
        mock_jira_client.get.side_effect = [sample_screen_tabs, fields_with_target]

        result = add_field_to_screen(mock_jira_client, 10001, 'customfield_10002')

        assert result is True
        mock_jira_client.post.assert_not_called()

    def test_add_field_dry_run(self, mock_jira_client):
        """Test dry-run mode does not make changes."""
        result = add_field_to_screen(mock_jira_client, 10001, 'customfield_10002', dry_run=True)

        assert result is True
        mock_jira_client.get.assert_not_called()
        mock_jira_client.post.assert_not_called()

    def test_add_field_no_tabs(self, mock_jira_client):
        """Test handling when screen has no tabs."""
        mock_jira_client.get.return_value = []

        result = add_field_to_screen(mock_jira_client, 10001, 'customfield_10002')

        assert result is False


@pytest.mark.fields
@pytest.mark.unit
class TestConfigureAgileFieldsBasic:
    """Test basic configure_agile_fields functionality."""

    def test_configure_agile_fields_success(
        self,
        mock_jira_client,
        sample_project_response,
        sample_fields_response,
        sample_screen_schemes_response,
        sample_screen_scheme_mapping,
        sample_screen_scheme,
        sample_screen,
        sample_screen_tabs,
        sample_screen_fields
    ):
        """Test successful Agile field configuration."""
        mock_jira_client.get.side_effect = [
            sample_project_response,  # Project check
            sample_fields_response,   # Find agile fields
            sample_project_response,  # find_project_screens project
            sample_screen_schemes_response,
            sample_screen_scheme_mapping,
            sample_screen_scheme,
            sample_screen,
            sample_screen,
            sample_screen,
            sample_screen_tabs,  # add_field_to_screen
            sample_screen_fields,
            sample_screen_tabs,
            sample_screen_fields,
            sample_screen_tabs,
            sample_screen_fields
        ]
        mock_jira_client.post.return_value = {}

        result = configure_agile_fields(project_key='TEST', client=mock_jira_client)

        assert result is not None
        assert result['project'] == 'TEST'
        assert result['dry_run'] is False
        assert 'fields_found' in result
        assert 'screens_found' in result
        assert 'fields_added' in result


@pytest.mark.fields
@pytest.mark.unit
class TestConfigureAgileFieldsDryRun:
    """Test dry-run functionality."""

    def test_configure_dry_run_no_changes(
        self,
        mock_jira_client,
        sample_project_response,
        sample_fields_response,
        sample_screen_schemes_response,
        sample_screen_scheme_mapping,
        sample_screen_scheme,
        sample_screen
    ):
        """Test dry-run mode shows preview without changes."""
        mock_jira_client.get.side_effect = [
            sample_project_response,
            sample_fields_response,
            sample_project_response,
            sample_screen_schemes_response,
            sample_screen_scheme_mapping,
            sample_screen_scheme,
            sample_screen,
            sample_screen,
            sample_screen
        ]

        result = configure_agile_fields(
            project_key='TEST',
            dry_run=True,
            client=mock_jira_client
        )

        assert result['dry_run'] is True
        # No POST calls should be made in dry-run
        mock_jira_client.post.assert_not_called()


@pytest.mark.fields
@pytest.mark.unit
class TestConfigureAgileFieldsValidation:
    """Test validation in configure_agile_fields."""

    def test_reject_team_managed_project(self, mock_jira_client, sample_project_team_managed):
        """Test that team-managed projects are rejected."""
        from error_handler import ValidationError
        mock_jira_client.get.return_value = sample_project_team_managed

        with pytest.raises(ValidationError) as exc_info:
            configure_agile_fields(project_key='TEAM', client=mock_jira_client)

        assert 'team-managed' in str(exc_info.value).lower()

    def test_no_agile_fields_found(self, mock_jira_client, sample_project_response):
        """Test error when no Agile fields exist in instance."""
        from error_handler import ValidationError
        mock_jira_client.get.side_effect = [
            sample_project_response,
            [{'id': 'summary', 'name': 'Summary', 'custom': False}]  # No agile fields
        ]

        with pytest.raises(ValidationError) as exc_info:
            configure_agile_fields(project_key='TEST', client=mock_jira_client)

        assert 'no agile fields' in str(exc_info.value).lower()


@pytest.mark.fields
@pytest.mark.unit
class TestConfigureAgileFieldsErrorHandling:
    """Test error handling in configure_agile_fields."""

    def test_project_not_found(self, mock_jira_client):
        """Test handling of non-existent project."""
        from error_handler import JiraError
        mock_jira_client.get.side_effect = JiraError("Project not found", status_code=404)

        with pytest.raises(JiraError) as exc_info:
            configure_agile_fields(project_key='NOTEXIST', client=mock_jira_client)
        assert exc_info.value.status_code == 404

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 authentication error."""
        from error_handler import AuthenticationError
        mock_jira_client.get.side_effect = AuthenticationError("Invalid token")

        with pytest.raises(AuthenticationError):
            configure_agile_fields(project_key='TEST', client=mock_jira_client)

    def test_permission_denied_error(self, mock_jira_client):
        """Test handling of 403 permission denied."""
        from error_handler import JiraError
        mock_jira_client.get.side_effect = JiraError("Permission denied", status_code=403)

        with pytest.raises(JiraError) as exc_info:
            configure_agile_fields(project_key='TEST', client=mock_jira_client)
        assert exc_info.value.status_code == 403

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from error_handler import JiraError
        mock_jira_client.get.side_effect = JiraError("Rate limit exceeded", status_code=429)

        with pytest.raises(JiraError) as exc_info:
            configure_agile_fields(project_key='TEST', client=mock_jira_client)
        assert exc_info.value.status_code == 429

    def test_server_error(self, mock_jira_client):
        """Test handling of 500 server error."""
        from error_handler import JiraError
        mock_jira_client.get.side_effect = JiraError("Server error", status_code=500)

        with pytest.raises(JiraError) as exc_info:
            configure_agile_fields(project_key='TEST', client=mock_jira_client)
        assert exc_info.value.status_code == 500
```

**1.1.5 Create tests/unit/test_create_field.py:**

```python
"""
Unit Tests: create_field.py

Tests for creating custom JIRA fields.
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Path setup
test_dir = Path(__file__).parent
tests_dir = test_dir.parent
jira_fields_dir = tests_dir.parent
scripts_dir = jira_fields_dir / 'scripts'
shared_lib_dir = jira_fields_dir.parent / 'shared' / 'scripts' / 'lib'

sys.path.insert(0, str(scripts_dir))
sys.path.insert(0, str(shared_lib_dir))

from create_field import create_field, FIELD_TYPES


@pytest.mark.fields
@pytest.mark.unit
class TestCreateFieldBasic:
    """Test basic create_field functionality."""

    def test_create_text_field(self, mock_jira_client, sample_created_field):
        """Test creating a text field."""
        mock_jira_client.post.return_value = sample_created_field

        result = create_field(
            name='Test Field',
            field_type='text',
            client=mock_jira_client
        )

        assert result is not None
        assert result['name'] == 'Test Field'
        mock_jira_client.post.assert_called_once()
        call_args = mock_jira_client.post.call_args
        assert call_args[0][0] == '/rest/api/3/field'
        assert call_args[1]['data']['name'] == 'Test Field'

    def test_create_number_field(self, mock_jira_client, sample_created_field):
        """Test creating a number field."""
        mock_jira_client.post.return_value = sample_created_field

        result = create_field(
            name='Story Points',
            field_type='number',
            client=mock_jira_client
        )

        assert result is not None
        call_args = mock_jira_client.post.call_args
        assert call_args[1]['data']['type'] == FIELD_TYPES['number']['type']

    def test_create_select_field(self, mock_jira_client, sample_created_field):
        """Test creating a select field."""
        mock_jira_client.post.return_value = sample_created_field

        result = create_field(
            name='Priority Level',
            field_type='select',
            client=mock_jira_client
        )

        assert result is not None
        call_args = mock_jira_client.post.call_args
        assert call_args[1]['data']['type'] == FIELD_TYPES['select']['type']

    def test_create_field_with_description(self, mock_jira_client, sample_created_field):
        """Test creating a field with description."""
        mock_jira_client.post.return_value = sample_created_field

        result = create_field(
            name='Test Field',
            field_type='text',
            description='A test description',
            client=mock_jira_client
        )

        assert result is not None
        call_args = mock_jira_client.post.call_args
        assert call_args[1]['data']['description'] == 'A test description'


@pytest.mark.fields
@pytest.mark.unit
class TestCreateFieldAllTypes:
    """Test creating all supported field types."""

    @pytest.mark.parametrize('field_type', list(FIELD_TYPES.keys()))
    def test_create_all_field_types(self, mock_jira_client, sample_created_field, field_type):
        """Test creating each supported field type."""
        mock_jira_client.post.return_value = sample_created_field

        result = create_field(
            name=f'Test {field_type}',
            field_type=field_type,
            client=mock_jira_client
        )

        assert result is not None
        call_args = mock_jira_client.post.call_args
        assert call_args[1]['data']['type'] == FIELD_TYPES[field_type]['type']
        assert call_args[1]['data']['searcherKey'] == FIELD_TYPES[field_type]['searcher']


@pytest.mark.fields
@pytest.mark.unit
class TestCreateFieldValidation:
    """Test validation in create_field."""

    def test_invalid_field_type(self, mock_jira_client):
        """Test error on invalid field type."""
        from error_handler import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            create_field(
                name='Test Field',
                field_type='invalid_type',
                client=mock_jira_client
            )

        assert 'invalid field type' in str(exc_info.value).lower()
        mock_jira_client.post.assert_not_called()

    def test_validation_error_lists_valid_types(self, mock_jira_client):
        """Test that validation error lists valid types."""
        from error_handler import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            create_field(
                name='Test Field',
                field_type='bogus',
                client=mock_jira_client
            )

        error_message = str(exc_info.value).lower()
        # Should list at least some valid types
        assert 'text' in error_message or 'valid types' in error_message


@pytest.mark.fields
@pytest.mark.unit
class TestCreateFieldErrorHandling:
    """Test error handling in create_field."""

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 authentication error."""
        from error_handler import AuthenticationError
        mock_jira_client.post.side_effect = AuthenticationError("Invalid token")

        with pytest.raises(AuthenticationError):
            create_field(name='Test', field_type='text', client=mock_jira_client)

    def test_permission_denied_error(self, mock_jira_client):
        """Test handling of 403 permission denied (requires admin)."""
        from error_handler import JiraError
        mock_jira_client.post.side_effect = JiraError("Admin permission required", status_code=403)

        with pytest.raises(JiraError) as exc_info:
            create_field(name='Test', field_type='text', client=mock_jira_client)
        assert exc_info.value.status_code == 403

    def test_duplicate_field_error(self, mock_jira_client):
        """Test handling of duplicate field name."""
        from error_handler import JiraError
        mock_jira_client.post.side_effect = JiraError("Field with this name already exists", status_code=400)

        with pytest.raises(JiraError) as exc_info:
            create_field(name='Existing Field', field_type='text', client=mock_jira_client)
        assert exc_info.value.status_code == 400

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from error_handler import JiraError
        mock_jira_client.post.side_effect = JiraError("Rate limit exceeded", status_code=429)

        with pytest.raises(JiraError) as exc_info:
            create_field(name='Test', field_type='text', client=mock_jira_client)
        assert exc_info.value.status_code == 429

    def test_server_error(self, mock_jira_client):
        """Test handling of 500 server error."""
        from error_handler import JiraError
        mock_jira_client.post.side_effect = JiraError("Server error", status_code=500)

        with pytest.raises(JiraError) as exc_info:
            create_field(name='Test', field_type='text', client=mock_jira_client)
        assert exc_info.value.status_code == 500


@pytest.mark.fields
@pytest.mark.unit
class TestCreateFieldClientManagement:
    """Test client lifecycle management."""

    def test_closes_client_on_success(self, sample_created_field):
        """Test that client is closed after successful operation."""
        mock_client = MagicMock()
        mock_client.post.return_value = sample_created_field

        with patch('create_field.get_jira_client', return_value=mock_client):
            create_field(name='Test', field_type='text')

        mock_client.close.assert_called_once()

    def test_closes_client_on_error(self):
        """Test that client is closed even when operation fails."""
        from error_handler import JiraError
        mock_client = MagicMock()
        mock_client.post.side_effect = JiraError("Test error")

        with patch('create_field.get_jira_client', return_value=mock_client):
            with pytest.raises(JiraError):
                create_field(name='Test', field_type='text')

        mock_client.close.assert_called_once()

    def test_does_not_close_provided_client(self, mock_jira_client, sample_created_field):
        """Test that provided client is not closed."""
        mock_jira_client.post.return_value = sample_created_field

        create_field(name='Test', field_type='text', client=mock_jira_client)

        mock_jira_client.close.assert_not_called()
```

---

### 1.2 Missing pytest Markers on Live Integration Test Classes

**Impact:** Inconsistent test categorization, cannot run by marker
**File:** `tests/live_integration/test_field_management.py`
**Classes Affected:** 6 classes

| Line | Class Name |
|------|------------|
| 19 | `TestListFields` |
| 85 | `TestCheckProjectFields` |
| 146 | `TestFieldDiscovery` |
| 175 | `TestFieldMetadata` |
| 207 | `TestProjectFieldContext` |

**Remediation:**

```python
# Add to each test class:
@pytest.mark.fields
@pytest.mark.integration
class TestListFields:
    """Tests for listing JIRA fields."""
```

---

### 1.3 Missing conftest.py at tests/ Level

**Impact:** Cannot share fixtures between unit and integration tests
**File:** `tests/conftest.py` (does not exist)

**Create `tests/conftest.py`:**

```python
"""
Test Configuration for jira-fields skill.

Shared fixtures for both unit and integration tests.
"""

import pytest


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "fields: mark test as fields skill test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
```

---

## Phase 2: High Priority Issues

### 2.1 Weak Assertions in Live Integration Tests

**Impact:** Tests pass even when functionality is broken
**File:** `tests/live_integration/test_field_management.py`

| Line | Current Assertion | Issue | Fix |
|------|-------------------|-------|-----|
| 42-43 | `assert fields is not None; assert isinstance(fields, list)` | Empty list passes | Add `assert len(fields) >= 0 or fields is not None # expected` |
| 54-55 | `assert fields is not None; assert isinstance(fields, list)` | No content validation | Verify field structure |
| 98 | `assert 'available_fields' in result or 'fields' in result` | Too permissive OR | Use explicit check based on expected structure |
| 132 | `assert 'agile_fields' in result or 'fields' in result` | Too permissive OR | Check specific structure |
| 143 | `assert ... or 'style' in result or 'simplified' in str(result)` | String check fallback | Check specific key |
| 156 | `assert isinstance(sprint_fields, list)` | Empty list is valid | Document expectation |
| 164 | `assert isinstance(points_fields, list)` | Empty list is valid | Document expectation |
| 172 | `assert isinstance(epic_fields, list)` | Empty list is valid | Document expectation |

**Remediation Template:**

```python
# Before (weak):
assert fields is not None
assert isinstance(fields, list)

# After (strong):
assert fields is not None, "API returned None instead of list"
assert isinstance(fields, list), f"Expected list, got {type(fields)}"
assert len(fields) > 0, "Expected at least one field, got empty list"

# Verify structure
for field in fields[:3]:  # Check first 3
    assert 'id' in field, "Field missing 'id'"
    assert 'name' in field, "Field missing 'name'"
```

---

### 2.2 Missing Error Handling Tests in Live Integration

**Impact:** Error scenarios untested in real environment
**File:** `tests/live_integration/test_field_management.py`
**Missing Tests:** All error handling tests

| Error Type | Test Needed |
|------------|-------------|
| Invalid project key | `test_check_fields_invalid_project` |
| Invalid issue type | `test_check_fields_invalid_issue_type` |
| Invalid field ID | `test_configure_invalid_field_id` |
| Team-managed project rejection | `test_configure_team_managed_rejected` |

**Remediation Template:**

```python
@pytest.mark.fields
@pytest.mark.integration
class TestFieldErrorHandling:
    """Test error handling in field management."""

    def test_check_fields_invalid_project(self, jira_client):
        """Test error handling for non-existent project."""
        from error_handler import JiraError

        with pytest.raises(JiraError):
            check_project_fields(
                project_key='NONEXISTENTPROJECT',
                client=jira_client
            )

    def test_check_fields_invalid_issue_type(self, jira_client, test_project):
        """Test error handling for non-existent issue type."""
        result = check_project_fields(
            project_key=test_project['key'],
            issue_type='NonExistentType',
            client=jira_client
        )
        # Should return empty or handle gracefully
        assert result is not None
```

---

### 2.3 Missing Tests for configure_agile_fields.py in Live Integration

**Impact:** Core functionality untested in real environment
**File:** `tests/live_integration/test_field_management.py`
**Missing Class:** `TestConfigureAgileFields`

```python
@pytest.mark.fields
@pytest.mark.integration
class TestConfigureAgileFields:
    """Tests for configuring Agile fields."""

    def test_configure_agile_fields_dry_run(self, jira_client, test_project):
        """Test dry-run mode for Agile field configuration."""
        from configure_agile_fields import configure_agile_fields

        result = configure_agile_fields(
            project_key=test_project['key'],
            dry_run=True,
            client=jira_client
        )

        assert result is not None
        assert result.get('dry_run') is True
        assert 'fields_found' in result
        assert 'screens_found' in result

    def test_configure_agile_fields_auto_detect(self, jira_client, test_project):
        """Test automatic Agile field detection."""
        from configure_agile_fields import find_agile_fields

        fields = find_agile_fields(jira_client)

        assert isinstance(fields, dict)
        assert 'story_points' in fields
        assert 'epic_link' in fields
        assert 'sprint' in fields
```

---

### 2.4 Missing Tests for create_field.py in Live Integration

**Impact:** Field creation untested in real environment
**File:** `tests/live_integration/test_field_management.py`
**Missing Class:** `TestCreateField`

Note: Field creation tests should be carefully managed as fields cannot be easily deleted. Consider using dry-run or documenting cleanup requirements.

```python
@pytest.mark.fields
@pytest.mark.integration
@pytest.mark.skip(reason="Field creation requires admin privileges and cannot be undone")
class TestCreateField:
    """Tests for creating custom fields."""

    def test_create_field_validation_only(self, jira_client):
        """Test field creation validation (without actual creation)."""
        from create_field import FIELD_TYPES
        from error_handler import ValidationError

        # Validate that invalid types are rejected
        with pytest.raises(ValidationError):
            from create_field import create_field
            create_field(
                name='Test',
                field_type='invalid',
                client=jira_client
            )
```

---

## Phase 3: Medium Priority Issues

### 3.1 Fixture Mutation Issues

**Impact:** Potential test pollution between tests
**Files Affected:** Live integration tests using fixtures directly

| File | Lines | Issue |
|------|-------|-------|
| `conftest.py` | 71-121 | `test_project` fixture modifies dict in place |

**Remediation:**

```python
# In conftest.py - use deepcopy for fixture data
import copy

@pytest.fixture
def sample_project_data():
    return copy.deepcopy({
        'id': '10001',
        'key': 'TEST',
        'name': 'Test Project'
    })
```

---

### 3.2 Missing Edge Case Tests

**Priority order by impact:**

| Category | Script | Missing Edge Case |
|----------|--------|-------------------|
| Empty results | `list_fields.py` | No custom fields in instance |
| Empty results | `check_project_fields.py` | Project with no issue types |
| Boundary values | `list_fields.py` | Field name with special characters |
| Boundary values | `create_field.py` | Maximum length field name |
| Empty filter | `list_fields.py` | Empty string filter pattern |
| Invalid input | `configure_agile_fields.py` | Invalid custom field ID format |

**Remediation Template:**

```python
def test_empty_filter_pattern(self, mock_jira_client, sample_fields_response):
    """Test that empty filter pattern returns all fields."""
    mock_jira_client.get.return_value = sample_fields_response

    result = list_fields(filter_pattern='', client=mock_jira_client)

    # Empty string should match all (no filtering)
    assert len(result) > 0
```

---

### 3.3 Unused Imports in Live Integration Tests

**Impact:** Code hygiene
**Files Affected:**

| File | Line | Unused Import |
|------|------|---------------|
| `test_field_management.py` | 10 | `List` (used but could be checked) |
| `conftest.py` | 9-13 | Various potential unused |

**Verification Command:**

```bash
pylint .claude/skills/jira-fields/tests/ --disable=all --enable=unused-import
```

---

## Phase 4: Low Priority Issues

### 4.1 Improve Test Documentation

**Impact:** Maintainability
**Action:** Add docstrings explaining test prerequisites and expected outcomes

```python
def test_list_all_custom_fields(self, jira_client):
    """
    Test listing all custom fields.

    Prerequisites:
        - JIRA instance has at least one custom field

    Expected:
        - Returns list of custom fields
        - Each field has 'id', 'name', 'type' properties
        - All fields have customfield_* IDs
    """
```

---

### 4.2 Add Test Count Verification

**Impact:** Catch accidental test deletion

```python
# tests/test_coverage_check.py
import pytest
from pathlib import Path

def test_minimum_test_count():
    """Ensure test count doesn't regress."""
    test_dir = Path(__file__).parent
    test_files = list(test_dir.rglob('test_*.py'))

    test_count = 0
    for f in test_files:
        content = f.read_text()
        test_count += content.count('def test_')

    # Minimum expected tests (update as tests are added)
    MIN_TESTS = 80  # Target after remediation
    assert test_count >= MIN_TESTS, f"Expected {MIN_TESTS}+ tests, found {test_count}"
```

---

## Implementation Checklist

### Phase 1 Checklist (Critical)

- [ ] Create `tests/__init__.py`
- [ ] Create `tests/conftest.py` with marker registration
- [ ] Create `tests/unit/` directory
- [ ] Create `tests/unit/__init__.py`
- [ ] Create `tests/unit/conftest.py` with fixtures
- [ ] Create `tests/unit/test_list_fields.py` (~20 tests)
- [ ] Create `tests/unit/test_check_project_fields.py` (~15 tests)
- [ ] Create `tests/unit/test_configure_agile_fields.py` (~20 tests)
- [ ] Create `tests/unit/test_create_field.py` (~18 tests)
- [ ] Add pytest markers to all live integration test classes (6 classes)

### Phase 2 Checklist (High Priority)

- [ ] Fix 8 weak assertions in test_field_management.py
- [ ] Add error handling tests to live integration (4+ tests)
- [ ] Add TestConfigureAgileFields class to live integration
- [ ] Document create_field test limitations

### Phase 3 Checklist (Medium Priority)

- [ ] Add deepcopy to fixtures that could be mutated
- [ ] Add 6+ edge case tests (empty results, boundary values)
- [ ] Remove unused imports

### Phase 4 Checklist (Low Priority)

- [ ] Add comprehensive docstrings to all test methods
- [ ] Add test count verification

---

## Verification Commands

```bash
# Run all jira-fields tests (unit only - no live JIRA needed)
pytest .claude/skills/jira-fields/tests/unit/ -v

# Run with markers
pytest .claude/skills/jira-fields/tests/ -v -m "fields and unit"

# Run live integration tests (requires JIRA credentials)
pytest .claude/skills/jira-fields/tests/live_integration/ --profile development -v

# Check test count
pytest .claude/skills/jira-fields/tests/ --collect-only | grep "test session starts" -A 5

# Verify no unused imports
pylint .claude/skills/jira-fields/tests/ --disable=all --enable=unused-import

# Check coverage
pytest .claude/skills/jira-fields/tests/unit/ --cov=.claude/skills/jira-fields/scripts --cov-report=term-missing
```

---

## Success Criteria

1. **Unit tests exist:** All 4 scripts have comprehensive unit tests
2. **All tests pass:** `pytest` exits with code 0
3. **No weak assertions:** All assertions validate meaningful conditions
4. **Consistent markers:** All test classes have `@pytest.mark.fields` and appropriate level marker
5. **Coverage maintained:** Unit test coverage >80%
6. **Error scenarios tested:** All HTTP error codes (401, 403, 404, 429, 500) have tests

---

## Test Count Summary

| Category | Current | After Remediation |
|----------|---------|-------------------|
| Unit tests | 0 | ~73 |
| Live integration tests | 18 | ~25 |
| **Total** | **18** | **~98** |

---

## Notes

- Phase 1 is critical - without unit tests, the skill cannot be properly validated in CI/CD
- Live integration tests are valuable but should complement, not replace, unit tests
- Consider adding a CI job that runs only unit tests (no JIRA credentials needed)
- Field creation tests should be carefully managed as fields are not easily deleted
