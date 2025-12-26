# Test Remediation Plan: jira-lifecycle Skill

**Created:** 2025-12-26
**Status:** Draft
**Test Files Reviewed:** 11
**Total Issues Identified:** ~85+

---

## Executive Summary

This plan addresses test quality issues discovered during a comprehensive review of the `jira-lifecycle` skill test suite. Issues are organized by priority and grouped into actionable phases.

**Issue Breakdown:**
| Category | Count |
|----------|-------|
| Scripts without tests | 4 |
| Missing pytest markers | 11 classes |
| Unused imports (MagicMock) | 10 files |
| Missing error handling tests | 11 files |
| Missing deepcopy for fixtures | All test files |
| Weak/missing assertions | 3 instances |

**Estimated Effort:**
- Phase 1 (Critical): 4-6 hours
- Phase 2 (High Priority): 4-6 hours
- Phase 3 (Medium Priority): 3-4 hours
- Phase 4 (Low Priority): 1-2 hours

---

## Phase 1: Critical Issues (Must Fix)

### 1.1 Scripts Without Tests

**Impact:** Zero test coverage on critical workflow scripts
**Scripts Affected:** 4 scripts with no test files

| Script | Functionality | Priority |
|--------|--------------|----------|
| `scripts/get_transitions.py` | Get available transitions for an issue | HIGH |
| `scripts/resolve_issue.py` | Resolve an issue with resolution | HIGH |
| `scripts/reopen_issue.py` | Reopen a closed/resolved issue | HIGH |
| `scripts/assign_issue.py` | Assign/reassign issues | HIGH |

**Remediation - Create test files:**

**File: `tests/test_get_transitions.py`**
```python
"""
Tests for get_transitions.py - Get available transitions for an issue.
"""

import pytest
from unittest.mock import patch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


@pytest.mark.lifecycle
@pytest.mark.unit
class TestGetTransitions:
    """Tests for getting issue transitions."""

    @patch('get_transitions.get_jira_client')
    def test_get_transitions_success(self, mock_get_client, mock_jira_client, sample_transitions):
        """Test getting transitions for an issue."""
        import copy
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.return_value = copy.deepcopy(sample_transitions)

        from get_transitions import get_transitions

        result = get_transitions('PROJ-123', profile=None)

        assert len(result) == 3
        assert any(t['name'] == 'In Progress' for t in result)
        mock_jira_client.get_transitions.assert_called_once_with('PROJ-123')

    @patch('get_transitions.get_jira_client')
    def test_get_transitions_empty(self, mock_get_client, mock_jira_client):
        """Test handling when no transitions available."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.return_value = []

        from get_transitions import get_transitions

        result = get_transitions('PROJ-123', profile=None)

        assert result == []

    @patch('get_transitions.get_jira_client')
    def test_get_transitions_invalid_issue_key(self, mock_get_client, mock_jira_client):
        """Test error on invalid issue key."""
        from error_handler import ValidationError

        with pytest.raises(ValidationError):
            from get_transitions import get_transitions
            get_transitions('invalid', profile=None)

    @patch('get_transitions.get_jira_client')
    def test_get_transitions_issue_not_found(self, mock_get_client, mock_jira_client):
        """Test handling of 404 when issue doesn't exist."""
        from error_handler import NotFoundError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.side_effect = NotFoundError("Issue not found")

        from get_transitions import get_transitions

        with pytest.raises(NotFoundError):
            get_transitions('PROJ-999', profile=None)
```

