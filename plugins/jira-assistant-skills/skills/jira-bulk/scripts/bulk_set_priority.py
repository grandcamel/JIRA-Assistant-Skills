#!/usr/bin/env python3
"""
Bulk set priority on multiple JIRA issues.

Sets priority on multiple issues, with support for:
- Issue keys or JQL queries
- Standard priority values
- Dry-run preview
- Progress tracking

Usage:
    python bulk_set_priority.py --issues PROJ-1,PROJ-2 --priority High
    python bulk_set_priority.py --jql "project=PROJ AND type=Bug" --priority Blocker
    python bulk_set_priority.py --jql "labels=urgent" --priority Highest --dry-run
"""

import argparse
import sys
from collections.abc import Callable
from typing import Any

from bulk_utils import execute_bulk_operation, get_issues_to_process

from jira_assistant_skills_lib import (
    JiraError,
    ValidationError,
    get_jira_client,
    print_error,
)

# Standard JIRA priorities
STANDARD_PRIORITIES = [
    "Highest",
    "High",
    "Medium",
    "Low",
    "Lowest",
    "Blocker",
    "Critical",
    "Major",
    "Minor",
    "Trivial",
]


def validate_priority(priority: str) -> str:
    """
    Validate and normalize priority name.

    Args:
        priority: Priority name

    Returns:
        Normalized priority name

    Raises:
        ValidationError: If priority is not valid
    """
    # Case-insensitive match
    for std in STANDARD_PRIORITIES:
        if std.lower() == priority.lower():
            return std

    raise ValidationError(
        f"Invalid priority: '{priority}'. "
        f"Valid priorities: {', '.join(STANDARD_PRIORITIES)}"
    )


def bulk_set_priority(
    client=None,
    issue_keys: list[str] | None = None,
    jql: str | None = None,
    priority: str | None = None,
    dry_run: bool = False,
    max_issues: int = 100,
    delay_between_ops: float = 0.1,
    progress_callback: Callable | None = None,
    show_progress: bool = True,
    confirm_threshold: int = 50,
    skip_confirmation: bool = False,
) -> dict[str, Any]:
    """
    Set priority on multiple issues.

    Args:
        client: JiraClient instance (optional, created if not provided)
        issue_keys: List of issue keys to update
        jql: JQL query to find issues (alternative to issue_keys)
        priority: Priority name to set
        dry_run: If True, preview without making changes
        max_issues: Maximum number of issues to process
        delay_between_ops: Delay between operations (seconds)
        progress_callback: Optional callback(current, total, issue_key, status)
        show_progress: If True, show tqdm progress bar (default: True)
        confirm_threshold: Prompt for confirmation above this count (default: 50)
        skip_confirmation: If True, skip confirmation prompt (default: False)

    Returns:
        Dict with success, failed, errors, etc.
    """
    # Validate priority first
    priority = validate_priority(priority)

    close_client = False
    if client is None:
        client = get_jira_client()
        close_client = True

    try:
        # Get issues to process using shared utility
        issues = get_issues_to_process(
            client,
            issue_keys=issue_keys,
            jql=jql,
            max_issues=max_issues,
            fields=["key", "summary", "priority"],
        )

        def priority_operation(issue: dict, index: int, total: int) -> str:
            """Execute priority update for a single issue."""
            issue_key = issue.get("key")
            client.update_issue(
                issue_key, fields={"priority": {"name": priority}}, notify_users=False
            )
            return priority

        def format_dry_run_item(issue: dict) -> str:
            """Format issue for dry-run preview."""
            key = issue.get("key")
            current = issue.get("fields", {}).get("priority")
            current_name = current.get("name", "None") if current else "None"
            return f"{key} ({current_name} -> {priority})"

        # Execute bulk operation using shared utility
        result = execute_bulk_operation(
            issues=issues,
            operation_func=priority_operation,
            dry_run=dry_run,
            dry_run_message=f"[DRY RUN] Would set priority to '{priority}' on {len(issues)} issue(s):",
            dry_run_item_formatter=format_dry_run_item,
            delay=delay_between_ops,
            progress_callback=progress_callback,
            success_message_formatter=lambda key,
            _: f"Set {key} priority to '{priority}'",
            show_progress=show_progress,
            progress_desc=f"Setting priority to '{priority}'",
            confirm_threshold=confirm_threshold,
            skip_confirmation=skip_confirmation,
            operation_name=f"set priority to '{priority}' on",
        )

        return result

    finally:
        if close_client:
            client.close()


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Bulk set priority on JIRA issues",
        epilog="Example: python bulk_set_priority.py --issues PROJ-1,PROJ-2 --priority High",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--issues", "-i", help="Comma-separated issue keys (e.g., PROJ-1,PROJ-2)"
    )
    group.add_argument("--jql", "-q", help="JQL query to find issues")

    parser.add_argument(
        "--priority",
        "-p",
        required=True,
        help=f"Priority to set ({', '.join(STANDARD_PRIORITIES[:5])})",
    )
    parser.add_argument(
        "--max-issues",
        type=int,
        default=100,
        help="Maximum issues to process (default: 100)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without making them"
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompt for large operations",
    )
    parser.add_argument(
        "--no-progress", action="store_true", help="Disable progress bar"
    )

    args = parser.parse_args(argv)

    try:
        # Validate priority before any client creation
        priority = validate_priority(args.priority)

        issue_keys = None
        if args.issues:
            issue_keys = [k.strip() for k in args.issues.split(",")]

        result = bulk_set_priority(
            issue_keys=issue_keys,
            jql=args.jql,
            priority=priority,
            dry_run=args.dry_run,
            max_issues=args.max_issues,
            show_progress=not args.no_progress,
            skip_confirmation=args.yes,
        )

        if result.get("cancelled"):
            print("\nOperation cancelled by user.")
            sys.exit(0)

        print(f"\nSummary: {result['success']} succeeded, {result['failed']} failed")

        if result["failed"] > 0:
            sys.exit(1)

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled")
        sys.exit(130)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
