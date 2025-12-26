# Test Remediation Plan: jira-search Skill

**Created:** 2025-12-26
**Status:** Draft
**Test Files Reviewed:** 13
**Total Issues Identified:** ~85

---

## Executive Summary

This plan addresses test quality issues discovered during a comprehensive review of the `jira-search` skill test suite. Issues are organized by priority and grouped into actionable phases.

**Estimated Effort:**
- Phase 1 (Critical): 2-3 hours
- Phase 2 (High Priority): 3-4 hours
- Phase 3 (Medium Priority): 2-3 hours
- Phase 4 (Low Priority): 1-2 hours

---

## Phase 1: Critical Issues (Must Fix)

### 1.1 Missing pytest Marker Registration

**Impact:** pytest warnings, inconsistent test selection
**File:** `tests/conftest.py`

**Current state:** No `pytest_configure` function exists in conftest.py

**Add at top of conftest.py (after imports):**

```python
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "search: mark test as search skill test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
```

---

### 1.2 Missing pytest Markers on All Test Classes

**Impact:** Inconsistent test categorization, cannot filter tests by type
**Files Affected:** 12 test files (all test files)

| File | Line | Class Name |
|------|------|------------|
| `test_jql_fields.py` | 15 | `TestGetAllFields` |
| `test_jql_functions.py` | 15 | `TestGetFunctions` |
| `test_jql_validate.py` | 15 | `TestValidateJQL` |
| `test_jql_suggest.py` | 15 | `TestSuggestValues` |
| `test_jql_build.py` | 15 | `TestBuildJQL` |
| `test_create_filter.py` | 15 | `TestCreateFilter` |
| `test_get_filters.py` | 15 | `TestGetFilters` |
| `test_favourite_filter.py` | 14 | `TestFavouriteFilter` |
| `test_update_filter.py` | 15 | `TestUpdateFilter` |
| `test_delete_filter.py` | 14 | `TestDeleteFilter` |
| `test_share_filter.py` | 14 | `TestShareFilter` |
| `test_filter_subscriptions.py` | 14 | `TestFilterSubscriptions` |

**Remediation:**

```python
# Add to each test class:
@pytest.mark.search
@pytest.mark.unit
class TestClassName:
    """Test description."""
```

---

### 1.3 Fixture Mutation Issues

**Impact:** Potential test pollution between tests - fixtures are modified directly
**Files Affected:** 5 files

| File | Lines | Issue |
|------|-------|-------|
| `test_create_filter.py` | 36-37 | `sample_filter['description'] = 'All bugs...'` |
| `test_create_filter.py` | 52-53 | `sample_filter['favourite'] = True` |
| `test_create_filter.py` | 68-70 | `sample_filter['sharePermissions'] = [...]` |
| `test_create_filter.py` | 88-90 | `sample_filter['sharePermissions'] = [...]` |
| `test_favourite_filter.py` | 19 | `sample_filter['favourite'] = True` |
| `test_favourite_filter.py` | 41 | `sample_filter['favourite'] = True` |
| `test_update_filter.py` | 20 | `sample_filter['name'] = 'My Open Bugs'` |
| `test_update_filter.py` | 33 | `sample_filter['jql'] = new_jql` |
| `test_update_filter.py` | 44 | `sample_filter['description'] = 'Updated...'` |
| `test_update_filter.py` | 56-57 | Multiple field mutations |

**Remediation Template:**

```python
# Before (mutation risk):
def test_create_filter_with_description(self, mock_jira_client, sample_filter):
    sample_filter['description'] = 'All bugs in the project'  # Mutates fixture!
    mock_jira_client.create_filter.return_value = sample_filter

# After (safe):
def test_create_filter_with_description(self, mock_jira_client, sample_filter):
    import copy
    expected = copy.deepcopy(sample_filter)
    expected['description'] = 'All bugs in the project'
    mock_jira_client.create_filter.return_value = expected
```

**Update conftest.py fixtures to use deepcopy:**

```python
# In conftest.py, update fixtures to return copies:
@pytest.fixture
def sample_filter():
    """Sample filter response."""
    import copy
    return copy.deepcopy({
        'id': '10042',
        'name': 'My Bugs',
        # ... rest of fixture
    })
```

---

### 1.4 Missing CLI Test Coverage

