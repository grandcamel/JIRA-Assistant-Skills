# Move Common Transition Logic to Shared Library

## Summary

Extracted the duplicated `find_transition_by_name()` function from jira-lifecycle scripts into a new shared library module `transition_helpers.py`. Added a second helper function `find_transition_by_keywords()` to support the keyword-based matching patterns used in resolve_issue.py and reopen_issue.py.

## Problem

The `find_transition_by_name()` function was duplicated in `transition_issue.py`, with similar keyword-based matching logic duplicated in `resolve_issue.py` and `reopen_issue.py`.

## Solution

### 1. Created New Shared Module

**File**: `.claude/skills/shared/scripts/lib/transition_helpers.py`

```python
"""
Transition matching helpers for JIRA workflow operations.

Provides functions to find transitions by name with fuzzy matching
support (case-insensitive, exact and partial matching).
"""

from typing import List, Dict, Any, Optional


def find_transition_by_name(transitions: List[Dict[str, Any]], name: str) -> Dict[str, Any]:
    """
    Find a transition by name (case-insensitive, partial match).

    The search uses a two-phase approach:
    1. First, look for an exact match (case-insensitive)
    2. If no exact match, look for partial matches

    Args:
        transitions: List of transition objects from JIRA API
        name: Transition name to find

    Returns:
        Transition object matching the name

    Raises:
        ValidationError: If transition not found or ambiguous
    """
    from error_handler import ValidationError

    if not transitions:
        raise ValidationError(f"No transitions available to match '{name}'")

    name_lower = name.lower()

    # Phase 1: Exact match (case-insensitive)
    exact_matches = [t for t in transitions if t['name'].lower() == name_lower]
    if len(exact_matches) == 1:
        return exact_matches[0]
    elif len(exact_matches) > 1:
        raise ValidationError(
            f"Multiple exact matches for transition '{name}': " +
            ', '.join(t['name'] for t in exact_matches)
        )

    # Phase 2: Partial match (case-insensitive)
    partial_matches = [t for t in transitions if name_lower in t['name'].lower()]
    if len(partial_matches) == 1:
        return partial_matches[0]
    elif len(partial_matches) > 1:
        raise ValidationError(
            f"Ambiguous transition name '{name}'. Matches: " +
            ', '.join(t['name'] for t in partial_matches)
        )

    # No matches found
    raise ValidationError(
        f"Transition '{name}' not found. Available: " +
        ', '.join(t['name'] for t in transitions)
    )


def find_transition_by_keywords(transitions: List[Dict[str, Any]],
                                 keywords: List[str],
                                 prefer_exact: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Find a transition matching any of the given keywords.

    Useful for finding common transitions like "resolve", "reopen", "done" etc.
    Uses case-insensitive partial matching.

    Args:
        transitions: List of transition objects from JIRA API
        keywords: List of keywords to search for in transition names
        prefer_exact: If provided, prefer an exact match for this keyword

    Returns:
        Matching transition or None if not found
    """
    if not transitions:
        return None

    # Find all transitions matching any keyword
    matching = [
        t for t in transitions
        if any(keyword.lower() in t['name'].lower() for keyword in keywords)
    ]

    if not matching:
        return None

    # If prefer_exact is specified, look for exact match first
    if prefer_exact:
        prefer_lower = prefer_exact.lower()
        exact = [t for t in matching if t['name'].lower() == prefer_lower]
        if exact:
            return exact[0]

    # Return first match
    return matching[0]


def format_transition_list(transitions: List[Dict[str, Any]]) -> str:
    """
    Format a list of transitions for display.

    Args:
        transitions: List of transition objects

    Returns:
        Formatted string with transition names and IDs
    """
    if not transitions:
        return "No transitions available"

    lines = []
    for t in transitions:
        target = t.get('to', {}).get('name', 'Unknown')
        lines.append(f"  - {t['name']} (ID: {t['id']}) -> {target}")

    return '\n'.join(lines)
```

### 2. Updated transition_issue.py

Replaced the local `find_transition_by_name()` function with an import from the shared library:

```python
from config_manager import get_jira_client
from error_handler import print_error, JiraError, ValidationError
from validators import validate_issue_key, validate_transition_id
from formatters import print_success, format_transitions
from adf_helper import text_to_adf
from transition_helpers import find_transition_by_name
```

Removed ~40 lines of duplicated function code.

### 3. Updated resolve_issue.py

Replaced the inline keyword matching logic with the shared `find_transition_by_keywords()` function:

```python
from config_manager import get_jira_client
from error_handler import print_error, JiraError, ValidationError
from validators import validate_issue_key
from formatters import print_success, format_transitions
from adf_helper import text_to_adf
from transition_helpers import find_transition_by_keywords


# Keywords that indicate a resolution/completion transition
RESOLVE_KEYWORDS = ['done', 'resolve', 'close', 'complete']


def resolve_issue(issue_key: str, resolution: str = "Fixed",
                 comment: str = None, profile: str = None) -> None:
    # ...
    transition = find_transition_by_keywords(
        transitions,
        RESOLVE_KEYWORDS,
        prefer_exact='done'
    )
    # ...
```

### 4. Updated reopen_issue.py

Replaced the inline keyword matching logic with the shared `find_transition_by_keywords()` function:

