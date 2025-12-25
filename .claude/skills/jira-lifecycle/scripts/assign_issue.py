#!/usr/bin/env python3
"""
Assign or reassign a JIRA issue.

Usage:
    python assign_issue.py PROJ-123 --user user@example.com
    python assign_issue.py PROJ-123 --user 5b10ac8d82e05b22cc7d4ef5
    python assign_issue.py PROJ-123 --self
    python assign_issue.py PROJ-123 --unassign
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import print_error, JiraError, ValidationError
from validators import validate_issue_key
from formatters import print_success


def assign_issue(issue_key: str, user: str = None, assign_to_self: bool = False,
                unassign: bool = False, profile: str = None) -> None:
    """
    Assign or reassign an issue.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        user: User account ID or email
        assign_to_self: Assign to current user
        unassign: Remove assignee
        profile: JIRA profile to use
    """
    issue_key = validate_issue_key(issue_key)

    if sum([bool(user), assign_to_self, unassign]) != 1:
        raise ValidationError("Specify exactly one of: --user, --self, or --unassign")

    client = get_jira_client(profile)

    fields = {}

    if unassign:
        fields['assignee'] = None
    elif assign_to_self:
        fields['assignee'] = {'accountId': '-1'}
    else:
        if '@' in user:
            fields['assignee'] = {'emailAddress': user}
        else:
            fields['assignee'] = {'accountId': user}

    client.update_issue(issue_key, fields, notify_users=True)
    client.close()


def main():
    parser = argparse.ArgumentParser(
        description='Assign or reassign a JIRA issue',
        epilog='Example: python assign_issue.py PROJ-123 --user user@example.com'
    )

    parser.add_argument('issue_key',
                       help='Issue key (e.g., PROJ-123)')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--user', '-u',
                      help='User to assign (account ID or email)')
    group.add_argument('--self', '-s',
                      action='store_true',
                      help='Assign to yourself')
    group.add_argument('--unassign',
                      action='store_true',
                      help='Remove assignee')

    parser.add_argument('--profile',
                       help='JIRA profile to use (default: from config)')

    args = parser.parse_args()

    try:
        assign_issue(
            issue_key=args.issue_key,
            user=args.user,
            assign_to_self=args.self,
            unassign=args.unassign,
            profile=args.profile
        )

        if args.unassign:
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
