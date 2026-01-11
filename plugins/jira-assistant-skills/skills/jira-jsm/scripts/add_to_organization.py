#!/usr/bin/env python3
"""
Add users to a JSM organization.

Usage:
    python add_to_organization.py 12345 --account-id 5b10ac8d82e05b22cc7d4ef5
    python add_to_organization.py 12345 --account-id "id1,id2,id3"
    python add_to_organization.py 12345 --account-id "id1,id2" --dry-run
"""

import argparse
import sys

from jira_assistant_skills_lib import (
    JiraError,
    get_jira_client,
    print_error,
    print_success,
)


def parse_account_ids(account_id_string: str) -> list:
    """
    Parse comma-separated account IDs.

    Args:
        account_id_string: Comma-separated account IDs

    Returns:
        List of account IDs
    """
    return [id.strip() for id in account_id_string.split(",") if id.strip()]


def add_users_to_organization_func(
    organization_id: int, account_ids: list
) -> None:
    """
    Add users to an organization.

    Args:
        organization_id: Organization ID
        account_ids: List of user account IDs
    """
    with get_jira_client() as client:
        client.add_users_to_organization(organization_id, account_ids)


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Add users to a JSM organization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Add single user:
    %(prog)s 12345 --account-id 5b10ac8d82e05b22cc7d4ef5

  Add multiple users:
    %(prog)s 12345 --account-id "id1,id2,id3"

  Dry-run:
    %(prog)s 12345 --account-id "id1,id2" --dry-run
        """,
    )

    parser.add_argument("organization_id", type=int, help="Organization ID")
    parser.add_argument(
        "--account-id", required=True, help="User account ID(s) (comma-separated)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be added without adding"
    )

    args = parser.parse_args(argv)

    try:
        account_ids = parse_account_ids(args.account_id)

        if not account_ids:
            print_error("Invalid or empty account IDs")
            return 1

        if args.dry_run:
            print("DRY RUN MODE - No changes will be made\n")
            print(
                f"Would add {len(account_ids)} user(s) to organization {args.organization_id}:"
            )
            for account_id in account_ids:
                print(f"  - {account_id}")
            return 0

        add_users_to_organization_func(
            organization_id=args.organization_id,
            account_ids=account_ids,
        )

        print_success(
            f"Successfully added {len(account_ids)} user(s) to organization {args.organization_id}"
        )

        return 0

    except JiraError as e:
        print_error(f"Failed to add users to organization: {e}")
        return 1
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
