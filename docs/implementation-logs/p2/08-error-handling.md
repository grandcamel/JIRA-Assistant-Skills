# Error Handling Consistency Improvements

## Overview

This document describes improvements made to error handling consistency across multiple skills in the Jira-Assistant-Skills project.

## Changes Made

### 1. jira-jsm: approve_request.py

**File:** `.claude/skills/jira-jsm/scripts/approve_request.py`

**Issue:** Using `print()` for error output instead of the standardized `print_error()` function from the shared error_handler module.

**Before:**
```python
from error_handler import handle_errors, JiraError, NotFoundError, PermissionError

# ... later in the code ...

        except (JiraError, NotFoundError, PermissionError) as e:
            print(f"\nError: Could not get approval {approval_id}: {e}")
            continue
```

**After:**
```python
from error_handler import handle_errors, print_error, JiraError, NotFoundError, PermissionError

# ... later in the code ...

        except (JiraError, NotFoundError, PermissionError) as e:
            print_error(f"Could not get approval {approval_id}: {e}")
            continue
```

**Benefits:**
- Consistent error output format across all scripts
- Errors are properly directed to stderr
- Can include debug information when needed
- Follows project error handling conventions

---

### 2. jira-bulk: bulk_clone.py

**File:** `.claude/skills/jira-bulk/scripts/bulk_clone.py`

**Issue:** Issue retrieval in the bulk operation loop did not have try/except handling, causing the entire operation to fail if any single issue could not be retrieved.

**Before:**
```python
        # Get issues to process
        if issue_keys:
            issue_keys = [validate_issue_key(k) for k in issue_keys[:max_issues]]
            issues = []
            for key in issue_keys:
                issue = client.get_issue(key)
                issues.append(issue)
        elif jql:
```

**After:**
```python
        # Get issues to process
        retrieval_errors = {}
        if issue_keys:
            issue_keys = [validate_issue_key(k) for k in issue_keys[:max_issues]]
            issues = []
            for key in issue_keys:
                try:
                    issue = client.get_issue(key)
                    issues.append(issue)
                except JiraError as e:
                    retrieval_errors[key] = str(e)
                    print_warning(f"Could not retrieve {key}: {e}")
        elif jql:
            jql = validate_jql(jql)
            result = client.search_issues(jql, fields=['*all'], max_results=max_issues)
            issues = result.get('issues', [])
            retrieval_errors = {}  # JQL search handles its own errors
```

**Additional changes to return values:**
```python
        # Merge retrieval errors with cloning errors
        all_errors = {**retrieval_errors, **errors}
        return {
            'success': success,
            'failed': failed,
            'total': total,
            'errors': all_errors,
            'created_issues': created_issues,
            'retrieval_failed': len(retrieval_errors)
        }
```

**Summary output update:**
```python
        retrieval_failed = result.get('retrieval_failed', 0)
        if retrieval_failed > 0:
            print(f"\nSummary: {result['success']} cloned, {result['failed']} failed, {retrieval_failed} could not be retrieved")
        else:
            print(f"\nSummary: {result['success']} cloned, {result['failed']} failed")

        if result['failed'] > 0 or retrieval_failed > 0:
            sys.exit(1)
```

**Benefits:**
- Graceful handling of individual issue retrieval failures
- Bulk operations continue with remaining issues instead of failing entirely
- Clear reporting of retrieval failures separate from cloning failures
- Exit code properly reflects any failures

---

### 3. jira-collaborate: Shared User Lookup Helper

**New File:** `.claude/skills/shared/scripts/lib/user_helpers.py`

Created a new shared helper module to centralize user lookup functionality that was duplicated across scripts.

**New Helper Functions:**