**Impact:** CLI argument parsing and main() functions are not tested
**Files Affected:** All 12 test files

Each script likely has a `main()` function and CLI argument parsing that are not tested. This is a systematic gap.

**Remediation - Add CLI test class to each test file:**

```python
class TestJqlFieldsCLI:
    """CLI integration tests for jql_fields.py."""

    def test_cli_default_output(self, mock_jira_client, sample_autocomplete_data, capsys):
        """Test CLI with default arguments."""
        mock_jira_client.get_jql_autocomplete.return_value = sample_autocomplete_data

        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            import sys
            with patch.object(sys, 'argv', ['jql_fields.py']):
                from jql_fields import main
                main()

        captured = capsys.readouterr()
        assert 'assignee' in captured.out
        assert 'status' in captured.out

    def test_cli_json_format(self, mock_jira_client, sample_autocomplete_data, capsys):
        """Test CLI with JSON output."""
        mock_jira_client.get_jql_autocomplete.return_value = sample_autocomplete_data

        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            import sys
            with patch.object(sys, 'argv', ['jql_fields.py', '--format', 'json']):
                from jql_fields import main
                main()

        captured = capsys.readouterr()
        import json
        parsed = json.loads(captured.out)
        assert isinstance(parsed, list)

    def test_cli_custom_only(self, mock_jira_client, sample_autocomplete_data, capsys):
        """Test CLI with --custom-only flag."""
        mock_jira_client.get_jql_autocomplete.return_value = sample_autocomplete_data

        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            import sys
            with patch.object(sys, 'argv', ['jql_fields.py', '--custom-only']):
                from jql_fields import main
                main()

        captured = capsys.readouterr()
        assert 'customfield_10016' in captured.out
```

---

## Phase 2: High Priority Issues

### 2.1 Missing API Error Handling Tests

**Impact:** Error scenarios untested, poor user experience on failures
**Coverage Gap:** Most test files missing tests for:
- `AuthenticationError` (401)
- `ForbiddenError` (403)
- Rate limiting (429)
- Server errors (500, 502, 503, 504)
- Network timeout/connection errors

**Files to Update:** All 12 test files

**Current coverage (partial):**

| File | 404 NotFoundError | 403 PermissionError | 401 Auth | 429 Rate | 500 Server |
|------|-------------------|---------------------|----------|----------|------------|
| `test_jql_fields.py` | No | No | No | No | No |
| `test_jql_functions.py` | No | No | No | No | No |
| `test_jql_validate.py` | No | No | No | No | No |
| `test_jql_suggest.py` | No | No | No | No | No |
| `test_jql_build.py` | No | No | No | No | No |
| `test_create_filter.py` | No | No | No | No | No |
| `test_get_filters.py` | No | No | No | No | No |
| `test_favourite_filter.py` | Yes (line 60) | No | No | No | No |
| `test_update_filter.py` | Yes (line 83) | Yes (line 71) | No | No | No |
| `test_delete_filter.py` | Yes (line 39) | Yes (line 27) | No | No | No |
| `test_share_filter.py` | No | Yes (line 132) | No | No | No |
| `test_filter_subscriptions.py` | Yes (line 72) | No | No | No | No |

**Remediation Template - Add to each test file:**

```python
class TestApiErrorHandling:
    """Test API error handling scenarios."""

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from error_handler import AuthenticationError
        mock_jira_client.get_jql_autocomplete.side_effect = AuthenticationError(
            "Invalid API token"
        )

        from jql_fields import get_fields
        with pytest.raises(AuthenticationError):
            get_fields(mock_jira_client)

    def test_forbidden_error(self, mock_jira_client):
        """Test handling of 403 forbidden."""
        from error_handler import ForbiddenError
        mock_jira_client.get_jql_autocomplete.side_effect = ForbiddenError(
            "You don't have permission to access this resource"
        )

        from jql_fields import get_fields
        with pytest.raises(ForbiddenError):
            get_fields(mock_jira_client)

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from error_handler import JiraError
        mock_jira_client.get_jql_autocomplete.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        from jql_fields import get_fields
        with pytest.raises(JiraError) as exc_info:
            get_fields(mock_jira_client)
        assert exc_info.value.status_code == 429

    def test_server_error(self, mock_jira_client):
        """Test handling of 500 internal server error."""
        from error_handler import JiraError
        mock_jira_client.get_jql_autocomplete.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        from jql_fields import get_fields
        with pytest.raises(JiraError) as exc_info:
            get_fields(mock_jira_client)
        assert exc_info.value.status_code == 500

    def test_network_timeout(self, mock_jira_client):
        """Test handling of network timeout."""
        from error_handler import JiraError
        mock_jira_client.get_jql_autocomplete.side_effect = JiraError(
            "Connection timeout"
        )

        from jql_fields import get_fields
        with pytest.raises(JiraError):
            get_fields(mock_jira_client)
```