**File: `tests/test_resolve_issue.py`**
```python
"""
Tests for resolve_issue.py - Resolve a JIRA issue.
"""

import pytest
from unittest.mock import patch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


@pytest.mark.lifecycle
@pytest.mark.unit
class TestResolveIssue:
    """Tests for resolving issues."""

    @patch('resolve_issue.get_jira_client')
    def test_resolve_issue_success(self, mock_get_client, mock_jira_client, sample_transitions):
        """Test resolving an issue with default resolution."""
        import copy
        transitions = copy.deepcopy(sample_transitions)
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.return_value = transitions

        from resolve_issue import resolve_issue

        resolve_issue('PROJ-123', resolution='Fixed', profile=None)

        mock_jira_client.transition_issue.assert_called_once()
        call_args = mock_jira_client.transition_issue.call_args
        assert call_args[0][0] == 'PROJ-123'
        assert call_args[1]['fields']['resolution'] == {'name': 'Fixed'}

    @patch('resolve_issue.get_jira_client')
    def test_resolve_issue_with_comment(self, mock_get_client, mock_jira_client, sample_transitions):
        """Test resolving an issue with a comment."""
        import copy
        transitions = copy.deepcopy(sample_transitions)
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.return_value = transitions

        from resolve_issue import resolve_issue

        resolve_issue('PROJ-123', resolution='Fixed', comment='Bug fixed', profile=None)

        call_args = mock_jira_client.transition_issue.call_args
        assert 'comment' in call_args[1]['fields']

    @patch('resolve_issue.get_jira_client')
    def test_resolve_issue_no_transitions(self, mock_get_client, mock_jira_client):
        """Test error when no transitions available."""
        from error_handler import ValidationError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.return_value = []

        from resolve_issue import resolve_issue

        with pytest.raises(ValidationError, match="No transitions available"):
            resolve_issue('PROJ-123', resolution='Fixed', profile=None)

    @patch('resolve_issue.get_jira_client')
    def test_resolve_issue_no_resolve_transition(self, mock_get_client, mock_jira_client):
        """Test error when no resolution transition found."""
        from error_handler import ValidationError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.return_value = [
            {'id': '1', 'name': 'Start Progress'}
        ]

        from resolve_issue import resolve_issue

        with pytest.raises(ValidationError, match="No resolution transition"):
            resolve_issue('PROJ-123', resolution='Fixed', profile=None)


@pytest.mark.lifecycle
@pytest.mark.unit
class TestResolveIssueErrorHandling:
    """Test API error handling for resolve_issue."""

    @patch('resolve_issue.get_jira_client')
    def test_authentication_error(self, mock_get_client, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from error_handler import AuthenticationError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.side_effect = AuthenticationError("Invalid token")

        from resolve_issue import resolve_issue

        with pytest.raises(AuthenticationError):
            resolve_issue('PROJ-123', resolution='Fixed', profile=None)

    @patch('resolve_issue.get_jira_client')
    def test_permission_denied(self, mock_get_client, mock_jira_client, sample_transitions):
        """Test handling of 403 forbidden."""
        import copy
        from error_handler import PermissionError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.return_value = copy.deepcopy(sample_transitions)
        mock_jira_client.transition_issue.side_effect = PermissionError("Cannot transition")

        from resolve_issue import resolve_issue

        with pytest.raises(PermissionError):
            resolve_issue('PROJ-123', resolution='Fixed', profile=None)
```

**File: `tests/test_reopen_issue.py`**
```python
"""
Tests for reopen_issue.py - Reopen a closed/resolved issue.
"""

import pytest
from unittest.mock import patch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


@pytest.mark.lifecycle
@pytest.mark.unit
class TestReopenIssue:
    """Tests for reopening issues."""

    @patch('reopen_issue.get_jira_client')
    def test_reopen_issue_success(self, mock_get_client, mock_jira_client):
        """Test reopening a resolved issue."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.return_value = [
            {'id': '11', 'name': 'Reopen'},
            {'id': '21', 'name': 'Start Progress'}
        ]

        from reopen_issue import reopen_issue

        reopen_issue('PROJ-123', profile=None)

        mock_jira_client.transition_issue.assert_called_once()
        call_args = mock_jira_client.transition_issue.call_args
        assert call_args[0][1] == '11'  # Reopen transition ID

    @patch('reopen_issue.get_jira_client')
    def test_reopen_issue_with_comment(self, mock_get_client, mock_jira_client):
        """Test reopening with a comment."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.return_value = [
            {'id': '11', 'name': 'Reopen'}
        ]

        from reopen_issue import reopen_issue

        reopen_issue('PROJ-123', comment='Regression found', profile=None)

        call_args = mock_jira_client.transition_issue.call_args
        assert call_args[1]['fields'] is not None

    @patch('reopen_issue.get_jira_client')
    def test_reopen_issue_uses_todo_fallback(self, mock_get_client, mock_jira_client):
        """Test falling back to To Do transition when no Reopen."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.return_value = [
            {'id': '11', 'name': 'To Do'},
            {'id': '21', 'name': 'Done'}
        ]

        from reopen_issue import reopen_issue

        reopen_issue('PROJ-123', profile=None)

        call_args = mock_jira_client.transition_issue.call_args
        assert call_args[0][1] == '11'  # To Do transition ID

    @patch('reopen_issue.get_jira_client')
    def test_reopen_issue_no_transitions(self, mock_get_client, mock_jira_client):
        """Test error when no transitions available."""
        from error_handler import ValidationError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.return_value = []

        from reopen_issue import reopen_issue

        with pytest.raises(ValidationError, match="No transitions available"):
            reopen_issue('PROJ-123', profile=None)

    @patch('reopen_issue.get_jira_client')
    def test_reopen_issue_no_reopen_transition(self, mock_get_client, mock_jira_client):
        """Test error when no reopen transition found."""
        from error_handler import ValidationError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.return_value = [
            {'id': '21', 'name': 'Done'}
        ]

        from reopen_issue import reopen_issue

        with pytest.raises(ValidationError, match="No reopen transition"):
            reopen_issue('PROJ-123', profile=None)
```

