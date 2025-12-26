# Fix jira-search Unit Test Failures

**Date**: 2025-12-26
**Issue**: 11 unit test failures in jira-search skill
**Root Cause**: Tests expected direct client method calls, but implementations use caching layer by default

## Summary

Added `use_cache=False` parameter to 11 function calls in tests that assert on client method calls. This bypasses the caching layer and ensures direct API method invocation for proper mocking.

## Files Modified

### 1. `.claude/skills/jira-search/tests/test_jql_fields.py`

5 tests fixed:

| Test Method | Line | Change |
|------------|------|--------|
| `test_get_all_fields` | 25 | `get_fields(mock_jira_client)` -> `get_fields(mock_jira_client, use_cache=False)` |
| `test_authentication_error` | 112 | `get_fields(mock_jira_client)` -> `get_fields(mock_jira_client, use_cache=False)` |
| `test_forbidden_error` | 124 | `get_fields(mock_jira_client)` -> `get_fields(mock_jira_client, use_cache=False)` |
| `test_rate_limit_error` | 136 | `get_fields(mock_jira_client)` -> `get_fields(mock_jira_client, use_cache=False)` |
| `test_server_error` | 149 | `get_fields(mock_jira_client)` -> `get_fields(mock_jira_client, use_cache=False)` |

### 2. `.claude/skills/jira-search/tests/test_jql_suggest.py`

6 tests fixed:

| Test Method | Line | Change |
|------------|------|--------|
| `test_suggest_project_values` | 29 | `get_suggestions(mock_jira_client, 'project')` -> `get_suggestions(mock_jira_client, 'project', use_cache=False)` |
| `test_suggest_with_prefix` | 73 | `get_suggestions(mock_jira_client, 'status', prefix='In Pr')` -> `get_suggestions(mock_jira_client, 'status', prefix='In Pr', use_cache=False)` |
| `test_authentication_error` | 122 | `get_suggestions(mock_jira_client, 'status')` -> `get_suggestions(mock_jira_client, 'status', use_cache=False)` |
| `test_forbidden_error` | 134 | `get_suggestions(mock_jira_client, 'status')` -> `get_suggestions(mock_jira_client, 'status', use_cache=False)` |
| `test_rate_limit_error` | 146 | `get_suggestions(mock_jira_client, 'status')` -> `get_suggestions(mock_jira_client, 'status', use_cache=False)` |
| `test_server_error` | 159 | `get_suggestions(mock_jira_client, 'status')` -> `get_suggestions(mock_jira_client, 'status', use_cache=False)` |

## Test Results

```
cd .claude/skills/jira-search/tests && pytest . -v --ignore=live_integration -p no:cacheprovider

============================= 117 passed in 0.62s ==============================
```

All 117 tests now pass (previously 106 passed, 11 failed).

## Technical Details

The `get_fields()` and `get_suggestions()` functions have a `use_cache=True` default parameter. When caching is enabled:
- The autocomplete cache layer intercepts API calls
- Mock client methods are not called directly
- Tests asserting on `mock_jira_client.get_jql_*.assert_called_once()` fail

Passing `use_cache=False` bypasses the cache and ensures:
- Direct client method invocation
- Proper exception propagation for error handling tests
- Accurate mock assertion verification
