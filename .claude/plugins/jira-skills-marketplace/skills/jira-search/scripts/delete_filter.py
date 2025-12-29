#!/usr/bin/env python3
"""
Delete a saved filter.

Deletes a filter owned by the current user.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add shared library to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import JiraError, print_error


def get_filter_info(client, filter_id: str) -> Dict[str, Any]:
    """
    Get filter info for confirmation.

    Args:
        client: JIRA client
        filter_id: Filter ID

    Returns:
        Filter object
    """
    return client.get_filter(filter_id)


def delete_filter(client, filter_id: str) -> None:
    """
    Delete a filter.

    Args:
        client: JIRA client
        filter_id: Filter ID
    """
    client.delete_filter(filter_id)


def dry_run_delete(client, filter_id: str) -> str:
    """
    Preview what would be deleted.

    Args:
        client: JIRA client
        filter_id: Filter ID

    Returns:
        Dry run message
    """
    filter_data = get_filter_info(client, filter_id)

    lines = [
        "DRY RUN - No changes will be made",
        "",
        f"Would delete filter:",
        f"  ID:   {filter_id}",
        f"  Name: {filter_data.get('name', 'N/A')}",
        f"  JQL:  {filter_data.get('jql', 'N/A')}",
    ]

    return "\n".join(lines)


def confirm_delete(filter_data: Dict[str, Any]) -> bool:
    """
    Prompt for confirmation.

    Args:
        filter_data: Filter object

    Returns:
        True if confirmed
    """
    print("Are you sure you want to delete filter?")
    print(f"  ID:   {filter_data.get('id', 'N/A')}")
    print(f"  Name: {filter_data.get('name', 'N/A')}")
    print(f"  JQL:  {filter_data.get('jql', 'N/A')}")
    print()

    response = input("Type 'yes' to confirm: ")
    return response.strip().lower() == 'yes'


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Delete a saved filter.',
        epilog='''
Examples:
  %(prog)s 10042                   # Delete with confirmation
  %(prog)s 10042 --yes             # Skip confirmation
  %(prog)s 10042 --dry-run         # Preview without deleting
        '''
    )

    parser.add_argument('filter_id',
                        help='Filter ID to delete')
    parser.add_argument('--yes', '-y', action='store_true',
                        help='Skip confirmation prompt')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview what would be deleted')
    parser.add_argument('--profile', '-p',
                        help='JIRA profile to use')

    args = parser.parse_args()

    try:
        client = get_jira_client(args.profile)

        if args.dry_run:
            print(dry_run_delete(client, args.filter_id))
            return

        # Get filter info for confirmation
        filter_data = get_filter_info(client, args.filter_id)

        # Confirm unless --yes
        if not args.yes:
            if not confirm_delete(filter_data):
                print("Cancelled.")
                return

        # Delete
        delete_filter(client, args.filter_id)

        print(f"Filter {args.filter_id} deleted successfully.")

    except JiraError as e:
        print_error(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
