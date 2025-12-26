# Test Remediation Plan: jira-jsm Skill

**Created:** 2025-12-26
**Status:** Draft
**Test Files Reviewed:** 39 (35 unit test files + 4 live integration test files)
**Total Issues Identified:** ~150+

---

## Executive Summary

This plan addresses test quality issues discovered during a comprehensive review of the `jira-jsm` skill test suite. Issues are organized by priority and grouped into actionable phases.

**Issue Summary by Category:**
| Category | Count | Severity |
|----------|-------|----------|
| Missing pytest markers | 38+ classes | Critical |
| Generic Exception catches | 12 instances | High |
| Missing error handling tests (401, 403, 404, 429, 500) | 35 files | High |
| Weak assertions | 8 instances | High |
| Fixture mutations | 5 instances | Medium |
| Hardcoded sleeps | 1 instance | Medium |
| Unused imports | 20+ instances | Low |

**Estimated Effort:**
- Phase 1 (Critical): 3-4 hours
- Phase 2 (High Priority): 5-7 hours
- Phase 3 (Medium Priority): 4-6 hours
- Phase 4 (Low Priority): 2-3 hours

---

## Phase 1: Critical Issues (Must Fix)

### 1.1 Missing pytest Marker Registration

**Impact:** pytest warnings, inconsistent test selection
**File:** `tests/conftest.py`

**Current State (line 1-61):** No `pytest_configure` function exists in the unit test conftest.py file.

**Remediation - Add at top of `tests/conftest.py`:**

```python
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "jsm: mark test as JSM skill test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "jsm_requests: mark test as request management")
    config.addinivalue_line("markers", "jsm_customers: mark test as customer/org management")
    config.addinivalue_line("markers", "jsm_approvals: mark test as approval workflow")
    config.addinivalue_line("markers", "jsm_sla: mark test as SLA management")
    config.addinivalue_line("markers", "jsm_queues: mark test as queue management")
    config.addinivalue_line("markers", "jsm_kb: mark test as knowledge base")
```

---

### 1.2 Missing pytest Markers on Test Classes

**Impact:** Tests cannot be filtered by category, inconsistent test organization
**Files Affected:** 18 files with class-based tests

| File | Lines | Classes Missing `@pytest.mark.unit` |
|------|-------|-------------------------------------|
| `test_get_request.py` | 20 | `TestGetRequest` |
| `test_get_request_status.py` | 19 | `TestGetRequestStatus` |
| `test_list_requests.py` | 19 | `TestListRequests` |
| `test_transition_request.py` | 19 | `TestTransitionRequest` |
| `test_search_kb.py` | 19 | `TestSearchKB` |
| `test_suggest_kb.py` | 19 | `TestSuggestKB` |
| `test_link_asset.py` | 19 | `TestLinkAsset` |
| `test_list_assets.py` | 20 | `TestListAssets` |
| `test_update_asset.py` | 19 | `TestUpdateAsset` |
| `test_phase4_sla_queue.py` | N/A | Multiple implicit classes (functions only) |

**Remediation:**

```python
# Before:
class TestGetRequest:
    """Test request retrieval functionality."""

# After:
@pytest.mark.jsm
@pytest.mark.unit
class TestGetRequest:
    """Test request retrieval functionality."""
```

---

### 1.3 Weak Assertions That Always Pass

**Impact:** Tests pass even when functionality is broken
**Files Affected:** 6 files

| File | Line | Current Assertion | Fix |
|------|------|-------------------|-----|
| `test_get_request_comments.py` | 90 | `assert mock_jira_client.get_request_comments.call_count >= 1` | `assert mock_jira_client.get_request_comments.call_count == 2` |
| `test_get_request_comments.py` | 109, 135, 151 | Weak `or` assertions | Use specific assertions |
| `test_list_pending_approvals.py` | 127 | `assert 'No pending approvals' in captured.out or '0 pending' in captured.out` | Test both paths explicitly |
| `test_approve_request.py` | 105 | `assert 'DRY RUN' in captured.out or 'would approve' in captured.out.lower()` | Use specific assertion |
| `test_decline_request.py` | 83 | `assert 'DRY RUN' in captured.out or 'would decline' in captured.out.lower()` | Use specific assertion |
| `test_decline_request.py` | 109 | `assert 'DECLINED' in captured.out or 'decline' in captured.out.lower()` | Use specific assertion |

