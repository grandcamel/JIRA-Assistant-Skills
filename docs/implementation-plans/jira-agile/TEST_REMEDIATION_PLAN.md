# Test Remediation Plan: jira-agile Skill

**Created:** 2025-12-26
**Status:** Draft
**Test Files Reviewed:** 15
**Total Issues Identified:** ~85+

---

## Executive Summary

This plan addresses test quality issues discovered during a comprehensive review of the `jira-agile` skill test suite. Issues are organized by priority and grouped into actionable phases.

### Issue Summary by Category

| Category | Count | Priority |
|----------|-------|----------|
| Empty CLI Test Stubs | 22 stubs across 12 files | Critical |
| Missing pytest Marker Registration | 1 file | Critical |
| Unused Imports | 13 files | Low |
| Fixture Mutations | 2 occurrences | Medium |
| Missing API Error Tests | All files (401, 403, 429, 500) | High |
| Weak/Missing Assertions | 3 occurrences | Medium |
| Missing Dry-Run Tests | 2 scripts | High |

**Estimated Effort:**
- Phase 1 (Critical): 2-3 hours
- Phase 2 (High Priority): 4-5 hours
- Phase 3 (Medium Priority): 3-4 hours
- Phase 4 (Low Priority): 1-2 hours

---

## Phase 1: Critical Issues (Must Fix)

### 1.1 Empty CLI Test Stubs

**Impact:** False test coverage metrics, no actual CLI testing
**Files Affected:** 12 test files
**Total Empty Stubs:** 22
**Action:** Either implement actual CLI tests or remove stubs entirely

| File | Lines | Stub Count | Stub Functions |
|------|-------|------------|----------------|
| `tests/test_create_epic.py` | 187-195 | 2 stubs | `test_cli_minimal_args`, `test_cli_help_output` |
| `tests/test_add_to_epic.py` | 195-211 | 2 stubs | `test_cli_multiple_issues`, `test_cli_with_jql` |
| `tests/test_get_epic.py` | 196-210 | 2 stubs | `test_cli_basic`, `test_cli_with_children` |
| `tests/test_create_subtask.py` | 197-213 | 2 stubs | `test_cli_minimal_args`, `test_cli_help_output` |
| `tests/test_move_to_sprint.py` | 168-178 | 2 stubs | `test_cli_multiple_issues`, `test_cli_move_to_backlog` |
| `tests/test_get_sprint.py` | 167-177 | 2 stubs | `test_cli_basic`, `test_cli_active_sprint` |
| `tests/test_get_backlog.py` | 127-129 | 1 stub | `test_cli_basic` |
| `tests/test_estimate_issue.py` | 152-158 | 2 stubs | `test_cli_single_issue`, `test_cli_jql_query` |
| `tests/test_get_estimates.py` | 141-147 | 2 stubs | `test_cli_sprint`, `test_cli_epic` |
| `tests/test_create_sprint.py` | 172-183 | 2 stubs | `test_cli_minimal_args`, `test_cli_with_goal` |
| `tests/test_manage_sprint.py` | 175-184 | 2 stubs | `test_cli_start_sprint`, `test_cli_close_sprint` |
| `tests/test_rank_issue.py` | 148-157 | 2 stubs | `test_cli_before`, `test_cli_top` |

**Example - Current Empty Stub (test_create_epic.py:187-195):**

```python
@patch('sys.argv', ['create_epic.py', '--project', 'PROJ', '--summary', 'Test Epic'])
def test_cli_minimal_args(self, mock_jira_client, sample_epic_response):
    """Test CLI with minimal required arguments."""
    # This will fail initially - tests the CLI parsing
    mock_jira_client.create_issue.return_value = sample_epic_response

    # Import and run main
    # from create_epic import main
    # This is a placeholder - will implement when script exists
    pass
```

**Remediation - Option A (Implement CLI Tests):**

