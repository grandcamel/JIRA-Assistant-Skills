# Test Remediation Plan: Shared Library

**Created:** 2025-12-26
**Status:** Draft
**Test Files Reviewed:** 10
**Total Issues Identified:** ~85

---

## Executive Summary

This plan addresses test quality issues discovered during a comprehensive review of the shared library live integration test suite. Issues are organized by priority and grouped into actionable phases.

**Test Coverage Summary:**
- Total test files: 10 (including conftest.py and cleanup.py)
- Total test functions: 157 tests across 10 files
- Test classes: 43 classes covering 9 functional areas

**Estimated Effort:**
- Phase 1 (Critical): 2-3 hours
- Phase 2 (High Priority): 3-4 hours
- Phase 3 (Medium Priority): 4-6 hours
- Phase 4 (Low Priority): 1-2 hours

---

## Phase 1: Critical Issues (Must Fix)

### 1.1 Missing pytest Marker Registration

**Impact:** pytest warnings, inconsistent test selection
**File:** `tests/live_integration/conftest.py`

The conftest.py currently lacks marker registration for custom markers used across tests.

**Current State (lines 1-30):**
```python
"""
Live Integration Test Configuration
...
"""

import os
import sys
import uuid
import time
import pytest
from pathlib import Path
from typing import Generator, Dict, Any
```

**Remediation - Add at top of conftest.py after imports:**

```python
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "shared: mark test as shared library test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "api: mark test as requiring API access")
```

---

### 1.2 Missing pytest Markers on Test Classes

**Impact:** Inconsistent test categorization, no ability to filter by test type
**Files Affected:** 10 files, 43 classes

| File | Classes Missing Markers | Lines |
|------|------------------------|-------|
| `test_issue_lifecycle.py` | 6 classes | 11, 79, 124, 168, 216, 252 |
| `test_collaboration.py` | 6 classes | 13, 124, 236, 298, 331, 406 |
| `test_agile_workflow.py` | 6 classes | 12, 102, 194, 246, 336, 360 |
| `test_relationships.py` | 5 classes | 11, 39, 140, 208, 281 |
| `test_time_tracking.py` | 4 classes | 27, 155, 235, 320 |
| `test_search_filters.py` | 6 classes | 11, 56, 103, 273, 340, 467 |
| `test_component_management.py` | 3 classes | 11, 192, 348 |
| `test_version_management.py` | 3 classes | 13, 188, 343 |
| `test_project_lifecycle.py` | 4 classes | 14, 81, 118, 176 |

**Remediation Template:**

```python
# Before:
class TestIssueCreate:
    """Tests for issue creation."""

# After:
@pytest.mark.integration
@pytest.mark.shared
class TestIssueCreate:
    """Tests for issue creation."""
```

---

### 1.3 Weak Assertions That Always Pass

**Impact:** Tests pass even when functionality is broken
**Files Affected:** 2 files

| File | Line | Current Assertion | Fix |
|------|------|-------------------|-----|
| `test_search_filters.py` | 94 | `assert len(result['results']) >= 0` | `assert isinstance(result['results'], list)` |
| `test_collaboration.py` | 376, 389, 403 | `assert True` | Add meaningful assertions |

**Remediation for test_search_filters.py:94:**

```python
# Before (weak):
assert len(result['results']) >= 0  # May be empty if no issues exist

# After (strong):
assert 'results' in result
assert isinstance(result['results'], list)
# Optionally add a comment explaining why empty is acceptable
# NOTE: Results may be empty if no issues exist yet in the project
```

**Remediation for test_collaboration.py (lines 376, 389, 403):**

The notification tests use `assert True` after API calls without verifying outcomes.

```python
# test_collaboration.py:365-376 (Current - weak)
def test_notify_specific_user(self, jira_client, test_issue):
    """Test sending notification to a specific user."""
    current_user_id = jira_client.get_current_user_id()

    jira_client.notify_issue(
        test_issue['key'],
        subject="Test notification to specific user",
        text_body="User-specific notification test",
        to={'users': [{'accountId': current_user_id}]}
    )

    assert True  # Weak assertion

# After (stronger):
def test_notify_specific_user(self, jira_client, test_issue):
    """Test sending notification to a specific user."""
    current_user_id = jira_client.get_current_user_id()

    # Note: notify_issue returns None on success, raises on failure
    # The lack of exception IS the success verification
    try:
        jira_client.notify_issue(
            test_issue['key'],
            subject="Test notification to specific user",
            text_body="User-specific notification test",
            to={'users': [{'accountId': current_user_id}]}
        )
    except Exception as e:
        pytest.fail(f"Notification failed unexpectedly: {e}")
    # Success: no exception raised
```