**Remediation Template:**

```python
# Before (weak):
assert 'No pending approvals' in captured.out or '0 pending' in captured.out

# After (strong):
assert 'No pending approvals' in captured.out  # Single expected output
# OR split into two tests:
def test_empty_message_format_a(...):
    # Test one output format
def test_empty_message_format_b(...):
    # Test alternative output format
```

---

### 1.4 Generic Exception Catches (Should Use Specific Exceptions)

**Impact:** Tests pass even when wrong exception type is raised, hiding bugs
**Files Affected:** 6 files

| File | Lines | Current Pattern | Fix |
|------|-------|-----------------|-----|
| `test_link_asset.py` | 55, 58 | `mock_jira_client.link_asset_to_request.side_effect = Exception("Request not found")` | Use `NotFoundError` |
| `test_link_asset.py` | 62, 64 | `mock_jira_client.link_asset_to_request.side_effect = Exception("Asset not found")` | Use `NotFoundError` |
| `test_link_asset.py` | 71, 75 | `side_effect = Exception("Link failed")` | Use `JiraError` |
| `test_update_asset.py` | 80, 83 | `side_effect = Exception("Update failed")` | Use `JiraError` |
| `test_phase4_sla_queue.py` | 287-289 (multiple) | `breached_sla2 = mock_breached_sla.copy()` | Use `copy.deepcopy()` |

**Remediation:**

```python
# Before (generic):
mock_jira_client.link_asset_to_request.side_effect = Exception("Request not found")

with patch('link_asset.get_jira_client', return_value=mock_jira_client):
    with pytest.raises(Exception, match="Request not found"):
        link_asset.link_asset(10001, "REQ-999")

# After (specific):
from error_handler import NotFoundError

mock_jira_client.link_asset_to_request.side_effect = NotFoundError("Request not found")

with patch('link_asset.get_jira_client', return_value=mock_jira_client):
    with pytest.raises(NotFoundError, match="Request not found"):
        link_asset.link_asset(10001, "REQ-999")
```

---

## Phase 2: High Priority Issues

### 2.1 Missing API Error Handling Tests

**Impact:** Error scenarios untested, poor user experience on failures
**Coverage Gap:** All 35 unit test files are missing tests for:
- `AuthenticationError` (401)
- `PermissionError` (403)
- Rate limiting (429)
- Server errors (500, 502, 503)
- Network timeout/connection errors

**Files Needing Error Tests:**

| File | Missing Error Tests |
|------|---------------------|
| `test_add_customer.py` | 401, 403, 429, 500 |
| `test_add_participant.py` | 401, 403, 429, 500 |
| `test_add_request_comment.py` | 429, 500 (has 401, 404) |
| `test_add_to_organization.py` | 401, 403, 429, 500 |
| `test_approve_request.py` | 429, 500 (has 403, 404) |
| `test_create_asset.py` | 401, 403, 429, 500 |
| `test_create_customer.py` | 401, 403, 429, 500 |
| `test_create_organization.py` | 401, 403, 429, 500 |
| `test_create_request.py` | 401, 403, 429, 500 |
| `test_create_service_desk.py` | 401, 403, 429, 500 |
| `test_decline_request.py` | 429, 500 (has 403) |
| `test_delete_organization.py` | 401, 403, 429, 500 |
| `test_find_affected_assets.py` | 401, 403, 429, 500 |
| `test_get_approvals.py` | 401, 403, 429, 500 |
| `test_get_asset.py` | 401, 403, 429, 500 |
| `test_get_kb_article.py` | 401, 403, 429, 500 |
| `test_get_organization.py` | 429, 500 (has 404) |
| `test_get_participants.py` | 401, 403, 429, 500 (has 404) |
| `test_get_request.py` | 401, 403, 429, 500 (has 404) |
| `test_get_request_comments.py` | 401, 403, 429, 500 |
| `test_get_request_status.py` | 401, 403, 429, 500 (has 404) |
| `test_get_request_type.py` | 401, 403, 429, 500 |
| `test_get_request_type_fields.py` | 401, 403, 429, 500 |
| `test_get_service_desk.py` | 401, 403, 429, 500 |
| `test_link_asset.py` | 401, 403, 429, 500 |
| `test_list_assets.py` | 401, 403, 429, 500 |
| `test_list_customers.py` | 401, 403, 429, 500 |
| `test_list_organizations.py` | 401, 403, 429 (has 500) |
| `test_list_pending_approvals.py` | 401, 403, 429, 500 |
| `test_list_request_types.py` | 401, 403, 429, 500 |
| `test_list_requests.py` | 401, 403, 429, 500 |
| `test_list_service_desks.py` | 401, 403, 429, 500 |
| `test_phase4_sla_queue.py` | 401, 403, 429, 500 (has partial) |
| `test_remove_customer.py` | 401, 403, 429, 500 |
| `test_remove_from_organization.py` | 429, 500 (has 403) |
| `test_remove_participant.py` | 429, 500 (has 403 implicit) |
| `test_search_kb.py` | 401, 403, 429, 500 |
| `test_suggest_kb.py` | 401, 403, 429, 500 |
| `test_transition_request.py` | 401, 403, 429, 500 (has 404) |
| `test_update_asset.py` | 401, 403, 429, 500 |

