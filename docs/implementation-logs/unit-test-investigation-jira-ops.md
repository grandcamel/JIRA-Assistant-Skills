# Unit Test Investigation: jira-ops Skill

**Date:** 2025-12-26
**Test Command:** `pytest .claude/skills/jira-ops/tests/ -v --ignore=live_integration -p no:cacheprovider`
**Failures:** 13 out of 97 tests

---

## Summary

There are two categories of test failures:

1. **CLI Argument Test (1 failure):** `test_verbose_flag` in `test_cli_args.py` - Missing `-v/--verbose` flag in `cache_status.py`
2. **Negative Scenario Tests (12 failures):** Tests expect `cache_warm.py` to exit with an error when API errors occur, but exceptions are silently caught

---

## Failure Category 1: Missing Verbose Flag

### Test: `TestCacheStatusCLI::test_verbose_flag`

**File:** `/Users/jasonkrueger/IdeaProjects/Jira-Assistant-Skills/.claude/skills/jira-ops/tests/test_cli_args.py:58-67`

**Test Code:**
```python
def test_verbose_flag(self):
    """Test -v/--verbose flag."""
    import cache_status

    with patch('sys.argv', ['cache_status.py', '-v']):
        try:
            cache_status.main()
        except SystemExit as e:
            if e.code == 2:
                pytest.fail("-v flag should be valid")
```

**Failure Reason:**
The test expects `cache_status.py` to accept a `-v/--verbose` flag, but examining the implementation at `/Users/jasonkrueger/IdeaProjects/Jira-Assistant-Skills/.claude/skills/jira-ops/scripts/cache_status.py:50-78`, the script only defines these arguments:
- `--json`
- `--profile`
- `--cache-dir`

There is **no** `--verbose` or `-v` argument defined.

**Root Cause:** Implementation missing feature

**Verdict:** The **implementation needs to be updated** to add the `-v/--verbose` flag.

**Fix Required (cache_status.py):** Add the verbose argument to argparse configuration:
```python
parser.add_argument(
    "--verbose",
    "-v",
    action="store_true",
    help="Verbose output"
)
```

---

## Failure Category 2: Negative Scenario Tests (12 failures)

All 12 failures share the same root cause.

### Affected Tests:

| Test Class | Test Method | Error Type Mocked |
|------------|-------------|-------------------|
| `TestInvalidCredentials` | `test_authentication_error_401` | `AuthenticationError` |
| `TestInvalidCredentials` | `test_invalid_token_format` | `AuthenticationError` |
| `TestInvalidCredentials` | `test_expired_token` | `AuthenticationError` |
| `TestNetworkErrors` | `test_connection_timeout` | `requests.exceptions.Timeout` |
| `TestNetworkErrors` | `test_connection_refused` | `requests.exceptions.ConnectionError` |
| `TestNetworkErrors` | `test_dns_resolution_failure` | `requests.exceptions.ConnectionError` |
| `TestRateLimiting` | `test_rate_limit_429` | `RateLimitError` |
| `TestRateLimiting` | `test_rate_limit_with_retry_after` | `RateLimitError` (attribute check) |
| `TestServerErrors` | `test_internal_server_error_500` | `ServerError` |
| `TestServerErrors` | `test_bad_gateway_502` | `ServerError` |
| `TestServerErrors` | `test_service_unavailable_503` | `ServerError` |
| `TestServerErrors` | `test_gateway_timeout_504` | `ServerError` |

### Test Pattern:

All tests follow this pattern:
```python
def test_authentication_error_401(self, mock_jira_client):
    from error_handler import AuthenticationError

    mock_jira_client.get.side_effect = AuthenticationError(
        "Invalid authentication credentials"
    )

    import cache_warm

    with patch('cache_warm.get_jira_client', return_value=mock_jira_client):
        with patch('cache_warm.HAS_CONFIG_MANAGER', True):
            with patch('sys.argv', ['cache_warm.py', '--projects']):
                with pytest.raises(SystemExit) as exc_info:
                    cache_warm.main()

                # Should exit with error code
                assert exc_info.value.code != 0
```

### Failure Analysis:

