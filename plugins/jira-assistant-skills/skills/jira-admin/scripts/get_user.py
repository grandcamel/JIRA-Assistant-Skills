#!/usr/bin/env python3
"""
Get JIRA user details by account ID or email.

Supports:
- Lookup by accountId
- Lookup by email address
- Get current authenticated user (/myself)
- Include groups and application roles
- Privacy-aware output formatting
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import print_error, JiraError


def get_user_by_id(client, account_id: str, expand: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Get user details by account ID.

    Args:
        client: JiraClient instance
        account_id: User's account ID
        expand: Optional fields to expand (e.g., ['groups', 'applicationRoles'])

    Returns:
        User object
    """
    return client.get_user(account_id=account_id, expand=expand)


def get_user_by_email(client, email: str, expand: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Get user details by email address.

    Note: This may fail if the user's email is privacy-restricted.

    Args:
        client: JiraClient instance
        email: User's email address
        expand: Optional fields to expand

    Returns:
        User object
    """
    return client.get_user(email=email, expand=expand)


def get_current_user(client, expand: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Get the current authenticated user.

    Args:
        client: JiraClient instance
        expand: Optional fields to expand

    Returns:
        User object for authenticated user
    """
    return client.get_current_user(expand=expand)


def format_user_field(value: Any, field_name: str = '') -> str:
    """
    Format a user field with privacy-aware handling.

    Args:
        value: Field value (may be None or empty)
        field_name: Name of the field (for context)

    Returns:
        Formatted string value
    """
    if value is None or value == '':
        return '[hidden]'
    return str(value)


def format_user_text(user: Dict[str, Any]) -> str:
    """
    Format user details as readable text.

    Args:
        user: User object

    Returns:
        Formatted text output
    """
    lines = []
    lines.append("User Details")
    lines.append("=" * 50)
    lines.append("")

    # Check for unknown/deleted user
    account_id = user.get('accountId', 'N/A')
    if account_id == 'unknown':
        lines.append("Note: This represents a deleted or anonymized user.")
        lines.append("")

    lines.append(f"Account ID:      {account_id}")
    lines.append(f"Display Name:    {user.get('displayName', 'N/A')}")
    lines.append(f"Email Address:   {format_user_field(user.get('emailAddress'))}")
    lines.append(f"Account Type:    {user.get('accountType', 'N/A')}")
    lines.append(f"Status:          {'Active' if user.get('active', True) else 'Inactive'}")
    lines.append(f"Time Zone:       {format_user_field(user.get('timeZone'))}")
    lines.append(f"Locale:          {format_user_field(user.get('locale'))}")

    # Groups
    groups = user.get('groups', {})
    if isinstance(groups, dict) and groups.get('items'):
        lines.append("")
        lines.append("Groups:")
        for group in groups.get('items', []):
            lines.append(f"  - {group.get('name', 'Unknown')}")
    elif isinstance(groups, list):
        lines.append("")
        lines.append("Groups:")
        for group in groups:
            if isinstance(group, dict):
                lines.append(f"  - {group.get('name', 'Unknown')}")
            else:
                lines.append(f"  - {group}")

    # Application Roles
    roles = user.get('applicationRoles', {})
    if isinstance(roles, dict) and roles.get('items'):
        lines.append("")
        lines.append("Application Roles:")
        for role in roles.get('items', []):
            lines.append(f"  - {role.get('name', 'Unknown')}")

    # Privacy notice
    email = user.get('emailAddress')
    timezone = user.get('timeZone')
    if email is None or timezone is None:
        lines.append("")
        lines.append("Note: Some fields are hidden due to user privacy settings.")

    return '\n'.join(lines)


def format_user_json(user: Dict[str, Any]) -> str:
    """
    Format user as JSON.

    Args:
        user: User object

    Returns:
        JSON string
    """
    return json.dumps(user, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description='Get JIRA user details by account ID or email',
        epilog='''
Examples:
  %(prog)s --account-id 5b10ac8d82e05b22cc7d4ef5
  %(prog)s --email john.doe@example.com
  %(prog)s --me
  %(prog)s --email john@example.com --include-groups
  %(prog)s --email john@example.com --include-roles
  %(prog)s --email john@example.com --output json
''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # User identification (mutually exclusive)
    id_group = parser.add_mutually_exclusive_group(required=True)
    id_group.add_argument('--account-id', '-a', help='User account ID')
    id_group.add_argument('--email', '-e', help='User email address')
    id_group.add_argument('--me', action='store_true', help='Get current user')

    # Options
    parser.add_argument('--include-groups', '-g', action='store_true',
                        help='Include group memberships')
    parser.add_argument('--include-roles', '-r', action='store_true',
                        help='Include application roles')
    parser.add_argument('--output', '-o', choices=['text', 'json'],
                        default='text', help='Output format (default: text)')
    parser.add_argument('--profile', help='JIRA profile to use')

    args = parser.parse_args()

    try:
        client = get_jira_client(args.profile)

        # Build expand list
        expand = []
        if args.include_groups:
            expand.append('groups')
        if args.include_roles:
            expand.append('applicationRoles')

        # Get user
        if args.me:
            user = get_current_user(client, expand=expand if expand else None)
        elif args.account_id:
            user = get_user_by_id(client, args.account_id, expand=expand if expand else None)
        else:
            user = get_user_by_email(client, args.email, expand=expand if expand else None)

        # Format output
        if args.output == 'json':
            print(format_user_json(user))
        else:
            print(format_user_text(user))

        client.close()

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