**Remediation Template:**

```python
class TestApiErrorHandling:
    """Test API error handling scenarios."""

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from error_handler import AuthenticationError
        mock_jira_client.get_request.side_effect = AuthenticationError("Invalid token")

        from get_request import get_service_request
        with pytest.raises(AuthenticationError):
            get_service_request('SD-101')

    def test_permission_error(self, mock_jira_client):
        """Test handling of 403 forbidden."""
        from error_handler import PermissionError
        mock_jira_client.get_request.side_effect = PermissionError("Access denied")

        from get_request import get_service_request
        with pytest.raises(PermissionError):
            get_service_request('SD-101')

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from error_handler import JiraError
        mock_jira_client.get_request.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        from get_request import get_service_request
        with pytest.raises(JiraError) as exc_info:
            get_service_request('SD-101')
        assert exc_info.value.status_code == 429

    def test_server_error(self, mock_jira_client):
        """Test handling of 500 server error."""
        from error_handler import JiraError
        mock_jira_client.get_request.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        from get_request import get_service_request
        with pytest.raises(JiraError) as exc_info:
            get_service_request('SD-101')
        assert exc_info.value.status_code == 500
```

---

### 2.2 Missing Dry-Run Tests

**Impact:** Dry-run feature untested, could modify data unexpectedly
**Scripts Affected:** 4

| Script | Test File | Missing Test |
|--------|-----------|--------------|
| `add_customer.py` | `test_add_customer.py` | `test_add_customer_dry_run` |
| `add_participant.py` | `test_add_participant.py` | `test_add_participant_dry_run` |
| `add_to_organization.py` | `test_add_to_organization.py` | `test_add_to_organization_dry_run` |
| `create_request.py` | `test_create_request.py` | `test_create_request_dry_run` |

Note: Some scripts do have dry-run tests (e.g., `approve_request.py`, `decline_request.py`, `remove_from_organization.py`, `remove_participant.py`, `update_asset.py`).

**Remediation Template:**

```python
def test_add_customer_dry_run(self, mock_jira_client, capsys):
    """Test dry-run mode shows preview without changes."""
    from add_customer import main

    with patch('add_customer.get_jira_client', return_value=mock_jira_client):
        result = main(['1', '--email', 'test@example.com', '--dry-run'])

    assert result == 0
    captured = capsys.readouterr()
    assert 'DRY RUN' in captured.out
    # Verify no actual API call was made
    mock_jira_client.add_customer_to_service_desk.assert_not_called()
```

---

### 2.3 Tests With Imports Inside Test Functions

**Impact:** Import errors not caught at collection time, harder to debug
**Files Affected:** 20+ files