---

## Phase 2: High Priority Issues

### 2.1 Cleanup Not in try/finally Blocks

**Impact:** Resource leakage when tests fail, orphaned JIRA resources
**Pattern:** Multiple tests perform cleanup outside try/finally

**Files Affected:** 9 files with cleanup issues

| File | Affected Tests | Cleanup Pattern Issue |
|------|----------------|----------------------|
| `test_issue_lifecycle.py` | 4 tests | Lines 25, 43, 57, 75 - cleanup outside try/finally |
| `test_agile_workflow.py` | 9 tests | Lines 29, 50, 154, 190, 214, 241, 269, 291, 331 |
| `test_relationships.py` | 8 tests | Lines 76, 107, 135, 171, 203, 241, 275 |
| `test_component_management.py` | 3 tests | Lines 28, 46, 62 |
| `test_version_management.py` | 2 tests | Lines 32, 55 |

**Example Issue - test_issue_lifecycle.py:14-27:**

```python
# Current (cleanup not protected):
def test_create_task(self, jira_client, test_project):
    """Test creating a basic task."""
    issue = jira_client.create_issue({
        'project': {'key': test_project['key']},
        'summary': f'Test Task {uuid.uuid4().hex[:8]}',
        'issuetype': {'name': 'Task'}
    })

    assert issue['key'].startswith(test_project['key'])
    assert 'id' in issue

    # Cleanup - will not run if assertion above fails!
    jira_client.delete_issue(issue['key'])
```

**Remediation:**

```python
# Fixed (cleanup protected by try/finally):
def test_create_task(self, jira_client, test_project):
    """Test creating a basic task."""
    issue = jira_client.create_issue({
        'project': {'key': test_project['key']},
        'summary': f'Test Task {uuid.uuid4().hex[:8]}',
        'issuetype': {'name': 'Task'}
    })

    try:
        assert issue['key'].startswith(test_project['key'])
        assert 'id' in issue
    finally:
        # Cleanup always runs
        try:
            jira_client.delete_issue(issue['key'])
        except Exception:
            pass  # Issue may have been deleted by test
```

**Full List of Tests Requiring try/finally Wrapping:**

1. `test_issue_lifecycle.py`:
   - `test_create_task` (line 14)
   - `test_create_story` (line 28)
   - `test_create_bug` (line 46)
   - `test_create_subtask` (line 60)

2. `test_agile_workflow.py`:
   - `test_create_sprint` (line 15)
   - `test_create_sprint_with_dates` (line 32)
   - `test_move_multiple_issues_to_sprint` (line 131)
   - `test_get_sprint_issues` (line 158)
   - `test_get_backlog` (line 197)
   - `test_rank_issues` (line 217)
   - `test_create_epic` (line 253)
   - `test_add_issue_to_epic` (line 272)
   - `test_get_epic_children` (line 294)

3. `test_relationships.py`:
   - `test_create_blocks_link` (line 42)
   - `test_create_relates_link` (line 80)
   - `test_create_duplicate_link` (line 111)
   - `test_get_issue_links` (line 143)
   - `test_get_link_by_id` (line 176)
   - `test_delete_link` (line 211)
   - `test_delete_all_links` (line 245)

4. `test_component_management.py`:
   - `test_create_component` (line 14)
   - `test_create_component_with_lead` (line 31)
   - `test_create_component_with_assignee_type` (line 49)

5. `test_version_management.py`:
   - `test_create_version` (line 16)
   - `test_create_version_with_dates` (line 35)

---

### 2.2 Hardcoded Field IDs

**Impact:** Tests may fail on different JIRA instances with different custom field IDs
**Files Affected:** 2 files

| File | Line | Field | Current ID |
|------|------|-------|------------|
| `test_agile_workflow.py` | 106 | Sprint Field | `customfield_10020` |
| `test_agile_workflow.py` | 364 | Story Points | `customfield_10016` |
| `conftest.py` | 251 | Epic Name (commented) | `customfield_10011` |

**Current Implementation - test_agile_workflow.py:102-116:**