```python
@patch('sys.argv', ['create_epic.py', '--project', 'PROJ', '--summary', 'Test Epic'])
def test_cli_minimal_args(self, mock_jira_client, sample_epic_response, capsys):
    """Test CLI with minimal required arguments."""
    mock_jira_client.create_issue.return_value = sample_epic_response

    with patch('config_manager.get_jira_client', return_value=mock_jira_client):
        from create_epic import main
        try:
            main()
        except SystemExit as e:
            assert e.code == 0  # Successful exit

    captured = capsys.readouterr()
    assert 'PROJ-100' in captured.out  # Created issue key in output
```

**Remediation - Option B (Remove Stubs and Document):**

```python
# Remove empty test methods entirely and add class-level docstring:
@pytest.mark.agile
@pytest.mark.unit
class TestCreateEpicCLI:
    """
    Test command-line interface for create_epic.py.

    TODO: CLI tests pending implementation - see TEST_REMEDIATION_PLAN.md
    Currently tracking 2 missing tests:
    - test_cli_minimal_args
    - test_cli_help_output
    """
    pass  # No empty test methods
```

---

### 1.2 Missing pytest Marker Registration

**Impact:** pytest warnings, inconsistent test selection
**File:** `tests/conftest.py`

**Current State (conftest.py missing `pytest_configure`):**

The conftest.py file uses `@pytest.mark.agile`, `@pytest.mark.unit`, and `@pytest.mark.integration` markers but does not register them with pytest.

**Remediation - Add to `tests/conftest.py` (after line 22):**

```python
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "agile: mark test as agile skill test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
```

---

## Phase 2: High Priority Issues

### 2.1 Missing API Error Handling Tests

**Impact:** Error scenarios untested, poor user experience on failures
**Coverage Gap:** All test files missing tests for:
- `AuthenticationError` (401)
- `ForbiddenError` (403)
- Rate limiting (429)
- Server errors (500, 502, 503)
- Network timeout/connection errors

**Files to Update:** All 14 test files (excluding conftest.py and __init__.py)

**Remediation Template - Add to each test file:**

```python
@pytest.mark.agile
@pytest.mark.unit
class TestApiErrorHandling:
    """Test API error handling scenarios."""

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from error_handler import AuthenticationError
        from create_epic import create_epic  # Adjust import per file

        mock_jira_client.create_issue.side_effect = AuthenticationError(
            "Invalid API token"
        )

        with pytest.raises(AuthenticationError):
            create_epic(
                project="PROJ",
                summary="Test",
                client=mock_jira_client
            )

    def test_forbidden_error(self, mock_jira_client):
        """Test handling of 403 forbidden."""
        from error_handler import ForbiddenError
        from create_epic import create_epic

        mock_jira_client.create_issue.side_effect = ForbiddenError(
            "Insufficient permissions"
        )

        with pytest.raises(ForbiddenError):
            create_epic(
                project="PROJ",
                summary="Test",
                client=mock_jira_client
            )

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from error_handler import JiraError
        from create_epic import create_epic

        mock_jira_client.create_issue.side_effect = JiraError(
            "Rate limit exceeded",
            status_code=429
        )

        with pytest.raises(JiraError) as exc_info:
            create_epic(
                project="PROJ",
                summary="Test",
                client=mock_jira_client
            )
        assert exc_info.value.status_code == 429

    def test_server_error(self, mock_jira_client):
        """Test handling of 500 server error."""
        from error_handler import JiraError
        from create_epic import create_epic

        mock_jira_client.create_issue.side_effect = JiraError(
            "Internal server error",
            status_code=500
        )

        with pytest.raises(JiraError) as exc_info:
            create_epic(
                project="PROJ",
                summary="Test",
                client=mock_jira_client
            )
        assert exc_info.value.status_code == 500
```

---

### 2.2 Missing Dry-Run Tests

**Impact:** Dry-run feature incompletely tested
**Scripts with dry_run support but missing negative assertion:**