| File | Lines | Pattern |
|------|-------|---------|
| `test_get_request_comments.py` | 11-12, 37-38, 56-57, 84-85, 103-104, 116-117, 128-129, 143-144 | `from get_request_comments import main` inside test |
| `test_list_pending_approvals.py` | 51-52, 81-82, 110-111, 121-122, 152-153, 185-186, 221-222 | Same pattern |
| `test_add_request_comment.py` | 13-14, 26-27, 45-46, 56-57, 68-79, 93-94, 109-110, 121-122, 138-139 | Same pattern |
| `test_approve_request.py` | 12-13, 26-27, 40-41, 56-57, 71-72, 86-87, 99-100 | Same pattern |
| `test_decline_request.py` | 18-19, 34-35, 48-49, 64-65, 77-78, 101-102 | Same pattern |

**Remediation:**

```python
# Before (imports inside test):
def test_get_all_comments(mock_jira_client, sample_comments_response):
    mock_jira_client.get_request_comments.return_value = sample_comments_response

    from get_request_comments import main  # Import inside test
    with patch('get_request_comments.get_jira_client', return_value=mock_jira_client):
        result = main(['REQ-123'])

# After (imports at top of file):
import sys
from pathlib import Path

scripts_path = str(Path(__file__).parent.parent / 'scripts')
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

from get_request_comments import main  # Import at top

def test_get_all_comments(mock_jira_client, sample_comments_response):
    mock_jira_client.get_request_comments.return_value = sample_comments_response

    with patch('get_request_comments.get_jira_client', return_value=mock_jira_client):
        result = main(['REQ-123'])
```

---

## Phase 3: Medium Priority Issues

### 3.1 Fixture Mutation Issues

**Impact:** Potential test pollution between tests
**Files Affected:** 4

| File | Lines | Issue |
|------|-------|-------|
| `test_phase4_sla_queue.py` | 287-289 | `breached_sla2 = mock_breached_sla.copy()` - uses shallow copy |
| `test_add_request_comment.py` | 75 | `sample_comment_public['body'] = multiline_body` - mutates fixture |
| `test_decline_request.py` | 62 | `declined_approval = {**sample_approval_pending, "finalDecision": "decline"}` - OK but inconsistent |

**Remediation:**

```python
# Before (mutation risk with shallow copy):
def test_check_multiple_breaches(mock_breached_sla):
    breached_sla2 = mock_breached_sla.copy()  # Shallow copy - nested dicts shared!
    breached_sla2['id'] = "3"

# After (safe with deepcopy):
import copy

def test_check_multiple_breaches(mock_breached_sla):
    breached_sla2 = copy.deepcopy(mock_breached_sla)  # Deep copy - fully independent
    breached_sla2['id'] = "3"
    breached_sla2['name'] = "Another Breached SLA"
```

---

### 3.2 Hardcoded Sleep in Live Integration Tests

**Impact:** Slows down tests, brittle timing assumptions
**File:** `tests/live_integration/conftest.py`

| File | Line | Pattern |
|------|------|---------|
| `live_integration/conftest.py` | 177 | `time.sleep(3)` after creating service desk |

**Remediation:**

```python
# Before (hardcoded sleep):
project = jira_client.create_project(...)
time.sleep(3)  # Wait for service desk to be created
service_desks = jira_client.get_service_desks()

# After (polling with timeout):
import time

def wait_for_service_desk(client, project_key, timeout=30, poll_interval=2):
    """Poll until service desk is available."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        service_desks = client.get_service_desks()
        service_desk = next(
            (sd for sd in service_desks.get('values', [])
             if sd.get('projectKey') == project_key),
            None
        )
        if service_desk:
            return service_desk
        time.sleep(poll_interval)
    raise TimeoutError(f"Service desk for {project_key} not available after {timeout}s")

# Usage:
project = jira_client.create_project(...)
service_desk = wait_for_service_desk(jira_client, project_key)
```

---

### 3.3 Missing Edge Case Tests

**Priority order by impact:**

