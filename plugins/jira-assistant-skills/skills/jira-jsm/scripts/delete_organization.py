#!/usr/bin/env python3
"""
Delete a JSM organization.

Usage:
    python delete_organization.py 12345 --yes
    python delete_organization.py 12345 --dry-run
"""

import sys
import os
import argparse
from pathlib import Path


from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError
from jira_assistant_skills_lib import print_success


def delete_organization_func(organization_id: int, profile: str = None) -> None:
    """
    Delete an organization.

    Args:
        organization_id: Organization ID
        profile: JIRA profile to use
    """
    with get_jira_client(profile) as client:
        client.delete_organization(organization_id)


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Delete a JSM organization',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Delete organization (with confirmation skip):
    %(prog)s 12345 --yes

  Dry-run:
    %(prog)s 12345 --dry-run
        """
    )

    parser.add_argument('organization_id', type=int,
                        help='Organization ID')
    parser.add_argument('--yes', '-y', action='store_true',
                        help='Skip confirmation prompt')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be deleted without deleting')
    parser.add_argument('--profile',
                        help='JIRA profile to use from config')

    args = parser.parse_args(argv)

    try:
        if args.dry_run:
            print("DRY RUN MODE - No changes will be made\n")
            print(f"Would delete organization {args.organization_id}")
            return 0

        if not args.yes:
            print_error("Confirmation required. Use --yes flag to confirm deletion.")
            return 1

        delete_organization_func(
            organization_id=args.organization_id,
            profile=args.profile
        )

        print_success(f"Successfully deleted organization {args.organization_id}")

        return 0

    except JiraError as e:
        print_error(f"Failed to delete organization: {e}")
        return 1
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