**File: `tests/test_assign_issue.py`**
```python
"""
Tests for assign_issue.py - Assign or reassign a JIRA issue.
"""

import pytest
from unittest.mock import patch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


@pytest.mark.lifecycle
@pytest.mark.unit
class TestAssignIssue:
    """Tests for issue assignment."""

    @patch('assign_issue.get_jira_client')
    def test_assign_issue_by_account_id(self, mock_get_client, mock_jira_client):
        """Test assigning issue by account ID."""
        mock_get_client.return_value = mock_jira_client

        from assign_issue import assign_issue

        assign_issue('PROJ-123', user='5b10ac8d82e05b22cc7d4ef5', profile=None)

        mock_jira_client.assign_issue.assert_called_once_with(
            'PROJ-123', '5b10ac8d82e05b22cc7d4ef5'
        )

    @patch('assign_issue.get_jira_client')
    def test_assign_issue_to_self(self, mock_get_client, mock_jira_client):
        """Test assigning issue to current user."""
        mock_get_client.return_value = mock_jira_client

        from assign_issue import assign_issue

        assign_issue('PROJ-123', assign_to_self=True, profile=None)

        mock_jira_client.assign_issue.assert_called_once_with('PROJ-123', '-1')

    @patch('assign_issue.get_jira_client')
    def test_unassign_issue(self, mock_get_client, mock_jira_client):
        """Test removing assignee from issue."""
        mock_get_client.return_value = mock_jira_client

        from assign_issue import assign_issue

        assign_issue('PROJ-123', unassign=True, profile=None)

        mock_jira_client.assign_issue.assert_called_once_with('PROJ-123', None)

    @patch('assign_issue.get_jira_client')
    def test_assign_requires_one_option(self, mock_get_client, mock_jira_client):
        """Test error when no assignment option specified."""
        from error_handler import ValidationError

        from assign_issue import assign_issue

        with pytest.raises(ValidationError, match="Specify exactly one"):
            assign_issue('PROJ-123', profile=None)

    @patch('assign_issue.get_jira_client')
    def test_assign_rejects_multiple_options(self, mock_get_client, mock_jira_client):
        """Test error when multiple assignment options specified."""
        from error_handler import ValidationError

        from assign_issue import assign_issue

        with pytest.raises(ValidationError, match="Specify exactly one"):
            assign_issue('PROJ-123', user='test', assign_to_self=True, profile=None)


@pytest.mark.lifecycle
@pytest.mark.unit
class TestAssignIssueErrorHandling:
    """Test API error handling for assign_issue."""

    @patch('assign_issue.get_jira_client')
    def test_issue_not_found(self, mock_get_client, mock_jira_client):
        """Test handling of 404 when issue doesn't exist."""
        from error_handler import NotFoundError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.assign_issue.side_effect = NotFoundError("Issue not found")

        from assign_issue import assign_issue

        with pytest.raises(NotFoundError):
            assign_issue('PROJ-999', user='test', profile=None)

    @patch('assign_issue.get_jira_client')
    def test_permission_denied(self, mock_get_client, mock_jira_client):
        """Test handling of 403 when not allowed to assign."""
        from error_handler import PermissionError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.assign_issue.side_effect = PermissionError("Cannot assign")

        from assign_issue import assign_issue

        with pytest.raises(PermissionError):
            assign_issue('PROJ-123', user='test', profile=None)
```

---

### 1.2 Missing pytest Marker Registration

