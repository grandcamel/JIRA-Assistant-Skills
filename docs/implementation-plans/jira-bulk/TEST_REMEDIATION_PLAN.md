# Test Remediation Plan: jira-bulk Skill

**Created:** 2025-12-26
**Status:** Draft
**Test Files Reviewed:** 6 (4 unit + 2 live integration)
**Total Issues Identified:** ~45

---

## Executive Summary

This plan addresses test quality issues discovered during a comprehensive review of the `jira-bulk` skill test suite. Issues are organized by priority and grouped into actionable phases.

**Issue Breakdown:**
- Critical (Phase 1): 8 issues
- High Priority (Phase 2): 12 issues
- Medium Priority (Phase 3): 15 issues
- Low Priority (Phase 4): 10 issues

**Estimated Effort:**
- Phase 1 (Critical): 1-2 hours
- Phase 2 (High Priority): 2-3 hours
- Phase 3 (Medium Priority): 2-3 hours
- Phase 4 (Low Priority): 1-2 hours

---

## Phase 1: Critical Issues (Must Fix)

### 1.1 Missing pytest Marker Registration

**Impact:** pytest warnings, inconsistent test selection
**File:** `tests/conftest.py`

The `conftest.py` file lacks `pytest_configure` to register custom markers.

**Add at top of conftest.py (after imports):**

```python
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "bulk: mark test as bulk operations skill test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
```

---

### 1.2 Missing pytest Markers on All Test Classes

**Impact:** Inconsistent test categorization, cannot filter tests by type
**Files Affected:** 4 unit test files, 1 live integration file
**Classes Affected:** 42 test classes total

| File | Line | Classes Missing Markers |
|------|------|------------------------|
| `test_bulk_assign.py` | 15, 39, 63, 88, 115, 140, 166, 189, 218 | 9 classes |
| `test_bulk_set_priority.py` | 15, 39, 66, 84, 110, 139, 162, 196 | 8 classes |
| `test_bulk_clone.py` | 15, 45, 73, 97, 122, 147, 174, 198, 230, 259 | 10 classes |
| `test_bulk_transition.py` | 15, 41, 70, 97, 121, 149, 180, 212, 238, 275, 302 | 11 classes |
| `live_integration/test_bulk_operations.py` | 22, 128, 210, 285, 378 | 5 classes |

**Remediation:**

```python
# Add to each unit test class:
@pytest.mark.bulk
@pytest.mark.unit
class TestBulkAssignToUser:
    """Test assigning multiple issues to specific user."""

# Add to each live integration test class:
@pytest.mark.bulk
@pytest.mark.integration
class TestBulkTransition:
    """Tests for bulk transition operations."""
```

---

### 1.3 Weak Assertions That Always Pass

**Impact:** Tests pass even when functionality is broken
**Files Affected:** 2 files

| File | Line | Current Assertion | Fix |
|------|------|-------------------|-----|
| `test_bulk_assign.py` | 186 | `assert result['failed'] >= 0` | `assert result['failed'] > 0` or check specific error message |
| `test_bulk_transition.py` | 177 | `assert elapsed >= 0.05` | This is reasonable but could be flaky; consider mocking time |

**Remediation for test_bulk_assign.py:186:**

```python
# Before (weak):
assert result['failed'] >= 0  # Either fails or handles gracefully

# After (strong):
# The invalid user should cause failure OR return error status
assert result['failed'] >= 1 or result.get('error') is not None or result['success'] == 0
```

**Remediation for test_bulk_transition.py:177:**

```python
# Before (potentially flaky):
assert elapsed >= 0.05  # At least some delay

# After (more robust):
# Verify delay_between_ops was applied (9 delays for 10 issues)
expected_min_delay = 9 * 0.01  # 0.09 seconds minimum
assert elapsed >= expected_min_delay * 0.5, f"Expected at least {expected_min_delay * 0.5}s, got {elapsed}s"
```

---

### 1.4 Response Key Mismatch: `success` vs `successful`

**Impact:** Unit tests and live integration tests use different response keys
**Severity:** Tests will fail when implementation changes or vice versa

**Unit tests use:** `result['success']`
**Live integration tests use:** `result['successful']`