| Category | Test File | Missing Edge Case |
|----------|-----------|-------------------|
| Empty results | `test_get_approvals.py` | No approvals exist |
| Empty results | `test_list_assets.py` | No assets found with IQL |
| Empty results | `test_search_kb.py` | No articles match query |
| Boundary values | `test_create_request.py` | Max summary length |
| Boundary values | `test_create_organization.py` | Max name length |
| Pagination | `test_list_customers.py` | Multi-page results |
| Pagination | `test_list_requests.py` | Start beyond total |
| Invalid input | `test_create_request.py` | Invalid request type ID |
| Invalid input | `test_get_service_desk.py` | Non-numeric service desk ID |
| Invalid input | `test_transition_request.py` | Invalid transition ID format |

**Remediation Template:**

```python
def test_empty_approvals_list(self, mock_jira_client):
    """Test handling when no approvals exist."""
    mock_jira_client.get_request_approvals.return_value = {
        'values': [],
        'size': 0,
        'start': 0,
        'limit': 50,
        'isLastPage': True
    }

    from get_approvals import get_approvals_func
    result = get_approvals_func('REQ-123')

    assert len(result['values']) == 0
    assert result['size'] == 0

def test_pagination_beyond_total(self, mock_jira_client):
    """Test pagination when start exceeds total results."""
    mock_jira_client.search_issues.return_value = {
        'issues': [],
        'total': 10,
        'startAt': 100,  # Beyond total
        'maxResults': 50
    }

    result = list_requests.list_service_requests(
        service_desk_id='1',
        start_at=100
    )

    assert len(result['issues']) == 0
```

---

### 3.4 Inconsistent Mock Client Setup

**Impact:** Tests may not accurately simulate real behavior
**Files Affected:** Multiple files use different mocking patterns

| Pattern | Files Using | Recommendation |
|---------|-------------|----------------|
| `mock_jira_client` fixture | Most files | Keep - consistent |
| `MagicMock()` inline | `test_get_participants.py:46` | Replace with fixture |
| `MagicMock()` inline | `test_list_organizations.py:58-60` | Replace with fixture |

**Remediation:**

```python
# Before (inline MagicMock):
def test_get_participants_empty():
    from unittest.mock import MagicMock
    mock_client = MagicMock()
    mock_client.get_request_participants.return_value = {'values': [], 'size': 0}

    with patch('get_participants.get_jira_client', return_value=mock_client):
        ...

# After (use fixture consistently):
def test_get_participants_empty(mock_jira_client):
    mock_jira_client.get_request_participants.return_value = {'values': [], 'size': 0}

    with patch('get_participants.get_jira_client', return_value=mock_jira_client):
        ...
```

---

## Phase 4: Low Priority Issues

### 4.1 Remove Unused Imports

**Impact:** Code hygiene
**Files Affected:** 20+

```bash
# Files with unused imports:
tests/test_add_customer.py:7           # unused: json
tests/test_add_participant.py:7        # unused: json
tests/test_add_to_organization.py:7    # unused: json
tests/test_create_customer.py:6        # unused: json
tests/test_create_organization.py:6    # unused: json
tests/test_delete_organization.py:6    # unused: json
tests/test_find_affected_assets.py:6   # unused: json
tests/test_get_approvals.py:6          # unused: json
tests/test_get_asset.py:6              # unused: json
tests/test_get_kb_article.py:6         # unused: json
tests/test_get_organization.py:8       # potentially unused
tests/test_get_participants.py:8       # potentially unused
tests/test_get_request_comments.py:149 # json imported inside function
tests/test_list_pending_approvals.py:192 # json imported inside function
tests/test_remove_customer.py:7        # unused: json
tests/test_remove_from_organization.py:7 # unused: json
tests/test_remove_participant.py:7     # unused: json
tests/test_phase4_sla_queue.py:16      # unused: MagicMock
```

**Remediation:**

```python
# Before:
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import json  # Unused
from pathlib import Path

# After:
import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path
```

---

### 4.2 Inconsistent File Header Docstrings

**Impact:** Documentation quality
**Files with minimal/missing docstrings:**

