#!/usr/bin/env python3
"""
Bulk delete multiple JIRA issues.

Permanently deletes multiple issues with support for:
- Issue keys or JQL queries
- Dry-run preview (REQUIRED for safety)
- Subtask deletion control
- Progress tracking

WARNING: This is a destructive operation. Deleted issues cannot be recovered.

Usage:
    python bulk_delete.py --jql "project=DEMO" --dry-run
    python bulk_delete.py --jql "project=DEMO" --yes
    python bulk_delete.py --issues DEMO-1,DEMO-2,DEMO-3 --dry-run
    python bulk_delete.py --issues DEMO-1,DEMO-2 --yes --no-subtasks
"""

import argparse
import sys
from collections.abc import Callable
from typing import Any

from bulk_utils import execute_bulk_operation, get_issues_to_process

from jira_assistant_skills_lib import (
    JiraError,
    get_jira_client,
    print_error,
    print_warning,
)


def bulk_delete(
    client=None,
    issue_keys: list[str] | None = None,
    jql: str | None = None,
    dry_run: bool = False,
    max_issues: int = 100,
    delete_subtasks: bool = True,
    delay_between_ops: float = 0.1,
    progress_callback: Callable | None = None,
    show_progress: bool = True,
    confirm_threshold: int = 10,
    skip_confirmation: bool = False,
) -> dict[str, Any]:
    """
    Delete multiple issues permanently.

    Args:
        client: JiraClient instance (optional, created if not provided)
        issue_keys: List of issue keys to delete
        jql: JQL query to find issues (alternative to issue_keys)
        dry_run: If True, preview without making changes
        max_issues: Maximum number of issues to process (default: 100)
        delete_subtasks: If True, also delete subtasks (default: True)
        delay_between_ops: Delay between operations (seconds)
        progress_callback: Optional callback(current, total, issue_key, status)
        show_progress: If True, show tqdm progress bar (default: True)
        confirm_threshold: Prompt for confirmation above this count (default: 10)
        skip_confirmation: If True, skip confirmation prompt (default: False)

    Returns:
        Dict with success, failed, errors, etc.
    """
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
            fields=["key", "summary", "issuetype", "status", "subtasks"],
        )

        # Count subtasks for information
        total_subtasks = 0
        for issue in issues:
            subtasks = issue.get("fields", {}).get("subtasks", [])
            if subtasks:
                total_subtasks += len(subtasks)

        subtask_note = ""
        if delete_subtasks and total_subtasks > 0:
            subtask_note = f" (plus {total_subtasks} subtasks)"
        elif not delete_subtasks and total_subtasks > 0:
            subtask_note = f" (excluding {total_subtasks} subtasks)"

        def delete_operation(issue: dict, index: int, total: int) -> str:
            """Execute deletion for a single issue."""
            issue_key = issue.get("key")
            client.delete_issue(issue_key, delete_subtasks=delete_subtasks)
            return "deleted"

        def format_dry_run_item(issue: dict) -> str:
            """Format issue for dry-run preview."""
            key = issue.get("key")
            fields = issue.get("fields", {})
            summary = fields.get("summary", "")
            issue_type = fields.get("issuetype", {}).get("name", "")
            status = fields.get("status", {}).get("name", "")
            subtasks = fields.get("subtasks", [])

            # Truncate summary if too long
            if len(summary) > 50:
                summary = summary[:47] + "..."

            result = f"{key} [{issue_type}] {status}: {summary}"
            if subtasks and delete_subtasks:
                result += f" (+{len(subtasks)} subtasks)"
            return result

        # Execute bulk operation using shared utility
        result = execute_bulk_operation(
            issues=issues,
            operation_func=delete_operation,
            dry_run=dry_run,
            dry_run_message=f"[DRY RUN] Would DELETE {len(issues)} issue(s){subtask_note}:",
            dry_run_item_formatter=format_dry_run_item,
            delay=delay_between_ops,
            progress_callback=progress_callback,
            success_message_formatter=lambda key, _: f"Deleted {key}",
            show_progress=show_progress,
            progress_desc="Deleting",
            confirm_threshold=confirm_threshold,
            skip_confirmation=skip_confirmation,
            operation_name=f"PERMANENTLY DELETE{subtask_note}",
        )

        return result

    finally:
        if close_client:
            client.close()


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Bulk delete JIRA issues (DESTRUCTIVE - cannot be undone)",
        epilog="Example: python bulk_delete.py --jql 'project=DEMO' --dry-run",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--issues", "-i", help="Comma-separated issue keys (e.g., PROJ-1,PROJ-2)"
    )
    group.add_argument("--jql", "-q", help="JQL query to find issues")

    parser.add_argument(
        "--max-issues",
        type=int,
        default=100,
        help="Maximum issues to process (default: 100)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview deletions without making changes (RECOMMENDED)",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompt (use with caution)",
    )
    parser.add_argument(
        "--no-subtasks",
        action="store_true",
        help="Do NOT delete subtasks (default: delete subtasks)",
    )
    parser.add_argument(
        "--no-progress", action="store_true", help="Disable progress bar"
    )

    args = parser.parse_args(argv)

    # Safety warning for non-dry-run
    if not args.dry_run and not args.yes:
        print_warning(
            "WARNING: This will PERMANENTLY delete issues. "
            "Consider using --dry-run first to preview."
        )

    try:
        issue_keys = None
        if args.issues:
            issue_keys = [k.strip() for k in args.issues.split(",")]

        result = bulk_delete(
            issue_keys=issue_keys,
            jql=args.jql,
            dry_run=args.dry_run,
            max_issues=args.max_issues,
            delete_subtasks=not args.no_subtasks,
            show_progress=not args.no_progress,
            skip_confirmation=args.yes,
        )

        if result.get("cancelled"):
            print("\nOperation cancelled by user.")
            sys.exit(0)

        if result.get("dry_run"):
            print(f"\n[DRY RUN] {result['would_process']} issue(s) would be deleted.")
            print("Run without --dry-run to execute.")
        else:
            print(f"\nSummary: {result['success']} deleted, {result['failed']} failed")

        if result.get("failed", 0) > 0:
            print("\nFailed issues:")
            for key, error in result.get("errors", {}).items():
                print(f"  {key}: {error}")
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
