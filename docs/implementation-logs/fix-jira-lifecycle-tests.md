# Fix jira-lifecycle Unit Test

**Date:** 2025-12-26
**File Modified:** `.claude/skills/jira-lifecycle/tests/test_move_issues_version.py`

## Problem

The `test_permission_error` test in `TestMoveIssuesVersionErrorHandling` was failing because it expected `PermissionError` to be raised, but the `move_issues_to_version()` function implements a resilient bulk operation pattern that catches exceptions per-issue and continues processing.

## Root Cause

The test expectation was incorrect. Bulk operations in this codebase are designed to:
1. Catch ALL exceptions during individual issue updates
2. Log errors as warnings and store them in an `errors` dictionary
3. Continue processing remaining issues
4. Return a summary dict with `moved`, `failed`, and `errors` counts

This is consistent with other bulk operations in the codebase (e.g., `bulk_transition.py`, `bulk_assign.py`).

## Fix Applied

Changed the test from expecting an exception to verifying the error is captured in the result:

**Before:**
```python
with pytest.raises(PermissionError):
    move_issues_to_version(jql='project = PROJ', target_version='v2.0.0', profile=None)
```

**After:**
```python
result = move_issues_to_version(
    jql='project = PROJ',
    target_version='v2.0.0',
    profile=None,
    show_progress=False
)

assert result['moved'] == 0
assert result['failed'] == 2
assert 'PROJ-123' in result['errors']
assert 'PROJ-124' in result['errors']
assert 'Cannot update issue' in result['errors']['PROJ-123']
```

## Test Results

```
============================= 165 passed in 0.70s ==============================
```

All 165 unit tests in jira-lifecycle now pass.