| File | Lines | Key Used |
|------|-------|----------|
| `test_bulk_assign.py` | 34, 59, 82, 111, 137, 214 | `success` |
| `test_bulk_set_priority.py` | 34, 62, 135, 159, 218 | `success` |
| `test_bulk_clone.py` | 40, 69, 94, 226, 255 | `success` |
| `test_bulk_transition.py` | 35, 65, 91, 118, 144, 176, 207, 233, 297, 328 | `success` |
| `live_integration/test_bulk_operations.py` | 34, 54, 73, 112, 142, 170, 188, 224, 241, 258, 296, 321, 341, 390, 402, 416 | `successful` |

**Remediation:**

Either standardize all tests to use the same key, or verify what the actual implementation returns and align all tests accordingly. If the implementation returns `successful`:

```python
# Before:
assert result['success'] == 3

# After:
assert result['successful'] == 3
```

---

## Phase 2: High Priority Issues

### 2.1 Missing API Error Handling Tests

**Impact:** Error scenarios untested, poor user experience on failures
**Coverage Gap:** All 4 unit test files missing tests for:
- `AuthenticationError` (401)
- `PermissionError` (403)
- `NotFoundError` (404)
- Rate limiting (429)
- Server errors (500, 502, 503, 504)

**Files to Update:**
- `test_bulk_assign.py`
- `test_bulk_set_priority.py`
- `test_bulk_clone.py`
- `test_bulk_transition.py`

**Remediation Template (add to each test file):**

```python
class TestBulkAssignApiErrors:
    """Test API error handling scenarios."""

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from bulk_assign import bulk_assign
        from error_handler import AuthenticationError

        mock_jira_client.assign_issue.side_effect = AuthenticationError("Invalid token")

        with pytest.raises(AuthenticationError):
            bulk_assign(
                client=mock_jira_client,
                issue_keys=['PROJ-1'],
                assignee='user-123',
                dry_run=False
            )

    def test_permission_denied_error(self, mock_jira_client):
        """Test handling of 403 forbidden."""
        from bulk_assign import bulk_assign
        from error_handler import JiraError

        mock_jira_client.assign_issue.side_effect = JiraError(
            "You do not have permission", status_code=403
        )

        result = bulk_assign(
            client=mock_jira_client,
            issue_keys=['PROJ-1'],
            assignee='user-123',
            dry_run=False
        )

        assert result['failed'] == 1
        assert 'PROJ-1' in result.get('errors', {})

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from bulk_assign import bulk_assign
        from error_handler import JiraError

        mock_jira_client.assign_issue.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        result = bulk_assign(
            client=mock_jira_client,
            issue_keys=['PROJ-1'],
            assignee='user-123',
            dry_run=False
        )

        assert result['failed'] == 1

    def test_not_found_error(self, mock_jira_client):
        """Test handling of 404 not found."""
        from bulk_assign import bulk_assign
        from error_handler import JiraError

        mock_jira_client.assign_issue.side_effect = JiraError(
            "Issue not found", status_code=404
        )

        result = bulk_assign(
            client=mock_jira_client,
            issue_keys=['PROJ-999'],
            assignee='user-123',
            dry_run=False
        )

        assert result['failed'] == 1

    def test_server_error(self, mock_jira_client):
        """Test handling of 500 server error."""
        from bulk_assign import bulk_assign
        from error_handler import JiraError

        mock_jira_client.assign_issue.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        result = bulk_assign(
            client=mock_jira_client,
            issue_keys=['PROJ-1'],
            assignee='user-123',
            dry_run=False
        )

        assert result['failed'] == 1
```

---

### 2.2 Missing Dry-Run Result Verification Tests

**Impact:** Dry-run tests verify no changes but don't fully validate return structure
**Files Affected:** All 4 unit test files

Current dry-run tests verify `assert_not_called()` but don't always verify all result fields.

**Remediation Template:**

```python
def test_bulk_assign_dry_run_result_structure(self, mock_jira_client, sample_issues):
    """Test dry-run returns complete preview information."""
    from bulk_assign import bulk_assign

    mock_jira_client.search_issues.return_value = {
        'issues': sample_issues,
        'total': 3
    }

    result = bulk_assign(
        client=mock_jira_client,
        jql="project=PROJ",
        assignee='user-123',
        dry_run=True
    )

    # Verify result structure
    assert result.get('dry_run') is True
    assert result.get('would_process') == 3
    assert 'preview' in result or 'issues' in result  # Preview info
    mock_jira_client.assign_issue.assert_not_called()
```