```python
class TestSprintIssueManagement:
    """Tests for moving issues to/from sprints."""

    # Sprint field ID - may vary by JIRA instance
    SPRINT_FIELD = 'customfield_10020'

    def _verify_issue_in_sprint(self, jira_client, sprint_id, issue_key):
        """Verify an issue is assigned to a sprint by checking its sprint field."""
        issue = jira_client.get_issue(issue_key)
        sprint_field = issue['fields'].get(self.SPRINT_FIELD, [])
        # ...
```

**Remediation Option A - Environment Variable Override:**

```python
class TestSprintIssueManagement:
    """Tests for moving issues to/from sprints."""

    # Sprint field ID - may vary by JIRA instance
    # Override via JIRA_SPRINT_FIELD_ID environment variable
    SPRINT_FIELD = os.environ.get('JIRA_SPRINT_FIELD_ID', 'customfield_10020')
```

**Remediation Option B - Fixture-based Configuration:**

Add to `conftest.py`:

```python
@pytest.fixture(scope="session")
def agile_field_ids():
    """
    Return Agile custom field IDs for the current JIRA instance.

    These can be overridden via environment variables for different instances.
    """
    return {
        'sprint': os.environ.get('JIRA_SPRINT_FIELD_ID', 'customfield_10020'),
        'story_points': os.environ.get('JIRA_STORY_POINTS_FIELD_ID', 'customfield_10016'),
        'epic_link': os.environ.get('JIRA_EPIC_LINK_FIELD_ID', 'customfield_10014'),
        'epic_name': os.environ.get('JIRA_EPIC_NAME_FIELD_ID', 'customfield_10011'),
    }
```

Then update tests to use fixture:

```python
class TestSprintIssueManagement:
    """Tests for moving issues to/from sprints."""

    def _verify_issue_in_sprint(self, jira_client, sprint_id, issue_key, sprint_field_id):
        """Verify an issue is assigned to a sprint by checking its sprint field."""
        issue = jira_client.get_issue(issue_key)
        sprint_field = issue['fields'].get(sprint_field_id, [])
        # ...

    def test_move_issue_to_sprint(self, jira_client, test_sprint, test_issue, agile_field_ids):
        """Test moving an issue to a sprint."""
        jira_client.move_issues_to_sprint(test_sprint['id'], [test_issue['key']])

        assert self._verify_issue_in_sprint(
            jira_client,
            test_sprint['id'],
            test_issue['key'],
            agile_field_ids['sprint']
        )
```

---

### 2.3 Missing Error Handling Tests

**Impact:** Error scenarios completely untested
**Coverage Gap:** No tests for API error responses (401, 403, 404, 429, 500)

**Current State:** Zero tests for error handling across all 157 test functions

**Remediation - Add new test class to conftest.py or create new file:**

```python
# tests/live_integration/test_error_handling.py

"""
Live Integration Tests: Error Handling

Tests for error handling scenarios against a real JIRA instance.
Note: These tests may need special setup/teardown to trigger error conditions.
"""

import pytest
from error_handler import NotFoundError, AuthenticationError, ValidationError, JiraError


@pytest.mark.integration
@pytest.mark.shared
class TestNotFoundErrors:
    """Tests for 404 Not Found error handling."""

    def test_get_nonexistent_issue(self, jira_client):
        """Test 404 error when issue doesn't exist."""
        with pytest.raises(NotFoundError):
            jira_client.get_issue('NONEXISTENT-99999')

    def test_get_nonexistent_project(self, jira_client):
        """Test 404 error when project doesn't exist."""
        with pytest.raises(NotFoundError):
            jira_client.get_project('ZZZNONEXISTENT')

    def test_get_nonexistent_sprint(self, jira_client):
        """Test 404 error when sprint doesn't exist."""
        with pytest.raises(NotFoundError):
            jira_client.get_sprint(99999999)

    def test_get_nonexistent_filter(self, jira_client):
        """Test 404 error when filter doesn't exist."""
        with pytest.raises(NotFoundError):
            jira_client.get_filter('99999999')


@pytest.mark.integration
@pytest.mark.shared
class TestValidationErrors:
    """Tests for 400 Bad Request validation errors."""

    def test_create_issue_missing_project(self, jira_client):
        """Test validation error when project is missing."""
        with pytest.raises((ValidationError, JiraError)):
            jira_client.create_issue({
                'summary': 'Test Issue',
                'issuetype': {'name': 'Task'}
                # Missing 'project' field
            })

    def test_create_issue_invalid_type(self, jira_client, test_project):
        """Test validation error when issue type is invalid."""
        with pytest.raises((ValidationError, JiraError)):
            jira_client.create_issue({
                'project': {'key': test_project['key']},
                'summary': 'Test Issue',
                'issuetype': {'name': 'InvalidTypeXYZ123'}
            })

    def test_invalid_jql_query(self, jira_client):
        """Test validation error for malformed JQL."""
        with pytest.raises((ValidationError, JiraError)):
            jira_client.search_issues('projct = INVALID AND statuss = Open')


@pytest.mark.integration
@pytest.mark.shared
class TestPermissionErrors:
    """Tests for 403 Forbidden permission errors.

    Note: These tests may require specific project/user setup.
    Skip if unable to create permission-restricted scenarios.
    """

    @pytest.mark.skip(reason="Requires specific permission setup")
    def test_delete_protected_issue(self, jira_client):
        """Test 403 error when deleting issue without permission."""
        # This would require a project where the test user lacks delete permission
        pass
```

