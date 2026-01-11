#!/usr/bin/env python3
"""
Bulk assign multiple JIRA issues.

Assigns multiple issues to a user, with support for:
- Issue keys or JQL queries
- Assignment by account ID or email
- Self-assignment using 'self' keyword
- Unassigning issues
- Dry-run preview
- Progress tracking

Usage:
    python bulk_assign.py --issues PROJ-1,PROJ-2 --assignee "john.doe"
    python bulk_assign.py --jql "project=PROJ AND status=Open" --assignee self
    python bulk_assign.py --jql "project=PROJ" --unassign
    python bulk_assign.py --issues PROJ-1 --assignee "john@company.com" --dry-run
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


def resolve_user_id(client, user_identifier: str) -> str | None:
    """
    Resolve a user identifier to an account ID.

    Args:
        client: JiraClient instance
        user_identifier: Account ID, email, or 'self'

    Returns:
        Account ID string or None for unassign
    """
    if user_identifier is None:
        return None

    if user_identifier.lower() == "self":
        return client.get_current_user_id()

    # Check if it looks like an email
    if "@" in user_identifier:
        # Try to find user by email
        try:
            users = client.get(
                "/rest/api/3/user/search",
                params={"query": user_identifier},
                operation="search users",
            )
            if users and len(users) > 0:
                # Find exact email match
                for user in users:
                    if user.get("emailAddress", "").lower() == user_identifier.lower():
                        return user["accountId"]
                # Fall back to first result
                return users[0]["accountId"]
        except JiraError:
            pass

    # Assume it's already an account ID
    return user_identifier


def bulk_assign(
    client=None,
    issue_keys: list[str] | None = None,
    jql: str | None = None,
    assignee: str | None = None,
    unassign: bool = False,
    dry_run: bool = False,
    max_issues: int = 100,
    delay_between_ops: float = 0.1,
    progress_callback: Callable | None = None,
    show_progress: bool = True,
    confirm_threshold: int = 50,
    skip_confirmation: bool = False,
) -> dict[str, Any]:
    """
    Assign multiple issues to a user.

    Args:
        client: JiraClient instance (optional, created if not provided)
        issue_keys: List of issue keys to assign
        jql: JQL query to find issues (alternative to issue_keys)
        assignee: User to assign (account ID, email, or 'self')
        unassign: If True, remove assignee
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
    close_client = False
    if client is None:
        client = get_jira_client()
        close_client = True

    try:
        # Resolve assignee ID
        account_id = None
        if unassign:
            account_id = None
            action = "unassign"
        elif assignee:
            account_id = resolve_user_id(client, assignee)
            if account_id is None and assignee.lower() != "self":
                raise ValidationError(f"Could not resolve user: {assignee}")
            action = f"assign to {assignee}"
        else:
            raise ValidationError("Either --assignee or --unassign must be provided")

        # Get issues to process using shared utility
        issues = get_issues_to_process(
            client,
            issue_keys=issue_keys,
            jql=jql,
            max_issues=max_issues,
            fields=["key", "summary", "assignee"],
        )

        def assign_operation(issue: dict, index: int, total: int) -> str:
            """Execute assignment for a single issue."""
            issue_key = issue.get("key")
            client.assign_issue(issue_key, account_id)
            return action

        def format_dry_run_item(issue: dict) -> str:
            """Format issue for dry-run preview."""
            key = issue.get("key")
            current = issue.get("fields", {}).get("assignee")
            current_name = (
                current.get("displayName", "Unassigned") if current else "Unassigned"
            )
            return f"{key} (current: {current_name})"

        # Execute bulk operation using shared utility
        result = execute_bulk_operation(
            issues=issues,
            operation_func=assign_operation,
            dry_run=dry_run,
            dry_run_message=f"[DRY RUN] Would {action} {len(issues)} issue(s):",
            dry_run_item_formatter=format_dry_run_item,
            delay=delay_between_ops,
            progress_callback=progress_callback,
            success_message_formatter=lambda key, _: f"{action.capitalize()}d {key}",
            show_progress=show_progress,
            progress_desc=f"{action.capitalize()}ing",
            confirm_threshold=confirm_threshold,
            skip_confirmation=skip_confirmation,
            operation_name=action,
        )

        return result

    finally:
        if close_client:
            client.close()


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Bulk assign JIRA issues to a user",
        epilog="Example: python bulk_assign.py --issues PROJ-1,PROJ-2 --assignee self",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--issues", "-i", help="Comma-separated issue keys (e.g., PROJ-1,PROJ-2)"
    )
    group.add_argument("--jql", "-q", help="JQL query to find issues")

    assign_group = parser.add_mutually_exclusive_group(required=True)
    assign_group.add_argument(
        "--assignee", "-a", help='User to assign (account ID, email, or "self")'
    )
    assign_group.add_argument(
        "--unassign", "-u", action="store_true", help="Remove assignee from issues"
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
        issue_keys = None
        if args.issues:
            issue_keys = [k.strip() for k in args.issues.split(",")]

        result = bulk_assign(
            issue_keys=issue_keys,
            jql=args.jql,
            assignee=args.assignee,
            unassign=args.unassign,
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