---

### 2.3 Missing Input Validation Tests

**Impact:** Invalid inputs not tested
**Files Affected:** All 4 unit test files

Missing tests for:
- Empty issue keys list with no JQL
- Both issue_keys and JQL provided (conflict)
- Invalid JQL syntax
- Invalid issue key format

**Remediation Template:**

```python
class TestBulkAssignInputValidation:
    """Test input validation scenarios."""

    def test_no_issues_and_no_jql(self, mock_jira_client):
        """Test error when neither issue_keys nor JQL provided."""
        from bulk_assign import bulk_assign
        from error_handler import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            bulk_assign(
                client=mock_jira_client,
                assignee='user-123',
                dry_run=False
            )

        assert 'issue_keys' in str(exc_info.value).lower() or 'jql' in str(exc_info.value).lower()

    def test_invalid_issue_key_format(self, mock_jira_client):
        """Test error for invalid issue key format."""
        from bulk_assign import bulk_assign
        from error_handler import ValidationError

        with pytest.raises(ValidationError):
            bulk_assign(
                client=mock_jira_client,
                issue_keys=['invalid-key-format'],
                assignee='user-123',
                dry_run=False
            )
```

---

## Phase 3: Medium Priority Issues

### 3.1 Fixture Mutation Issue

**Impact:** Potential test pollution between tests
**File:** `test_bulk_clone.py`
**Line:** 155

```python
# Current (mutation risk):
issue = sample_issues[1].copy()  # Shallow copy - nested dicts still shared!
```

**Remediation:**

```python
# After (safe):
import copy
issue = copy.deepcopy(sample_issues[1])
```

---

### 3.2 Missing Edge Case Tests

**Priority order by impact:**

| Category | Test File | Missing Edge Case |
|----------|-----------|-------------------|
| Boundary | `test_bulk_transition.py` | Large batch (1000+ issues) |
| Boundary | `test_bulk_clone.py` | Clone with very long summary |
| Error | `test_bulk_assign.py` | Assign to deactivated user |
| Error | `test_bulk_set_priority.py` | Priority not found in project |
| Duplicate | `test_bulk_clone.py` | Cloning same issue twice |
| Concurrent | `test_bulk_transition.py` | Issue already transitioned by another user |

**Remediation Template:**

```python
def test_large_batch_handling(self, mock_jira_client, sample_transitions):
    """Test handling of large batch operations."""
    from bulk_transition import bulk_transition

    # Generate 1000 issue keys
    issue_keys = [f'PROJ-{i}' for i in range(1, 1001)]

    mock_jira_client.get_transitions.return_value = sample_transitions
    mock_jira_client.transition_issue.return_value = None

    result = bulk_transition(
        client=mock_jira_client,
        issue_keys=issue_keys,
        target_status='Done',
        dry_run=False
    )

    assert result['success'] == 1000
    assert mock_jira_client.transition_issue.call_count == 1000
```

---

### 3.3 Missing JSON Output Format Tests

**Impact:** JSON output untested, could break API consumers
**Files Affected:** All 4 unit test files

**Remediation Template:**

```python
class TestBulkAssignOutputFormat:
    """Test output formatting."""

    def test_json_output_format(self, mock_jira_client, sample_issues):
        """Test JSON output is valid and contains expected fields."""
        import json
        from bulk_assign import bulk_assign, format_json_output

        mock_jira_client.assign_issue.return_value = None

        result = bulk_assign(
            client=mock_jira_client,
            issue_keys=['PROJ-1', 'PROJ-2'],
            assignee='user-123',
            dry_run=False
        )

        # Verify result is JSON-serializable
        json_output = json.dumps(result)
        parsed = json.loads(json_output)

        assert 'success' in parsed or 'successful' in parsed
        assert 'failed' in parsed
        assert 'total' in parsed
```

---

### 3.4 Missing Rollback/Recovery Tests

**Impact:** No verification of behavior when partial operations fail mid-batch
**Files Affected:** All 4 unit test files

**Remediation Template:**