| Script | Test File | Issue |
|--------|-----------|-------|
| `estimate_issue.py` | `test_estimate_issue.py` | No dry_run test |
| `rank_issue.py` | `test_rank_issue.py` | No dry_run test |

**Note:** `add_to_epic.py` and `move_to_sprint.py` already have dry-run tests with proper assertions.

**Remediation for test_estimate_issue.py:**

```python
def test_estimate_dry_run(self, mock_jira_client):
    """Test dry-run mode shows preview without making changes."""
    from estimate_issue import estimate_issue

    result = estimate_issue(
        issue_keys=["PROJ-1", "PROJ-2"],
        points=5,
        dry_run=True,
        client=mock_jira_client
    )

    # Verify dry-run response
    assert result.get('dry_run') is True or result.get('would_update') == 2
    # Verify NO actual update was called
    mock_jira_client.update_issue.assert_not_called()
```

**Remediation for test_rank_issue.py:**

```python
def test_rank_dry_run(self, mock_jira_client):
    """Test dry-run mode for ranking."""
    from rank_issue import rank_issue

    result = rank_issue(
        issue_keys=["PROJ-1"],
        before_key="PROJ-2",
        dry_run=True,
        client=mock_jira_client
    )

    # Verify dry-run response
    assert result.get('dry_run') is True or result.get('would_rank') == 1
    # Verify NO actual ranking was called
    mock_jira_client.rank_issues.assert_not_called()
```

---

### 2.3 Missing Not Found (404) Error Tests

**Impact:** Error handling for non-existent resources untested for some scripts
**Files with 404 tests:** `test_create_epic.py`, `test_add_to_epic.py`, `test_get_epic.py`, `test_create_subtask.py`, `test_create_sprint.py`
**Files MISSING 404 tests:**

| File | Missing Test |
|------|--------------|
| `test_get_sprint.py` | `test_get_sprint_not_found` |
| `test_get_backlog.py` | `test_get_backlog_invalid_board` |
| `test_estimate_issue.py` | `test_estimate_issue_not_found` |
| `test_get_estimates.py` | `test_get_estimates_sprint_not_found` |
| `test_manage_sprint.py` | `test_start_sprint_not_found`, `test_close_sprint_not_found` |
| `test_rank_issue.py` | `test_rank_issue_not_found` |

**Remediation Template:**

```python
def test_get_sprint_not_found(self, mock_jira_client):
    """Test error when sprint doesn't exist."""
    from get_sprint import get_sprint
    from error_handler import JiraError

    mock_jira_client.get_sprint.side_effect = JiraError(
        "Sprint does not exist",
        status_code=404
    )

    with pytest.raises(JiraError) as exc_info:
        get_sprint(sprint_id=999, client=mock_jira_client)

    assert exc_info.value.status_code == 404
```

---

## Phase 3: Medium Priority Issues

### 3.1 Fixture Mutations

**Impact:** Potential test pollution between tests
**Files Affected:** 2

| File | Lines | Issue |
|------|-------|-------|
| `test_manage_sprint.py` | 36-37, 62-63, 109-110, 129-130 | Uses shallow `.copy()` on `sample_sprint_response` |
| `test_get_backlog.py` | 103-105 | Uses shallow `.copy()` on nested dict |

**Example - Current (test_manage_sprint.py:36-37):**

```python
def test_start_sprint(self, mock_jira_client, sample_sprint_response):
    """Test starting a sprint (moves from future to active)."""
    from manage_sprint import start_sprint

    # Sprint starts as 'future', becomes 'active'
    started_sprint = sample_sprint_response.copy()  # Shallow copy!
    started_sprint['state'] = 'active'
```

**Remediation:**

```python
def test_start_sprint(self, mock_jira_client, sample_sprint_response):
    """Test starting a sprint (moves from future to active)."""
    import copy
    from manage_sprint import start_sprint

    # Sprint starts as 'future', becomes 'active'
    started_sprint = copy.deepcopy(sample_sprint_response)  # Deep copy!
    started_sprint['state'] = 'active'
```

