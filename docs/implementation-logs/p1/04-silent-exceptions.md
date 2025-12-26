# Silent Exception Handling Fix

## Task
Fix silent exception handling in `create_issue.py` that swallows errors without providing user feedback.

## File Analyzed
`.claude/skills/jira-issue/scripts/create_issue.py`

## Exception Blocks Found

### Block 1: Lines 148-152 (blocks link creation)
**Before:**
```python
try:
    client.create_link('Blocks', issue_key, target_key)
    links_created.append(f"blocks {target_key}")
except Exception:
    pass  # Continue even if link fails
```

**Problem:** Silent failure - user has no idea if link creation failed or why.

### Block 2: Lines 157-161 (relates-to link creation)
**Before:**
```python
try:
    client.create_link('Relates', issue_key, target_key)
    links_created.append(f"relates to {target_key}")
except Exception:
    pass  # Continue even if link fails
```

**Problem:** Silent failure - same issue as Block 1.

## Solution Design

1. Add `links_failed` list to track failed link operations
2. Catch specific `JiraError` types instead of bare `Exception`
3. For recoverable errors (`PermissionError`, `NotFoundError`), record the failure and continue
4. For other errors, re-raise to fail fast (e.g., `AuthenticationError`, `ServerError`)
5. Include failed links in the result output
6. Update imports to include specific error types

## Changes Made

### Import Update
**Before:**
```python
from error_handler import print_error, JiraError
```

**After:**
```python
from error_handler import print_error, JiraError, PermissionError, NotFoundError
```

### Link Creation Logic Update
**Before (blocks):**
```python
# Create issue links after creation
links_created = []
if blocks:
    for target_key in blocks:
        target_key = validate_issue_key(target_key)
        try:
            client.create_link('Blocks', issue_key, target_key)
            links_created.append(f"blocks {target_key}")
        except Exception:
            pass  # Continue even if link fails

if relates_to:
    for target_key in relates_to:
        target_key = validate_issue_key(target_key)
        try:
            client.create_link('Relates', issue_key, target_key)
            links_created.append(f"relates to {target_key}")
        except Exception:
            pass  # Continue even if link fails

if links_created:
    result['links_created'] = links_created
```

**After:**
```python
# Create issue links after creation
links_created = []
links_failed = []
if blocks:
    for target_key in blocks:
        target_key = validate_issue_key(target_key)
        try:
            client.create_link('Blocks', issue_key, target_key)
            links_created.append(f"blocks {target_key}")
        except JiraError as e:
            if isinstance(e, (PermissionError, NotFoundError)):
                links_failed.append(f"blocks {target_key}: {str(e)}")
            else:
                raise

if relates_to:
    for target_key in relates_to:
        target_key = validate_issue_key(target_key)
        try:
            client.create_link('Relates', issue_key, target_key)
            links_created.append(f"relates to {target_key}")
        except JiraError as e:
            if isinstance(e, (PermissionError, NotFoundError)):
                links_failed.append(f"relates to {target_key}: {str(e)}")
            else:
                raise

if links_created:
    result['links_created'] = links_created
if links_failed:
    result['links_failed'] = links_failed
```

### Output Update in main()
**Before:**
```python
if args.output == 'json':
    print(json.dumps(result, indent=2))
else:
    print_success(f"Created issue: {issue_key}")
    print(f"URL: {result.get('self', '').replace('/rest/api/3/issue/', '/browse/')}")
    links_created = result.get('links_created', [])
    if links_created:
        print(f"Links: {', '.join(links_created)}")
```

**After:**
```python
if args.output == 'json':
    print(json.dumps(result, indent=2))
else:
    print_success(f"Created issue: {issue_key}")
    print(f"URL: {result.get('self', '').replace('/rest/api/3/issue/', '/browse/')}")
    links_created = result.get('links_created', [])
    if links_created:
        print(f"Links: {', '.join(links_created)}")
    links_failed = result.get('links_failed', [])
    if links_failed:
        print(f"Links failed: {', '.join(links_failed)}")
```

## Test Results

Running unit tests to verify the fix:

```bash
pytest .claude/skills/jira-issue/tests/test_create_issue.py -v
```

**Results: 29 passed in 0.28s**

### Test Updates Made

The existing test `test_create_issue_link_failure_continues` was updated to use a `NotFoundError` instead of a generic `Exception`, and now also verifies that `links_failed` is populated.

A new test `test_create_issue_link_failure_reraises_auth_error` was added to verify that non-recoverable errors (like `AuthenticationError`) are properly re-raised rather than silently handled.

## Files Modified

1. `.claude/skills/jira-issue/scripts/create_issue.py`
   - Lines 24: Added `PermissionError, NotFoundError` to imports
   - Lines 143-173: Updated link creation logic with proper error handling

2. `.claude/skills/jira-issue/tests/test_create_issue.py`
   - Lines 308-342: Updated and expanded link failure tests

## Summary

- Fixed 2 silent exception blocks
- Added proper error categorization (recoverable vs. fatal)
- Added `links_failed` tracking in result
- Updated output to show failed links to user
- Maintains backward compatibility (issue still created even if links fail)
- All 29 tests pass