```python
#!/usr/bin/env python3
"""
User lookup helper functions for JIRA API operations.

Provides reusable utilities for resolving user identifiers
(email addresses, usernames) to JIRA account IDs.
"""

from typing import Optional, Dict, Any


class UserNotFoundError(Exception):
    """Raised when a user cannot be found in JIRA."""

    def __init__(self, identifier: str, message: Optional[str] = None):
        self.identifier = identifier
        if message:
            super().__init__(message)
        else:
            super().__init__(f"User not found: {identifier}")


def resolve_user_to_account_id(client, user_identifier: str) -> str:
    """
    Resolve a user identifier (email or account ID) to a JIRA account ID.

    If the identifier contains '@', it is treated as an email address and
    a user search is performed. Otherwise, it is assumed to be an account ID.

    Args:
        client: JiraClient instance with active session
        user_identifier: Email address or JIRA account ID

    Returns:
        JIRA account ID

    Raises:
        UserNotFoundError: If user search returns no results
    """
    if '@' in user_identifier:
        # Treat as email - perform user search
        users = client.search_users(user_identifier, max_results=1)
        if not users:
            raise UserNotFoundError(user_identifier)
        return users[0]['accountId']
    else:
        # Assume it's already an account ID
        return user_identifier


def get_user_display_info(client, account_id: str) -> Dict[str, Any]:
    """
    Get display information for a user by account ID.
    """
    return client.get(
        '/rest/api/3/user',
        params={'accountId': account_id},
        operation=f"get user {account_id}"
    )


def resolve_users_batch(client, user_identifiers: list) -> Dict[str, str]:
    """
    Resolve multiple user identifiers to account IDs.
    """
    resolved = {}
    for identifier in user_identifiers:
        try:
            account_id = resolve_user_to_account_id(client, identifier)
            resolved[identifier] = account_id
        except UserNotFoundError:
            pass
    return resolved
```

**Updated File:** `.claude/skills/jira-collaborate/scripts/manage_watchers.py`

**Before (add_watcher function):**
```python
def add_watcher(issue_key: str, user: str, profile: str = None) -> None:
    """Add a watcher to an issue."""
    issue_key = validate_issue_key(issue_key)
    client = get_jira_client(profile)

    if '@' in user:
        user_response = client.get(f'/rest/api/3/user/search?query={user}',
                                   operation="search for user")
        if not user_response:
            raise ValidationError(f"User not found: {user}")
        account_id = user_response[0]['accountId']
    else:
        account_id = user

    client.post(f'/rest/api/3/issue/{issue_key}/watchers',
               data=f'"{account_id}"',
               operation=f"add watcher to {issue_key}")
    client.close()
```

**After:**
```python
from user_helpers import resolve_user_to_account_id, UserNotFoundError

def add_watcher(issue_key: str, user: str, profile: str = None) -> None:
    """Add a watcher to an issue."""
    issue_key = validate_issue_key(issue_key)
    client = get_jira_client(profile)

    try:
        account_id = resolve_user_to_account_id(client, user)
    except UserNotFoundError as e:
        client.close()
        raise ValidationError(str(e))

    client.post(f'/rest/api/3/issue/{issue_key}/watchers',
               data=f'"{account_id}"',
               operation=f"add watcher to {issue_key}")
    client.close()
```

**Same pattern applied to `remove_watcher` function.**

**Benefits:**
- DRY principle: User lookup logic centralized in one place
- Consistent error handling with custom `UserNotFoundError` exception
- Reusable across all skills needing user resolution
- Additional helper functions for batch operations and user info retrieval
- Uses existing `client.search_users()` method for cleaner implementation

---

## Files Modified

1. `.claude/skills/jira-jsm/scripts/approve_request.py`
   - Added `print_error` import
   - Changed `print()` to `print_error()` for error output

2. `.claude/skills/jira-bulk/scripts/bulk_clone.py`
   - Added try/except around individual issue retrieval
   - Added `retrieval_errors` tracking
   - Updated return values to include `retrieval_failed` count
   - Updated summary output to show retrieval failures

3. `.claude/skills/shared/scripts/lib/user_helpers.py` (NEW)
   - Created shared user lookup helper module
   - `UserNotFoundError` exception class
   - `resolve_user_to_account_id()` function
   - `get_user_display_info()` function
   - `resolve_users_batch()` function

4. `.claude/skills/jira-collaborate/scripts/manage_watchers.py`
   - Added import for `resolve_user_to_account_id` and `UserNotFoundError`
   - Refactored `add_watcher()` to use shared helper
   - Refactored `remove_watcher()` to use shared helper

---

## Testing Recommendations

1. **approve_request.py**: Verify error messages appear on stderr with proper formatting
2. **bulk_clone.py**: Test with a mix of valid and invalid issue keys to verify graceful handling
3. **manage_watchers.py**: Test with both email addresses and account IDs
4. **user_helpers.py**: Unit test the new helper functions with mock client

---

## Summary

These improvements enhance error handling consistency across the codebase by:

1. **Standardizing error output** - Using `print_error()` for all error messages ensures consistent formatting and proper stderr output
2. **Adding graceful failure handling** - Bulk operations now handle individual failures without failing the entire operation
3. **Centralizing reusable logic** - The new `user_helpers.py` module eliminates code duplication and provides a single source of truth for user resolution logic