**Example - test_get_backlog.py:103-105 (nested dict issue):**

```python
def test_get_backlog_with_epics(self, mock_jira_client, sample_issue_response):
    """Test grouping backlog by epic."""
    from get_backlog import get_backlog

    issue_with_epic = sample_issue_response.copy()  # Shallow!
    issue_with_epic['fields'] = sample_issue_response['fields'].copy()  # Still references same nested dicts!
```

**Remediation:**

```python
def test_get_backlog_with_epics(self, mock_jira_client, sample_issue_response):
    """Test grouping backlog by epic."""
    import copy
    from get_backlog import get_backlog

    issue_with_epic = copy.deepcopy(sample_issue_response)  # Full deep copy
    issue_with_epic['fields']['customfield_10014'] = 'PROJ-100'
```

---

### 3.2 Weak Assertions

**Impact:** Tests may pass when functionality is broken
**Occurrences:** 3

| File | Line | Current Assertion | Issue |
|------|------|-------------------|-------|
| `test_get_backlog.py` | 59-60 | `assert 'jql' in str(call_args) or call_args[1].get('jql')` | String-based call_args check is fragile |
| `test_get_backlog.py` | 119 | `assert 'by_epic' in result or 'grouped' in result or len(result['issues']) > 0` | Too permissive, always passes |
| `test_rank_issue.py` | 74 | `assert call_args[1].get('after') == "PROJ-3" or 'after' in str(call_args)` | Fallback to string check defeats purpose |

**Remediation - test_get_backlog.py:59-60:**

```python
# Before (weak):
call_args = mock_jira_client.get_board_backlog.call_args
assert 'jql' in str(call_args) or call_args[1].get('jql')

# After (strong):
call_args = mock_jira_client.get_board_backlog.call_args
assert call_args[1].get('jql') == "priority=High"  # Exact value check
```

**Remediation - test_get_backlog.py:119:**

```python
# Before (weak - always passes):
assert 'by_epic' in result or 'grouped' in result or len(result['issues']) > 0

# After (strong):
assert 'by_epic' in result, "Expected epic grouping in result"
assert 'PROJ-100' in result['by_epic'], "Expected epic PROJ-100 in grouped results"
```

**Remediation - test_rank_issue.py:74:**

```python
# Before (weak):
assert call_args[1].get('after') == "PROJ-3" or 'after' in str(call_args)

# After (strong):
assert call_args[1].get('rank_after') == "PROJ-3" or call_args[1].get('after') == "PROJ-3"
```

---

### 3.3 Missing Edge Case Tests

**Priority order by impact:**

| Category | Test File | Missing Edge Case |
|----------|-----------|-------------------|
| Empty results | `test_get_backlog.py` | Empty backlog board |
| Empty results | `test_get_estimates.py` | Sprint with no issues |
| Empty results | `test_get_epic.py` | Epic with no children |
| Boundary values | `test_estimate_issue.py` | Negative story points |
| Boundary values | `test_estimate_issue.py` | Maximum story points (100+) |
| Duplicate handling | `test_add_to_epic.py` | Issue already in epic |
| Invalid input | `test_create_sprint.py` | Empty sprint name |
| Invalid input | `test_move_to_sprint.py` | Empty issue list |
| State validation | `test_manage_sprint.py` | Start already-active sprint |
| State validation | `test_manage_sprint.py` | Close already-closed sprint |

**Remediation Template - Empty Results:**

```python
def test_get_backlog_empty(self, mock_jira_client):
    """Test handling empty backlog."""
    from get_backlog import get_backlog

    mock_jira_client.get_board_backlog.return_value = {
        'issues': [],
        'total': 0
    }

    result = get_backlog(board_id=123, client=mock_jira_client)

    assert result is not None
    assert result['total'] == 0
    assert len(result['issues']) == 0
```

**Remediation Template - State Validation:**