---

### 2.2 Missing Dry-Run Tests

**Impact:** Dry-run feature may have bugs that go undetected
**Scripts with dry-run capability:**

| Script | Test File | Has Dry-Run Test |
|--------|-----------|------------------|
| `delete_filter.py` | `test_delete_filter.py` | Yes (line 62) |
| `create_filter.py` | `test_create_filter.py` | No |
| `update_filter.py` | `test_update_filter.py` | No |
| `share_filter.py` | `test_share_filter.py` | No |

**Remediation - Add dry-run tests:**

```python
# test_create_filter.py
def test_create_filter_dry_run(self, mock_jira_client, sample_filter):
    """Test dry-run mode previews creation without making changes."""
    from create_filter import dry_run_create

    result = dry_run_create(
        name='My Bugs',
        jql='project = PROJ AND type = Bug'
    )

    assert 'Would create filter' in result
    assert 'My Bugs' in result
    mock_jira_client.create_filter.assert_not_called()

# test_update_filter.py
def test_update_filter_dry_run(self, mock_jira_client, sample_filter):
    """Test dry-run mode shows preview without changes."""
    mock_jira_client.get_filter.return_value = sample_filter

    from update_filter import dry_run_update

    result = dry_run_update(mock_jira_client, '10042', name='New Name')

    assert 'Would update filter' in result
    assert '10042' in result
    mock_jira_client.update_filter.assert_not_called()

# test_share_filter.py
def test_share_filter_dry_run(self, mock_jira_client, sample_filter):
    """Test dry-run mode for sharing."""
    mock_jira_client.get_filter.return_value = sample_filter

    from share_filter import dry_run_share

    result = dry_run_share(mock_jira_client, '10042', 'project', 'PROJ')

    assert 'Would share filter' in result
    mock_jira_client.add_filter_permission.assert_not_called()
```

---

### 2.3 Missing Error Response Fixtures

**Impact:** Test code duplicates error response setup
**File:** `tests/conftest.py`

**Add standard error response fixtures:**

```python
@pytest.fixture
def filter_not_found_error():
    """Sample 404 error for filter not found."""
    return {
        'errorMessages': ['Filter 99999 not found'],
        'errors': {}
    }

@pytest.fixture
def permission_denied_error():
    """Sample 403 error for permission denied."""
    return {
        'errorMessages': ['You are not the owner of this filter'],
        'errors': {}
    }

@pytest.fixture
def validation_error_response():
    """Sample 400 error for validation failure."""
    return {
        'errorMessages': [],
        'errors': {
            'jql': "JQL parse error: Field 'projct' does not exist"
        }
    }

@pytest.fixture
def rate_limit_error():
    """Sample 429 rate limit error."""
    return {
        'errorMessages': ['Rate limit exceeded. Retry after 60 seconds.'],
        'errors': {}
    }
```

---

## Phase 3: Medium Priority Issues

### 3.1 Missing Edge Case Tests

**Priority order by impact:**

| Category | Test File | Missing Edge Case |
|----------|-----------|-------------------|
| Empty results | `test_jql_fields.py` | No fields returned |
| Empty results | `test_jql_functions.py` | No functions returned |
| Empty results | `test_get_filters.py` | No filters found |
| Boundary values | `test_create_filter.py` | Max name length (255 chars) |
| Boundary values | `test_jql_build.py` | Empty clauses list |
| Special characters | `test_create_filter.py` | JQL with special chars |
| Special characters | `test_jql_validate.py` | JQL with Unicode |
| Invalid input | `test_jql_suggest.py` | Invalid field name |
| Invalid input | `test_jql_build.py` | Invalid order_by field |
| Pagination | `test_get_filters.py` | Large result sets |

**Remediation Templates:**

