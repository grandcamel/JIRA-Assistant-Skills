# Test Remediation Plan: jira-time Skill

**Created:** 2025-12-26
**Status:** Draft
**Test Files Reviewed:** 10
**Total Issues Identified:** ~85

---

## Executive Summary

This plan addresses test quality issues discovered during a comprehensive review of the `jira-time` skill test suite. Issues are organized by priority and grouped into actionable phases.

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

**Add at top of conftest.py (after line 8):**

```python
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "time: mark test as time tracking skill test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
```

---

### 1.2 Missing pytest Markers on All Test Classes

**Impact:** Inconsistent test categorization, cannot filter tests by type
**Files Affected:** 9 test files (all test files)

| File | Classes Missing Markers | Lines |
|------|------------------------|-------|
| `test_add_worklog.py` | 6 classes | 18, 47, 79, 100, 143, 165 |
| `test_get_worklogs.py` | 5 classes | 18, 43, 75, 113, 127 |
| `test_update_worklog.py` | 2 classes | 18, 87 |
| `test_delete_worklog.py` | 3 classes | 18, 49, 69 |
| `test_set_estimate.py` | 3 classes | 18, 83, 103 |
| `test_get_time_tracking.py` | 2 classes | 18, 59 |
| `test_export_timesheets.py` | 2 classes | 54, 99 |
| `test_time_report.py` | 4 classes | 63, 116, 169, 202 |
| `test_bulk_log_time.py` | 4 classes | 18, 53, 78, 105 |

**Remediation:**

```python
# Add to each test class:
@pytest.mark.time
@pytest.mark.unit
class TestClassName:
    """Test description."""
```

**Example for test_add_worklog.py line 18:**

```python
# Before:
class TestAddWorklogTimeSpent:
    """Tests for basic time logging."""

# After:
@pytest.mark.time
@pytest.mark.unit
class TestAddWorklogTimeSpent:
    """Tests for basic time logging."""
```

---

### 1.3 Fixture Mutation Risk in conftest.py

**Impact:** Potential test pollution between tests using shared fixtures
**File:** `tests/conftest.py` lines 74-151

The `sample_worklogs` fixture mutates `sample_worklog` by embedding it directly in the list. While pytest creates new fixture instances per test by default, the nested structure creates a risk.

**Current (line 74-78):**

```python
@pytest.fixture
def sample_worklogs(sample_worklog):
    """Sample list of worklogs for an issue."""
    return {
        "startAt": 0,
        # ... sample_worklog is embedded directly
```

**Remediation - Option A (use deepcopy in fixture):**

```python
import copy

@pytest.fixture
def sample_worklogs(sample_worklog):
    """Sample list of worklogs for an issue."""
    worklog_copy = copy.deepcopy(sample_worklog)
    return {
        "startAt": 0,
        "maxResults": 20,
        "total": 3,
        "worklogs": [
            worklog_copy,
            # ... rest of worklogs
        ]
    }
```

**Remediation - Option B (return fresh dict each time):**

```python
@pytest.fixture
def sample_worklogs():
    """Sample list of worklogs for an issue - creates fresh data each call."""
    def _make_worklog(id, author_email, author_name, time_spent, seconds, date, comment):
        return {
            "id": id,
            "author": {"emailAddress": author_email, "displayName": author_name, "active": True},
            # ... full structure
        }

    return {
        "startAt": 0,
        "maxResults": 20,
        "total": 3,
        "worklogs": [
            _make_worklog("10045", "alice@company.com", "Alice Smith", "2h", 7200, "2025-01-15", "Debugging"),
            _make_worklog("10046", "bob@company.com", "Bob Jones", "1h 30m", 5400, "2025-01-15", "Code review"),
            _make_worklog("10047", "alice@company.com", "Alice Smith", "4h", 14400, "2025-01-16", "Implemented fix"),
        ]
    }
```

---

### 1.4 Missing deepcopy in Tests That Modify Fixtures

**Impact:** Test pollution between tests
**Files Affected:** 2

| File | Line | Issue |
|------|------|-------|
| `test_update_worklog.py` | 23 | `{**sample_worklog, ...}` creates shallow copy |
| `test_update_worklog.py` | 39 | `{**sample_worklog, ...}` creates shallow copy |