---

## Phase 3: Medium Priority Issues

### 3.1 Notification Tests with Weak Assertions

**Impact:** Notification functionality effectively untested
**File:** `test_collaboration.py`
**Lines:** 365-403

The notification tests (3 tests) all use `assert True` after API calls.

**Current State:**

```python
# Lines 365-376
def test_notify_specific_user(self, jira_client, test_issue):
    """Test sending notification to a specific user."""
    current_user_id = jira_client.get_current_user_id()

    jira_client.notify_issue(...)

    assert True  # No actual verification

# Lines 378-389 - same pattern
# Lines 391-403 - same pattern
```

**Remediation:**

Since JIRA's notify API doesn't return notification details, we should at minimum verify the call completes without error and document the limitation:

```python
def test_notify_specific_user(self, jira_client, test_issue):
    """
    Test sending notification to a specific user.

    Note: JIRA's notify API returns empty on success. We verify success
    by the absence of exceptions. Email delivery cannot be verified.
    """
    current_user_id = jira_client.get_current_user_id()

    # This should not raise an exception
    jira_client.notify_issue(
        test_issue['key'],
        subject="Test notification to specific user",
        text_body="User-specific notification test",
        to={'users': [{'accountId': current_user_id}]}
    )
    # Success: API call completed without exception
    # Note: Cannot verify actual email delivery via API
```

---

### 3.2 Missing Edge Case Tests

**Priority order by impact:**

| Category | File | Missing Edge Case |
|----------|------|-------------------|
| Empty results | `test_search_filters.py` | Search with no matches |
| Boundary values | `test_time_tracking.py` | Zero time estimate |
| Boundary values | `test_time_tracking.py` | Maximum time format |
| Invalid input | `test_agile_workflow.py` | Sprint with invalid board |
| Concurrent ops | All files | Race condition handling |
| Unicode | `test_issue_lifecycle.py` | Unicode in summary/description |
| Long strings | `test_issue_lifecycle.py` | 255+ char summary |

**Remediation Template - Empty Results Test:**

```python
# Add to test_search_filters.py
def test_search_no_matches(self, jira_client, test_project):
    """Test JQL search that returns no results."""
    # Use a filter guaranteed to return no results
    jql = f"project = {test_project['key']} AND summary ~ 'zzznonexistent999'"
    result = jira_client.search_issues(jql)

    assert 'issues' in result
    assert result['total'] == 0
    assert len(result['issues']) == 0
```

**Remediation Template - Unicode Test:**

```python
# Add to test_issue_lifecycle.py
def test_create_issue_unicode(self, jira_client, test_project):
    """Test creating issue with Unicode characters."""
    summary = f'Test Issue \u4e2d\u6587 \u65e5\u672c\u8a9e {uuid.uuid4().hex[:8]}'

    issue = jira_client.create_issue({
        'project': {'key': test_project['key']},
        'summary': summary,
        'issuetype': {'name': 'Task'}
    })

    try:
        assert issue['key'].startswith(test_project['key'])

        # Verify Unicode preserved
        fetched = jira_client.get_issue(issue['key'])
        assert '\u4e2d\u6587' in fetched['fields']['summary']
    finally:
        jira_client.delete_issue(issue['key'])
```

---

### 3.3 Inconsistent Import Patterns

**Impact:** Maintenance burden, potential confusion
**Files Affected:** All test files

Some files import `uuid` at module level but also import it locally in test functions.

**Example - test_issue_lifecycle.py:**

```python
# Line 8 - module level import
import uuid

# Line 257, 295, 330, etc. - redundant local imports
def test_resolve_issue(self, jira_client, test_project):
    """Test resolving an issue with a resolution."""
    import uuid  # Redundant!
    issue = jira_client.create_issue({...})
```

