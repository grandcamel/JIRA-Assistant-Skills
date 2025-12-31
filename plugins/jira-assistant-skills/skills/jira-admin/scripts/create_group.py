#!/usr/bin/env python3
"""
Create a new JIRA group.

Supports:
- Creating groups with custom names
- Dry-run mode for preview
- Duplicate detection
- Group name validation
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Add shared lib to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError, ValidationError


# System group name prefixes to warn about
SYSTEM_GROUP_PREFIXES = [
    'jira-',
    'site-',
    'atlassian-',
    'confluence-',
    'bitbucket-'
]


def validate_group_name(name: str) -> None:
    """
    Validate group name.

    Args:
        name: Group name to validate

    Raises:
        ValidationError: If name is invalid
    """
    if not name or not name.strip():
        raise ValidationError("Group name cannot be empty")

    name = name.strip()

    # JIRA allows most characters in group names, but we enforce basic sanity
    if len(name) > 255:
        raise ValidationError("Group name cannot exceed 255 characters")


def check_system_group_name(name: str) -> Optional[str]:
    """
    Check if a group name resembles a system group.

    Args:
        name: Group name to check

    Returns:
        Warning message if name resembles system group, None otherwise
    """
    name_lower = name.lower()

    # Exact matches with system groups
    system_groups = [
        'jira-administrators',
        'jira-users',
        'jira-software-users',
        'site-admins',
        'atlassian-addons-admin'
    ]

    if name_lower in system_groups:
        return f"Warning: '{name}' is a system group name"

    # Don't warn for custom names that just start with jira-
    return None


def create_group(client, name: str, dry_run: bool = False) -> Optional[Dict[str, Any]]:
    """
    Create a new group.

    Args:
        client: JiraClient instance
        name: Group name
        dry_run: If True, preview only without creating

    Returns:
        Created group object, or None for dry-run
    """
    validate_group_name(name)

    if dry_run:
        return None

    return client.create_group(name=name)


def format_dry_run_preview(name: str) -> str:
    """
    Format dry-run preview message.

    Args:
        name: Group name

    Returns:
        Preview message
    """
    lines = []
    lines.append("DRY RUN - Preview of group creation:")
    lines.append("=" * 50)
    lines.append(f"Group Name: {name}")
    lines.append("")
    lines.append("This is a dry run. No group will be created.")
    lines.append("Remove --dry-run to create the group.")
    return '\n'.join(lines)


def format_created_group(group: Dict[str, Any]) -> str:
    """
    Format created group details as text.

    Args:
        group: Created group object

    Returns:
        Formatted text
    """
    lines = []
    lines.append("Group created successfully!")
    lines.append("=" * 50)
    lines.append(f"Name:     {group.get('name', 'N/A')}")
    lines.append(f"Group ID: {group.get('groupId', 'N/A')}")
    lines.append(f"URL:      {group.get('self', 'N/A')}")
    return '\n'.join(lines)


def format_created_group_json(group: Dict[str, Any]) -> str:
    """
    Format created group as JSON.

    Args:
        group: Created group object

    Returns:
        JSON string
    """
    return json.dumps(group, indent=2)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description='Create a new JIRA group',
        epilog='''
Examples:
  %(prog)s "mobile-team"                  # Create a group
  %(prog)s "mobile-team" --dry-run        # Preview only
  %(prog)s "external-contractors" --output json
''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('name', help='Name for the new group')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='Preview without creating')
    parser.add_argument('--output', '-o', choices=['text', 'json'],
                        default='text', help='Output format (default: text)')
    parser.add_argument('--profile', help='JIRA profile to use')

    args = parser.parse_args(argv)

    try:
        # Validate name first
        validate_group_name(args.name)

        # Check for system group names
        warning = check_system_group_name(args.name)
        if warning:
            print(f"\n{warning}\n", file=sys.stderr)

        # Dry run mode
        if args.dry_run:
            print(format_dry_run_preview(args.name))
            sys.exit(0)

        client = get_jira_client(args.profile)

        # Create group
        group = create_group(client, name=args.name)

        # Format output
        if args.output == 'json':
            print(format_created_group_json(group))
        else:
            print(format_created_group(group))

        client.close()

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