Looking at `cache_warm.py` lines 41-60 (`warm_projects` function):

```python
def warm_projects(client, cache, verbose=False):
    """Fetch and cache project list."""
    if verbose:
        print("Fetching projects...")

    try:
        response = client.get("/rest/api/3/project", operation="fetch projects")
        # ... process response ...
    except Exception as e:
        if verbose:
            print(f"  Error fetching projects: {e}")
        return 0  # <-- SILENTLY CATCHES ALL EXCEPTIONS, RETURNS 0
```

**Root Cause:** Each warming function (`warm_projects`, `warm_fields`, `warm_issue_types`, `warm_priorities`, `warm_statuses`) has a `try/except Exception` block that catches ALL exceptions, prints them only if verbose, and returns 0.

The `main()` function at lines 228-253 also has a generic `try/except Exception` handler, but the exceptions never propagate to it because they are caught in the individual warming functions first.

**Result:** When an API error is raised (e.g., `AuthenticationError`), it is silently caught, the function returns 0, and the script prints "Cache warming complete. Cached 0 items." and exits successfully (no `sys.exit(1)`).

**Test Output Confirms This:**
```
Cache warming complete. Cached 0 items.
Total cache size: 0.0 MB
```

### Special Case: `test_rate_limit_with_retry_after`

**File:** `test_negative_scenarios.py:175-182`

```python
def test_rate_limit_with_retry_after(self, mock_jira_client):
    from error_handler import RateLimitError

    error = RateLimitError(retry_after=120)

    assert error.retry_after == 120  # <-- AttributeError: 'RateLimitError' object has no attribute 'retry_after'
```

**Root Cause:** The `RateLimitError` class at `/Users/jasonkrueger/IdeaProjects/Jira-Assistant-Skills/.claude/skills/shared/scripts/lib/error_handler.py:76-85`:

```python
class RateLimitError(JiraError):
    """Raised when API rate limit is exceeded."""

    def __init__(self, retry_after: Optional[int] = None, **kwargs):
        message = "API rate limit exceeded"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        else:
            message += ". Please wait before retrying"
        super().__init__(message, **kwargs)
```

The `retry_after` parameter is **not stored as an instance attribute**. It is only used to construct the message string and then discarded.

**Verdict:** The **implementation needs to be updated** to store `retry_after` as an instance attribute:

```python
class RateLimitError(JiraError):
    def __init__(self, retry_after: Optional[int] = None, **kwargs):
        self.retry_after = retry_after  # <-- Add this line
        message = "API rate limit exceeded"
        # ... rest of implementation
```

---

## Summary of Required Fixes

### Implementation Fixes Required:

| File | Issue | Fix |
|------|-------|-----|
| `cache_status.py` | Missing `-v/--verbose` flag | Add argparse argument for verbose flag |
| `cache_warm.py` | Exceptions silently caught in warming functions | Either: (a) Re-raise critical exceptions (AuthenticationError, etc.) from warming functions, or (b) Track errors and call `sys.exit(1)` in main if critical errors occurred |
| `error_handler.py` | `RateLimitError.retry_after` not stored | Add `self.retry_after = retry_after` in `__init__` |

### Alternative: Test Fixes (if current behavior is intentional)

If the design intention is that `cache_warm.py` should gracefully continue when individual warming operations fail:

| Test File | Issue | Fix |
|-----------|-------|-----|
| `test_negative_scenarios.py` | Tests expect `SystemExit` for all errors | Change tests to verify error is logged and script continues, OR only expect exit for `get_jira_client()` failures |
| `test_negative_scenarios.py:181` | Test expects `retry_after` attribute | Fix test to check message string instead |

---

## Recommendation

The **implementations should be fixed** because:

1. **Verbose flag consistency:** `cache_warm.py` has `-v/--verbose`, so `cache_status.py` should too for consistency
2. **Error propagation:** Silent failure on authentication errors is a poor UX - users should know immediately if their credentials are invalid
3. **Attribute access:** If a `RateLimitError` is raised, callers should be able to access `retry_after` to implement proper retry logic

The current behavior where `cache_warm.py` silently succeeds with "0 items cached" when authentication fails is confusing for users.
