#!/usr/bin/env python3
"""
Remove customers from a JSM service desk.

Usage:
    python remove_customer.py SD-1 --account-id 5b10ac8d82e05b22cc7d4ef5 --yes
    python remove_customer.py SD-1 --account-id "id1,id2" --yes
    python remove_customer.py SD-1 --account-id id1 --dry-run
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


def remove_customer_from_service_desk(
    service_desk_id: str, account_ids: list
) -> None:
    """
    Remove customers from a service desk.

    Args:
        service_desk_id: Service desk ID or key
        account_ids: List of customer account IDs
    """
    with get_jira_client() as client:
        client.remove_customers_from_service_desk(service_desk_id, account_ids)


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Remove customers from a JSM service desk",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Remove single customer (with confirmation skip):
    %(prog)s SD-1 --account-id 5b10ac8d82e05b22cc7d4ef5 --yes

  Remove multiple customers:
    %(prog)s SD-1 --account-id "id1,id2" --yes

  Dry-run:
    %(prog)s SD-1 --account-id id1 --dry-run
        """,
    )

    parser.add_argument("service_desk_id", help="Service desk ID or key (e.g., SD-1)")
    parser.add_argument(
        "--account-id", required=True, help="Customer account ID(s) (comma-separated)"
    )
    parser.add_argument(
        "--yes", "-y", action="store_true", help="Skip confirmation prompt"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without removing",
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
                f"Would remove {len(account_ids)} customer(s) from service desk {args.service_desk_id}:"
            )
            for account_id in account_ids:
                print(f"  - {account_id}")
            return 0

        if not args.yes:
            print_error("Confirmation required. Use --yes flag to confirm removal.")
            return 1

        remove_customer_from_service_desk(
            service_desk_id=args.service_desk_id,
            account_ids=account_ids,
        )

        print_success(
            f"Successfully removed {len(account_ids)} customer(s) from service desk {args.service_desk_id}"
        )

        return 0

    except JiraError as e:
        print_error(f"Failed to remove customer(s): {e}")
        return 1
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
