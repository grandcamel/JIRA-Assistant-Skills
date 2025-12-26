# Refactor Large Functions in share_filter.py

## Summary

Refactored `.claude/skills/jira-search/scripts/share_filter.py` to extract handler functions from an oversized `main()` function. The refactoring improves maintainability and testability while preserving existing functionality.

## Problem

The original `main()` function was 130+ lines, handling argument parsing and all command dispatch logic in a single function. This violated the Single Responsibility Principle and made the code harder to test and maintain.

## Changes Made

### New Handler Functions

Six handler functions were extracted, each focused on a specific operation:

```python
def handle_list_permissions(client, args) -> None:
    """
    Handle listing filter permissions.

    Args:
        client: JIRA client
        args: Parsed command-line arguments
    """
```

```python
def handle_unshare(client, args) -> None:
    """
    Handle removing a share permission.

    Args:
        client: JIRA client
        args: Parsed command-line arguments
    """
```

```python
def handle_share_project(client, args) -> None:
    """
    Handle sharing filter with a project or project role.

    Args:
        client: JIRA client
        args: Parsed command-line arguments
    """
```

```python
def handle_share_group(client, args) -> None:
    """
    Handle sharing filter with a group.

    Args:
        client: JIRA client
        args: Parsed command-line arguments
    """
```

```python
def handle_share_global(client, args) -> None:
    """
    Handle sharing filter globally with all authenticated users.

    Args:
        client: JIRA client
        args: Parsed command-line arguments
    """
```

```python
def handle_share_user(client, args) -> None:
    """
    Handle sharing filter with a specific user.

    Args:
        client: JIRA client
        args: Parsed command-line arguments
    """
```

### Refactored main() Function

The `main()` function now uses a clean dispatch pattern:

```python
def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(...)
    # ... argument setup (unchanged) ...

    args = parser.parse_args()

    try:
        client = get_jira_client(args.profile)

        if args.list:
            handle_list_permissions(client, args)
        elif args.unshare:
            handle_unshare(client, args)
        elif args.project:
            handle_share_project(client, args)
        elif args.group:
            handle_share_group(client, args)
        elif args.share_global:
            handle_share_global(client, args)
        elif args.user:
            handle_share_user(client, args)
        else:
            parser.print_help()

    except JiraError as e:
        print_error(e)
        sys.exit(1)
```

## Line Count Comparison

| Metric | Before | After |
|--------|--------|-------|
| Total file lines | 310 | 363 |
| main() lines | ~130 | 65 |
| Number of handler functions | 0 | 6 |

Note: Total file lines increased because the handler functions include docstrings and proper structure, but each individual function is now much smaller and focused.

### main() Function Breakdown (After)

- Argument parsing: ~42 lines (unchanged)
- Dispatch logic: ~18 lines (reduced from ~88 lines)
- Error handling: 5 lines (unchanged)

## Test Results

All 12 existing unit tests pass after refactoring:

```
$ pytest .claude/skills/jira-search/tests/test_share_filter.py -v

test_share_with_project PASSED
test_share_with_project_role PASSED
test_share_with_group PASSED
test_share_globally PASSED
test_share_with_user PASSED
test_unshare PASSED
test_list_permissions PASSED
test_share_not_owner PASSED
test_authentication_error PASSED
test_filter_not_found PASSED
test_rate_limit_error PASSED
test_server_error PASSED

12 passed in 0.15s
```

## Benefits

1. **Improved Readability**: Each handler function has a single, clear responsibility
2. **Better Testability**: Handler functions can be tested independently
3. **Easier Maintenance**: Changes to one operation don't affect others
4. **Consistent Error Handling**: All handlers follow the same pattern
5. **Self-Documenting**: Function names clearly indicate their purpose

## Files Modified

- `.claude/skills/jira-search/scripts/share_filter.py`
