# Fix jira-relationships Unit Test Failures

## Summary

Fixed 8 unit test failures in the jira-relationships skill by updating test expectations to match the current semantic link flag CLI interface.

## Date

2025-12-26

## Files Modified

1. `.claude/skills/jira-relationships/tests/test_cli_args.py`
2. `.claude/skills/jira-relationships/tests/test_concurrent_operations.py`

## Changes Made

### test_cli_args.py

#### TestLinkIssueCLI (4 fixes)

1. **test_required_args**: Updated docstring and second test case
   - Changed: `assert exc_info.value.code == 2` to `assert exc_info.value.code == 1`
   - Reason: Missing link type now raises ValidationError (exit code 1), not argparse error (exit code 2)

2. **test_valid_positional_args**: Updated CLI arguments
   - Before: `['link_issue.py', 'PROJ-123', 'PROJ-456']`
   - After: `['link_issue.py', 'PROJ-123', '--blocks', 'PROJ-456']`
   - Added mock for `get_link_types()` method

3. **test_type_option**: Updated CLI arguments
   - Before: `['link_issue.py', 'PROJ-123', 'PROJ-456', '--type', link_type]`
   - After: `['link_issue.py', 'PROJ-123', '--type', link_type, '--to', 'PROJ-456']`
   - Added mock for `get_link_types()` method

4. **test_profile_option**: Updated CLI arguments
   - Before: `['link_issue.py', 'PROJ-123', 'PROJ-456', '--profile', 'development']`
   - After: `['link_issue.py', 'PROJ-123', '--blocks', 'PROJ-456', '--profile', 'development']`
   - Added mock for `get_link_types()` method

#### TestBulkLinkCLI (3 fixes)

5. **test_requires_issues_or_jql**: Updated CLI arguments
   - Before: `['bulk_link.py', '--target', 'PROJ-100', '--type', 'Blocks']`
   - After: `['bulk_link.py', '--blocks', 'PROJ-100']`

6. **test_target_required**: Renamed and updated
   - Renamed: `test_target_required` to reflect new behavior
   - Before: `['bulk_link.py', '--issues', 'PROJ-1', '--type', 'Blocks']`
   - After: `['bulk_link.py', '--issues', 'PROJ-1']`

7. **test_type_required**: Renamed to `test_type_with_to_required`
   - Updated docstring to clarify that `--type` requires `--to`

8. **test_valid_input**: Updated CLI arguments
   - Before: `['bulk_link.py', '--issues', 'PROJ-1,PROJ-2', '--target', 'PROJ-100', '--type', 'Blocks', '--dry-run']`
   - After: `['bulk_link.py', '--issues', 'PROJ-1,PROJ-2', '--blocks', 'PROJ-100', '--dry-run']`

9. **test_skip_existing_option**: Updated CLI arguments
   - Before: `['bulk_link.py', '--issues', 'PROJ-1', '--target', 'PROJ-100', '--type', 'Blocks', '--skip-existing', '--dry-run']`
   - After: `['bulk_link.py', '--issues', 'PROJ-1', '--blocks', 'PROJ-100', '--skip-existing', '--dry-run']`

10. **test_jql_input**: Updated CLI arguments
    - Before: `['bulk_link.py', '--jql', '...', '--target', 'PROJ-100', '--type', 'Relates', '--dry-run']`
    - After: `['bulk_link.py', '--jql', '...', '--relates-to', 'PROJ-100', '--dry-run']`

### test_concurrent_operations.py

11. **test_concurrent_bulk_link_operations**: Fixed invalid issue key format
    - Before: `f'PROJ-TARGET-{i}'` (invalid: contains two hyphens)
    - After: `f'PROJ-{100+i}'` (valid: PROJ-100, PROJ-101, PROJ-102)

## Test Results

```
============================= test session starts ==============================
platform darwin -- Python 3.14.0, pytest-9.0.2

collected 111 items

test_bulk_link.py: 12 passed
test_cli_args.py: 10 passed  (previously 8 failed)
test_clone_issue.py: 13 passed
test_concurrent_operations.py: 7 passed  (previously 1 failed)
test_get_blockers.py: 13 passed
test_get_dependencies.py: 10 passed
test_get_link_types.py: 9 passed
test_get_links.py: 12 passed
test_link_issue.py: 15 passed
test_unlink_issue.py: 10 passed

============================= 111 passed in 0.73s ==============================
```

## Root Cause Analysis

The tests were written for an older CLI interface that used:
- Two positional arguments (`inward_key`, `outward_key`)
- `--target` and `--type` options for bulk operations

The current implementation uses semantic link flags:
- Single positional argument plus semantic flags (`--blocks`, `--duplicates`, `--relates-to`, etc.)
- Or explicit `--type NAME --to ISSUE` syntax

No changes were needed to the script implementations; only the tests required updates.