```python
# Empty results tests
def test_get_fields_empty_response(self, mock_jira_client):
    """Test handling when no fields are returned."""
    mock_jira_client.get_jql_autocomplete.return_value = {
        'visibleFieldNames': [],
        'visibleFunctionNames': [],
        'jqlReservedWords': []
    }

    from jql_fields import get_fields

    fields = get_fields(mock_jira_client)

    assert fields == []

# Boundary value tests
def test_create_filter_max_name_length(self, mock_jira_client, sample_filter):
    """Test creating filter with maximum name length."""
    import copy
    max_name = 'A' * 255
    expected = copy.deepcopy(sample_filter)
    expected['name'] = max_name
    mock_jira_client.create_filter.return_value = expected

    from create_filter import create_filter

    result = create_filter(
        mock_jira_client,
        name=max_name,
        jql='project = PROJ'
    )

    assert len(result['name']) == 255

# Special characters tests
def test_validate_jql_with_unicode(self, mock_jira_client):
    """Test validating JQL containing Unicode characters."""
    mock_jira_client.parse_jql.return_value = {
        'queries': [{
            'query': 'summary ~ "recherche"',
            'errors': []
        }]
    }

    from jql_validate import validate_jql

    result = validate_jql(mock_jira_client, 'summary ~ "recherche"')

    assert result['valid'] is True

# Pagination tests
def test_search_filters_pagination(self, mock_jira_client):
    """Test pagination through large filter sets."""
    mock_jira_client.search_filters.return_value = {
        'startAt': 0,
        'maxResults': 50,
        'total': 150,
        'isLast': False,
        'values': [{'id': str(i), 'name': f'Filter {i}'} for i in range(50)]
    }

    from get_filters import search_filters

    result = search_filters(mock_jira_client, filter_name='Filter')

    assert result['total'] == 150
    assert result['isLast'] is False
    assert len(result['values']) == 50
```

---

### 3.2 Unused Imports

**Impact:** Code hygiene, potential confusion
**Files Affected:** 8 files

| File | Line | Unused Import |
|------|------|---------------|
| `conftest.py` | 6 | `MagicMock` used but could use simpler `Mock` |
| `test_jql_fields.py` | 7 | `MagicMock` - only `patch` needed |
| `test_jql_functions.py` | 7 | `MagicMock` - only `patch` needed |
| `test_jql_validate.py` | 7 | `MagicMock` - only `patch` needed |
| `test_jql_build.py` | 7 | `MagicMock` - not used (no mocking in tests) |
| `test_create_filter.py` | 7 | `MagicMock` - not used directly |
| `test_get_filters.py` | 7 | `MagicMock` - not used directly |
| `test_update_filter.py` | 7 | `MagicMock` - not used directly |

**Remediation:**

```python
# Before:
from unittest.mock import MagicMock, patch

# After (where only patch is needed):
from unittest.mock import patch

# After (where neither is used):
# Remove the import entirely
```

---

### 3.3 Missing JSON/CSV Output Format Tests

**Impact:** Output formatting untested
**Files Affected:**

| File | Has Text Format Test | Has JSON Format Test | Has CSV Format Test |
|------|---------------------|---------------------|-------------------|
| `test_jql_fields.py` | Yes (line 65) | Yes (line 80) | No |
| `test_jql_functions.py` | Yes (line 66) | No | No |
| `test_jql_validate.py` | Yes (line 96) | No | No |
| `test_jql_suggest.py` | No | No | No |
| `test_jql_build.py` | Yes (line 78) | No | No |
| `test_get_filters.py` | Yes (line 86) | Yes (line 97) | No |

**Remediation - Add JSON output tests:**

```python
# test_jql_functions.py
def test_format_json_output(self, mock_jira_client, sample_autocomplete_data):
    """Test JSON output format."""
    from jql_functions import format_functions_json

    functions = sample_autocomplete_data['visibleFunctionNames']
    output = format_functions_json(functions)

    import json
    parsed = json.loads(output)
    assert isinstance(parsed, list)
    assert len(parsed) == 6
    assert parsed[0]['value'] == 'currentUser()'

# test_jql_suggest.py
def test_format_suggestions_text(self, mock_jira_client, sample_jql_suggestions):
    """Test text output format for suggestions."""
    from jql_suggest import format_suggestions_text

    output = format_suggestions_text(sample_jql_suggestions['results'])

    assert 'Open' in output
    assert 'In Progress' in output

def test_format_suggestions_json(self, mock_jira_client, sample_jql_suggestions):
    """Test JSON output format for suggestions."""
    from jql_suggest import format_suggestions_json

    output = format_suggestions_json(sample_jql_suggestions['results'])

    import json
    parsed = json.loads(output)
    assert isinstance(parsed, list)
    assert len(parsed) == 5
```

