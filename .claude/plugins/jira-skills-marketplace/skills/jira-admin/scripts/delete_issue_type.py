#!/usr/bin/env python3
"""
Delete an issue type from JIRA.

Deletes an issue type, optionally migrating existing issues to an alternative type.
Requires 'Administer Jira' global permission.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import JiraError, print_error
from formatters import format_table


def get_alternatives_for_type(
    issue_type_id: str,
    client=None,
    profile: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get alternative issue types for migration.

    Args:
        issue_type_id: Issue type ID to get alternatives for
        client: JiraClient instance (for testing)
        profile: Configuration profile name

    Returns:
        List of alternative issue types

    Raises:
        JiraError: On API failure
    """
    if client is None:
        client = get_jira_client(profile=profile)

    try:
        return client.get_issue_type_alternatives(issue_type_id)
    finally:
        if client:
            client.close()


def delete_issue_type(
    issue_type_id: str,
    alternative_id: Optional[str] = None,
    client=None,
    profile: Optional[str] = None,
    dry_run: bool = False
) -> bool:
    """
    Delete an issue type.

    Args:
        issue_type_id: Issue type ID to delete
        alternative_id: Alternative issue type ID for existing issues
        client: JiraClient instance (for testing)
        profile: Configuration profile name
        dry_run: If True, simulate without actual deletion

    Returns:
        True if successful

    Raises:
        NotFoundError: If issue type not found
        PermissionError: If lacking admin permission
        JiraError: On API failure (e.g., issues exist without alternative)
    """
    if dry_run:
        return True

    if client is None:
        client = get_jira_client(profile=profile)

    try:
        client.delete_issue_type(
            issue_type_id,
            alternative_issue_type_id=alternative_id
        )
        return True
    finally:
        if client:
            client.close()


def format_alternatives(alternatives: List[Dict[str, Any]]) -> str:
    """Format alternatives for display."""
    if not alternatives:
        return "No alternative issue types available."

    headers = ['ID', 'Name']
    rows = [[alt.get('id', ''), alt.get('name', '')] for alt in alternatives]

    return format_table(headers, rows)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Delete an issue type from JIRA',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Delete issue type (no existing issues)
  python delete_issue_type.py 10005

  # Delete and migrate issues to alternative type
  python delete_issue_type.py 10005 --alternative-id 10001

  # Show alternative types before deleting
  python delete_issue_type.py 10005 --show-alternatives

  # Dry run (simulate deletion)
  python delete_issue_type.py 10005 --dry-run

  # Force delete without confirmation
  python delete_issue_type.py 10005 --force

  # Use specific profile
  python delete_issue_type.py 10005 --profile production

Note:
  Requires 'Administer Jira' global permission.
  If issues exist with this type, you must specify --alternative-id.
  Use --show-alternatives to see valid alternative types.
"""
    )

    parser.add_argument(
        'issue_type_id',
        help='Issue type ID to delete'
    )
    parser.add_argument(
        '--alternative-id',
        help='Alternative issue type ID for existing issues'
    )
    parser.add_argument(
        '--show-alternatives',
        action='store_true',
        help='Show alternative issue types and exit'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate deletion without making changes'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Skip confirmation prompt'
    )
    parser.add_argument(
        '--profile',
        help='Configuration profile to use'
    )

    args = parser.parse_args()

    try:
        # Show alternatives only
        if args.show_alternatives:
            alternatives = get_alternatives_for_type(
                issue_type_id=args.issue_type_id,
                profile=args.profile
            )
            print(f"Alternative issue types for ID {args.issue_type_id}:")
            print(format_alternatives(alternatives))
            return

        # Confirmation prompt
        if not args.force and not args.dry_run:
            confirm = input(
                f"Are you sure you want to delete issue type {args.issue_type_id}? "
                "This cannot be undone. [y/N]: "
            )
            if confirm.lower() != 'y':
                print("Deletion cancelled.")
                return

        # Perform deletion
        if args.dry_run:
            print(f"[DRY RUN] Would delete issue type {args.issue_type_id}")
            if args.alternative_id:
                print(f"[DRY RUN] Issues would be migrated to type {args.alternative_id}")
        else:
            delete_issue_type(
                issue_type_id=args.issue_type_id,
                alternative_id=args.alternative_id,
                profile=args.profile
            )
            print(f"Issue type {args.issue_type_id} deleted successfully.")
            if args.alternative_id:
                print(f"Existing issues migrated to type {args.alternative_id}.")

    except JiraError as e:
        print_error(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
