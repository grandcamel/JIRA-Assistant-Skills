# Test Remediation Plan: jira-relationships Skill

**Created:** 2025-12-26
**Status:** Draft
**Test Files Reviewed:** 9
**Total Issues Identified:** ~65

---

## Executive Summary

This plan addresses test quality issues discovered during a comprehensive review of the `jira-relationships` skill test suite. Issues are organized by priority and grouped into actionable phases.

**Issue Summary:**
| Category | Count | Files Affected |
|----------|-------|----------------|
| Missing pytest markers | 11 classes | All 8 test files |
| Missing error handling tests | 24+ | All 8 test files |
| Weak/OR assertions | 8 | 4 test files |
| Missing dry-run tests | 2 | 2 test files |
| Fixture mutation risks | 3 | 2 test files |
| API signature mismatches | 4 | 3 test files |
| Missing edge case tests | 10 | 5 test files |
| Unused imports | 4 | 4 test files |

**Estimated Effort:**
- Phase 1 (Critical): 2-3 hours
- Phase 2 (High Priority): 3-4 hours
- Phase 3 (Medium Priority): 4-5 hours
- Phase 4 (Low Priority): 1-2 hours

---

## Phase 1: Critical Issues (Must Fix)

### 1.1 Missing pytest Marker Registration

**Impact:** pytest warnings, inconsistent test selection
**File:** `tests/conftest.py`

**Current (missing):** No `pytest_configure` function

**Add at top of conftest.py (after imports):**

```python
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "relationships: mark test as relationships skill test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
```

---

### 1.2 Missing pytest Markers on Test Classes

**Impact:** Inconsistent test categorization, cannot run tests by marker
**Files Affected:** All 8 test files, 11 test classes total

| File | Line | Class |
|------|------|-------|
| `test_get_link_types.py` | 12 | `TestGetLinkTypes` |
| `test_link_issue.py` | 13 | `TestLinkIssue` |
| `test_unlink_issue.py` | 11 | `TestUnlinkIssue` |
| `test_get_blockers.py` | 82 | `TestGetBlockers` |
| `test_get_dependencies.py` | 12 | `TestGetDependencies` |
| `test_bulk_link.py` | 40 | `TestBulkLink` |
| `test_bulk_link.py` | 157 | `TestBulkLinkFormat` |
| `test_clone_issue.py` | 94 | `TestCloneIssue` |
| `test_clone_issue.py` | 217 | `TestCloneIssueFormat` |
| `test_get_links.py` | 12 | `TestGetLinks` |

**Remediation:**

```python
# Add to each test class:
@pytest.mark.relationships
@pytest.mark.unit
class TestClassName:
    """Test description."""
```

**Example fix for test_link_issue.py line 13:**

```python
# Before:
class TestLinkIssue:
    """Tests for the link_issue function."""

# After:
@pytest.mark.relationships
@pytest.mark.unit
class TestLinkIssue:
    """Tests for the link_issue function."""
```

---

### 1.3 Weak Assertions That Always Pass

**Impact:** Tests pass even when functionality is broken
**Files Affected:** 4 files, 8 assertions

| File | Line | Current Assertion | Issue | Fix |
|------|------|-------------------|-------|-----|
| `test_get_blockers.py` | 107 | `assert 'blocking' in result or 'blockers' in result` | OR always passes if blockers exists | `assert 'blockers' in result` |
| `test_get_blockers.py` | 121-122 | `all_blockers = result.get('all_blockers', result.get('blockers', []))` | Silently uses fallback | Check which key exists explicitly |
| `test_get_blockers.py` | 137-138 | Same fallback pattern | Silently uses fallback | Check which key exists explicitly |
| `test_get_blockers.py` | 153 | `assert result.get('circular', False) or 'circular' in str(result).lower()` | String check is weak fallback | `assert result.get('circular') is True` |
| `test_get_blockers.py` | 182 | `assert 'blockers' in parsed or isinstance(parsed, list)` | OR allows wrong structure | `assert 'blockers' in parsed` |
| `test_get_dependencies.py` | 61 | `assert 'graph' in output.lower() or 'flowchart' in output.lower()` | OR - unclear expected format | Choose one expected format |
| `test_clone_issue.py` | 115 | `assert 'PROJ-123' in fields['summary'] or 'Clone' in fields['summary'] or ...` | Triple OR - too permissive | Pick the actual expected format |
| `test_clone_issue.py` | 167-168 | `assert mock_jira_client.create_issue.call_count >= 1` | `>= 1` - should check exact count | `assert mock_jira_client.create_issue.call_count == 3` |