---

### 3.4 Test Isolation Issues - Import Side Effects

**Impact:** Tests may affect each other through import caching
**Files Affected:** All test files

**Current pattern (potential issue):**

```python
def test_some_function(self, mock_jira_client, sample_data):
    from module_name import function_name  # Import inside test
    result = function_name(mock_jira_client)
```

**Recommendation:** While importing inside tests is acceptable, ensure modules don't have side effects on import. Consider adding `importlib.reload()` for tests that need fresh module state:

```python
def test_with_fresh_module(self, mock_jira_client):
    """Test requiring fresh module state."""
    import importlib
    import jql_fields
    importlib.reload(jql_fields)

    result = jql_fields.get_fields(mock_jira_client)
```

---

## Phase 4: Low Priority Issues

### 4.1 Inconsistent Docstring Patterns

**Impact:** Documentation inconsistency
**Pattern to standardize:**

```python
# Preferred format:
def test_get_all_fields(self, mock_jira_client, sample_autocomplete_data):
    """Test fetching all searchable fields.

    Verifies that:
    - All fields from autocomplete data are returned
    - Field structure includes value and displayName
    - API is called exactly once
    """
```

---

### 4.2 Missing Type Hints in Test Functions

**Impact:** IDE support, code clarity
**Files Affected:** All test files

```python
# Current:
def test_get_all_fields(self, mock_jira_client, sample_autocomplete_data):

# Improved (optional):
def test_get_all_fields(
    self,
    mock_jira_client: MagicMock,
    sample_autocomplete_data: dict
) -> None:
```

---

### 4.3 Add Test Count Verification

**Impact:** Catch accidental test deletion

**Add to CI/CD or pre-commit:**

```python
# tests/test_coverage_check.py
import pytest
from pathlib import Path

def test_minimum_test_count():
    """Ensure test count doesn't regress."""
    test_dir = Path(__file__).parent
    test_files = list(test_dir.rglob('test_*.py'))

    # Count test functions
    test_count = 0
    for f in test_files:
        content = f.read_text()
        test_count += content.count('def test_')

    # Minimum expected tests (update as tests are added)
    MIN_TESTS = 60  # Current count ~60 tests
    assert test_count >= MIN_TESTS, f"Expected {MIN_TESTS}+ tests, found {test_count}"
```

---

### 4.4 Missing conftest.py Import for patch

**Impact:** Minor - each test file imports patch separately
**Optimization:** Add shared patch import to conftest.py

```python
# In conftest.py, add:
from unittest.mock import patch

@pytest.fixture
def mock_get_jira_client(mock_jira_client):
    """Fixture to patch get_jira_client."""
    with patch('config_manager.get_jira_client', return_value=mock_jira_client):
        yield mock_jira_client
```

---

## Implementation Checklist

### Phase 1 Checklist (Critical)

- [ ] Add `pytest_configure` to conftest.py for marker registration
- [ ] Add `@pytest.mark.search` and `@pytest.mark.unit` to all 12 test classes
- [ ] Fix fixture mutation in 5 files (use deepcopy)
- [ ] Update conftest.py fixtures to return copies
- [ ] Add CLI test class stubs to all test files (or document as TODO)

### Phase 2 Checklist (High Priority)

- [ ] Add API error handling tests to all 12 test files:
  - [ ] test_jql_fields.py - AuthenticationError, ForbiddenError, RateLimitError
  - [ ] test_jql_functions.py - AuthenticationError, ForbiddenError, RateLimitError
  - [ ] test_jql_validate.py - AuthenticationError, ForbiddenError, RateLimitError
  - [ ] test_jql_suggest.py - AuthenticationError, ForbiddenError, RateLimitError
  - [ ] test_jql_build.py - (validation errors only, no API calls)
  - [ ] test_create_filter.py - AuthenticationError, RateLimitError
  - [ ] test_get_filters.py - AuthenticationError, NotFoundError
  - [ ] test_favourite_filter.py - AuthenticationError (already has NotFoundError)
  - [ ] test_update_filter.py - AuthenticationError, RateLimitError (already has PermissionError, NotFoundError)
  - [ ] test_delete_filter.py - AuthenticationError, RateLimitError (already has PermissionError, NotFoundError)
  - [ ] test_share_filter.py - AuthenticationError, NotFoundError (already has PermissionError)
  - [ ] test_filter_subscriptions.py - AuthenticationError (already has NotFoundError)