**Impact:** pytest warnings, inconsistent test selection
**File:** `tests/conftest.py`

**Add at top of conftest.py:**

```python
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "lifecycle: mark test as lifecycle skill test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
```

---

### 1.3 Missing pytest Markers on Test Classes

**Impact:** Inconsistent test categorization
**Files Affected:** All 11 test files

| File | Line | Classes Missing Markers |
|------|------|------------------------|
| `tests/test_transition_issue.py` | 17, 54, 118 | `TestFindTransitionByName`, `TestTransitionIssue`, `TestTransitionWithSprint` |
| `tests/test_create_version.py` | 14 | `TestCreateVersion` |
| `tests/test_get_versions.py` | 14 | `TestGetVersions` |
| `tests/test_release_version.py` | 14 | `TestReleaseVersion` |
| `tests/test_archive_version.py` | 14 | `TestArchiveVersion` |
| `tests/test_move_issues_version.py` | 14 | `TestMoveIssuesVersion` |
| `tests/test_create_component.py` | 14 | `TestCreateComponent` |
| `tests/test_get_components.py` | 14 | `TestGetComponents` |
| `tests/test_update_component.py` | 14 | `TestUpdateComponent` |
| `tests/test_delete_component.py` | 14 | `TestDeleteComponent` |

**Remediation:**

```python
# Add to each test class:
@pytest.mark.lifecycle
@pytest.mark.unit
class TestClassName:
    """Test description."""
```

---

## Phase 2: High Priority Issues

### 2.1 Missing Error Handling Tests

**Impact:** Error scenarios untested, poor user experience on failures
**Coverage Gap:** All test files missing tests for:
- `AuthenticationError` (401)
- `PermissionError` (403)
- `NotFoundError` (404)
- Rate limiting (429)
- Server errors (500, 502, 503, 504)
- Network timeout/connection errors

**Files to Update:** All 11 test files

**Remediation Template:**

```python
@pytest.mark.lifecycle
@pytest.mark.unit
class TestApiErrorHandling:
    """Test API error handling scenarios."""

    @patch('module_name.get_jira_client')
    def test_authentication_error(self, mock_get_client, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from error_handler import AuthenticationError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.some_method.side_effect = AuthenticationError("Invalid token")

        from module_name import function_name

        with pytest.raises(AuthenticationError):
            function_name(...)

    @patch('module_name.get_jira_client')
    def test_permission_error(self, mock_get_client, mock_jira_client):
        """Test handling of 403 forbidden."""
        from error_handler import PermissionError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.some_method.side_effect = PermissionError("Access denied")

        from module_name import function_name

        with pytest.raises(PermissionError):
            function_name(...)

    @patch('module_name.get_jira_client')
    def test_not_found_error(self, mock_get_client, mock_jira_client):
        """Test handling of 404 not found."""
        from error_handler import NotFoundError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.some_method.side_effect = NotFoundError("Resource not found")

        from module_name import function_name

        with pytest.raises(NotFoundError):
            function_name(...)

    @patch('module_name.get_jira_client')
    def test_rate_limit_error(self, mock_get_client, mock_jira_client):
        """Test handling of 429 rate limit."""
        from error_handler import JiraError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.some_method.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        from module_name import function_name

        with pytest.raises(JiraError) as exc_info:
            function_name(...)
        assert exc_info.value.status_code == 429

    @patch('module_name.get_jira_client')
    def test_server_error(self, mock_get_client, mock_jira_client):
        """Test handling of 500 server error."""
        from error_handler import JiraError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.some_method.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        from module_name import function_name

        with pytest.raises(JiraError) as exc_info:
            function_name(...)
        assert exc_info.value.status_code == 500
```

**Files needing error handling tests:**

| Test File | Priority Methods to Test |
|-----------|-------------------------|
| `test_transition_issue.py` | `transition_issue`, `find_transition_by_name` |
| `test_create_version.py` | `create_version` |
| `test_get_versions.py` | `get_versions`, `get_version_by_id` |
| `test_release_version.py` | `release_version`, `release_version_by_name` |
| `test_archive_version.py` | `archive_version`, `archive_version_by_name` |
| `test_move_issues_version.py` | `move_issues_to_version`, `move_specific_issues` |
| `test_create_component.py` | `create_component` |
| `test_get_components.py` | `get_components`, `get_component_by_id` |
| `test_update_component.py` | `update_component` |
| `test_delete_component.py` | `delete_component` |

