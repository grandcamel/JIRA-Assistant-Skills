# Date Parsing Deduplication Implementation Log

**Task**: Deduplicate date parsing logic across jira-agile and jira-time skills
**Date**: 2025-12-26
**Status**: Complete

## Problem Analysis

Date parsing was duplicated in 4 scripts across 2 skills:

| Skill | Script | Duplicate Function |
|-------|--------|--------------------|
| jira-agile | create_sprint.py | `parse_date()` (24 lines) |
| jira-agile | manage_sprint.py | `parse_date()` (13 lines) |
| jira-time | get_worklogs.py | Inline code with `parse_relative_date()` + `.strftime()` |
| jira-time | time_report.py | Uses `parse_relative_date()` (already shared) |

### Original Duplicate Code Pattern

**jira-agile/create_sprint.py** (lines 27-50):
```python
def parse_date(date_str: str) -> str:
    """
    Parse date string into ISO format for JIRA API.
    ...
    """
    if not date_str:
        return None

    # Already in full ISO format
    if 'T' in date_str:
        return date_str

    # Simple date format YYYY-MM-DD
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%Y-%m-%dT00:00:00.000Z')
    except ValueError:
        raise ValidationError(f"Invalid date format: {date_str}. Use YYYY-MM-DD format.")
```

**jira-time/get_worklogs.py** (lines 168-182):
```python
if since:
    try:
        dt = parse_relative_date(since)
        since = dt.strftime('%Y-%m-%dT%H:%M:%S.000+0000')
    except ValueError:
        pass  # Use as-is if not a relative date
```

## Solution

Added two new functions to `.claude/skills/shared/scripts/lib/time_utils.py`:

### 1. `parse_date_to_iso()`

Unified function that handles all date input formats and returns ISO 8601 format with 'Z' suffix.

```python
def parse_date_to_iso(date_str: str, base_date: Optional[datetime] = None) -> str:
    """
    Parse various date formats to ISO 8601 format for JIRA API.

    Combines parsing of relative dates, simple dates, and full ISO dates
    into a single function that returns a consistent ISO format.

    Args:
        date_str: Date string in various formats:
                  - Relative: 'today', 'yesterday', 'last-week', 'this-month'
                  - Simple: 'YYYY-MM-DD' (e.g., '2025-01-20')
                  - Full ISO: '2025-01-20T00:00:00.000Z'
        base_date: Base date for relative calculations (default: now)

    Returns:
        ISO 8601 date string like '2025-01-20T00:00:00.000Z'

    Raises:
        ValueError: If date format is unrecognized

    Examples:
        >>> parse_date_to_iso('2025-01-20')
        '2025-01-20T00:00:00.000Z'
        >>> parse_date_to_iso('2025-01-20T10:30:00.000Z')
        '2025-01-20T10:30:00.000Z'
        >>> parse_date_to_iso('today')  # doctest: +SKIP
        '2025-01-15T00:00:00.000Z'
    """
```

### 2. `convert_to_jira_datetime_string()`

Wrapper that returns the '+0000' timezone format preferred by some JIRA APIs.

```python
def convert_to_jira_datetime_string(date_str: str, base_date: Optional[datetime] = None) -> str:
    """
    Convert a date string to JIRA datetime format with timezone offset.

    Similar to parse_date_to_iso but returns format with +0000 timezone
    offset instead of 'Z', which is preferred for some JIRA APIs.

    Args:
        date_str: Date string in various formats
        base_date: Base date for relative calculations (default: now)

    Returns:
        JIRA datetime string like '2025-01-20T00:00:00.000+0000'

    Examples:
        >>> convert_to_jira_datetime_string('2025-01-20')
        '2025-01-20T00:00:00.000+0000'
    """
```

## Files Modified

### 1. `.claude/skills/shared/scripts/lib/time_utils.py`

Added two new functions at the end of the file (lines 330-436):
- `parse_date_to_iso()` - Main unified date parsing function
- `convert_to_jira_datetime_string()` - Wrapper for +0000 format