- [ ] Add 3 missing dry-run tests (create_filter, update_filter, share_filter)
- [ ] Add error response fixtures to conftest.py

### Phase 3 Checklist (Medium Priority)

- [ ] Add 10+ edge case tests:
  - [ ] Empty results for fields, functions, filters
  - [ ] Max name length for filter creation
  - [ ] Empty clauses list for JQL builder
  - [ ] Special characters in JQL
  - [ ] Unicode in JQL validation
  - [ ] Invalid field name for suggestions
  - [ ] Pagination handling
- [ ] Remove unused imports from 8 files
- [ ] Add missing JSON output format tests to 4 files
- [ ] Add missing text output format tests to 1 file (test_jql_suggest.py)

### Phase 4 Checklist (Low Priority)

- [ ] Standardize docstring format
- [ ] Consider adding type hints to test functions
- [ ] Add test count verification script
- [ ] Add shared mock_get_jira_client fixture to conftest.py

---

## Verification Commands

```bash
# Run all search tests
pytest .claude/skills/jira-search/tests/ -v

# Run only unit tests
pytest .claude/skills/jira-search/tests/ -v -m unit

# Run only search skill tests
pytest .claude/skills/jira-search/tests/ -v -m search

# Check test count
pytest .claude/skills/jira-search/tests/ --collect-only | grep "test session starts" -A 5

# Verify no unused imports (requires pylint)
pylint .claude/skills/jira-search/tests/ --disable=all --enable=unused-import

# Check for fixture mutations
grep -rn "sample_filter\[" .claude/skills/jira-search/tests/
grep -rn "sample_autocomplete_data\[" .claude/skills/jira-search/tests/
```

---

## Success Criteria

1. **All tests pass:** `pytest` exits with code 0
2. **No fixture mutations:** grep commands for direct fixture assignment return no results
3. **Consistent markers:** All test classes have `@pytest.mark.search` and `@pytest.mark.unit`
4. **No pytest warnings:** About unknown markers
5. **Coverage maintained:** Test count >= 60
6. **Error handling covered:** Each file has tests for at least 401, 403, 404, 429 errors where applicable
7. **No unused imports:** pylint reports clean

---

## Test File Summary

| File | Tests | Markers | Mutations | Error Tests | Dry-Run | Output Tests |
|------|-------|---------|-----------|-------------|---------|--------------|
| `conftest.py` | 12 fixtures | - | - | - | - | - |
| `test_jql_fields.py` | 6 | Missing | None | Missing | N/A | Text, JSON |
| `test_jql_functions.py` | 5 | Missing | None | Missing | N/A | Text only |
| `test_jql_validate.py` | 7 | Missing | None | Missing | N/A | Text only |
| `test_jql_suggest.py` | 6 | Missing | None | Missing | N/A | None |
| `test_jql_build.py` | 6 | Missing | None | Partial | N/A | Text only |
| `test_create_filter.py` | 7 | Missing | 4 | Partial | Missing | None |
| `test_get_filters.py` | 7 | Missing | None | Missing | N/A | Text, JSON |
| `test_favourite_filter.py` | 5 | Missing | 2 | Partial | N/A | None |
| `test_update_filter.py` | 7 | Missing | 4 | Partial | Missing | None |
| `test_delete_filter.py` | 5 | Missing | None | Good | Good | None |
| `test_share_filter.py` | 10 | Missing | None | Partial | Missing | None |
| `test_filter_subscriptions.py` | 4 | Missing | None | Partial | N/A | None |

**Total current tests:** ~75
**Target after remediation:** ~120+

---

## Notes

- Prioritize Phase 1 before merging to main
- Phase 2 should be completed before next release
- Phases 3-4 can be addressed incrementally
- Consider adding pre-commit hooks to prevent regression
- The jira-search skill tests are relatively well-structured but lack comprehensive error handling coverage