**Current (line 23):**

```python
def test_update_worklog_time(self, mock_jira_client, sample_worklog):
    """Test updating time spent."""
    updated_worklog = {**sample_worklog, 'timeSpent': '3h', 'timeSpentSeconds': 10800}
```

**Remediation:**

```python
import copy

def test_update_worklog_time(self, mock_jira_client, sample_worklog):
    """Test updating time spent."""
    updated_worklog = copy.deepcopy(sample_worklog)
    updated_worklog.update({'timeSpent': '3h', 'timeSpentSeconds': 10800})
```

---

## Phase 2: High Priority Issues

### 2.1 Missing API Error Handling Tests (401, 403, 429, 500)

**Impact:** Error scenarios untested, poor user experience on failures
**Coverage Gap:** All test files are missing tests for:
- `AuthenticationError` (401)
- `PermissionDeniedError` (403)
- Rate limiting (429)
- Server errors (500)
- Network timeout/connection errors

**Files to Update:** All 9 test files

| File | Missing Error Tests |
|------|---------------------|
| `test_add_worklog.py` | 401, 403, 429, 500 |
| `test_get_worklogs.py` | 401, 403, 429, 500 |
| `test_update_worklog.py` | 401, 429, 500 |
| `test_delete_worklog.py` | 401, 403, 429, 500 |
| `test_set_estimate.py` | 401, 403, 429, 500 |
| `test_get_time_tracking.py` | ALL (no error tests) |
| `test_export_timesheets.py` | ALL (no error tests) |
| `test_time_report.py` | ALL (no error tests) |
| `test_bulk_log_time.py` | 401, 429, 500 |

**Remediation Template - Add to each test file:**

```python
class TestApiErrorHandling:
    """Test API error handling scenarios."""

    @pytest.mark.time
    @pytest.mark.unit
    def test_authentication_error_401(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from error_handler import AuthenticationError
        mock_jira_client.add_worklog.side_effect = AuthenticationError("Invalid token")

        from add_worklog import add_worklog
        with pytest.raises(AuthenticationError):
            add_worklog(mock_jira_client, 'PROJ-123', '2h')

    @pytest.mark.time
    @pytest.mark.unit
    def test_permission_denied_403(self, mock_jira_client):
        """Test handling of 403 forbidden."""
        from error_handler import PermissionDeniedError
        mock_jira_client.add_worklog.side_effect = PermissionDeniedError(
            "You do not have permission to log work on this issue"
        )

        from add_worklog import add_worklog
        with pytest.raises(PermissionDeniedError):
            add_worklog(mock_jira_client, 'PROJ-123', '2h')

    @pytest.mark.time
    @pytest.mark.unit
    def test_rate_limit_error_429(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from error_handler import JiraError
        mock_jira_client.add_worklog.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        from add_worklog import add_worklog
        with pytest.raises(JiraError) as exc_info:
            add_worklog(mock_jira_client, 'PROJ-123', '2h')
        assert exc_info.value.status_code == 429

    @pytest.mark.time
    @pytest.mark.unit
    def test_server_error_500(self, mock_jira_client):
        """Test handling of 500 server error."""
        from error_handler import JiraError
        mock_jira_client.add_worklog.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        from add_worklog import add_worklog
        with pytest.raises(JiraError) as exc_info:
            add_worklog(mock_jira_client, 'PROJ-123', '2h')
        assert exc_info.value.status_code == 500

    @pytest.mark.time
    @pytest.mark.unit
    def test_network_timeout(self, mock_jira_client):
        """Test handling of network timeout."""
        from error_handler import JiraError
        mock_jira_client.add_worklog.side_effect = JiraError("Connection timeout")

        from add_worklog import add_worklog
        with pytest.raises(JiraError):
            add_worklog(mock_jira_client, 'PROJ-123', '2h')
```

---

### 2.2 Missing Time Validation Edge Cases

**Impact:** Invalid time inputs may not be properly rejected
**Files Affected:** 3 files

| File | Missing Edge Case | Lines |
|------|-------------------|-------|
| `test_add_worklog.py` | Zero time, negative time, fractional values, boundary values | After 162 |
| `test_set_estimate.py` | Zero estimate, max estimate, invalid characters | After 100 |
| `test_bulk_log_time.py` | Zero time for bulk, empty issue list | After 129 |

