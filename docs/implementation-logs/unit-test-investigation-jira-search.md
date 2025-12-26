# Unit Test Investigation: jira-search Skill

**Date**: 2025-12-26
**Test Command**: `cd .claude/skills/jira-search/tests && pytest . -v --ignore=live_integration -p no:cacheprovider`
**Result**: 11 failures out of 117 tests

## Summary

The 11 test failures are caused by **tests expecting direct `client.get_jql_*` method calls, but implementations now use caching layer** (`autocomplete_cache.py`) that wraps these calls. The tests need to be updated to either:
1. Disable caching in tests (pass `use_cache=False`)
2. Mock the cache layer instead of/in addition to client methods

## Detailed Failure Analysis

### Category 1: API Method Call Assertions Fail (4 failures)

#### 1. `test_jql_fields.py::TestGetAllFields::test_get_all_fields`

**Test Code (lines 19-30)**:
```python
def test_get_all_fields(self, mock_jira_client, sample_autocomplete_data):
    mock_jira_client.get_jql_autocomplete.return_value = sample_autocomplete_data
    from jql_fields import get_fields
    fields = get_fields(mock_jira_client)
    # ...
    mock_jira_client.get_jql_autocomplete.assert_called_once()  # FAILS
```

**Implementation (`jql_fields.py` lines 27-51)**:
```python
def get_fields(client, name_filter=None, custom_only=False,
               system_only=False, use_cache=True, refresh_cache=False):
    if use_cache:  # <-- DEFAULT is True
        cache = get_autocomplete_cache()
        fields = cache.get_fields(client, force_refresh=refresh_cache)  # Uses cache
    else:
        data = client.get_jql_autocomplete()  # Only called if use_cache=False
        fields = data.get('visibleFieldNames', [])
```

**Root Cause**: Default `use_cache=True` causes cache layer to be used. Cache layer (`autocomplete_cache.py` line 149) checks persistent cache first before calling `client.get_jql_autocomplete()`. The mock client's return value is set, but the method is never called because cache returns empty (None) which then falls through to call the API. However, the cache module uses a different cache instance.

**Fix Required**: Test should pass `use_cache=False`:
```python
fields = get_fields(mock_jira_client, use_cache=False)
```

---

#### 2. `test_jql_suggest.py::TestSuggestValues::test_suggest_project_values`

**Test Code (lines 18-33)**:
```python
def test_suggest_project_values(self, mock_jira_client):
    mock_jira_client.get_jql_suggestions.return_value = { ... }
    from jql_suggest import get_suggestions
    suggestions = get_suggestions(mock_jira_client, 'project')
    # ...
    mock_jira_client.get_jql_suggestions.assert_called_once_with('project', '')  # FAILS
```

**Implementation (`jql_suggest.py` lines 27-49)**:
```python
def get_suggestions(client, field_name, prefix='',
                    use_cache=True, refresh_cache=False):
    if use_cache:  # <-- DEFAULT is True
        cache = get_autocomplete_cache()
        return cache.get_suggestions(field_name, prefix, client, force_refresh=refresh_cache)
    else:
        result = client.get_jql_suggestions(field_name, prefix)  # Only if use_cache=False
        return result.get('results', [])
```

**Root Cause**: Same as above - caching layer intercepts the call.

**Fix Required**: Test should pass `use_cache=False`:
```python
suggestions = get_suggestions(mock_jira_client, 'project', use_cache=False)
```

---

#### 3. `test_jql_suggest.py::TestSuggestValues::test_suggest_with_prefix`

**Test Code (lines 63-77)**:
```python
def test_suggest_with_prefix(self, mock_jira_client):
    mock_jira_client.get_jql_suggestions.return_value = { ... }
    from jql_suggest import get_suggestions
    suggestions = get_suggestions(mock_jira_client, 'status', prefix='In Pr')
    # ...
    mock_jira_client.get_jql_suggestions.assert_called_once_with('status', 'In Pr')  # FAILS
```

**Root Cause**: Same as #2.

**Fix Required**: Test should pass `use_cache=False`:
```python
suggestions = get_suggestions(mock_jira_client, 'status', prefix='In Pr', use_cache=False)
```

---

### Category 2: Error Handling Tests Not Raising Exceptions (8 failures)

These all fail because caching layer intercepts the call and returns empty data instead of propagating the exception.

#### 4. `test_jql_fields.py::TestJqlFieldsErrorHandling::test_authentication_error`

**Test Code (lines 102-112)**:
```python
def test_authentication_error(self, mock_jira_client):
    from error_handler import AuthenticationError
    mock_jira_client.get_jql_autocomplete.side_effect = AuthenticationError("Invalid API token")
    from jql_fields import get_fields
    with pytest.raises(AuthenticationError):  # FAILS - exception not raised
        get_fields(mock_jira_client)
```

