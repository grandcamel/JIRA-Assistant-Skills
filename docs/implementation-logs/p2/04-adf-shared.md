# P2-04: Move ADF Building to Shared Library

## Problem Statement
47+ lines of manual ADF building code were duplicated in jira-dev scripts (link_commit.py, link_pr.py). Both scripts contained nearly identical logic for parsing wiki-style markup (`*bold*`, `[text|url]`) and converting it to Atlassian Document Format.

## Solution
Added a new `wiki_markup_to_adf()` function to the shared adf_helper.py library and refactored both scripts to use it.

## Changes Made

### 1. New Function Added to adf_helper.py

**File:** `.claude/skills/shared/scripts/lib/adf_helper.py`

Added two new functions:

#### `wiki_markup_to_adf(text: str) -> Dict[str, Any]`
Converts JIRA wiki markup to ADF format. Supports:
- `*bold*` -> strong text
- `[text|url]` -> linked text
- Plain text paragraphs (multiline support)

```python
def wiki_markup_to_adf(text: str) -> Dict[str, Any]:
    """
    Convert JIRA wiki markup to ADF format.

    Args:
        text: Text with wiki markup

    Returns:
        ADF document dictionary
    """
```

#### `_parse_wiki_inline(text: str) -> List[Dict[str, Any]]`
Helper function that parses inline wiki formatting within a single line.

### 2. Code Removed from link_commit.py

**File:** `.claude/skills/jira-dev/scripts/link_commit.py`

**Before (47 lines):**
```python
# Use ADF (Atlassian Document Format) for comment
comment_data = {
    "body": {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": []
            }
        ]
    }
}

# Build ADF content from lines
lines = comment_body.split('\n')
for i, line in enumerate(lines):
    if line.strip():
        # Handle wiki-style formatting to ADF
        # *text* -> bold
        content = []
        # ... 40+ more lines of manual parsing
```

**After (4 lines):**
```python
# Convert wiki markup to ADF using shared helper
comment_data = {
    "body": wiki_markup_to_adf(comment_body)
}
```

**Lines removed:** ~47 lines of duplicated ADF building code

### 3. Code Removed from link_pr.py

**File:** `.claude/skills/jira-dev/scripts/link_pr.py`

**Before (47 lines):**
```python
# Build ADF content
lines = comment_body.split('\n')
content_blocks = []

for line in lines:
    if line.strip():
        text_content = []
        # Handle wiki-style formatting
        if '*:*' in line:
            # ... 40+ more lines of manual parsing
```

**After (4 lines):**
```python
# Convert wiki markup to ADF using shared helper
comment_data = {
    "body": wiki_markup_to_adf(comment_body)
}
```

**Lines removed:** ~47 lines of duplicated ADF building code

### 4. Import Updates

Both files now import from the shared library:
```python
from adf_helper import wiki_markup_to_adf
```

## Test Coverage Added

**File:** `.claude/skills/shared/tests/unit/test_adf_helper.py`

Created 21 unit tests in two test classes:

### TestWikiMarkupToAdf (11 tests)
- `test_empty_text` - Empty string handling
- `test_none_text` - None input handling
- `test_plain_text` - Plain text without formatting
- `test_bold_text` - `*bold*` formatting
- `test_wiki_link` - `[text|url]` formatting
- `test_mixed_bold_and_text` - Combination of bold and plain text
- `test_bold_with_link` - Bold field with link value (commit format)
- `test_multiline_text` - Multiple paragraphs
- `test_empty_lines_skipped` - Empty lines not included
- `test_commit_comment_format` - Full commit comment structure
- `test_pr_comment_format` - Full PR comment structure

### TestParseWikiInline (10 tests)
- `test_empty_string` - Empty string returns empty text node
- `test_plain_text_only` - Plain text without formatting
- `test_bold_only` - Bold text only
- `test_link_only` - Wiki link only
- `test_text_before_bold` - Plain text before bold
- `test_text_after_bold` - Plain text after bold
- `test_multiple_bold_sections` - Multiple bold sections
- `test_bold_with_colon` - Bold text with colon (field format)
- `test_link_with_special_chars_in_url` - URLs with query parameters
- `test_bold_followed_by_link` - Bold label followed by link

## Test Results

### New Unit Tests
```
21 passed in 0.10s
```

### Existing Tests (Link Commit)
```
6 passed in 0.14s
```

### Existing Tests (Link PR)
```
7 passed in 0.17s
```

All 34 tests pass successfully.

## Summary

| Metric | Value |
|--------|-------|
| Lines of duplicate code removed | ~94 lines (47 per file) |
| New shared function added | `wiki_markup_to_adf()` |
| New helper function added | `_parse_wiki_inline()` |
| New unit tests added | 21 |
| Existing tests verified | 13 (6 + 7) |
| Files modified | 3 |
| New files created | 2 |

## Files Modified
- `.claude/skills/shared/scripts/lib/adf_helper.py` - Added `wiki_markup_to_adf()` and `_parse_wiki_inline()`
- `.claude/skills/jira-dev/scripts/link_commit.py` - Replaced 47 lines with 4 lines using shared function
- `.claude/skills/jira-dev/scripts/link_pr.py` - Replaced 47 lines with 4 lines using shared function

## New Files Created
- `.claude/skills/shared/tests/unit/__init__.py` - Package init for unit tests
- `.claude/skills/shared/tests/unit/test_adf_helper.py` - 21 unit tests for wiki markup conversion