**Remediation - Add to test_add_worklog.py:**

```python
class TestAddWorklogTimeValidationEdgeCases:
    """Tests for time format edge cases."""

    @pytest.mark.time
    @pytest.mark.unit
    def test_add_worklog_zero_time(self, mock_jira_client):
        """Test validation rejects zero time."""
        from add_worklog import add_worklog
        from error_handler import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            add_worklog(mock_jira_client, 'PROJ-123', '0h')
        assert 'zero' in str(exc_info.value).lower() or 'invalid' in str(exc_info.value).lower()

    @pytest.mark.time
    @pytest.mark.unit
    def test_add_worklog_negative_time(self, mock_jira_client):
        """Test validation rejects negative time."""
        from add_worklog import add_worklog
        from error_handler import ValidationError

        with pytest.raises(ValidationError):
            add_worklog(mock_jira_client, 'PROJ-123', '-2h')

    @pytest.mark.time
    @pytest.mark.unit
    def test_add_worklog_max_time_boundary(self, mock_jira_client, sample_worklog):
        """Test maximum allowed time value (e.g., 52w or JIRA's max)."""
        mock_jira_client.add_worklog.return_value = sample_worklog

        from add_worklog import add_worklog
        # JIRA typically allows up to 52 weeks
        result = add_worklog(mock_jira_client, 'PROJ-123', '52w')
        assert mock_jira_client.add_worklog.called

    @pytest.mark.time
    @pytest.mark.unit
    def test_add_worklog_invalid_characters(self, mock_jira_client):
        """Test validation rejects special characters in time."""
        from add_worklog import add_worklog
        from error_handler import ValidationError

        for invalid in ['2h!', '2h@30m', '2h 30m;', '2h--30m']:
            with pytest.raises(ValidationError):
                add_worklog(mock_jira_client, 'PROJ-123', invalid)

    @pytest.mark.time
    @pytest.mark.unit
    def test_add_worklog_whitespace_only(self, mock_jira_client):
        """Test validation rejects whitespace-only time."""
        from add_worklog import add_worklog
        from error_handler import ValidationError

        with pytest.raises(ValidationError):
            add_worklog(mock_jira_client, 'PROJ-123', '   ')

    @pytest.mark.time
    @pytest.mark.unit
    def test_add_worklog_mixed_case_time_units(self, mock_jira_client, sample_worklog):
        """Test that time units are case-insensitive."""
        mock_jira_client.add_worklog.return_value = sample_worklog

        from add_worklog import add_worklog
        # Should accept uppercase/mixed case
        for time_str in ['2H', '2h 30M', '1D', '1W']:
            add_worklog(mock_jira_client, 'PROJ-123', time_str)
```

**Remediation - Add to test_set_estimate.py:**

```python
class TestSetEstimateEdgeCases:
    """Tests for estimate edge cases."""

    @pytest.mark.time
    @pytest.mark.unit
    def test_set_estimate_zero_original(self, mock_jira_client):
        """Test setting zero original estimate clears it."""
        mock_jira_client.set_time_tracking.return_value = None
        mock_jira_client.get_time_tracking.return_value = {}

        from set_estimate import set_estimate
        result = set_estimate(mock_jira_client, 'PROJ-123', original_estimate='0')

        mock_jira_client.set_time_tracking.assert_called_once()

    @pytest.mark.time
    @pytest.mark.unit
    def test_set_estimate_very_large(self, mock_jira_client):
        """Test setting very large estimate (boundary)."""
        from set_estimate import set_estimate
        from error_handler import ValidationError

        # Test that extremely large values are handled
        # JIRA has limits on estimate size
        with pytest.raises(ValidationError):
            set_estimate(mock_jira_client, 'PROJ-123', original_estimate='9999w')

    @pytest.mark.time
    @pytest.mark.unit
    def test_set_estimate_remaining_exceeds_original(self, mock_jira_client):
        """Test when remaining estimate exceeds original."""
        mock_jira_client.set_time_tracking.return_value = None
        mock_jira_client.get_time_tracking.return_value = {
            'originalEstimate': '1d',
            'remainingEstimate': '2d'  # Remaining > Original
        }

        from set_estimate import set_estimate
        # This might be a warning case or allowed by JIRA
        result = set_estimate(
            mock_jira_client, 'PROJ-123',
            original_estimate='1d',
            remaining_estimate='2d'
        )
        # Verify it handles this case (success or warning)
        assert mock_jira_client.set_time_tracking.called
```

