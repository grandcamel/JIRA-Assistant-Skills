#!/usr/bin/env python3
"""
Remove participants from a request.

Usage:
    python remove_participant.py REQ-123 --account-id 5b10ac8d82e05b22cc7d4ef5 --yes
    python remove_participant.py REQ-123 --account-id "id1,id2" --yes
    python remove_participant.py REQ-123 --account-id id1 --dry-run
"""

import sys
import os
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import print_error, JiraError
from formatters import print_success


def parse_account_ids(account_id_string: str) -> list:
    """
    Parse comma-separated account IDs.

    Args:
        account_id_string: Comma-separated account IDs

    Returns:
        List of account IDs
    """
    return [id.strip() for id in account_id_string.split(',') if id.strip()]


def remove_participant_func(issue_key: str, account_ids: list = None,
                             usernames: list = None, profile: str = None) -> dict:
    """
    Remove participants from a request.

    Args:
        issue_key: Request issue key
        account_ids: List of user account IDs
        usernames: List of usernames (legacy)
        profile: JIRA profile to use

    Returns:
        Updated participants data
    """
    with get_jira_client(profile) as client:
        return client.remove_request_participants(issue_key, account_ids=account_ids,
                                                   usernames=usernames)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Remove participants from a request',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Remove single participant (with confirmation skip):
    %(prog)s REQ-123 --account-id 5b10ac8d82e05b22cc7d4ef5 --yes

  Remove multiple participants:
    %(prog)s REQ-123 --account-id "id1,id2" --yes

  Dry-run:
    %(prog)s REQ-123 --account-id id1 --dry-run
        """
    )

    parser.add_argument('issue_key',
                        help='Request issue key (e.g., REQ-123)')
    parser.add_argument('--account-id',
                        help='User account ID(s) (comma-separated)')
    parser.add_argument('--username',
                        help='Username(s) (comma-separated, legacy)')
    parser.add_argument('--yes', '-y', action='store_true',
                        help='Skip confirmation prompt')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be removed without removing')
    parser.add_argument('--profile',
                        help='JIRA profile to use from config')

    args = parser.parse_args()

    try:
        if not args.account_id and not args.username:
            print_error("Either --account-id or --username is required")
            return 1

        account_ids = parse_account_ids(args.account_id) if args.account_id else None
        usernames = parse_account_ids(args.username) if args.username else None

        if args.dry_run:
            print("DRY RUN MODE - No changes will be made\n")
            print(f"Would remove participants from request {args.issue_key}:")
            if account_ids:
                print(f"  Account IDs: {', '.join(account_ids)}")
            if usernames:
                print(f"  Usernames: {', '.join(usernames)}")
            return 0

        if not args.yes:
            print_error("Confirmation required. Use --yes flag to confirm removal.")
            return 1

        remove_participant_func(
            issue_key=args.issue_key,
            account_ids=account_ids,
            usernames=usernames,
            profile=args.profile
        )

        count = (len(account_ids) if account_ids else 0) + (len(usernames) if usernames else 0)
        print_success(f"Successfully removed {count} participant(s) from request {args.issue_key}")

        return 0

    except JiraError as e:
        print_error(f"Failed to remove participants: {e}")
        return 1
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