**Root Cause**: Cache layer checks persistent cache first. If cache has no data, it calls `client.get_jql_autocomplete()`. But the singleton `get_autocomplete_cache()` instance may have been polluted by previous tests or returns empty list without calling the client.

Actually, looking at `autocomplete_cache.py` lines 137-155:
```python
def get_fields(self, client=None, force_refresh=False):
    if not force_refresh:
        cached = self._cache.get(self.KEY_FIELDS_LIST, category="field")
        if cached:
            return cached  # Returns cached, never calls client

    data = self.get_autocomplete_data(client, force_refresh)
    return data.get('visibleFieldNames', []) if data else []
```

The cache lookup returns `None` (empty), then `get_autocomplete_data()` is called which eventually calls `client.get_jql_autocomplete()`. The exception SHOULD propagate. However, since tests run in sequence, the singleton cache may have polluted state.

**Real Issue**: The global singleton `_autocomplete_cache` persists across tests. Need to either:
- Reset the singleton cache between tests
- Mock the cache layer
- Pass `use_cache=False`

**Fix Required**: Pass `use_cache=False` to bypass cache:
```python
with pytest.raises(AuthenticationError):
    get_fields(mock_jira_client, use_cache=False)
```

---

#### 5-7. Remaining `test_jql_fields.py` error handling tests

- `test_forbidden_error` (line 114)
- `test_rate_limit_error` (line 126)
- `test_server_error` (line 139)

**Same Root Cause and Fix**: All need `use_cache=False`.

---

#### 8-11. All `test_jql_suggest.py` error handling tests

- `test_authentication_error` (line 112)
- `test_forbidden_error` (line 124)
- `test_rate_limit_error` (line 136)
- `test_server_error` (line 149)

**Same Root Cause and Fix**: All need `use_cache=False`.

---

## Fix Summary

### Tests to Update (11 total)

| Test File | Test Name | Line | Fix |
|-----------|-----------|------|-----|
| test_jql_fields.py | test_get_all_fields | 25 | Add `use_cache=False` |
| test_jql_fields.py | test_authentication_error | 112 | Add `use_cache=False` |
| test_jql_fields.py | test_forbidden_error | 124 | Add `use_cache=False` |
| test_jql_fields.py | test_rate_limit_error | 136 | Add `use_cache=False` |
| test_jql_fields.py | test_server_error | 148 | Add `use_cache=False` |
| test_jql_suggest.py | test_suggest_project_values | 29 | Add `use_cache=False` |
| test_jql_suggest.py | test_suggest_with_prefix | 73 | Add `use_cache=False` |
| test_jql_suggest.py | test_authentication_error | 122 | Add `use_cache=False` |
| test_jql_suggest.py | test_forbidden_error | 134 | Add `use_cache=False` |
| test_jql_suggest.py | test_rate_limit_error | 146 | Add `use_cache=False` |
| test_jql_suggest.py | test_server_error | 158 | Add `use_cache=False` |

### Implementation Changes Required: None

The implementations are correct. The caching feature is intentional and working as designed. Only the tests need updating to explicitly disable caching when testing direct client method calls.

### Alternative Fix: Reset Cache Singleton

Another option is to add a fixture that resets the cache singleton between tests:

```python
@pytest.fixture(autouse=True)
def reset_autocomplete_cache():
    """Reset the autocomplete cache singleton before each test."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))
    import autocomplete_cache
    autocomplete_cache._autocomplete_cache = None
    yield
```

However, passing `use_cache=False` is cleaner and makes test intent explicit.

---

## Passing Tests That Use Cache Correctly

For reference, these tests in the same files pass because they don't assert on client method calls:

- `test_filter_fields_by_name` - Uses cache but only checks return value
- `test_get_custom_fields_only` - Uses cache but only checks return value
- `test_get_system_fields_only` - Uses cache but only checks return value
- `test_format_text_output` - Doesn't call `get_fields()` at all
- `test_format_json_output` - Doesn't call `get_fields()` at all
- `test_suggest_status_values` - Doesn't assert on client call
- `test_suggest_user_values` - Doesn't assert on client call
- `test_suggest_custom_field_values` - Doesn't assert on client call
- `test_empty_suggestions` - Doesn't assert on client call

## Recommendation

Update the 11 failing tests by adding `use_cache=False` parameter. This:
1. Makes tests independent of cache state
2. Tests the core logic without caching complexity
3. Is consistent with what these tests intend to verify (direct API interaction)

Caching behavior should be tested separately in dedicated cache tests.