---

### 2.3 Missing Dry-Run Tests

**Impact:** Dry-run feature untested in some scripts
**Files Affected:** 2 files

| Script | Test File | Status |
|--------|-----------|--------|
| `delete_worklog.py` | `test_delete_worklog.py` | Has dry-run test (line 52) |
| `bulk_log_time.py` | `test_bulk_log_time.py` | Has dry-run test (line 56) |
| `set_estimate.py` | `test_set_estimate.py` | **MISSING** |
| `update_worklog.py` | `test_update_worklog.py` | **MISSING** |

**Remediation - Add to test_set_estimate.py:**

```python
class TestSetEstimateDryRun:
    """Tests for dry-run mode."""

    @pytest.mark.time
    @pytest.mark.unit
    def test_set_estimate_dry_run(self, mock_jira_client, sample_time_tracking):
        """Test dry-run mode shows preview without changes."""
        mock_jira_client.get_time_tracking.return_value = sample_time_tracking

        from set_estimate import set_estimate
        result = set_estimate(
            mock_jira_client, 'PROJ-123',
            original_estimate='3d',
            dry_run=True
        )

        # Should NOT call set_time_tracking
        mock_jira_client.set_time_tracking.assert_not_called()
        assert result.get('dry_run') is True
        assert 'current' in result or 'originalEstimate' in result
```

**Remediation - Add to test_update_worklog.py:**

```python
class TestUpdateWorklogDryRun:
    """Tests for dry-run mode."""

    @pytest.mark.time
    @pytest.mark.unit
    def test_update_worklog_dry_run(self, mock_jira_client, sample_worklog):
        """Test dry-run mode shows preview without changes."""
        mock_jira_client.get_worklog.return_value = sample_worklog

        from update_worklog import update_worklog
        result = update_worklog(
            mock_jira_client, 'PROJ-123', '10045',
            time_spent='4h',
            dry_run=True
        )

        # Should NOT call update_worklog
        mock_jira_client.update_worklog.assert_not_called()
        assert result.get('dry_run') is True
        assert result.get('current_time_spent') == '2h' or 'would_update' in result
```

---

### 2.4 Weak Assertion in Relative Date Test

**Impact:** Test passes without verifying correct date conversion
**File:** `test_add_worklog.py` lines 74-76

**Current (weak):**

```python
def test_add_worklog_with_relative_date(self, mock_jira_client, sample_worklog):
    """Test using relative date like 'yesterday'."""
    # ...
    call_args = mock_jira_client.add_worklog.call_args
    # Started should be converted to ISO format
    assert 'started' in call_args[1]
    assert call_args[1]['started'] is not None  # Weak - doesn't verify format
```

**Remediation (strong):**

```python
import re
from datetime import datetime, timedelta

def test_add_worklog_with_relative_date(self, mock_jira_client, sample_worklog):
    """Test using relative date like 'yesterday'."""
    mock_jira_client.add_worklog.return_value = sample_worklog

    from add_worklog import add_worklog
    result = add_worklog(
        mock_jira_client, 'PROJ-123', '2h',
        started='yesterday'
    )

    call_args = mock_jira_client.add_worklog.call_args
    started = call_args[1]['started']

    # Verify it's an ISO format datetime string
    iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
    assert re.match(iso_pattern, started), f"Expected ISO format, got: {started}"

    # Verify the date is actually yesterday
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    assert yesterday in started, f"Expected yesterday's date ({yesterday}) in {started}"
```

---

## Phase 3: Medium Priority Issues

### 3.1 Missing Empty Results / Edge Case Tests

**Impact:** Edge cases not covered
**Files Affected:** Multiple

| File | Missing Test |
|------|--------------|
| `test_get_worklogs.py` | Filter returns no matches |
| `test_time_report.py` | Report with no matching worklogs for date range |
| `test_bulk_log_time.py` | Empty issue list |
| `test_bulk_log_time.py` | JQL returns no results |
| `test_export_timesheets.py` | Export empty data |

