# Unit Test Investigation: jira-lifecycle

**Date:** 2025-12-26
**Investigator:** Claude
**Test File:** `.claude/skills/jira-lifecycle/tests/test_move_issues_version.py`
**Failure:** `TestMoveIssuesVersionErrorHandling::test_permission_error`

## Summary

The test expects `PermissionError` to be raised, but the implementation catches all exceptions during bulk issue updates and continues processing, logging warnings instead of propagating the error.

## Failure Analysis

### Test Code (lines 154-165)

```python
@patch('move_issues_version.get_jira_client')
def test_permission_error(self, mock_get_client, mock_jira_client, sample_issue_list):
    """Test handling of 403 forbidden."""
    from error_handler import PermissionError
    mock_get_client.return_value = mock_jira_client
    mock_jira_client.search_issues.return_value = copy.deepcopy(sample_issue_list)
    mock_jira_client.update_issue.side_effect = PermissionError("Cannot update issue")

    from move_issues_version import move_issues_to_version

    with pytest.raises(PermissionError):
        move_issues_to_version(jql='project = PROJ', target_version='v2.0.0', profile=None)
```

### Implementation Behavior (lines 72-98)

```python
for i, issue in issue_iterator:
    issue_key = issue['key']
    try:
        client.update_issue(
            issue_key,
            fields={field: [{'name': target_version}]}
        )
        moved += 1
        # ... success logging ...
    except Exception as e:
        failed += 1
        errors[issue_key] = str(e)
        # ... warning logging ...
```

### Root Cause

The `move_issues_to_version()` function is designed for **bulk operations** and uses a **resilient pattern**:
1. It catches ALL exceptions during individual issue updates (`except Exception`)
2. Errors are logged as warnings and stored in the `errors` dictionary
3. Processing continues with remaining issues
4. Returns a summary dict with `moved`, `failed`, and `errors` counts

This design is intentional - for bulk operations, failing one issue should not prevent processing of remaining issues. The test, however, expects the function to raise `PermissionError` on the first failure.

### Observed Output

The test output shows the expected behavior of the implementation:
```
Warning: [1/2] Failed PROJ-123: Cannot update issue
Warning: [2/2] Failed PROJ-124: Cannot update issue
```

Both issues were processed (failing gracefully), and no exception was raised.

## Verdict: Test Expectation Needs Fixing

The **test expectation is incorrect**, not the implementation.

### Rationale

1. **Bulk operation design pattern**: The implementation correctly follows a resilient bulk operation pattern where individual failures do not abort the entire batch.

2. **Consistency with other bulk operations**: Comparing with similar scripts in jira-bulk skill (e.g., `bulk_transition.py`, `bulk_assign.py`), they all use this same pattern of catching exceptions per-item and continuing.

3. **Return value contains error info**: The function returns error details that callers can inspect:
   ```python
   return {'moved': moved, 'failed': failed, 'total': total, 'errors': errors}
   ```

4. **Contrast with authentication error test**: The `test_authentication_error` test correctly expects an error to be raised because it mocks `search_issues` to fail - this happens BEFORE the bulk loop begins, so it propagates correctly. Permission errors during individual updates should NOT propagate.

## Recommended Fix

Update the test to verify that errors are captured and returned correctly, rather than expecting an exception:

```python
@patch('move_issues_version.get_jira_client')
def test_permission_error(self, mock_get_client, mock_jira_client, sample_issue_list):
    """Test handling of 403 forbidden during bulk update."""
    from error_handler import PermissionError
    mock_get_client.return_value = mock_jira_client
    mock_jira_client.search_issues.return_value = copy.deepcopy(sample_issue_list)
    mock_jira_client.update_issue.side_effect = PermissionError("Cannot update issue")

    from move_issues_version import move_issues_to_version

    result = move_issues_to_version(
        jql='project = PROJ',
        target_version='v2.0.0',
        profile=None,
        show_progress=False
    )

    # Bulk operations capture errors per-issue rather than raising
    assert result['moved'] == 0
    assert result['failed'] == 2
    assert 'PROJ-123' in result['errors']
    assert 'PROJ-124' in result['errors']
    assert 'Cannot update issue' in result['errors']['PROJ-123']
```

## Impact Assessment

- **Severity**: Low - one failing unit test
- **Type**: Test expectation mismatch, not production bug
- **Fix effort**: Minimal - update test assertion logic
