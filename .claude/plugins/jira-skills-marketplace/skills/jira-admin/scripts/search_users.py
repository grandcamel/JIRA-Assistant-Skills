#!/usr/bin/env python3
"""
Search JIRA users by name or email.

Supports:
- Name and email search
- Active-only filtering
- Assignable users for projects
- Multiple output formats (table, JSON, CSV)
- Privacy-aware output formatting
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


def search_users(client, query: str, start_at: int = 0, max_results: int = 50,
                 active_only: bool = True) -> List[Dict[str, Any]]:
    """
    Search for users by name or email.

    Args:
        client: JiraClient instance
        query: Search query (name or email)
        start_at: Starting index for pagination
        max_results: Maximum results to return
        active_only: If True, filter to active users only

    Returns:
        List of user objects
    """
    results = client.search_users(query=query, max_results=max_results, start_at=start_at)

    if active_only:
        results = [u for u in results if u.get('active', True)]

    return results


def search_assignable_users(client, query: str, project_key: str,
                            start_at: int = 0, max_results: int = 50) -> List[Dict[str, Any]]:
    """
    Find users assignable to issues in a project.

    Args:
        client: JiraClient instance
        query: Search query (name or email)
        project_key: Project key to search within
        start_at: Starting index for pagination
        max_results: Maximum results to return

    Returns:
        List of assignable user objects
    """
    return client.find_assignable_users(
        query=query,
        project_key=project_key,
        start_at=start_at,
        max_results=max_results
    )


def search_users_with_groups(client, query: str, start_at: int = 0,
                             max_results: int = 50, active_only: bool = True) -> List[Dict[str, Any]]:
    """
    Search for users and include their group memberships.

    Args:
        client: JiraClient instance
        query: Search query (name or email)
        start_at: Starting index for pagination
        max_results: Maximum results to return
        active_only: If True, filter to active users only

    Returns:
        List of user objects with groups included
    """
    users = search_users(client, query, start_at, max_results, active_only)

    # Fetch groups for each user
    for user in users:
        try:
            groups = client.get_user_groups(user['accountId'])
            user['groups'] = [g['name'] for g in groups]
        except Exception:
            user['groups'] = []

    return users


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


def format_users_table(users: List[Dict[str, Any]], show_groups: bool = False) -> str:
    """
    Format users as a table.

    Args:
        users: List of user objects
        show_groups: Whether to include groups column

    Returns:
        Formatted table string
    """
    try:
        from tabulate import tabulate
    except ImportError:
        # Fallback to simple formatting
        return format_users_simple(users, show_groups)

    headers = ['Account ID', 'Display Name', 'Email', 'Status']
    if show_groups:
        headers.append('Groups')

    rows = []
    for user in users:
        row = [
            user.get('accountId', 'N/A'),
            user.get('displayName', 'N/A'),
            format_user_field(user.get('emailAddress')),
            'Active' if user.get('active', True) else 'Inactive'
        ]
        if show_groups:
            groups = user.get('groups', [])
            if isinstance(groups, dict):
                groups = [g['name'] for g in groups.get('items', [])]
            row.append(', '.join(groups) if groups else '[none]')
        rows.append(row)

    return tabulate(rows, headers=headers, tablefmt='simple')


def format_users_simple(users: List[Dict[str, Any]], show_groups: bool = False) -> str:
    """
    Simple fallback formatting when tabulate is not available.

    Args:
        users: List of user objects
        show_groups: Whether to include groups column

    Returns:
        Formatted string
    """
    lines = []
    for user in users:
        line = f"{user.get('accountId', 'N/A'):<30} {user.get('displayName', 'N/A'):<20} "
        line += f"{format_user_field(user.get('emailAddress')):<30} "
        line += f"{'Active' if user.get('active', True) else 'Inactive'}"
        if show_groups:
            groups = user.get('groups', [])
            if isinstance(groups, dict):
                groups = [g['name'] for g in groups.get('items', [])]
            line += f" | {', '.join(groups) if groups else '[none]'}"
        lines.append(line)
    return '\n'.join(lines)


def format_users_json(users: List[Dict[str, Any]]) -> str:
    """
    Format users as JSON.

    Args:
        users: List of user objects

    Returns:
        JSON string
    """
    return json.dumps(users, indent=2)


def format_users_csv(users: List[Dict[str, Any]], show_groups: bool = False) -> str:
    """
    Format users as CSV.

    Args:
        users: List of user objects
        show_groups: Whether to include groups column

    Returns:
        CSV string
    """
    output = StringIO()
    fieldnames = ['accountId', 'displayName', 'emailAddress', 'active']
    if show_groups:
        fieldnames.append('groups')

    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()

    for user in users:
        row = {
            'accountId': user.get('accountId', ''),
            'displayName': user.get('displayName', ''),
            'emailAddress': user.get('emailAddress', ''),
            'active': 'true' if user.get('active', True) else 'false'
        }
        if show_groups:
            groups = user.get('groups', [])
            if isinstance(groups, dict):
                groups = [g['name'] for g in groups.get('items', [])]
            row['groups'] = ', '.join(groups) if groups else ''
        writer.writerow(row)

    return output.getvalue()


def main():
    parser = argparse.ArgumentParser(
        description='Search JIRA users by name or email',
        epilog='''
Examples:
  %(prog)s "john"                          # Search by name
  %(prog)s "john.doe@example.com"          # Search by email
  %(prog)s "john" --active-only            # Active users only (default)
  %(prog)s "john" --all                    # Include inactive users
  %(prog)s "john" --project PROJ --assignable  # Assignable users for project
  %(prog)s "john" --include-groups         # Include group memberships
  %(prog)s "john" --output json            # JSON output
  %(prog)s "john" --output csv > users.csv # Export to CSV
''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('query', help='Search query (name or email)')
    parser.add_argument('--project', '-p', help='Project key for assignable search')
    parser.add_argument('--assignable', '-a', action='store_true',
                        help='Search for assignable users (requires --project)')
    parser.add_argument('--active-only', action='store_true', default=True,
                        help='Only show active users (default)')
    parser.add_argument('--all', action='store_true',
                        help='Include inactive users')
    parser.add_argument('--include-groups', '-g', action='store_true',
                        help='Include group memberships (slower)')
    parser.add_argument('--start', type=int, default=0,
                        help='Starting index for pagination (default: 0)')
    parser.add_argument('--max-results', type=int, default=50,
                        help='Maximum results to return (default: 50)')
    parser.add_argument('--output', '-o', choices=['table', 'json', 'csv'],
                        default='table', help='Output format (default: table)')
    parser.add_argument('--profile', help='JIRA profile to use')

    args = parser.parse_args()

    # Validate assignable search
    if args.assignable and not args.project:
        parser.error('--assignable requires --project')

    try:
        client = get_jira_client(args.profile)

        # Determine active_only flag
        active_only = not args.all

        # Perform search
        if args.assignable:
            users = search_assignable_users(
                client,
                query=args.query,
                project_key=args.project,
                start_at=args.start,
                max_results=args.max_results
            )
        elif args.include_groups:
            users = search_users_with_groups(
                client,
                query=args.query,
                start_at=args.start,
                max_results=args.max_results,
                active_only=active_only
            )
        else:
            users = search_users(
                client,
                query=args.query,
                start_at=args.start,
                max_results=args.max_results,
                active_only=active_only
            )

        # Format output
        if not users:
            print(f'No users found matching "{args.query}"')
            sys.exit(0)

        print(f'Found {len(users)} user(s) matching "{args.query}"\n')

        if args.output == 'json':
            print(format_users_json(users))
        elif args.output == 'csv':
            print(format_users_csv(users, show_groups=args.include_groups))
        else:
            print(format_users_table(users, show_groups=args.include_groups))

        client.close()

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