**Remediation - Add to test_get_worklogs.py:**

```python
class TestGetWorklogsEdgeCases:
    """Tests for edge case handling."""

    @pytest.mark.time
    @pytest.mark.unit
    def test_filter_returns_no_matches(self, mock_jira_client, sample_worklogs):
        """Test when filter matches no worklogs."""
        mock_jira_client.get_worklogs.return_value = sample_worklogs

        from get_worklogs import get_worklogs
        result = get_worklogs(
            mock_jira_client, 'PROJ-123',
            author_filter='nonexistent@company.com'
        )

        assert len(result['worklogs']) == 0

    @pytest.mark.time
    @pytest.mark.unit
    def test_date_range_no_matches(self, mock_jira_client, sample_worklogs):
        """Test when date range matches no worklogs."""
        mock_jira_client.get_worklogs.return_value = sample_worklogs

        from get_worklogs import get_worklogs
        result = get_worklogs(
            mock_jira_client, 'PROJ-123',
            since='2030-01-01',
            until='2030-01-02'
        )

        assert len(result['worklogs']) == 0
```

**Remediation - Add to test_bulk_log_time.py:**

```python
@pytest.mark.time
@pytest.mark.unit
def test_bulk_log_empty_issue_list(self, mock_jira_client):
    """Test with empty issue list."""
    from bulk_log_time import bulk_log_time
    from error_handler import ValidationError

    with pytest.raises(ValidationError) as exc_info:
        bulk_log_time(mock_jira_client, issues=[], time_spent='30m')
    assert 'empty' in str(exc_info.value).lower() or 'no issues' in str(exc_info.value).lower()

@pytest.mark.time
@pytest.mark.unit
def test_bulk_log_jql_no_results(self, mock_jira_client):
    """Test when JQL returns no issues."""
    mock_jira_client.search_issues.return_value = {'issues': [], 'total': 0}

    from bulk_log_time import bulk_log_time
    result = bulk_log_time(
        mock_jira_client,
        jql='project=NONEXISTENT',
        time_spent='15m'
    )

    assert result['success_count'] == 0
    mock_jira_client.add_worklog.assert_not_called()
```

**Remediation - Add to test_export_timesheets.py:**

```python
class TestExportEmpty:
    """Tests for exporting empty data."""

    @pytest.mark.time
    @pytest.mark.unit
    def test_export_empty_csv(self):
        """Test CSV export with no entries."""
        from export_timesheets import format_csv

        empty_data = {
            'entries': [],
            'total_seconds': 0,
            'entry_count': 0
        }
        csv_output = format_csv(empty_data)

        # Should have header row only
        lines = csv_output.strip().split('\n')
        assert len(lines) == 1  # Header only
        assert 'Issue Key' in lines[0]

    @pytest.mark.time
    @pytest.mark.unit
    def test_export_empty_json(self):
        """Test JSON export with no entries."""
        from export_timesheets import format_json
        import json

        empty_data = {
            'entries': [],
            'total_seconds': 0,
            'entry_count': 0
        }
        json_output = format_json(empty_data)
        data = json.loads(json_output)

        assert data['entries'] == []
        assert data['total_seconds'] == 0
```

---

### 3.2 Missing Issue Key Validation Tests

**Impact:** Invalid issue keys may not be rejected
**Files Affected:** All files that accept issue keys

**Remediation - Add to test_add_worklog.py:**

```python
class TestIssueKeyValidation:
    """Tests for issue key validation."""

    @pytest.mark.time
    @pytest.mark.unit
    def test_invalid_issue_key_format(self, mock_jira_client):
        """Test validation rejects invalid issue key format."""
        from add_worklog import add_worklog
        from error_handler import ValidationError

        for invalid_key in ['', 'PROJ', '123', 'proj-123', 'PROJ-', '-123', 'PROJ 123']:
            with pytest.raises(ValidationError) as exc_info:
                add_worklog(mock_jira_client, invalid_key, '2h')
            assert 'issue key' in str(exc_info.value).lower()

    @pytest.mark.time
    @pytest.mark.unit
    def test_valid_issue_key_formats(self, mock_jira_client, sample_worklog):
        """Test various valid issue key formats."""
        mock_jira_client.add_worklog.return_value = sample_worklog

        from add_worklog import add_worklog

        for valid_key in ['PROJ-1', 'PROJ-123', 'AB-1', 'LONGPROJECT-99999']:
            add_worklog(mock_jira_client, valid_key, '2h')
            assert mock_jira_client.add_worklog.called
            mock_jira_client.add_worklog.reset_mock()
```