**Remediation Template:**

```python
# Before (weak):
assert 'blocking' in result or 'blockers' in result

# After (strong):
assert 'blockers' in result
assert len(result['blockers']) >= 0  # Or expected count
```

**test_get_blockers.py line 107:**

```python
# Before:
assert 'blocking' in result or 'blockers' in result

# After:
# For outward direction, result should still have 'blockers' key
# but containing issues that the source blocks
assert 'blockers' in result
# Outward blockers are found in outwardIssue links
outward_blockers = [b for b in result['blockers']]
assert len(outward_blockers) >= 0
```

**test_clone_issue.py line 115:**

```python
# Before:
assert 'PROJ-123' in fields['summary'] or 'Clone' in fields['summary'] or sample_issue['fields']['summary'] in fields['summary']

# After - match actual implementation in clone_issue.py line 58:
assert fields['summary'] == f"[Clone of PROJ-123] {sample_issue['fields']['summary']}"
```

---

### 1.4 API Signature Mismatches

**Impact:** Tests mock wrong function signatures, may not catch real bugs
**Files Affected:** 3 files

| File | Line | Test Expects | Actual Script Signature | Issue |
|------|------|--------------|-------------------------|-------|
| `test_link_issue.py` | 27-28 | `create_link("Blocks", "PROJ-2", "PROJ-1", None)` | Script calls `create_link(link_type, inward_key, outward_key, comment)` | Order depends on direction logic |
| `test_bulk_link.py` | 102 | `create_link(link_type, issue_key, target)` | Actual: `create_link(link_type, issue_key, target)` - 3 args | Should verify all 3 args |
| `test_clone_issue.py` | 133-135 | Check `link_call[0]` positional args | Actual: `create_link('Cloners', clone_key, issue_key)` | Args order verification |

**Remediation for test_link_issue.py lines 27-28:**

```python
# Current test expects:
mock_jira_client.create_link.assert_called_once_with(
    "Blocks", "PROJ-2", "PROJ-1", None
)

# But link_issue.py line 170 calls:
# client.create_link(link_type_obj['name'], inward_key, outward_key, adf_comment)
# For "PROJ-1 --blocks PROJ-2":
#   inward_key = PROJ-2 (is blocked by)
#   outward_key = PROJ-1 (blocks)

# Fix - verify the correct parameter order based on direction logic:
mock_jira_client.create_link.assert_called_once_with(
    "Blocks",  # link_type
    "PROJ-2",  # inward_key (target that "is blocked by")
    "PROJ-1",  # outward_key (source that "blocks")
    None       # comment
)
```

---

## Phase 2: High Priority Issues

### 2.1 Missing API Error Handling Tests

**Impact:** Error scenarios untested, poor user experience on failures
**Files Affected:** All 8 test files
**Coverage Gap:** All test files missing tests for:
- `AuthenticationError` (401)
- `ForbiddenError` (403)
- Rate limiting (429)
- Server errors (500, 502, 503)
- Network timeout/connection errors

| File | Missing Error Tests |
|------|---------------------|
| `test_get_link_types.py` | 401, 403, 429, 500, timeout |
| `test_link_issue.py` | 401, 403, 404 (issue not found), 429, 500 |
| `test_unlink_issue.py` | 401, 403, 404 (link not found), 429, 500 |
| `test_get_blockers.py` | 401, 403, 404, 429, 500, timeout |
| `test_get_dependencies.py` | 401, 403, 404, 429, 500 |
| `test_bulk_link.py` | 401, 403, 429, 500 (separate from partial failure) |
| `test_clone_issue.py` | 401, 403, 404, 429, 500 |
| `test_get_links.py` | 401, 403, 429, 500 (has 404 test) |

**Remediation Template - add to each test file:**