```python
def test_start_already_active_sprint(self, mock_jira_client, sample_sprint_response):
    """Test error when starting already-active sprint."""
    import copy
    from manage_sprint import start_sprint
    from error_handler import ValidationError

    active_sprint = copy.deepcopy(sample_sprint_response)
    active_sprint['state'] = 'active'
    mock_jira_client.get_sprint.return_value = active_sprint

    with pytest.raises(ValidationError) as exc_info:
        start_sprint(sprint_id=456, client=mock_jira_client)

    assert "already active" in str(exc_info.value).lower()
```

---

## Phase 4: Low Priority Issues

### 4.1 Remove Unused Imports

**Impact:** Code hygiene
**Files Affected:** 13

```
# Files with unused MagicMock import (imported but Mock used instead):
tests/conftest.py:9             - from unittest.mock import Mock, MagicMock
tests/test_create_epic.py:24    - from unittest.mock import Mock, patch, MagicMock
tests/test_add_to_epic.py:22    - from unittest.mock import Mock, patch, MagicMock
tests/test_get_epic.py:22       - from unittest.mock import Mock, patch, MagicMock
tests/test_create_subtask.py:22 - from unittest.mock import Mock, patch, MagicMock
tests/test_move_to_sprint.py:22 - from unittest.mock import Mock, patch, MagicMock
tests/test_get_sprint.py:22     - from unittest.mock import Mock, patch, MagicMock
tests/test_create_sprint.py:22  - from unittest.mock import Mock, patch, MagicMock
tests/test_manage_sprint.py:22  - from unittest.mock import Mock, patch, MagicMock
tests/test_rank_issue.py:22     - from unittest.mock import Mock, patch, MagicMock
tests/test_integration.py:21    - from unittest.mock import Mock, patch, MagicMock

# Files with unused patch import:
tests/test_get_backlog.py:20    - from unittest.mock import Mock (patch not imported but also unused)
tests/test_estimate_issue.py:20 - from unittest.mock import Mock, patch (patch unused)
tests/test_get_estimates.py:20  - from unittest.mock import Mock, patch (patch unused)
```

**Remediation:**

```python
# Before:
from unittest.mock import Mock, patch, MagicMock

# After (keep only what's used):
from unittest.mock import Mock, patch
# Or for files that don't use patch:
from unittest.mock import Mock
```

---

### 4.2 Inconsistent Assertion Patterns

**Impact:** Code maintainability
**Pattern to standardize across all tests:**

```python
# Avoid: String representation checking
assert 'jql' in str(call_args)
assert call_args is not None

# Prefer: Direct parameter access
call_kwargs = mock_jira_client.method.call_args.kwargs
assert call_kwargs.get('jql') == "expected_value"

# Or use assert_called_with for exact matching:
mock_jira_client.create_sprint.assert_called_once_with(
    board_id=123,
    name="Sprint 42",
    goal="Launch MVP"
)
```

---

### 4.3 Add Test Count Verification

**Impact:** Catch accidental test deletion

**Add to CI/CD or as a dedicated test:**

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
    # Current count: ~75 tests (excluding empty stubs)
    MIN_TESTS = 70
    assert test_count >= MIN_TESTS, f"Expected {MIN_TESTS}+ tests, found {test_count}"
```

---

## Implementation Checklist

### Phase 1 Checklist (Critical)

- [ ] Decide: Implement or remove CLI test stubs (22 stubs across 12 files)
- [ ] Add `pytest_configure` to conftest.py for marker registration

### Phase 2 Checklist (High Priority)

- [ ] Add API error handling tests to all 14 test files (auth, forbidden, rate limit, server error)
- [ ] Add dry-run tests for `estimate_issue.py` and `rank_issue.py`
- [ ] Add 404 error tests to 6 files missing them

### Phase 3 Checklist (Medium Priority)

- [ ] Fix fixture mutation in `test_manage_sprint.py` (4 occurrences)
- [ ] Fix fixture mutation in `test_get_backlog.py` (1 occurrence)
- [ ] Fix 3 weak assertions
- [ ] Add 10+ edge case tests (empty results, boundary values, state validation)

### Phase 4 Checklist (Low Priority)

- [ ] Remove unused `MagicMock` import from 11 files
- [ ] Remove unused `patch` import from 3 files
- [ ] Standardize assertion patterns
- [ ] Add test count verification

---

## Verification Commands

```bash
# Run all agile tests
pytest .claude/skills/jira-agile/tests/ -v