---

### 3.3 Missing JSON Output Format Tests

**Impact:** JSON output may have incorrect structure
**Files Affected:** 2 files

| File | Missing Test |
|------|--------------|
| `test_get_time_tracking.py` | JSON output format test |
| `test_time_report.py` | Complete JSON structure test |

**Remediation - Add to test_get_time_tracking.py:**

```python
class TestGetTimeTrackingOutput:
    """Tests for output formatting."""

    @pytest.mark.time
    @pytest.mark.unit
    def test_json_output_structure(self, mock_jira_client, sample_time_tracking):
        """Test JSON output has all required fields."""
        mock_jira_client.get_time_tracking.return_value = sample_time_tracking

        from get_time_tracking import get_time_tracking
        import json

        result = get_time_tracking(mock_jira_client, 'PROJ-123')

        # Verify JSON serializable
        json_str = json.dumps(result)
        parsed = json.loads(json_str)

        # Verify required fields
        assert 'originalEstimate' in parsed
        assert 'remainingEstimate' in parsed
        assert 'originalEstimateSeconds' in parsed
        assert 'remainingEstimateSeconds' in parsed
```

---

### 3.4 Unused Imports

**Impact:** Code hygiene
**Files Affected:** 4

| File | Line | Unused Import |
|------|------|---------------|
| `test_add_worklog.py` | 8 | `patch` imported but used minimally |
| `test_delete_worklog.py` | 8 | `patch` imported but never used |
| `test_export_timesheets.py` | 8 | `patch` imported but never used |
| `test_time_report.py` | 8 | `patch` imported but never used |
| `test_time_report.py` | 11 | `datetime, timedelta` imported but never used |

**Remediation:**

```python
# test_delete_worklog.py line 8
# Before:
from unittest.mock import Mock, patch

# After:
from unittest.mock import Mock

# test_time_report.py lines 8, 11
# Before:
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

# After:
from unittest.mock import Mock
# Remove datetime import entirely if not used
```

---

## Phase 4: Low Priority Issues

### 4.1 Inconsistent Assertion Patterns

**Impact:** Code maintainability, harder to debug failures
**Files Affected:** Multiple

**Pattern to standardize - Use structured assertions:**

```python
# Avoid: String checking on call_args
assert "'time_spent': '2h'" in str(call_args)

# Prefer: Direct parameter access
call_args = mock_jira_client.add_worklog.call_args
assert call_args.kwargs['time_spent'] == '2h'

# Or use assert_called_with:
mock_jira_client.add_worklog.assert_called_once_with(
    issue_key='PROJ-123',
    time_spent='2h',
    comment=ANY  # from unittest.mock import ANY
)
```

---

### 4.2 Missing CLI Test Coverage

**Impact:** CLI behavior not validated
**Files Affected:** All test files (no CLI tests exist)

While not critical, CLI tests would validate argument parsing and output formatting.

**Remediation Template:**

```python
class TestCLI:
    """Tests for CLI interface."""

    @pytest.mark.time
    @pytest.mark.unit
    def test_cli_help(self, capsys):
        """Test --help output."""
        import sys
        from unittest.mock import patch

        with patch.object(sys, 'argv', ['add_worklog.py', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                from add_worklog import main
                main()
            assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert 'usage:' in captured.out.lower()
        assert 'issue' in captured.out.lower()

    @pytest.mark.time
    @pytest.mark.unit
    def test_cli_missing_required_args(self, capsys):
        """Test error when required args missing."""
        import sys
        from unittest.mock import patch

        with patch.object(sys, 'argv', ['add_worklog.py']):
            with pytest.raises(SystemExit) as exc_info:
                from add_worklog import main
                main()
            assert exc_info.value.code != 0
```

---

### 4.3 Add Test Count Verification

**Impact:** Catch accidental test deletion

**Add to CI/CD or as a test:**

