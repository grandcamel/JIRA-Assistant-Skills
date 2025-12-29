#!/usr/bin/env python3
"""
Approve an approval request for a JSM request.

This script approves pending approval requests in JSM workflows,
typically used for change management and approval processes.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add shared lib to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import handle_errors, print_error, JiraError, NotFoundError, PermissionError


def get_jira_client(profile=None):
    """Get JIRA client (overridable for testing)."""
    from config_manager import get_jira_client as _get_client
    return _get_client(profile)


@handle_errors
def main(args=None):
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Approve JSM approval request',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Approve single approval
  %(prog)s REQ-123 --approval-id 10050

  # Skip confirmation
  %(prog)s REQ-123 --approval-id 10050 --yes

  # Dry run (show what would be approved)
  %(prog)s REQ-123 --approval-id 10050 --dry-run
        """
    )

    parser.add_argument('issue_key',
                        help='Request key (e.g., REQ-123)')
    parser.add_argument('--approval-id', required=True, action='append',
                        help='Approval ID to approve (can specify multiple times)')
    parser.add_argument('--yes', '-y', action='store_true',
                        help='Skip confirmation prompt')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be approved without making changes')
    parser.add_argument('--profile',
                        help='JIRA profile to use')

    parsed_args = parser.parse_args(args)

    # Get JIRA client
    jira = get_jira_client(parsed_args.profile)

    # Process each approval ID
    for approval_id in parsed_args.approval_id:
        # Get approval details for confirmation
        try:
            approval = jira.get_request_approval(parsed_args.issue_key, approval_id)
        except (JiraError, NotFoundError, PermissionError) as e:
            print_error(f"Could not get approval {approval_id}: {e}")
            continue

        approval_name = approval.get('name', 'Unknown')
        approvers = approval.get('approvers', [])
        approvers_str = ', '.join([a.get('displayName', 'Unknown') for a in approvers])
        created = approval.get('createdDate', '')

        # Format created date
        try:
            created_dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
            created_str = created_dt.strftime('%Y-%m-%d %H:%M')
        except:
            created_str = created[:16] if created else 'Unknown'

        # Show approval details
        print(f"\nApprove approval for {parsed_args.issue_key}?")
        print(f"\nApproval ID:   {approval_id}")
        print(f"Name:          {approval_name}")
        print(f"Approvers:     {approvers_str}")
        print(f"Created:       {created_str}")

        if parsed_args.dry_run:
            print(f"\n[DRY RUN] Would approve approval {approval_id} for {parsed_args.issue_key}")
            continue

        # Confirm unless --yes
        if not parsed_args.yes:
            confirm = input("\nType 'yes' to confirm: ")
            if confirm.lower() != 'yes':
                print("Cancelled.")
                continue

        # Approve the approval
        result = jira.answer_approval(parsed_args.issue_key, approval_id, 'approve')

        completed = result.get('completedDate', '')
        try:
            completed_dt = datetime.fromisoformat(completed.replace('Z', '+00:00'))
            completed_str = completed_dt.strftime('%Y-%m-%d %H:%M')
        except:
            completed_str = completed[:16] if completed else 'Just now'

        print(f"\nApproval {approval_id} APPROVED for {parsed_args.issue_key}.")
        print(f"\nStatus: approve")
        print(f"Completed: {completed_str}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