| File | Current State | Recommendation |
|------|---------------|----------------|
| `test_get_request_comments.py` | One-line docstring | Add full module docstring |
| `test_list_pending_approvals.py` | One-line docstring | Add full module docstring |
| `test_add_request_comment.py` | One-line docstring | Add full module docstring |
| `test_approve_request.py` | One-line docstring | Add full module docstring |
| `test_decline_request.py` | One-line docstring | Add full module docstring |

**Remediation Template:**

```python
"""
Tests for get_request_comments.py script.

Tests comment retrieval functionality including:
- Public and internal comment filtering
- Pagination handling
- Output format (text, JSON)
- Error handling (404, 403)
"""
```

---

### 4.3 Missing Test Count in Phase4 SLA Test File

**Impact:** Documentation consistency
**File:** `test_phase4_sla_queue.py`

The docstring claims "Total: 40 tests" but actual count should be verified.

**Remediation:**

```bash
# Verify test count
grep -c "def test_" .claude/skills/jira-jsm/tests/test_phase4_sla_queue.py
```

Update docstring to match actual count.

---

## Implementation Checklist

### Phase 1 Checklist (Critical)

- [ ] Add `pytest_configure` to `tests/conftest.py` with marker registration
- [ ] Add `@pytest.mark.jsm` and `@pytest.mark.unit` to all 18 test classes
- [ ] Fix 8 weak assertions in 6 files
- [ ] Replace 12 generic `Exception` catches with specific exception types

### Phase 2 Checklist (High Priority)

- [ ] Add error handling tests (401, 403, 429, 500) to all 35 unit test files
- [ ] Add 4 dry-run tests for scripts missing them
- [ ] Move imports from inside test functions to module level (20+ files)

### Phase 3 Checklist (Medium Priority)

- [ ] Fix fixture mutation in 3 files (use `copy.deepcopy`)
- [ ] Replace hardcoded `time.sleep(3)` with polling in live integration conftest
- [ ] Add 10+ edge case tests (empty results, pagination, invalid input)
- [ ] Standardize mock client setup (replace inline `MagicMock`)

### Phase 4 Checklist (Low Priority)

- [ ] Remove unused imports from 20+ files
- [ ] Add full module docstrings to 5 files
- [ ] Verify and update test count in `test_phase4_sla_queue.py` docstring

---

## Verification Commands

```bash
# Run all JSM tests
pytest .claude/skills/jira-jsm/tests/ -v

# Run only unit tests (after adding markers)
pytest .claude/skills/jira-jsm/tests/ -v -m unit

# Check for test count
pytest .claude/skills/jira-jsm/tests/ --collect-only | grep "test session starts" -A 5

# Check for generic Exception catches
grep -rn "Exception\(" .claude/skills/jira-jsm/tests/ | grep -v "pytest.raises"

# Check for weak assertions
grep -rn "assert.*>= 0" .claude/skills/jira-jsm/tests/
grep -rn "or len.*>= 0" .claude/skills/jira-jsm/tests/
grep -rn " or '.*' in " .claude/skills/jira-jsm/tests/

# Check for hardcoded sleeps
grep -rn "time.sleep" .claude/skills/jira-jsm/tests/

# Check for unused imports (requires pylint)
pylint .claude/skills/jira-jsm/tests/ --disable=all --enable=unused-import

# Check for shallow copies of fixtures
grep -rn "\.copy()" .claude/skills/jira-jsm/tests/
```

---

## Success Criteria

1. **All tests pass:** `pytest` exits with code 0
2. **No weak assertions:** grep commands return no results
3. **Consistent markers:** All test classes have `@pytest.mark.jsm` and `@pytest.mark.unit`
4. **No pytest warnings:** About unknown markers
5. **Coverage maintained:** Test count >= current count (~200+ tests)
6. **No unused imports:** pylint reports clean
7. **Specific exceptions:** No generic `Exception` catches in test assertions

---

## Notes

- Prioritize Phase 1 before merging to main
- Phase 2 should be completed before next release
- Phases 3-4 can be addressed incrementally
- Live integration tests (`tests/live_integration/`) already have proper markers registered in their own conftest
- Consider adding pre-commit hooks to prevent regression
- The `test_phase4_sla_queue.py` file is well-structured and can serve as a template for consolidating other tests