```python
class TestApiErrorHandling:
    """Test API error handling scenarios."""

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from error_handler import AuthenticationError
        mock_jira_client.get_link_types.side_effect = AuthenticationError("Invalid token")

        import get_link_types
        with patch.object(get_link_types, 'get_jira_client', return_value=mock_jira_client):
            with pytest.raises(AuthenticationError):
                get_link_types.get_link_types()

    def test_forbidden_error(self, mock_jira_client):
        """Test handling of 403 forbidden."""
        from error_handler import ForbiddenError
        mock_jira_client.get_link_types.side_effect = ForbiddenError("Insufficient permissions")

        import get_link_types
        with patch.object(get_link_types, 'get_jira_client', return_value=mock_jira_client):
            with pytest.raises(ForbiddenError):
                get_link_types.get_link_types()

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from error_handler import JiraError
        mock_jira_client.get_link_types.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        import get_link_types
        with patch.object(get_link_types, 'get_jira_client', return_value=mock_jira_client):
            with pytest.raises(JiraError) as exc_info:
                get_link_types.get_link_types()
            assert exc_info.value.status_code == 429

    def test_server_error(self, mock_jira_client):
        """Test handling of 500 server error."""
        from error_handler import JiraError
        mock_jira_client.get_link_types.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        import get_link_types
        with patch.object(get_link_types, 'get_jira_client', return_value=mock_jira_client):
            with pytest.raises(JiraError) as exc_info:
                get_link_types.get_link_types()
            assert exc_info.value.status_code == 500
```

---

### 2.2 Missing Dry-Run Tests

**Impact:** Dry-run feature untested for critical operations
**Files Affected:** 2

| Script | Test File | Current State | Missing |
|--------|-----------|---------------|---------|
| `clone_issue.py` | `test_clone_issue.py` | No dry-run support in script | Consider adding dry-run to script |
| `unlink_issue.py` | `test_unlink_issue.py` | Has dry-run test (line 62-77) | OK |
| `bulk_link.py` | `test_bulk_link.py` | Has dry-run test (line 78-93) | OK |
| `get_blockers.py` | `test_get_blockers.py` | No dry-run in script (read-only) | N/A |

**Note:** `clone_issue.py` modifies data but has no dry-run support. Consider adding dry-run to the script and corresponding test.

**Proposed test for clone_issue dry-run (after script updated):**

```python
def test_clone_dry_run(self, mock_jira_client, sample_issue):
    """Test dry-run mode shows preview without creating."""
    mock_jira_client.get_issue.return_value = sample_issue

    import clone_issue
    with patch.object(clone_issue, 'get_jira_client', return_value=mock_jira_client):
        result = clone_issue.clone_issue('PROJ-123', dry_run=True)

    # Should NOT create any issues
    mock_jira_client.create_issue.assert_not_called()
    mock_jira_client.create_link.assert_not_called()

    # Should return preview info
    assert result.get('dry_run') is True
    assert 'would_clone' in result
    assert result['original_key'] == 'PROJ-123'
```

---

### 2.3 Missing Edge Case Tests

**Impact:** Edge cases not covered, potential runtime errors
**Files Affected:** 5 test files

| File | Missing Edge Case | Severity |
|------|-------------------|----------|
| `test_get_link_types.py` | Empty link types response | High |
| `test_get_link_types.py` | Filter pattern matches nothing | Medium |
| `test_link_issue.py` | Multiple link types with same partial name | High |
| `test_link_issue.py` | Issue already linked (duplicate link) | Medium |
| `test_unlink_issue.py` | Multiple matching links when removing | High |
| `test_get_blockers.py` | Very deep blocker chain (performance) | Medium |
| `test_get_blockers.py` | Blocker with missing status field | Medium |
| `test_bulk_link.py` | Empty JQL results | High |
| `test_bulk_link.py` | JQL returns > 100 results (pagination) | High |
| `test_clone_issue.py` | Clone issue with unsupported field types | Medium |

**Remediation - test_get_link_types.py:**

```python
def test_empty_link_types(self, mock_jira_client):
    """Test handling when no link types exist."""
    mock_jira_client.get_link_types.return_value = []

    import get_link_types
    with patch.object(get_link_types, 'get_jira_client', return_value=mock_jira_client):
        result = get_link_types.get_link_types()

    assert result == []

def test_filter_matches_nothing(self, mock_jira_client, sample_link_types):
    """Test filter that matches no link types."""
    mock_jira_client.get_link_types.return_value = sample_link_types

    import get_link_types
    with patch.object(get_link_types, 'get_jira_client', return_value=mock_jira_client):
        result = get_link_types.get_link_types(filter_pattern='nonexistent')

    assert result == []
```