---

### 2.2 Missing Edge Case Tests

**Impact:** Edge cases untested, potential runtime errors
**Priority order by impact:**

| Category | Test File | Missing Edge Case |
|----------|-----------|-------------------|
| Empty results | `test_get_versions.py` | Empty versions list |
| Empty results | `test_get_components.py` | Empty components list |
| Invalid input | `test_transition_issue.py` | Invalid issue key format |
| Boundary | `test_create_version.py` | Version name max length |
| Boundary | `test_create_component.py` | Component name max length |
| Duplicate | `test_create_version.py` | Duplicate version name |
| Duplicate | `test_create_component.py` | Duplicate component name |
| Already in state | `test_release_version.py` | Version already released |
| Already in state | `test_archive_version.py` | Version already archived |

**Remediation Template:**

```python
def test_empty_results(self, mock_jira_client):
    """Test handling empty results gracefully."""
    mock_jira_client.get_versions.return_value = []

    result = get_versions('PROJ', profile=None)

    assert result == []
    assert len(result) == 0

def test_duplicate_name_error(self, mock_jira_client):
    """Test error when name already exists."""
    from error_handler import ValidationError
    mock_jira_client.create_version.side_effect = JiraError(
        "Version with this name already exists", status_code=400
    )

    with pytest.raises(JiraError):
        create_version(project='PROJ', name='v1.0.0', profile=None)
```

---

## Phase 3: Medium Priority Issues

### 3.1 Fixture Mutation Risk

**Impact:** Potential test pollution between tests
**Files Affected:** All 10 test files that use fixtures

Current pattern does not use `copy.deepcopy()` when modifying fixture data.

**Files requiring deepcopy:**

| File | Lines | Fixture Used |
|------|-------|--------------|
| `test_create_version.py` | All tests | `sample_version` |
| `test_get_versions.py` | All tests | `sample_versions_list`, `sample_version` |
| `test_release_version.py` | All tests | `sample_version_released`, `sample_versions_list` |
| `test_archive_version.py` | All tests | `sample_version_archived`, `sample_versions_list` |
| `test_move_issues_version.py` | All tests | `sample_issue_list` |
| `test_create_component.py` | All tests | `sample_component` |
| `test_get_components.py` | All tests | `sample_components_list`, `sample_component` |
| `test_update_component.py` | All tests | N/A (creates local data) |
| `test_delete_component.py` | All tests | `sample_component` |
| `test_transition_issue.py` | All tests | `sample_transitions` |

**Remediation:**

```python
# Before (mutation risk):
def test_something(self, mock_jira_client, sample_version):
    mock_jira_client.create_version.return_value = sample_version

# After (safe):
def test_something(self, mock_jira_client, sample_version):
    import copy
    mock_jira_client.create_version.return_value = copy.deepcopy(sample_version)
```

**Alternative - Fix fixtures directly in conftest.py:**

```python
@pytest.fixture
def sample_version():
    """Sample version response - returns fresh copy each time."""
    import copy
    data = {
        'id': '10000',
        'name': 'v1.0.0',
        # ... rest of data
    }
    return copy.deepcopy(data)
```

---

### 3.2 Missing JSON Output Format Tests

**Impact:** JSON output untested, could break API consumers
**Files Affected:** Most test files

| File | Has JSON Test | Status |
|------|--------------|--------|
| `test_get_versions.py` | No | MISSING |
| `test_get_components.py` | Yes (line 88-103) | OK |
| `test_transition_issue.py` | No | MISSING |
| `test_create_version.py` | No | MISSING |
| `test_create_component.py` | No | MISSING |

**Remediation Template:**

```python
def test_json_output_format(self, mock_jira_client, sample_data):
    """Test JSON output is valid and contains expected fields."""
    import json
    mock_jira_client.get_xxx.return_value = sample_data

    from module_name import get_xxx
    result = get_xxx(...)

    # Verify JSON serialization works
    json_str = json.dumps(result, indent=2)
    parsed = json.loads(json_str)

    assert 'id' in parsed
    assert 'name' in parsed
```

---

### 3.3 Missing Input Validation Tests

**Impact:** Invalid inputs could reach API layer
**Files Affected:** All script test files