# Run only unit tests
pytest .claude/skills/jira-agile/tests/ -v -m unit

# Run only integration tests
pytest .claude/skills/jira-agile/tests/ -v -m integration

# Check for test count
pytest .claude/skills/jira-agile/tests/ --collect-only | grep "test session starts" -A 5

# Verify no unused imports (requires pylint)
pylint .claude/skills/jira-agile/tests/ --disable=all --enable=unused-import

# Check for weak assertions
grep -rn "assert.*>= 0" .claude/skills/jira-agile/tests/
grep -rn "or len.*>= 0" .claude/skills/jira-agile/tests/
grep -rn "in str(call_args)" .claude/skills/jira-agile/tests/

# Find empty test stubs
grep -rn "def test_" .claude/skills/jira-agile/tests/ | xargs -I {} sh -c 'grep -A 5 "{}" | grep -q "pass$" && echo "{}"'
```

---

## Success Criteria

1. **All tests pass:** `pytest` exits with code 0
2. **No empty stubs:** All test methods have actual assertions
3. **No pytest warnings:** About unknown markers
4. **Consistent markers:** All test classes have `@pytest.mark.agile` and appropriate `@pytest.mark.unit` or `@pytest.mark.integration`
5. **Error handling covered:** Each script has tests for 401, 403, 404, 429, 500 errors
6. **No unused imports:** pylint reports clean
7. **Coverage maintained:** Test count >= 70 (after removing empty stubs)

---

## Notes

- Prioritize Phase 1 before merging to main
- Phase 2 should be completed before next release
- Phases 3-4 can be addressed incrementally
- Consider adding pre-commit hooks to prevent regression
- The test files follow TDD pattern - many were written before implementation, which explains the empty CLI stubs marked "will fail initially"

---

## File Reference Summary

| File | Line Count | Test Count | Empty Stubs | Issues |
|------|------------|------------|-------------|--------|
| `conftest.py` | 201 | 0 (fixtures) | 0 | Missing pytest_configure |
| `test_create_epic.py` | 196 | 9 | 2 | Unused MagicMock |
| `test_add_to_epic.py` | 212 | 9 | 2 | Unused MagicMock |
| `test_get_epic.py` | 211 | 10 | 2 | Unused MagicMock |
| `test_create_subtask.py` | 214 | 9 | 2 | Unused MagicMock |
| `test_move_to_sprint.py` | 179 | 8 | 2 | Unused MagicMock |
| `test_get_sprint.py` | 178 | 8 | 2 | Unused MagicMock, missing 404 test |
| `test_get_backlog.py` | 130 | 6 | 1 | Fixture mutation, weak assertions |
| `test_estimate_issue.py` | 159 | 8 | 2 | Missing dry-run test, missing 404 test |
| `test_get_estimates.py` | 148 | 6 | 2 | Missing 404 test |
| `test_create_sprint.py` | 184 | 8 | 2 | Unused MagicMock |
| `test_manage_sprint.py` | 185 | 8 | 2 | Fixture mutations (4x) |
| `test_rank_issue.py` | 158 | 8 | 2 | Weak assertion, missing dry-run |
| `test_integration.py` | 361 | 4 | 0 | Unused MagicMock |
| `__init__.py` | 2 | 0 | 0 | None |

**Total Tests:** ~91 (including 22 empty stubs)
**Actual Tests with Assertions:** ~69