```python
def test_partial_failure_state_consistency(self, mock_jira_client, sample_transitions):
    """Test state consistency after partial failure."""
    from bulk_transition import bulk_transition
    from error_handler import JiraError

    # Fail on 3rd issue of 5
    call_count = [0]

    def transition_side_effect(issue_key, transition_id, fields=None):
        call_count[0] += 1
        if call_count[0] == 3:
            raise JiraError("Network error")
        return None

    mock_jira_client.get_transitions.return_value = sample_transitions
    mock_jira_client.transition_issue.side_effect = transition_side_effect

    result = bulk_transition(
        client=mock_jira_client,
        issue_keys=['PROJ-1', 'PROJ-2', 'PROJ-3', 'PROJ-4', 'PROJ-5'],
        target_status='Done',
        dry_run=False
    )

    # Verify:
    # 1. Operation continues after failure
    # 2. Result accurately tracks successes and failures
    assert result['success'] == 4
    assert result['failed'] == 1
    assert mock_jira_client.transition_issue.call_count == 5
```

---

### 3.5 Live Integration Test Isolation

**Impact:** Tests may interfere with each other
**File:** `live_integration/test_bulk_operations.py`

Some tests modify issues that other tests depend on. Consider using unique fixtures per test.

**Current:** `bulk_issues` fixture is function-scoped but cleanup might not fully reset state.

**Remediation:**

```python
# Add explicit state reset after tests that modify issue status
def test_bulk_transition_multiple_issues(self, jira_client, test_project, bulk_issues):
    """Test transitioning multiple issues."""
    issue_keys = [i['key'] for i in bulk_issues]

    result = bulk_transition(...)

    # Verify all issues are in Done status
    for key in issue_keys:
        issue = jira_client.get_issue(key)
        assert issue['fields']['status']['name'] == 'Done'

    # CLEANUP: Reset issues to original state for other tests
    for key in issue_keys:
        try:
            # Get transitions and transition back to To Do if possible
            transitions = jira_client.get_transitions(key)
            to_do_transition = next((t for t in transitions if t['name'] == 'To Do'), None)
            if to_do_transition:
                jira_client.transition_issue(key, to_do_transition['id'])
        except Exception:
            pass  # Best effort cleanup
```

---

## Phase 4: Low Priority Issues

### 4.1 Remove Unused Imports

**Impact:** Code hygiene
**Files Affected:** 5 files

| File | Line | Unused Import |
|------|------|---------------|
| `conftest.py` | 7 | `MagicMock` (client is created fresh) |
| `test_bulk_assign.py` | 7 | `MagicMock` (not used directly), `patch` (not used) |
| `test_bulk_set_priority.py` | 7 | `MagicMock`, `patch` (not used) |
| `test_bulk_clone.py` | 7 | `MagicMock`, `patch` (not used) |
| `test_bulk_transition.py` | 7 | `MagicMock`, `call` (not used) |

**Remediation:**

```python
# Before:
from unittest.mock import MagicMock, patch, call

# After (only import what's used):
from unittest.mock import patch  # or remove entirely if not used
```

---

### 4.2 Inconsistent Test Docstrings

**Impact:** Documentation quality
**Pattern to standardize:**

Some docstrings repeat the class docstring. Each test method should have a unique, specific description.

```python
# Before:
class TestBulkTransitionByKeys:
    """Test transitioning multiple issues by key list."""

    def test_bulk_transition_by_keys_success(self, mock_jira_client, sample_issues, sample_transitions):
        """Test transitioning multiple issues by key list."""  # Duplicate!

# After:
class TestBulkTransitionByKeys:
    """Test transitioning multiple issues by key list."""

    def test_bulk_transition_by_keys_success(self, mock_jira_client, sample_issues, sample_transitions):
        """Test successful transition of 3 issues to Done status."""
```

---

### 4.3 Add Test Count Verification

**Impact:** Catch accidental test deletion
**File:** Create new `tests/test_coverage_check.py`

```python
# tests/test_coverage_check.py
import pytest
from pathlib import Path


def test_minimum_test_count():
    """Ensure test count doesn't regress."""
    test_dir = Path(__file__).parent
    test_files = list(test_dir.glob('test_*.py'))

    # Count test functions
    test_count = 0
    for f in test_files:
        content = f.read_text()
        test_count += content.count('def test_')

    # Minimum expected tests (update as tests are added)
    MIN_TESTS = 40  # Current: ~42 unit tests
    assert test_count >= MIN_TESTS, f"Expected {MIN_TESTS}+ tests, found {test_count}"
```

