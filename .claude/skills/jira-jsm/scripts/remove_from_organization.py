#!/usr/bin/env python3
"""
Remove users from a JSM organization.

Usage:
    python remove_from_organization.py 12345 --account-id 5b10ac8d82e05b22cc7d4ef5 --yes
    python remove_from_organization.py 12345 --account-id "id1,id2" --yes
    python remove_from_organization.py 12345 --account-id id1 --dry-run
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


def remove_users_from_organization_func(organization_id: int, account_ids: list,
                                         profile: str = None) -> None:
    """
    Remove users from an organization.

    Args:
        organization_id: Organization ID
        account_ids: List of user account IDs
        profile: JIRA profile to use
    """
    with get_jira_client(profile) as client:
        client.remove_users_from_organization(organization_id, account_ids)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Remove users from a JSM organization',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Remove single user (with confirmation skip):
    %(prog)s 12345 --account-id 5b10ac8d82e05b22cc7d4ef5 --yes

  Remove multiple users:
    %(prog)s 12345 --account-id "id1,id2" --yes

  Dry-run:
    %(prog)s 12345 --account-id id1 --dry-run
        """
    )

    parser.add_argument('organization_id', type=int,
                        help='Organization ID')
    parser.add_argument('--account-id', required=True,
                        help='User account ID(s) (comma-separated)')
    parser.add_argument('--yes', '-y', action='store_true',
                        help='Skip confirmation prompt')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be removed without removing')
    parser.add_argument('--profile',
                        help='JIRA profile to use from config')

    args = parser.parse_args()

    try:
        account_ids = parse_account_ids(args.account_id)

        if not account_ids:
            print_error("Invalid or empty account IDs")
            return 1

        if args.dry_run:
            print("DRY RUN MODE - No changes will be made\n")
            print(f"Would remove {len(account_ids)} user(s) from organization {args.organization_id}:")
            for account_id in account_ids:
                print(f"  - {account_id}")
            return 0

        if not args.yes:
            print_error("Confirmation required. Use --yes flag to confirm removal.")
            return 1

        remove_users_from_organization_func(
            organization_id=args.organization_id,
            account_ids=account_ids,
            profile=args.profile
        )

        print_success(f"Successfully removed {len(account_ids)} user(s) from organization {args.organization_id}")

        return 0

    except JiraError as e:
        print_error(f"Failed to remove users from organization: {e}")
        return 1
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