**Remediation - test_bulk_link.py:**

```python
def test_empty_jql_results(self, mock_jira_client):
    """Test JQL that returns no results."""
    mock_jira_client.search_issues.return_value = {'issues': [], 'total': 0}

    import bulk_link
    with patch.object(bulk_link, 'get_jira_client', return_value=mock_jira_client):
        result = bulk_link.bulk_link(
            jql='project = NONEXISTENT',
            target='PROJ-100',
            link_type='Blocks'
        )

    assert result['created'] == 0
    assert result['failed'] == 0
    mock_jira_client.create_link.assert_not_called()
```

---

## Phase 3: Medium Priority Issues

### 3.1 Fixture Mutation Risks

**Impact:** Potential test pollution between tests
**Files Affected:** 2

| File | Line | Fixture | Issue |
|------|------|---------|-------|
| `test_clone_issue.py` | 198-203 | `created_clone` | Modified in test (`created_clone['key'] = 'OTHER-999'`) |
| `conftest.py` | 134-146 | `sample_issue_with_links` | Uses `sample_issue_links` directly (no deepcopy) |
| `test_get_blockers.py` | 12-51 | `blocker_chain_links` | Dict accessed/modified in tests |

**Remediation for test_clone_issue.py line 198-203:**

```python
# Before:
def test_clone_to_different_project(self, mock_jira_client, sample_issue, created_clone):
    """Test cloning to different project."""
    mock_jira_client.get_issue.return_value = sample_issue
    # Clone goes to OTHER project
    created_clone['key'] = 'OTHER-999'  # MUTATES FIXTURE!
    mock_jira_client.create_issue.return_value = created_clone

# After:
def test_clone_to_different_project(self, mock_jira_client, sample_issue, created_clone):
    """Test cloning to different project."""
    import copy
    mock_jira_client.get_issue.return_value = sample_issue
    # Clone goes to OTHER project - use deepcopy to avoid mutation
    other_clone = copy.deepcopy(created_clone)
    other_clone['key'] = 'OTHER-999'
    mock_jira_client.create_issue.return_value = other_clone
```

**Remediation for conftest.py line 134:**

```python
# Before:
@pytest.fixture
def sample_issue_with_links(sample_issue_links):
    """Sample JIRA issue response with links."""
    return {
        ...
        "fields": {
            ...
            "issuelinks": sample_issue_links  # Direct reference!
        }
    }

# After:
@pytest.fixture
def sample_issue_with_links(sample_issue_links):
    """Sample JIRA issue response with links."""
    import copy
    return {
        ...
        "fields": {
            ...
            "issuelinks": copy.deepcopy(sample_issue_links)  # Safe copy
        }
    }
```

---

### 3.2 Missing JSON Output Format Validation

**Impact:** JSON output format may be incorrect
**Files Affected:** 3

| File | Test | Issue |
|------|------|-------|
| `test_get_blockers.py` | `test_blockers_json_format` | Only checks `'blockers' in parsed or isinstance(parsed, list)` |
| `test_get_dependencies.py` | Missing JSON format test | No JSON output validation |
| `test_clone_issue.py` | `test_format_json_output` | Only checks `'clone_key' in parsed` |

**Remediation for test_get_dependencies.py - add new test:**

```python
def test_format_json_output(self, mock_jira_client, sample_issue_links):
    """Test JSON output format."""
    mock_jira_client.get_issue_links.return_value = sample_issue_links

    import get_dependencies
    import json
    with patch.object(get_dependencies, 'get_jira_client', return_value=mock_jira_client):
        result = get_dependencies.get_dependencies("PROJ-123")
        output = get_dependencies.format_dependencies(result, output_format='json')

    # Should be valid JSON
    parsed = json.loads(output)
    assert isinstance(parsed, dict)
    assert 'dependencies' in parsed
    assert 'status_summary' in parsed
```

---

### 3.3 Incomplete Test Coverage for Format Functions