| Script | Validation Needed | Current Coverage |
|--------|-------------------|------------------|
| `transition_issue.py` | Issue key format | PARTIAL |
| `create_version.py` | Project key, name not empty | NONE |
| `get_versions.py` | Project key | NONE |
| `create_component.py` | Project key, name not empty | NONE |
| `assign_issue.py` | Issue key, account ID format | PARTIAL |

**Remediation Template:**

```python
class TestInputValidation:
    """Test input validation."""

    def test_invalid_issue_key(self):
        """Test error on invalid issue key."""
        from error_handler import ValidationError

        with pytest.raises(ValidationError):
            from script_name import function_name
            function_name(issue_key='invalid-key', ...)

    def test_empty_name(self):
        """Test error when name is empty."""
        from error_handler import ValidationError

        with pytest.raises(ValidationError):
            from script_name import function_name
            function_name(name='', ...)

    def test_invalid_project_key(self):
        """Test error on invalid project key."""
        from error_handler import ValidationError

        with pytest.raises(ValidationError):
            from script_name import function_name
            function_name(project='123invalid', ...)
```

---

## Phase 4: Low Priority Issues

### 4.1 Remove Unused Imports

**Impact:** Code hygiene
**Files Affected:** 10 files

All test files import `MagicMock` but only use `Mock` from conftest.py fixture:

```bash
# Files with unused MagicMock import:
tests/test_create_version.py:6 - from unittest.mock import MagicMock, patch
tests/test_get_versions.py:6 - from unittest.mock import MagicMock, patch
tests/test_release_version.py:6 - from unittest.mock import MagicMock, patch
tests/test_archive_version.py:6 - from unittest.mock import MagicMock, patch
tests/test_move_issues_version.py:6 - from unittest.mock import MagicMock, patch
tests/test_create_component.py:6 - from unittest.mock import MagicMock, patch
tests/test_get_components.py:6 - from unittest.mock import MagicMock, patch
tests/test_update_component.py:6 - from unittest.mock import MagicMock, patch
tests/test_delete_component.py:6 - from unittest.mock import MagicMock, patch
tests/test_transition_issue.py:9 - from unittest.mock import Mock, patch  # Mock also unused
```

**Remediation:**

```python
# Before:
from unittest.mock import MagicMock, patch

# After:
from unittest.mock import patch
```

---

### 4.2 Weak Assertions

**Impact:** Tests could pass when functionality broken
**Files Affected:** 2 files

| File | Line | Current Assertion | Fix |
|------|------|-------------------|-----|
| `test_get_versions.py` | 27 | `assert len(result) == 4` | Also verify structure |
| `test_get_components.py` | 27 | `assert len(result) == 4` | Also verify structure |

**Remediation:**

```python
# Before (weak):
assert len(result) == 4

# After (strong):
assert len(result) == 4
assert all('id' in item for item in result)
assert all('name' in item for item in result)
```

---

### 4.3 Inconsistent Path Setup

**Impact:** Maintenance burden
**Files Affected:** 10 test files

Current pattern in test files varies slightly. Standardize to match conftest.py:

```python
# Current (inconsistent between files):
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

# Standardized pattern (match conftest.py):
# Put all path setup in conftest.py and remove from individual files
```

---

### 4.4 Add Test Count Verification

**Impact:** Catch accidental test deletion
**Location:** Create as `tests/test_coverage_check.py`

```python
"""Verify test count doesn't regress."""

import pytest
from pathlib import Path


def test_minimum_test_count():
    """Ensure test count doesn't regress."""
    test_dir = Path(__file__).parent
    test_files = list(test_dir.glob('test_*.py'))

    # Count test functions (excluding this file)
    test_count = 0
    for f in test_files:
        if f.name == 'test_coverage_check.py':
            continue
        content = f.read_text()
        test_count += content.count('def test_')

    # Minimum expected tests (update as tests are added)
    # Current: ~70 tests, target after remediation: ~120
    MIN_TESTS = 70
    assert test_count >= MIN_TESTS, f"Expected {MIN_TESTS}+ tests, found {test_count}"
```

---

## Implementation Checklist

### Phase 1 Checklist (Critical)

- [ ] Create `tests/test_get_transitions.py` (4 tests)
- [ ] Create `tests/test_resolve_issue.py` (6 tests)
- [ ] Create `tests/test_reopen_issue.py` (5 tests)
- [ ] Create `tests/test_assign_issue.py` (7 tests)
- [ ] Add `pytest_configure` to conftest.py
- [ ] Add `@pytest.mark.lifecycle` and `@pytest.mark.unit` to all 11 test classes

