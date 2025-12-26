# Unit Test Investigation: jira-collaborate Skill

**Date:** 2025-12-26
**Failures:** 3
**Test File:** `.claude/skills/jira-collaborate/tests/test_manage_watchers.py`

## Summary

All 3 test failures stem from a **mismatch between test expectations and actual implementation**. The tests expect email-based user lookups to call `client.get()`, but the implementation uses `client.search_users()` via the `resolve_user_to_account_id()` helper function.

---

## Failure 1: `test_add_watcher_by_email`

### Test Expectation (lines 89-101)
```python
@patch('manage_watchers.get_jira_client')
def test_add_watcher_by_email(self, mock_get_client, mock_jira_client):
    """Test adding watcher by email (lookup required)."""
    mock_get_client.return_value = mock_jira_client
    mock_jira_client.get.return_value = [{'accountId': '5b10a2844c20165700ede21g'}]
    mock_jira_client.post.return_value = None

    from manage_watchers import add_watcher

    add_watcher('PROJ-123', 'alice@company.com', profile=None)

    mock_jira_client.get.assert_called_once()  # <-- FAILS
    mock_jira_client.post.assert_called_once()
```

### Actual Implementation (`manage_watchers.py` lines 34-48)
```python
def add_watcher(issue_key: str, user: str, profile: str = None) -> None:
    """Add a watcher to an issue."""
    issue_key = validate_issue_key(issue_key)
    client = get_jira_client(profile)

    try:
        account_id = resolve_user_to_account_id(client, user)  # <-- Uses search_users()
    except UserNotFoundError as e:
        client.close()
        raise ValidationError(str(e))
    ...
```

### Root Cause
- The test expects `client.get()` to be called for email lookup
- The implementation uses `resolve_user_to_account_id()` from `user_helpers.py`
- That helper calls `client.search_users()` (not `client.get()`) when an email is detected

### Resolution
**Test needs updating.** The test should mock `client.search_users()` instead of `client.get()`:
```python
mock_jira_client.search_users.return_value = [{'accountId': '5b10a2844c20165700ede21g'}]
# ...
mock_jira_client.search_users.assert_called_once()
```

---

## Failure 2: `test_add_watcher_user_not_found`

### Test Expectation (lines 103-114)
```python
@patch('manage_watchers.get_jira_client')
def test_add_watcher_user_not_found(self, mock_get_client, mock_jira_client):
    """Test error when user not found."""
    from error_handler import ValidationError

    mock_get_client.return_value = mock_jira_client
    mock_jira_client.get.return_value = []  # <-- Mocks wrong method

    from manage_watchers import add_watcher

    with pytest.raises(ValidationError):  # <-- FAILS, no exception raised
        add_watcher('PROJ-123', 'nonexistent@company.com', profile=None)
```

### Root Cause
- The test mocks `client.get()` to return an empty list
- The implementation calls `client.search_users()`, not `client.get()`
- Since `search_users` is NOT mocked, MagicMock returns a truthy object (not empty list)
- `resolve_user_to_account_id()` sees results, does not raise `UserNotFoundError`
- Therefore, no `ValidationError` is raised

### Resolution
**Test needs updating.** Mock `search_users` to return an empty list:
```python
mock_jira_client.search_users.return_value = []
```

---

## Failure 3: `test_remove_watcher_by_email`

### Test Expectation (lines 134-146)
```python
@patch('manage_watchers.get_jira_client')
def test_remove_watcher_by_email(self, mock_get_client, mock_jira_client):
    """Test removing watcher by email (lookup required)."""
    mock_get_client.return_value = mock_jira_client
    mock_jira_client.get.return_value = [{'accountId': '5b10a2844c20165700ede21g'}]
    mock_jira_client.delete.return_value = None

    from manage_watchers import remove_watcher

    remove_watcher('PROJ-123', 'alice@company.com', profile=None)

    mock_jira_client.get.assert_called_once()  # <-- FAILS
    mock_jira_client.delete.assert_called_once()
```

### Actual Implementation (`manage_watchers.py` lines 51-64)
```python
def remove_watcher(issue_key: str, user: str, profile: str = None) -> None:
    """Remove a watcher from an issue."""
    issue_key = validate_issue_key(issue_key)
    client = get_jira_client(profile)

    try:
        account_id = resolve_user_to_account_id(client, user)  # <-- Uses search_users()
    except UserNotFoundError as e:
        client.close()
        raise ValidationError(str(e))
    ...
```

### Root Cause
Same as Failure 1 - test mocks `client.get()` but implementation uses `client.search_users()`.

### Resolution
**Test needs updating.** Mock `search_users` instead of `get`:
```python
mock_jira_client.search_users.return_value = [{'accountId': '5b10a2844c20165700ede21g'}]
# ...
mock_jira_client.search_users.assert_called_once()
```

---

## Conclusion

| Finding | Details |
|---------|---------|
| **Root Cause** | Tests were written before `user_helpers.py` refactoring introduced `resolve_user_to_account_id()` |
| **Fix Required** | Update 3 tests to mock `search_users()` instead of `get()` |
| **Implementation Correct?** | Yes - implementation correctly uses shared helper |
| **Tests Correct?** | No - tests need to align with current implementation |

### Recommended Fix

```python
# For test_add_watcher_by_email and test_remove_watcher_by_email:
mock_jira_client.search_users.return_value = [{'accountId': '5b10a2844c20165700ede21g'}]
# Assert on search_users instead of get
mock_jira_client.search_users.assert_called_once()

# For test_add_watcher_user_not_found:
mock_jira_client.search_users.return_value = []
```
