#!/usr/bin/env python3
"""
Add participants to a request.

Usage:
    python add_participant.py REQ-123 --account-id 5b10ac8d82e05b22cc7d4ef5
    python add_participant.py REQ-123 --account-id "id1,id2,id3"
    python add_participant.py REQ-123 --account-id "id1,id2" --dry-run
"""

import sys
import os
import argparse
from pathlib import Path


from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError
from jira_assistant_skills_lib import print_success


def parse_account_ids(account_id_string: str) -> list:
    """
    Parse comma-separated account IDs.

    Args:
        account_id_string: Comma-separated account IDs

    Returns:
        List of account IDs
    """
    return [id.strip() for id in account_id_string.split(',') if id.strip()]


def add_participant_func(issue_key: str, account_ids: list = None,
                          usernames: list = None, profile: str = None) -> dict:
    """
    Add participants to a request.

    Args:
        issue_key: Request issue key
        account_ids: List of user account IDs
        usernames: List of usernames (legacy)
        profile: JIRA profile to use

    Returns:
        Updated participants data
    """
    with get_jira_client(profile) as client:
        return client.add_request_participants(issue_key, account_ids=account_ids,
                                                usernames=usernames)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Add participants to a request',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Add single participant:
    %(prog)s REQ-123 --account-id 5b10ac8d82e05b22cc7d4ef5

  Add multiple participants:
    %(prog)s REQ-123 --account-id "id1,id2,id3"

  Dry-run:
    %(prog)s REQ-123 --account-id "id1,id2" --dry-run
        """
    )

    parser.add_argument('issue_key',
                        help='Request issue key (e.g., REQ-123)')
    parser.add_argument('--account-id',
                        help='User account ID(s) (comma-separated)')
    parser.add_argument('--username',
                        help='Username(s) (comma-separated, legacy)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be added without adding')
    parser.add_argument('--profile',
                        help='JIRA profile to use from config')

    args = parser.parse_args()

    try:
        if not args.account_id and not args.username:
            print_error("Either --account-id or --username is required")
            return 1

        account_ids = parse_account_ids(args.account_id) if args.account_id else None
        usernames = parse_account_ids(args.username) if args.username else None

        # Validate parsed lists are non-empty
        if account_ids is not None and len(account_ids) == 0:
            print_error("Account ID list is empty after parsing. Provide valid comma-separated IDs.")
            return 1
        if usernames is not None and len(usernames) == 0:
            print_error("Username list is empty after parsing. Provide valid comma-separated usernames.")
            return 1

        if args.dry_run:
            print("DRY RUN MODE - No changes will be made\n")
            print(f"Would add participants to request {args.issue_key}:")
            if account_ids:
                print(f"  Account IDs: {', '.join(account_ids)}")
            if usernames:
                print(f"  Usernames: {', '.join(usernames)}")
            return 0

        add_participant_func(
            issue_key=args.issue_key,
            account_ids=account_ids,
            usernames=usernames,
            profile=args.profile
        )

        count = (len(account_ids) if account_ids else 0) + (len(usernames) if usernames else 0)
        print_success(f"Successfully added {count} participant(s) to request {args.issue_key}")

        return 0

    except JiraError as e:
        print_error(f"Failed to add participants: {e}")
        return 1
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
