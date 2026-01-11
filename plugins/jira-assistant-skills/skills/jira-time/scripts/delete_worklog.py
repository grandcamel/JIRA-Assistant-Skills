#!/usr/bin/env python3
"""
Delete a worklog (time entry) from a JIRA issue.

Removes a worklog with optional estimate adjustment.
"""

import argparse
import sys
from typing import Any

# Add shared lib to path
from jira_assistant_skills_lib import (
    JiraError,
    get_jira_client,
    print_error,
    validate_issue_key,
)


def delete_worklog(
    client,
    issue_key: str,
    worklog_id: str,
    adjust_estimate: str = "auto",
    new_estimate: str | None = None,
    increase_by: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any] | None:
    """
    Delete a worklog from an issue.

    Args:
        client: JiraClient instance
        issue_key: Issue key (e.g., 'PROJ-123')
        worklog_id: Worklog ID to delete
        adjust_estimate: How to adjust remaining estimate
        new_estimate: New remaining estimate
        increase_by: Amount to increase estimate
        dry_run: If True, show what would be deleted without deleting

    Returns:
        In dry_run mode, returns worklog info. Otherwise None.

    Raises:
        JiraError: If API call fails
    """
    if dry_run:
        # Fetch and return the worklog info for preview
        return client.get_worklog(issue_key, worklog_id)

    # Delete the worklog
    client.delete_worklog(
        issue_key=issue_key,
        worklog_id=worklog_id,
        adjust_estimate=adjust_estimate,
        new_estimate=new_estimate,
        increase_by=increase_by,
    )
    return None


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Delete a worklog (time entry) from a JIRA issue.",
        epilog="""
Examples:
  %(prog)s PROJ-123 --worklog-id 10045
  %(prog)s PROJ-123 --worklog-id 10045 --yes
  %(prog)s PROJ-123 --worklog-id 10045 --adjust-estimate new --new-estimate "2d"
  %(prog)s PROJ-123 --worklog-id 10045 --dry-run
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("issue_key", help="Issue key (e.g., PROJ-123)")
    parser.add_argument(
        "--worklog-id", "-w", required=True, help="Worklog ID to delete"
    )
    parser.add_argument(
        "--adjust-estimate",
        choices=["auto", "leave", "new", "manual"],
        default="auto",
        help="How to adjust remaining estimate (default: auto)",
    )
    parser.add_argument(
        "--new-estimate", help="New remaining estimate (when --adjust-estimate=new)"
    )
    parser.add_argument(
        "--increase-by",
        help="Amount to increase estimate (when --adjust-estimate=manual)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without deleting",
    )
    parser.add_argument(
        "--yes", "-y", action="store_true", help="Skip confirmation prompt"
    )

    args = parser.parse_args(argv)

    try:
        # Validate issue key
        validate_issue_key(args.issue_key)

        # Get client
        client = get_jira_client()

        # Get worklog info first (for confirmation or dry-run)
        worklog = client.get_worklog(args.issue_key, args.worklog_id)

        # Show worklog info
        time_spent = worklog.get("timeSpent", "Unknown")
        time_seconds = worklog.get("timeSpentSeconds", 0)
        author = worklog.get("author", {}).get("displayName", "Unknown")
        started = worklog.get("started", "")[:19].replace("T", " ")

        if args.dry_run:
            print("Dry-run mode - worklog would be deleted:")
            print(f"  Worklog ID: {args.worklog_id}")
            print(f"  Issue: {args.issue_key}")
            print(f"  Time: {time_spent} ({time_seconds} seconds)")
            print(f"  Author: {author}")
            print(f"  Started: {started}")
            print("\nRun without --dry-run to delete.")
            client.close()
            return

        # Confirm unless --yes
        if not args.yes:
            print(f"About to delete worklog from {args.issue_key}:")
            print(f"  Worklog ID: {args.worklog_id}")
            print(f"  Time: {time_spent}")
            print(f"  Author: {author}")
            print(f"  Started: {started}")
            confirm = input("\nAre you sure? (y/N): ")
            if confirm.lower() != "y":
                print("Cancelled.")
                client.close()
                return

        # Delete the worklog
        delete_worklog(
            client,
            args.issue_key,
            args.worklog_id,
            adjust_estimate=args.adjust_estimate,
            new_estimate=args.new_estimate,
            increase_by=args.increase_by,
        )

        print(f"Deleted worklog {args.worklog_id} from {args.issue_key}")
        print(f"  Time removed: {time_spent}")

        client.close()

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(1)


if __name__ == "__main__":
    main()
