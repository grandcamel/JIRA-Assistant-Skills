#!/usr/bin/env python3
"""
Add customers to a JSM service desk.

Usage:
    python add_customer.py SD-1 --account-id 5b10ac8d82e05b22cc7d4ef5
    python add_customer.py SD-1 --account-id "id1,id2,id3"
    python add_customer.py SD-1 --account-id id1 --dry-run
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


def validate_account_ids(account_ids: list) -> bool:
    """
    Validate account IDs list.

    Args:
        account_ids: List of account IDs

    Returns:
        True if valid, False otherwise
    """
    if not account_ids:
        return False
    return all(id.strip() for id in account_ids)


def add_customer_to_service_desk(service_desk_id: str, account_ids: list,
                                  profile: str = None) -> None:
    """
    Add customers to a service desk.

    Args:
        service_desk_id: Service desk ID or key
        account_ids: List of customer account IDs
        profile: JIRA profile to use
    """
    with get_jira_client(profile) as client:
        client.add_customers_to_service_desk(service_desk_id, account_ids)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Add customers to a JSM service desk',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Add single customer:
    %(prog)s SD-1 --account-id 5b10ac8d82e05b22cc7d4ef5

  Add multiple customers:
    %(prog)s SD-1 --account-id "id1,id2,id3"

  Dry-run:
    %(prog)s SD-1 --account-id id1 --dry-run
        """
    )

    parser.add_argument('service_desk_id',
                        help='Service desk ID or key (e.g., SD-1)')
    parser.add_argument('--account-id', required=True,
                        help='Customer account ID(s) (comma-separated)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be added without adding')
    parser.add_argument('--profile',
                        help='JIRA profile to use from config')

    args = parser.parse_args()

    try:
        account_ids = parse_account_ids(args.account_id)

        if not validate_account_ids(account_ids):
            print_error("Invalid or empty account IDs")
            return 1

        if args.dry_run:
            print("DRY RUN MODE - No changes will be made\n")
            print(f"Would add {len(account_ids)} customer(s) to service desk {args.service_desk_id}:")
            for account_id in account_ids:
                print(f"  - {account_id}")
            return 0

        add_customer_to_service_desk(
            service_desk_id=args.service_desk_id,
            account_ids=account_ids,
            profile=args.profile
        )

        print_success(f"Successfully added {len(account_ids)} customer(s) to service desk {args.service_desk_id}")

        return 0

    except JiraError as e:
        print_error(f"Failed to add customer(s): {e}")
        return 1
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