**Impact:** Output formatting may break without detection
**Files Affected:** 2

| File | Function | Missing Tests |
|------|----------|---------------|
| `test_get_blockers.py` | `format_blockers` | CSV format (if supported) |
| `test_get_dependencies.py` | `format_dependencies` | text format, JSON format |

**Remediation for test_get_dependencies.py:**

```python
def test_format_text_output(self, mock_jira_client, sample_issue_links):
    """Test human-readable text output."""
    mock_jira_client.get_issue_links.return_value = sample_issue_links

    import get_dependencies
    with patch.object(get_dependencies, 'get_jira_client', return_value=mock_jira_client):
        result = get_dependencies.get_dependencies("PROJ-123")
        output = get_dependencies.format_dependencies(result, output_format='text')

    # Should contain issue info
    assert 'PROJ-123' in output
    assert 'dependencies' in output.lower() or 'linked' in output.lower()
```

---

### 3.4 Tests Missing Assertions on Mock Call Arguments

**Impact:** Tests may pass with wrong function arguments
**Files Affected:** 4

| File | Line | Issue |
|------|------|-------|
| `test_link_issue.py` | 147 | `assert_called_once()` without verifying arguments |
| `test_clone_issue.py` | 108-109 | Checks `assert_called_once()` but not specific arguments |
| `test_get_links.py` | 24 | Good - verifies argument |
| `test_bulk_link.py` | 74 | `assert_called_once()` without argument check |

**Remediation for test_link_issue.py line 147:**

```python
# Before:
mock_jira_client.create_link.assert_called_once()

# After:
mock_jira_client.create_link.assert_called_once_with(
    "Blocks",  # link_type from link_type_obj['name']
    "PROJ-2",  # inward_key
    "PROJ-1",  # outward_key
    None       # comment
)
```

---

## Phase 4: Low Priority Issues

### 4.1 Remove Unused Imports

**Impact:** Code hygiene
**Files Affected:** 4

| File | Line | Unused Import |
|------|------|---------------|
| `test_link_issue.py` | 8 | `Mock` (only `patch` used from unittest.mock) |
| `test_unlink_issue.py` | 8 | `call` imported but not used |
| `test_bulk_link.py` | 8 | `call` imported but not used |
| `test_clone_issue.py` | 8 | `call` imported but not used |

**Remediation:**

```python
# Before:
from unittest.mock import Mock, patch, call

# After:
from unittest.mock import patch  # Only import what's used
```

---

### 4.2 Inconsistent Import Patterns

**Impact:** Maintenance burden
**Files Affected:** All test files

**Current pattern (repeated in each test method):**

```python
def test_something(self, mock_jira_client, ...):
    import get_link_types  # Import inside test
    with patch.object(get_link_types, 'get_jira_client', ...):
        result = get_link_types.get_link_types()
```

**Recommended pattern (import at module level):**

```python
# At top of file, after sys.path setup
import get_link_types

class TestGetLinkTypes:
    def test_something(self, mock_jira_client, ...):
        with patch.object(get_link_types, 'get_jira_client', ...):
            result = get_link_types.get_link_types()
```

**Note:** The current pattern works and is safe. Consider standardizing for consistency with other skills.

---

### 4.3 Add Docstrings to Test Classes

**Impact:** Documentation quality
**Files with minimal class docstrings:** All files have basic docstrings

**Current (acceptable):**

```python
class TestGetLinkTypes:
    """Tests for the get_link_types function."""
```

**Recommended (more descriptive):**

```python
class TestGetLinkTypes:
    """
    Tests for the get_link_types function.

    Tests cover:
    - Fetching all available link types
    - Required field validation
    - Text and JSON output formatting
    - Name filtering
    """
```

---

## Implementation Checklist

### Phase 1 Checklist (Critical)

- [ ] Add `pytest_configure` to `tests/conftest.py`
- [ ] Add `@pytest.mark.relationships` and `@pytest.mark.unit` to all 11 test classes
- [ ] Fix 8 weak/OR assertions in 4 test files
- [ ] Fix 4 API signature mismatches in 3 test files

### Phase 2 Checklist (High Priority)

- [ ] Add error handling tests to all 8 test files (401, 403, 429, 500)
- [ ] Add dry-run support to `clone_issue.py` and corresponding test
- [ ] Add 10 edge case tests across 5 files

