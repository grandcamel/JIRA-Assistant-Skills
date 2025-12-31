#!/usr/bin/env python3
"""
Manage watchers on a JIRA issue.

Usage:
    python manage_watchers.py PROJ-123 --add user@example.com
    python manage_watchers.py PROJ-123 --remove user@example.com
    python manage_watchers.py PROJ-123 --list
"""

import sys
import argparse
from pathlib import Path


from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError, ValidationError
from jira_assistant_skills_lib import validate_issue_key
from jira_assistant_skills_lib import print_success, format_table
from jira_assistant_skills_lib import resolve_user_to_account_id, UserNotFoundError


def list_watchers(issue_key: str, profile: str = None) -> list:
    """List watchers on an issue."""
    issue_key = validate_issue_key(issue_key)
    client = get_jira_client(profile)
    result = client.get(f'/rest/api/3/issue/{issue_key}/watchers',
                       operation=f"get watchers for {issue_key}")
    client.close()
    return result.get('watchers', [])


def add_watcher(issue_key: str, user: str, profile: str = None) -> None:
    """Add a watcher to an issue."""
    issue_key = validate_issue_key(issue_key)
    client = get_jira_client(profile)

    try:
        account_id = resolve_user_to_account_id(client, user)
    except UserNotFoundError as e:
        client.close()
        raise ValidationError(str(e))

    client.post(f'/rest/api/3/issue/{issue_key}/watchers',
               data=f'"{account_id}"',
               operation=f"add watcher to {issue_key}")
    client.close()


def remove_watcher(issue_key: str, user: str, profile: str = None) -> None:
    """Remove a watcher from an issue."""
    issue_key = validate_issue_key(issue_key)
    client = get_jira_client(profile)

    try:
        account_id = resolve_user_to_account_id(client, user)
    except UserNotFoundError as e:
        client.close()
        raise ValidationError(str(e))

    client.delete(f'/rest/api/3/issue/{issue_key}/watchers?accountId={account_id}',
                 operation=f"remove watcher from {issue_key}")
    client.close()


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description='Manage watchers on a JIRA issue',
        epilog='Example: python manage_watchers.py PROJ-123 --add user@example.com'
    )

    parser.add_argument('issue_key',
                       help='Issue key (e.g., PROJ-123)')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--add',
                      help='Add watcher (account ID or email)')
    group.add_argument('--remove',
                      help='Remove watcher (account ID or email)')
    group.add_argument('--list', '-l',
                      action='store_true',
                      help='List current watchers')

    parser.add_argument('--profile',
                       help='JIRA profile to use (default: from config)')

    args = parser.parse_args(argv)

    try:
        if args.list:
            watchers = list_watchers(args.issue_key, profile=args.profile)
            if not watchers:
                print(f"No watchers on {args.issue_key}")
            else:
                data = [
                    {
                        'Name': w.get('displayName', ''),
                        'Email': w.get('emailAddress', '')
                    }
                    for w in watchers
                ]
                print(format_table(data))

        elif args.add:
            add_watcher(args.issue_key, args.add, profile=args.profile)
            print_success(f"Added {args.add} as watcher to {args.issue_key}")

        elif args.remove:
            remove_watcher(args.issue_key, args.remove, profile=args.profile)
            print_success(f"Removed {args.remove} as watcher from {args.issue_key}")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