### Phase 2 Checklist (High Priority)

- [ ] Add error handling tests to `test_transition_issue.py` (5 tests)
- [ ] Add error handling tests to `test_create_version.py` (5 tests)
- [ ] Add error handling tests to `test_get_versions.py` (5 tests)
- [ ] Add error handling tests to `test_release_version.py` (5 tests)
- [ ] Add error handling tests to `test_archive_version.py` (5 tests)
- [ ] Add error handling tests to `test_move_issues_version.py` (5 tests)
- [ ] Add error handling tests to `test_create_component.py` (5 tests)
- [ ] Add error handling tests to `test_get_components.py` (5 tests)
- [ ] Add error handling tests to `test_update_component.py` (5 tests)
- [ ] Add error handling tests to `test_delete_component.py` (5 tests)
- [ ] Add edge case tests (10+ tests across files)

### Phase 3 Checklist (Medium Priority)

- [ ] Add `copy.deepcopy()` to all fixture usages in tests
- [ ] Add JSON output tests to 4 missing files
- [ ] Add input validation tests to 5 script test files
- [ ] OR: Update fixtures in conftest.py to return deep copies

### Phase 4 Checklist (Low Priority)

- [ ] Remove unused `MagicMock` import from 9 files
- [ ] Remove unused `Mock` import from 1 file
- [ ] Strengthen weak assertions in 2 files
- [ ] Standardize path setup across files
- [ ] Add test count verification

---

## Verification Commands

```bash
# Run all lifecycle tests
pytest .claude/skills/jira-lifecycle/tests/ -v

# Run only unit tests
pytest .claude/skills/jira-lifecycle/tests/ -v -m unit

# Run only lifecycle-marked tests
pytest .claude/skills/jira-lifecycle/tests/ -v -m lifecycle

# Check for test count
pytest .claude/skills/jira-lifecycle/tests/ --collect-only | grep "test session starts" -A 5

# Verify no unused imports (requires pylint)
pylint .claude/skills/jira-lifecycle/tests/ --disable=all --enable=unused-import

# Check for weak assertions
grep -rn "assert len.*>= 0" .claude/skills/jira-lifecycle/tests/
grep -rn "or len.*== 0" .claude/skills/jira-lifecycle/tests/
```

---

## Success Criteria

1. **All tests pass:** `pytest` exits with code 0
2. **No missing script coverage:** All 14 scripts have corresponding tests
3. **Error handling tested:** Each script has 401, 403, 404, 429, 500 tests
4. **Consistent markers:** All test classes have `@pytest.mark.lifecycle` and `@pytest.mark.unit`
5. **No pytest warnings:** About unknown markers
6. **No unused imports:** pylint reports clean
7. **Test count:** Minimum 120 tests after remediation (currently ~70)

---

## Appendix: Script-to-Test Mapping

| Script | Test File | Status |
|--------|-----------|--------|
| `transition_issue.py` | `test_transition_issue.py` | EXISTS |
| `get_transitions.py` | `test_get_transitions.py` | MISSING |
| `resolve_issue.py` | `test_resolve_issue.py` | MISSING |
| `reopen_issue.py` | `test_reopen_issue.py` | MISSING |
| `assign_issue.py` | `test_assign_issue.py` | MISSING |
| `create_version.py` | `test_create_version.py` | EXISTS |
| `get_versions.py` | `test_get_versions.py` | EXISTS |
| `release_version.py` | `test_release_version.py` | EXISTS |
| `archive_version.py` | `test_archive_version.py` | EXISTS |
| `move_issues_version.py` | `test_move_issues_version.py` | EXISTS |
| `create_component.py` | `test_create_component.py` | EXISTS |
| `get_components.py` | `test_get_components.py` | EXISTS |
| `update_component.py` | `test_update_component.py` | EXISTS |
| `delete_component.py` | `test_delete_component.py` | EXISTS |

---

## Notes

- Prioritize Phase 1 before merging to main
- Phase 2 should be completed before next release
- Phases 3-4 can be addressed incrementally
- Consider adding pre-commit hooks to prevent regression
- Current test count: ~70 tests
- Target test count: ~120 tests after remediation
