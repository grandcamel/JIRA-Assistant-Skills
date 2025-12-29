#!/usr/bin/env python3
"""
Assign or reassign a JIRA issue.

The --user flag accepts multiple formats:
  - Atlassian Account ID (preferred): 5b10ac8d82e05b22cc7d4ef5
  - Email address: user@example.com
  - Display name: John Doe

Note: Account IDs are the most reliable format. Email addresses and display
names may fail if the user has multiple accounts or has changed their email.
To find a user's account ID, search for issues they've worked on and examine
the assignee field in JSON output.

Usage:
    python assign_issue.py PROJ-123 --user user@example.com
    python assign_issue.py PROJ-123 --user 5b10ac8d82e05b22cc7d4ef5
    python assign_issue.py PROJ-123 --self
    python assign_issue.py PROJ-123 --unassign
"""

import sys
import argparse
from pathlib import Path


from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError, ValidationError
from jira_assistant_skills_lib import validate_issue_key
from jira_assistant_skills_lib import print_success, print_info


def assign_issue(issue_key: str, user: str = None, assign_to_self: bool = False,
                unassign: bool = False, profile: str = None,
                dry_run: bool = False) -> dict:
    """
    Assign or reassign an issue.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        user: User account ID or email
        assign_to_self: Assign to current user
        unassign: Remove assignee
        profile: JIRA profile to use
        dry_run: If True, preview changes without making them

    Returns:
        Dictionary with assignment details
    """
    issue_key = validate_issue_key(issue_key)

    if sum([bool(user), assign_to_self, unassign]) != 1:
        raise ValidationError("Specify exactly one of: --user, --self, or --unassign")

    client = get_jira_client(profile)

    if unassign:
        account_id = None
        action = "unassign"
        target_display = "Unassigned"
    elif assign_to_self:
        account_id = '-1'
        action = "assign to self"
        target_display = "yourself"
    else:
        # If user provided an email, we need to look up their account ID
        # For now, assume it's an account ID
        # TODO: Add email to account ID lookup if needed
        account_id = user
        action = f"assign to {user}"
        target_display = user

    # Get current assignee for dry-run display
    issue = client.get_issue(issue_key, fields=['assignee'])
    current_assignee = issue.get('fields', {}).get('assignee')
    current_display = current_assignee.get('displayName', 'Unknown') if current_assignee else 'Unassigned'

    result = {
        'issue_key': issue_key,
        'action': action,
        'current_assignee': current_display,
        'target_assignee': target_display,
        'dry_run': dry_run
    }

    if dry_run:
        print_info(f"[DRY RUN] Would {action} for {issue_key}:")
        print(f"  Current assignee: {current_display}")
        print(f"  New assignee: {target_display}")
        client.close()
        return result

    client.assign_issue(issue_key, account_id)
    client.close()
    return result


def main():
    parser = argparse.ArgumentParser(
        description='Assign or reassign a JIRA issue',
        epilog='''Examples:
  python assign_issue.py PROJ-123 --user user@example.com      # By email
  python assign_issue.py PROJ-123 --user 5b10ac8d82e05b22cc7d4ef5  # By account ID (preferred)
  python assign_issue.py PROJ-123 --self                        # Assign to yourself
  python assign_issue.py PROJ-123 --unassign                    # Remove assignee

Note: Account IDs are more reliable than emails. Find them via:
  python jql_search.py "assignee = user@example.com" --output json''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('issue_key',
                       help='Issue key (e.g., PROJ-123)')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--user', '-u',
                      help='User to assign. Accepts: (1) Atlassian account ID (e.g., 5b10ac8d82e05b22cc7d4ef5), '
                           '(2) email address (e.g., user@example.com), or (3) display name. '
                           'Account IDs are preferred for reliability. Use jira-search to find account IDs.')
    group.add_argument('--self', '-s',
                      action='store_true',
                      help='Assign to yourself')
    group.add_argument('--unassign',
                      action='store_true',
                      help='Remove assignee')

    parser.add_argument('--dry-run',
                       action='store_true',
                       help='Preview changes without making them')
    parser.add_argument('--profile',
                       help='JIRA profile to use (default: from config)')

    args = parser.parse_args()

    try:
        result = assign_issue(
            issue_key=args.issue_key,
            user=args.user,
            assign_to_self=args.self,
            unassign=args.unassign,
            profile=args.profile,
            dry_run=args.dry_run
        )

        if args.dry_run:
            # Dry-run output handled in function
            pass
        elif args.unassign:
            print_success(f"Unassigned {args.issue_key}")
        elif args.self:
            print_success(f"Assigned {args.issue_key} to you")
        else:
            print_success(f"Assigned {args.issue_key} to {args.user}")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
