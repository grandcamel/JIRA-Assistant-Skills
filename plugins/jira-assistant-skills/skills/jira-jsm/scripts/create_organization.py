#!/usr/bin/env python3
"""
Create a JSM organization.

Usage:
    python create_organization.py --name "Acme Corporation"
    python create_organization.py --name "Beta Industries" --output json
    python create_organization.py --name "Test Org" --dry-run
"""

import sys
import os
import argparse
import json
from pathlib import Path


from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError
from jira_assistant_skills_lib import print_success


def create_organization_func(name: str, profile: str = None) -> dict:
    """
    Create an organization.

    Args:
        name: Organization name
        profile: JIRA profile to use

    Returns:
        Created organization data
    """
    with get_jira_client(profile) as client:
        return client.create_organization(name)


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Create a JSM organization',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Create organization:
    %(prog)s --name "Acme Corporation"

  JSON output:
    %(prog)s --name "Beta Industries" --output json

  Dry-run:
    %(prog)s --name "Test Org" --dry-run
        """
    )

    parser.add_argument('--name', required=True,
                        help='Organization name')
    parser.add_argument('--output', choices=['text', 'json'], default='text',
                        help='Output format (default: text)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be created without creating')
    parser.add_argument('--profile',
                        help='JIRA profile to use from config')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show full API response')

    args = parser.parse_args(argv)

    try:
        if not args.name or not args.name.strip():
            print_error("Organization name cannot be empty")
            return 1

        if args.dry_run:
            print("DRY RUN MODE - No changes will be made\n")
            print(f"Would create organization:")
            print(f"  Name: {args.name}")
            return 0

        organization = create_organization_func(
            name=args.name,
            profile=args.profile
        )

        if args.output == 'json':
            if args.verbose:
                print(json.dumps(organization, indent=2))
            else:
                print(json.dumps({
                    'id': organization.get('id'),
                    'name': organization.get('name')
                }, indent=2))
        else:
            print_success("Organization created successfully!")
            print()
            print(f"ID:   {organization.get('id')}")
            print(f"Name: {organization.get('name')}")

            if args.verbose:
                print()
                print("Full response:")
                print(json.dumps(organization, indent=2))

        return 0

    except JiraError as e:
        print_error(f"Failed to create organization: {e}")
        return 1
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