```python
# tests/test_coverage_check.py
import pytest
from pathlib import Path

def test_minimum_test_count():
    """Ensure test count doesn't regress."""
    test_dir = Path(__file__).parent
    test_files = list(test_dir.glob('test_*.py'))

    # Count test functions
    test_count = 0
    for f in test_files:
        content = f.read_text()
        test_count += content.count('def test_')

    # Minimum expected tests (update as tests are added)
    MIN_TESTS = 45  # Current count is approximately 45
    assert test_count >= MIN_TESTS, f"Expected {MIN_TESTS}+ tests, found {test_count}"
```

---

## Implementation Checklist

### Phase 1 Checklist (Critical)

- [ ] Add `pytest_configure` to conftest.py with marker registration
- [ ] Add `@pytest.mark.time` and `@pytest.mark.unit` markers to all 31 test classes
- [ ] Update conftest.py fixtures to use deepcopy for nested fixtures
- [ ] Fix fixture mutation in test_update_worklog.py (2 locations)

### Phase 2 Checklist (High Priority)

- [ ] Add API error handling tests (401, 403, 429, 500) to all 9 test files
- [ ] Add time validation edge case tests (zero, negative, max, invalid chars)
- [ ] Add dry-run tests for set_estimate.py and update_worklog.py
- [ ] Fix weak assertion in test_add_worklog_with_relative_date

### Phase 3 Checklist (Medium Priority)

- [ ] Add empty results / edge case tests (5 tests across 3 files)
- [ ] Add issue key validation tests
- [ ] Add JSON output format tests
- [ ] Remove unused imports from 4 files

### Phase 4 Checklist (Low Priority)

- [ ] Standardize assertion patterns
- [ ] Consider adding CLI tests
- [ ] Add test count verification

---

## Verification Commands

```bash
# Run all time tracking tests
pytest .claude/skills/jira-time/tests/ -v

# Run only unit tests
pytest .claude/skills/jira-time/tests/ -v -m unit

# Run only time skill tests
pytest .claude/skills/jira-time/tests/ -v -m time

# Check for test count
pytest .claude/skills/jira-time/tests/ --collect-only | grep "test session starts" -A 5

# Verify no unused imports (requires pylint)
pylint .claude/skills/jira-time/tests/ --disable=all --enable=unused-import

# Check for weak assertions
grep -rn "assert.*>= 0" .claude/skills/jira-time/tests/
grep -rn "is not None$" .claude/skills/jira-time/tests/
```

---

## Success Criteria

1. **All tests pass:** `pytest` exits with code 0
2. **No weak assertions:** grep commands return no results
3. **Consistent markers:** All test classes have `@pytest.mark.time` and `@pytest.mark.unit`
4. **No pytest warnings:** About unknown markers
5. **Coverage maintained:** Test count >= current count (45+)
6. **No unused imports:** pylint reports clean
7. **Error handling tested:** All error codes (401, 403, 404, 429, 500) have test coverage

---

## Test File Summary

| File | Current Tests | Issues Found | Priority Fixes |
|------|---------------|--------------|----------------|
| `conftest.py` | 8 fixtures | 2 issues | Markers, deepcopy |
| `test_add_worklog.py` | 12 tests | 8 issues | Markers, validation edge cases, errors |
| `test_get_worklogs.py` | 9 tests | 6 issues | Markers, errors, edge cases |
| `test_update_worklog.py` | 6 tests | 5 issues | Markers, deepcopy, dry-run, errors |
| `test_delete_worklog.py` | 5 tests | 4 issues | Markers, errors |
| `test_set_estimate.py` | 6 tests | 5 issues | Markers, dry-run, edge cases, errors |
| `test_get_time_tracking.py` | 6 tests | 4 issues | Markers, errors, JSON output |
| `test_export_timesheets.py` | 5 tests | 4 issues | Markers, empty data, errors |
| `test_time_report.py` | 9 tests | 5 issues | Markers, errors, unused imports |
| `test_bulk_log_time.py` | 6 tests | 5 issues | Markers, edge cases, errors |

**Total:** 64 tests, ~85 issues

---

## Notes

- Prioritize Phase 1 before merging to main
- Phase 2 should be completed before next release
- Phases 3-4 can be addressed incrementally
- Consider adding pre-commit hooks to prevent regression
- The `time_utils.py` shared module should have its own test coverage if not already tested
