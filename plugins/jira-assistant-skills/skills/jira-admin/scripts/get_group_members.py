#!/usr/bin/env python3
"""
Get members of a JIRA group.

Supports:
- Lookup by group name or group ID
- Including inactive users
- Pagination
- Multiple output formats (table, JSON, CSV)
"""

import argparse
import sys
import json
import csv
from pathlib import Path
from io import StringIO
from typing import List, Dict, Any, Optional

# Add shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import print_error, JiraError


def get_members(client, group_name: Optional[str] = None,
                group_id: Optional[str] = None,
                include_inactive: bool = False,
                start_at: int = 0, max_results: int = 50) -> List[Dict[str, Any]]:
    """
    Get members of a group.

    Args:
        client: JiraClient instance
        group_name: Group name
        group_id: Group ID (preferred for GDPR compliance)
        include_inactive: Include inactive users
        start_at: Starting index for pagination
        max_results: Maximum results to return

    Returns:
        List of user objects
    """
    result = client.get_group_members(
        group_name=group_name,
        group_id=group_id,
        include_inactive=include_inactive,
        start_at=start_at,
        max_results=max_results
    )
    return result.get('values', [])


def format_user_field(value: Any) -> str:
    """
    Format a user field with privacy-aware handling.

    Args:
        value: Field value (may be None or empty)

    Returns:
        Formatted string value
    """
    if value is None or value == '':
        return '[hidden]'
    return str(value)


def format_members_table(members: List[Dict[str, Any]]) -> str:
    """
    Format group members as a table.

    Args:
        members: List of user objects

    Returns:
        Formatted table string
    """
    try:
        from tabulate import tabulate
    except ImportError:
        return format_members_simple(members)

    headers = ['Account ID', 'Display Name', 'Email', 'Status']
    rows = []
    for member in members:
        row = [
            member.get('accountId', 'N/A'),
            member.get('displayName', 'N/A'),
            format_user_field(member.get('emailAddress')),
            'Active' if member.get('active', True) else 'Inactive'
        ]
        rows.append(row)

    return tabulate(rows, headers=headers, tablefmt='simple')


def format_members_simple(members: List[Dict[str, Any]]) -> str:
    """
    Simple fallback formatting when tabulate is not available.

    Args:
        members: List of user objects

    Returns:
        Formatted string
    """
    lines = []
    for member in members:
        line = f"{member.get('accountId', 'N/A'):<30} "
        line += f"{member.get('displayName', 'N/A'):<20} "
        line += f"{format_user_field(member.get('emailAddress')):<30} "
        line += f"{'Active' if member.get('active', True) else 'Inactive'}"
        lines.append(line)
    return '\n'.join(lines)


def format_members_json(members: List[Dict[str, Any]]) -> str:
    """
    Format members as JSON.

    Args:
        members: List of user objects

    Returns:
        JSON string
    """
    return json.dumps(members, indent=2)


def format_members_csv(members: List[Dict[str, Any]]) -> str:
    """
    Format members as CSV.

    Args:
        members: List of user objects

    Returns:
        CSV string
    """
    output = StringIO()
    fieldnames = ['accountId', 'displayName', 'emailAddress', 'active']
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()

    for member in members:
        row = {
            'accountId': member.get('accountId', ''),
            'displayName': member.get('displayName', ''),
            'emailAddress': member.get('emailAddress', ''),
            'active': 'true' if member.get('active', True) else 'false'
        }
        writer.writerow(row)

    return output.getvalue()


def main():
    parser = argparse.ArgumentParser(
        description='Get members of a JIRA group',
        epilog='''
Examples:
  %(prog)s "jira-developers"            # Get members by group name
  %(prog)s --group-id abc123            # Get members by group ID
  %(prog)s "jira-developers" --include-inactive
  %(prog)s "jira-developers" --output json
  %(prog)s "jira-developers" --output csv > members.csv
''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('group_name', nargs='?', help='Group name')
    parser.add_argument('--group-id', '-i', help='Group ID (alternative to name)')
    parser.add_argument('--include-inactive', '-a', action='store_true',
                        help='Include inactive users')
    parser.add_argument('--start', type=int, default=0,
                        help='Starting index for pagination (default: 0)')
    parser.add_argument('--max-results', type=int, default=50,
                        help='Maximum results to return (default: 50)')
    parser.add_argument('--output', '-o', choices=['table', 'json', 'csv'],
                        default='table', help='Output format (default: table)')
    parser.add_argument('--profile', help='JIRA profile to use')

    args = parser.parse_args()

    # Require either group name or group ID
    if not args.group_name and not args.group_id:
        parser.error('Either group_name or --group-id is required')

    try:
        client = get_jira_client(args.profile)

        # Get members
        members = get_members(
            client,
            group_name=args.group_name,
            group_id=args.group_id,
            include_inactive=args.include_inactive,
            start_at=args.start,
            max_results=args.max_results
        )

        # Get group info for display
        group_identifier = args.group_name or args.group_id

        # Format output
        if not members:
            print(f'No members found in group "{group_identifier}"')
            sys.exit(0)

        print(f'Found {len(members)} member(s) in group "{group_identifier}"\n')

        if args.output == 'json':
            print(format_members_json(members))
        elif args.output == 'csv':
            print(format_members_csv(members))
        else:
            print(format_members_table(members))

        client.close()

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