```python
from config_manager import get_jira_client
from error_handler import print_error, JiraError, ValidationError
from validators import validate_issue_key
from formatters import print_success, format_transitions
from adf_helper import text_to_adf
from transition_helpers import find_transition_by_keywords


# Keywords that indicate a reopen/backlog transition
REOPEN_KEYWORDS = ['reopen', 'to do', 'todo', 'open', 'backlog']


def reopen_issue(issue_key: str, comment: str = None, profile: str = None) -> None:
    # ...
    transition = find_transition_by_keywords(
        transitions,
        REOPEN_KEYWORDS,
        prefer_exact='reopen'
    )

    # If no exact 'reopen', try 'to do' as secondary preference
    if transition and 'reopen' not in transition['name'].lower():
        todo_trans = find_transition_by_keywords(
            transitions,
            ['to do', 'todo'],
            prefer_exact='to do'
        )
        if todo_trans:
            transition = todo_trans
    # ...
```

### 5. Created Unit Tests

**File**: `.claude/skills/shared/tests/unit/test_transition_helpers.py`

Comprehensive test suite with 26 tests covering:

- `TestFindTransitionByName` (10 tests)
  - Exact match functionality
  - Case-insensitive matching
  - Partial match functionality
  - Error handling for not found
  - Error handling for ambiguous matches
  - Error handling for empty transitions
  - Preference of exact over partial matches

- `TestFindTransitionByKeywords` (7 tests)
  - Keyword matching functionality
  - prefer_exact parameter
  - No match returns None
  - Empty transitions handling
  - Case-insensitive keyword matching
  - Partial keyword matching

- `TestFormatTransitionList` (4 tests)
  - Basic formatting
  - Empty list handling
  - Target status inclusion
  - Missing 'to' field handling

- `TestIntegrationWithResolveKeywords` (2 tests)
  - Resolve workflow keyword patterns
  - Reopen workflow keyword patterns

- `TestEdgeCases` (3 tests)
  - Whitespace handling
  - Special characters in names
  - Unicode character handling

## Test Results

All tests pass:

```
$ python3 -m pytest .claude/skills/shared/tests/unit/test_transition_helpers.py -v
============================= test session starts ==============================
collected 26 items

test_transition_helpers.py::TestFindTransitionByName::test_exact_match PASSED
test_transition_helpers.py::TestFindTransitionByName::test_exact_match_case_insensitive PASSED
test_transition_helpers.py::TestFindTransitionByName::test_exact_match_uppercase PASSED
test_transition_helpers.py::TestFindTransitionByName::test_partial_match PASSED
test_transition_helpers.py::TestFindTransitionByName::test_partial_match_case_insensitive PASSED
test_transition_helpers.py::TestFindTransitionByName::test_not_found_raises_validation_error PASSED
test_transition_helpers.py::TestFindTransitionByName::test_ambiguous_partial_raises_validation_error PASSED
test_transition_helpers.py::TestFindTransitionByName::test_multiple_exact_matches_raises_validation_error PASSED
test_transition_helpers.py::TestFindTransitionByName::test_empty_transitions_raises_validation_error PASSED
test_transition_helpers.py::TestFindTransitionByName::test_prefers_exact_over_partial PASSED
test_transition_helpers.py::TestFindTransitionByKeywords::test_finds_first_matching_keyword PASSED
test_transition_helpers.py::TestFindTransitionByKeywords::test_prefer_exact_match PASSED
test_transition_helpers.py::TestFindTransitionByKeywords::test_no_match_returns_none PASSED
test_transition_helpers.py::TestFindTransitionByKeywords::test_empty_transitions_returns_none PASSED
test_transition_helpers.py::TestFindTransitionByKeywords::test_case_insensitive_keyword_match PASSED
test_transition_helpers.py::TestFindTransitionByKeywords::test_partial_keyword_match PASSED
test_transition_helpers.py::TestFindTransitionByKeywords::test_prefer_exact_no_match_falls_back PASSED
test_transition_helpers.py::TestFormatTransitionList::test_formats_transitions PASSED
test_transition_helpers.py::TestFormatTransitionList::test_empty_transitions PASSED
test_transition_helpers.py::TestFormatTransitionList::test_includes_target_status PASSED
test_transition_helpers.py::TestFormatTransitionList::test_handles_missing_to_field PASSED
test_transition_helpers.py::TestIntegrationWithResolveKeywords::test_resolve_keywords_pattern PASSED
test_transition_helpers.py::TestIntegrationWithResolveKeywords::test_reopen_keywords_pattern PASSED
test_transition_helpers.py::TestEdgeCases::test_whitespace_in_name PASSED
test_transition_helpers.py::TestEdgeCases::test_special_characters_in_name PASSED
test_transition_helpers.py::TestEdgeCases::test_unicode_in_name PASSED

============================== 26 passed in 0.09s ==============================
```

Existing jira-lifecycle tests continue to pass (42 total):
- test_transition_issue.py: 19 passed
- test_resolve_issue.py: 11 passed
- test_reopen_issue.py: 12 passed

## Files Changed

| File | Action |
|------|--------|
| `.claude/skills/shared/scripts/lib/transition_helpers.py` | Created (new shared module) |
| `.claude/skills/shared/tests/unit/test_transition_helpers.py` | Created (26 unit tests) |
| `.claude/skills/jira-lifecycle/scripts/transition_issue.py` | Updated (removed duplicate, added import) |
| `.claude/skills/jira-lifecycle/scripts/resolve_issue.py` | Updated (refactored to use shared helper) |
| `.claude/skills/jira-lifecycle/scripts/reopen_issue.py` | Updated (refactored to use shared helper) |

## Benefits

1. **DRY Principle**: Eliminated code duplication across 3 files
2. **Testability**: Centralized logic is now thoroughly unit tested (26 tests)
3. **Maintainability**: Single source of truth for transition matching logic
4. **Extensibility**: New helper function `find_transition_by_keywords()` can be reused
5. **Documentation**: Type hints and docstrings improve code readability