---

### 4.4 Standardize Assertion Patterns

**Impact:** Code maintainability

```python
# Avoid: Multiple assertions without context
assert result['success'] == 3
assert result['failed'] == 0

# Prefer: Grouped with message for failures
assert result['success'] == 3, f"Expected 3 successes, got {result['success']}"
assert result['failed'] == 0, f"Expected 0 failures, got {result['failed']}"

# Or use pytest's detailed diff:
assert result == {'success': 3, 'failed': 0, 'total': 3}
```

---

## Implementation Checklist

### Phase 1 Checklist (Critical)

- [ ] Add `pytest_configure` to `tests/conftest.py`
- [ ] Add `@pytest.mark.bulk` and `@pytest.mark.unit` to 38 unit test classes
- [ ] Add `@pytest.mark.bulk` and `@pytest.mark.integration` to 5 integration test classes
- [ ] Fix weak assertion at `test_bulk_assign.py:186`
- [ ] Stabilize timing assertion at `test_bulk_transition.py:177`
- [ ] Resolve `success` vs `successful` key mismatch across all files

### Phase 2 Checklist (High Priority)

- [ ] Add API error handling tests to `test_bulk_assign.py` (5 tests)
- [ ] Add API error handling tests to `test_bulk_set_priority.py` (5 tests)
- [ ] Add API error handling tests to `test_bulk_clone.py` (5 tests)
- [ ] Add API error handling tests to `test_bulk_transition.py` (5 tests)
- [ ] Add dry-run result structure tests (4 tests)
- [ ] Add input validation tests (4+ tests)

### Phase 3 Checklist (Medium Priority)

- [ ] Fix fixture mutation in `test_bulk_clone.py:155` (use deepcopy)
- [ ] Add edge case tests: large batch handling
- [ ] Add edge case tests: boundary conditions
- [ ] Add JSON output format tests (4 tests)
- [ ] Add partial failure state consistency tests (4 tests)
- [ ] Add test isolation improvements to live integration tests

### Phase 4 Checklist (Low Priority)

- [ ] Remove unused imports from 5 files
- [ ] Standardize test docstrings
- [ ] Add test count verification
- [ ] Standardize assertion patterns

---

## Verification Commands

```bash
# Run all bulk tests
pytest .claude/skills/jira-bulk/tests/ -v

# Run only unit tests
pytest .claude/skills/jira-bulk/tests/ -v -m unit --ignore=.claude/skills/jira-bulk/tests/live_integration

# Run only integration tests
pytest .claude/skills/jira-bulk/tests/live_integration/ -v --profile development

# Check for test count
pytest .claude/skills/jira-bulk/tests/ --collect-only | grep "test session starts" -A 5

# Verify no unused imports (requires pylint)
pylint .claude/skills/jira-bulk/tests/ --disable=all --enable=unused-import

# Check assertion quality (manual review)
grep -rn ">= 0" .claude/skills/jira-bulk/tests/
grep -rn "is not None or.*is None" .claude/skills/jira-bulk/tests/

# Check for success vs successful key usage
grep -rn "result\['success'\]" .claude/skills/jira-bulk/tests/
grep -rn "result\['successful'\]" .claude/skills/jira-bulk/tests/
```

---

## Success Criteria

1. **All tests pass:** `pytest` exits with code 0
2. **No weak assertions:** grep commands return no results for weak patterns
3. **Consistent markers:** All test classes have `@pytest.mark.bulk` and either `@pytest.mark.unit` or `@pytest.mark.integration`
4. **No pytest warnings:** About unknown markers
5. **Consistent response keys:** Either all tests use `success` or all use `successful`
6. **Coverage maintained:** Test count >= 42 (current count)
7. **No unused imports:** pylint reports clean

---

## Notes

- Prioritize Phase 1 before merging to main
- Phase 2 should be completed before next release
- Phases 3-4 can be addressed incrementally
- Consider adding pre-commit hooks to prevent regression
- The `success` vs `successful` key mismatch is the highest priority fix as it will cause test failures when tests are run against the actual implementation
