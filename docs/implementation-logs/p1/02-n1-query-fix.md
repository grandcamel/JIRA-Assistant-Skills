# N+1 Query Fix in bulk_clone.py

**Date:** 2025-12-26
**File:** `.claude/skills/jira-bulk/scripts/bulk_clone.py`
**Lines:** 263-270

## Problem

The `bulk_clone` function was making N+1 API calls when using JQL queries:

1. First API call: Search for issues matching JQL, returning only `key` field
2. N additional API calls: Fetch full details for each issue individually

This pattern is inefficient for bulk operations, especially when cloning many issues.

### Before (N+1 pattern)

```python
elif jql:
    jql = validate_jql(jql)
    result = client.search_issues(jql, fields=['key'], max_results=max_issues)
    issue_keys = [i['key'] for i in result.get('issues', [])]
    issues = []
    for key in issue_keys:
        issue = client.get_issue(key)  # N additional API calls!
        issues.append(issue)
```

**API calls for 10 issues:** 1 (search) + 10 (get each issue) = 11 calls

## Solution

Fetch all required fields in a single search call using `fields=['*all']`:

### After (Single Query)

```python
elif jql:
    jql = validate_jql(jql)
    result = client.search_issues(jql, fields=['*all'], max_results=max_issues)
    issues = result.get('issues', [])
```

**API calls for 10 issues:** 1 call total

## Performance Impact

| Issues | Before (N+1) | After (Single) | Improvement |
|--------|--------------|----------------|-------------|
| 10     | 11 calls     | 1 call         | 10x         |
| 50     | 51 calls     | 1 call         | 50x         |
| 100    | 101 calls    | 1 call         | 100x        |

The improvement scales linearly with the number of issues. For bulk operations with `max_issues=100`, this reduces API calls from 101 to 1, which:

1. **Reduces latency:** Each API call has network overhead (typically 50-200ms). For 100 issues, this saves 5-20 seconds of latency.
2. **Reduces rate limiting risk:** Fewer API calls means less chance of hitting JIRA's rate limits (429 errors).
3. **Improves reliability:** Fewer calls means fewer chances for transient failures.

## Test Results

All 15 `bulk_clone` unit tests pass:

```
.claude/skills/jira-bulk/tests/test_bulk_clone.py::TestBulkCloneBasic::test_bulk_clone_basic PASSED
.claude/skills/jira-bulk/tests/test_bulk_clone.py::TestBulkCloneWithSubtasks::test_bulk_clone_with_subtasks PASSED
.claude/skills/jira-bulk/tests/test_bulk_clone.py::TestBulkCloneWithLinks::test_bulk_clone_with_links PASSED
.claude/skills/jira-bulk/tests/test_bulk_clone.py::TestBulkCloneWithPrefix::test_bulk_clone_with_prefix PASSED
.claude/skills/jira-bulk/tests/test_bulk_clone.py::TestBulkCloneToProject::test_bulk_clone_to_project PASSED
.claude/skills/jira-bulk/tests/test_bulk_clone.py::TestBulkCloneStripValues::test_bulk_clone_strip_values PASSED
.claude/skills/jira-bulk/tests/test_bulk_clone.py::TestBulkCloneDryRun::test_bulk_clone_dry_run PASSED
.claude/skills/jira-bulk/tests/test_bulk_clone.py::TestBulkClonePartialFailure::test_bulk_clone_partial_failure PASSED
.claude/skills/jira-bulk/tests/test_bulk_clone.py::TestBulkCloneByJql::test_bulk_clone_by_jql PASSED
.claude/skills/jira-bulk/tests/test_bulk_clone.py::TestBulkCloneProgressCallback::test_bulk_clone_progress_callback PASSED
.claude/skills/jira-bulk/tests/test_bulk_clone.py::TestBulkCloneApiErrors::test_authentication_error PASSED
.claude/skills/jira-bulk/tests/test_bulk_clone.py::TestBulkCloneApiErrors::test_permission_denied_error PASSED
.claude/skills/jira-bulk/tests/test_bulk_clone.py::TestBulkCloneApiErrors::test_not_found_error PASSED
.claude/skills/jira-bulk/tests/test_bulk_clone.py::TestBulkCloneApiErrors::test_rate_limit_error PASSED
.claude/skills/jira-bulk/tests/test_bulk_clone.py::TestBulkCloneApiErrors::test_server_error PASSED

============================== 15 passed in 1.66s ==============================
```

All 62 jira-bulk unit tests pass:

```
============================== 62 passed in 4.72s ==============================
```

## Notes

1. The `issue_keys` path (lines 257-262) also has N API calls, but this is expected behavior when specific keys are provided. Users providing explicit keys may not have all data available via search.

2. The `test_bulk_clone_by_jql` test mocks `search_issues` to return full issue objects, which aligns with the new behavior. The test continues to pass without modification.

3. The `fields=['*all']` parameter tells JIRA to return all fields for each issue, matching what `get_issue()` would return individually.