### 2. `.claude/skills/jira-agile/scripts/create_sprint.py`

**Before:**
```python
from config_manager import get_jira_client
from error_handler import print_error, JiraError, ValidationError
from formatters import print_success


def parse_date(date_str: str) -> str:
    # ... 24 lines of duplicate code ...
```

**After:**
```python
from config_manager import get_jira_client
from error_handler import print_error, JiraError, ValidationError
from formatters import print_success
from time_utils import parse_date_to_iso
```

Updated usage:
```python
# Parse and validate dates using shared utility
try:
    parsed_start = parse_date_to_iso(start_date) if start_date else None
    parsed_end = parse_date_to_iso(end_date) if end_date else None
except ValueError as e:
    raise ValidationError(str(e))
```

### 3. `.claude/skills/jira-agile/scripts/manage_sprint.py`

**Before:**
```python
from config_manager import get_jira_client
from error_handler import print_error, JiraError, ValidationError
from formatters import print_success, print_warning


def parse_date(date_str: str) -> str:
    # ... 13 lines of duplicate code ...
```

**After:**
```python
from config_manager import get_jira_client
from error_handler import print_error, JiraError, ValidationError
from formatters import print_success, print_warning
from time_utils import parse_date_to_iso


def _parse_date_safe(date_str: str) -> str:
    """Parse date string into ISO format, converting ValueError to ValidationError."""
    if not date_str:
        return None
    try:
        return parse_date_to_iso(date_str)
    except ValueError as e:
        raise ValidationError(str(e))
```

### 4. `.claude/skills/jira-time/scripts/get_worklogs.py`

**Before:**
```python
from time_utils import format_seconds, parse_relative_date

# ... later in main() ...
if since:
    try:
        dt = parse_relative_date(since)
        since = dt.strftime('%Y-%m-%dT%H:%M:%S.000+0000')
    except ValueError:
        pass
```

**After:**
```python
from time_utils import format_seconds, convert_to_jira_datetime_string

# ... later in main() ...
if since:
    try:
        since = convert_to_jira_datetime_string(since)
    except ValueError:
        pass  # Use as-is if format is unrecognized
```

### 5. `.claude/skills/jira-time/scripts/time_report.py`

**No changes needed.** This script correctly uses `parse_relative_date()` to get a datetime object for comparison purposes, not a string. The existing implementation is appropriate.

## Test Results

All unit tests pass after the refactoring:

```
$ pytest .claude/skills/jira-agile/tests/test_create_sprint.py \
         .claude/skills/jira-agile/tests/test_manage_sprint.py -v
========================= 25 passed in 0.20s =========================

$ pytest .claude/skills/jira-time/tests/ -v --ignore=live_integration
========================= 99 passed in 0.38s =========================
```

## Validation

Manual verification of the new functions:

```python
>>> parse_date_to_iso('2025-01-20')
'2025-01-20T00:00:00.000Z'

>>> parse_date_to_iso('2025-01-20T10:30:00.000Z')
'2025-01-20T10:30:00.000Z'

>>> convert_to_jira_datetime_string('2025-01-20')
'2025-01-20T00:00:00.000+0000'

>>> parse_date_to_iso('')
ValueError: Date string cannot be empty

>>> parse_date_to_iso('invalid-date')
ValueError: Invalid date format: 'invalid-date'. Use YYYY-MM-DD, ISO format,
            or relative dates like 'today', 'yesterday'.
```

## Benefits

1. **Code reduction**: Removed ~50 lines of duplicate code across 3 files
2. **Consistency**: All date parsing now uses the same logic
3. **Enhanced features**: All scripts now support relative dates ('today', 'yesterday', etc.)
4. **Better error messages**: Unified error messages with helpful suggestions
5. **Maintainability**: Single location for date parsing logic

## Summary

| Metric | Before | After |
|--------|--------|-------|
| Duplicate functions | 2 | 0 |
| Inline date formatting | 2 locations | 0 |
| Lines of duplicate code | ~50 | 0 |
| Shared utility functions | 0 | 2 |
| Test status | All passing | All passing |
