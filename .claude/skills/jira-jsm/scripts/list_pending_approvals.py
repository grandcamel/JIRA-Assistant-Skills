#!/usr/bin/env python3
"""
List all pending approvals for current user (agent queue view).

This script shows a queue of all pending approvals across requests where
the current user is an approver, providing an agent-level view of their
approval workload.
"""

import sys
import argparse
import json
from pathlib import Path
from datetime import datetime

# Add shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import handle_errors


def get_jira_client(profile=None):
    """Get JIRA client (overridable for testing)."""
    from config_manager import get_jira_client as _get_client
    return _get_client(profile)


def format_pending_approvals_table(approvals: list, user_email: str = None) -> None:
    """Format pending approvals as table."""
    if not approvals:
        print("No pending approvals found.")
        return

    user_str = f" for {user_email}" if user_email else ""
    print(f"\nPending Approvals{user_str} ({len(approvals)} total):\n")

    print(f"{'Request':<12} {'Summary':<35} {'Approval ID':<12} {'Approval Name':<25} {'Created':<20} {'Action'}")
    print("─" * 140)

    for approval in approvals:
        request_key = approval.get('requestKey', 'Unknown')
        summary = approval.get('summary', '')[:34]
        approval_id = approval.get('approvalId', 'Unknown')
        approval_name = approval.get('approvalName', 'Unknown')[:24]
        created = approval.get('created', '')

        # Format date
        try:
            created_dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
            created_str = created_dt.strftime('%Y-%m-%d %H:%M')
        except:
            created_str = created[:16] if created else 'Unknown'

        action = "Approve | Decline"

        print(f"{request_key:<12} {summary:<35} {approval_id:<12} {approval_name:<25} {created_str:<20} {action}")

    print("\nTo approve/decline:")
    print("  python approve_request.py <REQUEST-KEY> --approval-id <APPROVAL-ID>")
    print("  python decline_request.py <REQUEST-KEY> --approval-id <APPROVAL-ID>")


@handle_errors
def main(args=None):
    """Main function."""
    parser = argparse.ArgumentParser(
        description='List all pending approvals (agent queue view)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # All pending approvals for current user
  %(prog)s

  # Filter by project
  %(prog)s --project SD

  # For specific user (admin only)
  %(prog)s --user alice@company.com

  # JSON output
  %(prog)s --output json
        """
    )

    parser.add_argument('--project',
                        help='Filter by project key')
    parser.add_argument('--user',
                        help='Show approvals for specific user (admin only)')
    parser.add_argument('--output', choices=['text', 'json'], default='text',
                        help='Output format (default: text)')
    parser.add_argument('--profile',
                        help='JIRA profile to use')

    parsed_args = parser.parse_args(args)

    # Get JIRA client
    jira = get_jira_client(parsed_args.profile)

    # Build JQL to find requests with pending approvals
    jql_parts = ['status != Resolved']

    if parsed_args.project:
        jql_parts.append(f'project = {parsed_args.project}')

    # Note: User filtering would require additional JQL or post-filtering
    # For now, we get all pending approvals and filter by canAnswerApproval

    jql = ' AND '.join(jql_parts)

    # Search for requests
    search_result = jira.search_issues(jql, max_results=100)

    pending_approvals = []

    # For each request, check for pending approvals
    for issue in search_result.get('issues', []):
        issue_key = issue['key']
        summary = issue.get('fields', {}).get('summary', '')

        try:
            approvals_resp = jira.get_request_approvals(issue_key)
            approvals = approvals_resp.get('values', [])

            for approval in approvals:
                if approval.get('finalDecision') == 'pending':
                    # Check if current user can answer this approval
                    if approval.get('canAnswerApproval', False):
                        pending_approvals.append({
                            'requestKey': issue_key,
                            'approvalId': approval.get('id'),
                            'approvalName': approval.get('name'),
                            'created': approval.get('createdDate'),
                            'summary': summary
                        })
        except Exception:
            # Skip requests where we can't get approvals (e.g., permissions)
            continue

    # Output
    if parsed_args.output == 'json':
        print(json.dumps(pending_approvals, indent=2))
    else:
        format_pending_approvals_table(pending_approvals, parsed_args.user)

    return 0


if __name__ == '__main__':
    sys.exit(main())
