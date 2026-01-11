#!/usr/bin/env python3
"""
Get approvals for a JSM request.

This script retrieves approval requests for JSM requests, showing approval status,
approvers, and action hints for pending approvals.
"""

import argparse
import json
import sys
from datetime import datetime

# Add shared lib to path
from jira_assistant_skills_lib import handle_errors


def get_jira_client():
    """Get JIRA client (overridable for testing)."""
    from jira_assistant_skills_lib import get_jira_client as _get_client

    return _get_client()


def format_approvals_table(approvals: list, issue_key: str) -> None:
    """Format approvals as table."""
    if not approvals:
        print("No approvals found.")
        return

    # Count by status
    pending_count = sum(1 for a in approvals if a.get("finalDecision") == "pending")
    approved_count = sum(1 for a in approvals if a.get("finalDecision") == "approve")
    declined_count = sum(1 for a in approvals if a.get("finalDecision") == "decline")

    print(
        f"\nApprovals for {issue_key} ({pending_count} pending, {approved_count} approved, {declined_count} declined):\n"
    )

    print(
        f"{'ID':<10} {'Name':<25} {'Status':<12} {'Approvers':<25} {'Created':<20} {'Completed'}"
    )
    print("─" * 120)

    for approval in approvals:
        approval_id = approval.get("id", "unknown")
        name = approval.get("name", "Unknown")[:24]
        decision = approval.get("finalDecision", "unknown").upper()

        # Format approvers
        approvers = approval.get("approvers", [])
        if len(approvers) == 1:
            approvers_str = approvers[0].get("displayName", "Unknown")[:24]
        elif len(approvers) > 1:
            approvers_str = f"{approvers[0].get('displayName', 'Unknown')[:15]} (+{len(approvers) - 1})"
        else:
            approvers_str = "None"

        # Format dates
        created = approval.get("createdDate", "")
        completed = approval.get("completedDate") or "-"

        try:
            created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            created_str = created_dt.strftime("%Y-%m-%d %H:%M")
        except:
            created_str = created[:16] if created else "Unknown"

        if completed != "-":
            try:
                completed_dt = datetime.fromisoformat(completed.replace("Z", "+00:00"))
                completed_str = completed_dt.strftime("%Y-%m-%d %H:%M")
            except:
                completed_str = completed[:16]
        else:
            completed_str = "-"

        print(
            f"{approval_id:<10} {name:<25} {decision:<12} {approvers_str:<25} {created_str:<20} {completed_str}"
        )

    # Show action hints for pending approvals
    if pending_count > 0:
        print("\nTo approve/decline:")
        print(f"  python approve_request.py {issue_key} --approval-id <APPROVAL-ID>")
        print(f"  python decline_request.py {issue_key} --approval-id <APPROVAL-ID>")


@handle_errors
def main(args=None):
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Get approvals for JSM request",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Pending approvals (default)
  %(prog)s REQ-123

  # All approvals (including completed)
  %(prog)s REQ-123 --all

  # Specific approval
  %(prog)s REQ-123 --id 10050

  # JSON output
  %(prog)s REQ-123 --output json
        """,
    )

    parser.add_argument("issue_key", help="Request key (e.g., REQ-123)")
    parser.add_argument("--id", help="Get specific approval by ID")
    parser.add_argument(
        "--pending", action="store_true", help="Show only pending approvals (default)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="show_all",
        help="Show all approvals (pending, approved, declined)",
    )
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    parsed_args = parser.parse_args(args)

    # Get JIRA client
    jira = get_jira_client()

    # Get specific approval by ID
    if parsed_args.id:
        approval = jira.get_request_approval(parsed_args.issue_key, parsed_args.id)
        if parsed_args.output == "json":
            print(json.dumps(approval, indent=2))
        else:
            format_approvals_table([approval], parsed_args.issue_key)
        return 0

    # Get all approvals
    response = jira.get_request_approvals(parsed_args.issue_key, start=0, limit=100)
    approvals = response.get("values", [])

    # Filter to pending only if not --all
    if not parsed_args.show_all:
        approvals = [a for a in approvals if a.get("finalDecision") == "pending"]

    # Output
    if parsed_args.output == "json":
        print(json.dumps(approvals, indent=2))
    else:
        format_approvals_table(approvals, parsed_args.issue_key)

    return 0


if __name__ == "__main__":
    sys.exit(main())