**Files with redundant uuid imports:**

| File | Lines with redundant import |
|------|----------------------------|
| `test_issue_lifecycle.py` | 257, 295, 330, 376, 420 |
| `test_collaboration.py` | 393, 411, 425, 451 |
| `test_agile_workflow.py` | 368, 393, 419 |

**Remediation:**

Remove redundant local imports since `uuid` is already imported at module level.

---

### 3.4 Missing Fixture Cleanup Safety

**Impact:** Resource leakage if fixture setup fails partway through
**File:** `conftest.py`
**Lines:** 78-146 (test_project fixture)

**Current State:**

```python
@pytest.fixture(scope="session")
def test_project(jira_client, keep_project, existing_project_key):
    # ... setup code ...

    project = jira_client.create_project(...)

    # Wait for board creation
    time.sleep(2)

    # Get the auto-created board
    boards = jira_client.get_all_boards(project_key=project_key)
    # If this fails, project exists but cleanup won't run!

    yield project_data

    # Cleanup
    if not keep_project and project_data.get('is_temporary', True):
        cleanup_project(jira_client, project_key)
```

**Remediation:**

```python
@pytest.fixture(scope="session")
def test_project(jira_client, keep_project, existing_project_key):
    if existing_project_key:
        # ... existing project logic ...
        return

    project_key = f"INT{uuid.uuid4().hex[:6].upper()}"
    project = None

    try:
        project = jira_client.create_project(
            key=project_key,
            name=f"Integration Test {project_key}",
            project_type_key='software',
            template_key='com.pyxis.greenhopper.jira:gh-simplified-agility-scrum',
            description='Temporary project for live integration tests'
        )

        time.sleep(2)

        boards = jira_client.get_all_boards(project_key=project_key)
        board_id = boards['values'][0]['id'] if boards.get('values') else None

        project_data = {
            'id': project['id'],
            'key': project_key,
            'name': f"Integration Test {project_key}",
            'board_id': board_id,
            'is_temporary': True
        }

        yield project_data

    finally:
        # Cleanup even if setup partially failed
        if project and not keep_project:
            try:
                cleanup_project(jira_client, project_key)
            except Exception as e:
                print(f"Warning: Cleanup failed for {project_key}: {e}")
```

---

## Phase 4: Low Priority Issues

### 4.1 Remove Redundant Local Imports

**Impact:** Code hygiene, slight performance improvement
**Files Affected:** 3 files

```bash
# Files with redundant uuid imports:
test_issue_lifecycle.py: lines 257, 295, 330, 376, 420
test_collaboration.py: lines 393, 411, 425, 451
test_agile_workflow.py: lines 368, 393, 419
```

**Remediation:**

Simply remove the `import uuid` statements from inside test functions since `uuid` is already imported at the module level in all these files.

---

### 4.2 Add Test Documentation

**Impact:** Maintainability, onboarding
**Files Affected:** All test files

Add module-level docstrings with test categories and requirements:

```python
"""
Live Integration Tests: Issue Lifecycle

Tests for issue CRUD operations against a real JIRA instance.

Test Categories:
- TestIssueCreate: Issue creation (Task, Story, Bug, Subtask)
- TestIssueRead: Issue retrieval and search
- TestIssueUpdate: Issue field updates and assignment
- TestIssueDelete: Issue deletion and cascading
- TestIssueTransitions: Workflow transitions
- TestIssueResolution: Resolution and reopening

Requirements:
- JIRA admin permissions (for project access)
- Valid JIRA profile configured
- Network access to JIRA instance

Usage:
    pytest test_issue_lifecycle.py --profile development -v
"""
```

---

### 4.3 Add Test Counts and Verification

**Impact:** Catch accidental test deletion or breakage
**File:** Create new `tests/live_integration/test_meta.py`

```python
"""Meta-tests to verify test suite integrity."""

import pytest
from pathlib import Path


@pytest.mark.integration
class TestSuiteIntegrity:
    """Verify test suite hasn't regressed."""

    def test_minimum_test_count(self):
        """Ensure we haven't lost tests."""
        test_dir = Path(__file__).parent
        test_files = list(test_dir.glob('test_*.py'))

        test_count = 0
        for f in test_files:
            content = f.read_text()
            test_count += content.count('def test_')

        # Current count: 157 tests
        MIN_TESTS = 150
        assert test_count >= MIN_TESTS, f"Expected {MIN_TESTS}+ tests, found {test_count}"

    def test_all_files_have_docstrings(self):
        """Ensure all test files have module docstrings."""
        test_dir = Path(__file__).parent
        test_files = list(test_dir.glob('test_*.py'))

        for f in test_files:
            content = f.read_text()
            assert content.strip().startswith('"""') or content.strip().startswith("'''"), \
                f"{f.name} missing module docstring"
```