### Phase 3 Checklist (Medium Priority)

- [ ] Fix fixture mutations in 3 locations
- [ ] Add JSON format validation to `test_get_dependencies.py`
- [ ] Add text format test to `test_get_dependencies.py`
- [ ] Add argument assertions to 3 test files

### Phase 4 Checklist (Low Priority)

- [ ] Remove unused imports from 4 files
- [ ] Consider standardizing import pattern (optional)
- [ ] Enhance class docstrings (optional)

---

## Verification Commands

```bash
# Run all relationships tests
pytest .claude/skills/jira-relationships/tests/ -v

# Run only unit tests (after markers added)
pytest .claude/skills/jira-relationships/tests/ -v -m unit

# Run only relationships tests
pytest .claude/skills/jira-relationships/tests/ -v -m relationships

# Check test count
pytest .claude/skills/jira-relationships/tests/ --collect-only | grep "test session starts" -A 5

# Check for weak assertions
grep -rn "assert.*or.*assert\|>= 0\|is not None or.*is None" .claude/skills/jira-relationships/tests/

# Check for unused imports (requires pylint)
pylint .claude/skills/jira-relationships/tests/ --disable=all --enable=unused-import

# Run with coverage
pytest .claude/skills/jira-relationships/tests/ -v --cov=.claude/skills/jira-relationships/scripts --cov-report=term-missing
```

---

## Success Criteria

1. **All tests pass:** `pytest` exits with code 0
2. **No weak assertions:** grep commands return no results
3. **Consistent markers:** All test classes have `@pytest.mark.relationships` and `@pytest.mark.unit`
4. **No pytest warnings:** About unknown markers
5. **Error handling coverage:** Each test file has tests for 401, 403, 429, 500 errors
6. **No fixture mutation:** All mutable fixtures use deepcopy
7. **No unused imports:** pylint reports clean

---

## File-by-File Summary

### tests/conftest.py
- **Issues:** Missing pytest_configure, fixture mutation risk
- **Fixes:** Add pytest_configure, use deepcopy for sample_issue_with_links
- **Effort:** 15 minutes

### tests/test_get_link_types.py
- **Issues:** Missing markers, missing error tests, missing edge cases
- **Fixes:** Add markers, add error handling tests, add empty response test
- **Effort:** 30 minutes

### tests/test_link_issue.py
- **Issues:** Missing markers, API signature mismatch, unused import, missing error tests
- **Fixes:** Add markers, fix create_link argument order, remove unused Mock, add error tests
- **Effort:** 45 minutes

### tests/test_unlink_issue.py
- **Issues:** Missing markers, unused import, missing error tests
- **Fixes:** Add markers, remove unused call import, add error tests
- **Effort:** 30 minutes

### tests/test_get_blockers.py
- **Issues:** Missing markers, 5 weak assertions, fixture mutation, missing error tests
- **Fixes:** Add markers, fix assertions, use deepcopy, add error tests
- **Effort:** 45 minutes

### tests/test_get_dependencies.py
- **Issues:** Missing markers, weak assertion, missing format tests, missing error tests
- **Fixes:** Add markers, fix mermaid assertion, add text/JSON tests, add error tests
- **Effort:** 45 minutes

### tests/test_bulk_link.py
- **Issues:** Missing markers (2 classes), unused import, missing edge cases
- **Fixes:** Add markers, remove unused call, add empty JQL test
- **Effort:** 30 minutes

### tests/test_clone_issue.py
- **Issues:** Missing markers (2 classes), weak assertions, fixture mutation, unused import
- **Fixes:** Add markers, fix assertions, use deepcopy, remove unused call
- **Effort:** 45 minutes

### tests/test_get_links.py
- **Issues:** Missing markers, missing error tests
- **Fixes:** Add markers, add error tests (already has 404 test - good)
- **Effort:** 20 minutes

---

## Notes

- Prioritize Phase 1 before merging to main
- Phase 2 should be completed before next release
- Phases 3-4 can be addressed incrementally
- Consider adding pre-commit hooks to prevent regression
- The jira-relationships tests are generally well-structured with good coverage of happy paths
- Main gaps are in error handling and edge cases