---

### 4.4 Standardize Assertion Messages

**Impact:** Better debugging experience
**Pattern:** Add assertion messages for complex assertions

```python
# Before:
assert issue['key'].startswith(test_project['key'])

# After:
assert issue['key'].startswith(test_project['key']), \
    f"Expected issue key to start with '{test_project['key']}', got '{issue['key']}'"
```

---

## Implementation Checklist

### Phase 1 Checklist (Critical)

- [ ] Add `pytest_configure` to `conftest.py` for marker registration
- [ ] Add `@pytest.mark.integration` and `@pytest.mark.shared` to all 43 test classes
- [ ] Fix weak assertion in `test_search_filters.py:94`
- [ ] Fix `assert True` statements in `test_collaboration.py` (lines 376, 389, 403)

### Phase 2 Checklist (High Priority)

- [ ] Wrap cleanup in try/finally for 4 tests in `test_issue_lifecycle.py`
- [ ] Wrap cleanup in try/finally for 9 tests in `test_agile_workflow.py`
- [ ] Wrap cleanup in try/finally for 8 tests in `test_relationships.py`
- [ ] Wrap cleanup in try/finally for 3 tests in `test_component_management.py`
- [ ] Wrap cleanup in try/finally for 2 tests in `test_version_management.py`
- [ ] Add `agile_field_ids` fixture for configurable custom field IDs
- [ ] Update hardcoded field IDs to use fixture/env vars
- [ ] Create `test_error_handling.py` with NotFound and Validation error tests

### Phase 3 Checklist (Medium Priority)

- [ ] Improve notification test assertions (3 tests)
- [ ] Add empty results edge case test to `test_search_filters.py`
- [ ] Add Unicode character test to `test_issue_lifecycle.py`
- [ ] Remove redundant local imports (3 files, 12+ instances)
- [ ] Fix fixture cleanup safety in `test_project` fixture

### Phase 4 Checklist (Low Priority)

- [ ] Add module-level docstrings to all test files
- [ ] Create `test_meta.py` for suite integrity checks
- [ ] Add assertion messages to complex assertions
- [ ] Document test coverage in README

---

## Verification Commands

```bash
# Run all shared library integration tests
pytest .claude/skills/shared/tests/live_integration/ --profile development -v

# Run with markers (after adding markers)
pytest .claude/skills/shared/tests/live_integration/ -m "integration and shared" -v

# Collect tests only (verify count)
pytest .claude/skills/shared/tests/live_integration/ --collect-only | grep "test session starts" -A 5

# Run specific test file
pytest .claude/skills/shared/tests/live_integration/test_issue_lifecycle.py -v

# Run with verbose error handling
pytest .claude/skills/shared/tests/live_integration/ --tb=long -v

# Check for marker warnings
pytest .claude/skills/shared/tests/live_integration/ --strict-markers
```

---

## Success Criteria

1. **All tests pass:** `pytest` exits with code 0
2. **No weak assertions:** No `>= 0` or `assert True` without context
3. **Consistent markers:** All test classes have `@pytest.mark.integration` and `@pytest.mark.shared`
4. **No pytest warnings:** About unknown markers
5. **Coverage maintained:** Test count >= 150 tests
6. **Cleanup safety:** All resource cleanup in try/finally blocks
7. **Configurable fields:** Agile custom fields use environment variable overrides

---

## Notes

- Prioritize Phase 1 before running tests in CI
- Phase 2 should be completed to prevent resource leakage
- Phases 3-4 can be addressed incrementally
- Consider adding pre-commit hooks to catch marker issues
- The cleanup.py utility can help recover from failed test runs

---

## Related Documentation

- [CLAUDE.md](/CLAUDE.md) - Project guidelines and testing strategy
- [jira-admin TEST_REMEDIATION_PLAN.md](/docs/implementation-plans/jira-admin/TEST_REMEDIATION_PLAN.md) - Similar remediation for jira-admin skill
- [Live Integration README](/Users/jasonkrueger/IdeaProjects/Jira-Assistant-Skills/.claude/skills/shared/tests/live_integration/README.md) - Test usage instructions
