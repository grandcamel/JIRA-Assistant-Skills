#!/usr/bin/env python3
"""
List JIRA groups with optional filtering.

Supports:
- Listing all groups
- Filtering by name query
- Including member counts
- Multiple output formats (table, JSON, CSV)
- System group identification
"""

import argparse
import sys
import json
import csv
from pathlib import Path
from io import StringIO
from typing import List, Dict, Any, Optional

# Add shared lib to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError


# Known system groups
SYSTEM_GROUPS = [
    'jira-administrators',
    'jira-users',
    'jira-software-users',
    'site-admins',
    'atlassian-addons-admin'
]


def list_groups(client, query: str = '', max_results: int = 50,
                case_insensitive: bool = True) -> List[Dict[str, Any]]:
    """
    List all groups with optional filtering.

    Args:
        client: JiraClient instance
        query: Optional query to filter groups by name
        max_results: Maximum results to return
        case_insensitive: Case-insensitive search (default True)

    Returns:
        List of group objects
    """
    result = client.find_groups(
        query=query,
        max_results=max_results,
        caseInsensitive=case_insensitive
    )
    return result.get('groups', [])


def list_groups_with_member_counts(client, query: str = '',
                                   max_results: int = 50) -> List[Dict[str, Any]]:
    """
    List groups with member count for each group.

    Note: This makes additional API calls per group, so may be slower.

    Args:
        client: JiraClient instance
        query: Optional query to filter groups by name
        max_results: Maximum results to return

    Returns:
        List of group objects with 'memberCount' field added
    """
    groups = list_groups(client, query, max_results)

    for group in groups:
        try:
            members_result = client.get_group_members(
                group_name=group['name'],
                max_results=1  # Just need the count
            )
            group['memberCount'] = members_result.get('total', 0)
        except Exception:
            group['memberCount'] = 'N/A'

    return groups


def is_system_group(group_name: str) -> bool:
    """
    Check if a group is a system/built-in group.

    Args:
        group_name: Group name to check

    Returns:
        True if system group, False otherwise
    """
    return group_name in SYSTEM_GROUPS


def format_groups_table(groups: List[Dict[str, Any]],
                        show_member_count: bool = False,
                        highlight_system: bool = False) -> str:
    """
    Format groups as a table.

    Args:
        groups: List of group objects
        show_member_count: Whether to include member count column
        highlight_system: Whether to highlight system groups

    Returns:
        Formatted table string
    """
    try:
        from tabulate import tabulate
    except ImportError:
        return format_groups_simple(groups, show_member_count, highlight_system)

    headers = ['Name', 'Group ID']
    if show_member_count:
        headers.append('Members')
    if highlight_system:
        headers.append('Type')

    rows = []
    for group in groups:
        name = group.get('name', 'N/A')
        row = [
            name,
            group.get('groupId', 'N/A')
        ]
        if show_member_count:
            row.append(group.get('memberCount', '-'))
        if highlight_system:
            row.append('System' if is_system_group(name) else 'Custom')
        rows.append(row)

    return tabulate(rows, headers=headers, tablefmt='simple')


def format_groups_simple(groups: List[Dict[str, Any]],
                         show_member_count: bool = False,
                         highlight_system: bool = False) -> str:
    """
    Simple fallback formatting when tabulate is not available.

    Args:
        groups: List of group objects
        show_member_count: Whether to include member count
        highlight_system: Whether to highlight system groups

    Returns:
        Formatted string
    """
    lines = []
    for group in groups:
        name = group.get('name', 'N/A')
        line = f"{name:<30} {group.get('groupId', 'N/A'):<40}"
        if show_member_count:
            line += f" {group.get('memberCount', '-'):>8}"
        if highlight_system:
            line += f" {'System' if is_system_group(name) else 'Custom':>8}"
        lines.append(line)
    return '\n'.join(lines)


def format_groups_json(groups: List[Dict[str, Any]]) -> str:
    """
    Format groups as JSON.

    Args:
        groups: List of group objects

    Returns:
        JSON string
    """
    return json.dumps(groups, indent=2)


def format_groups_csv(groups: List[Dict[str, Any]],
                      show_member_count: bool = False) -> str:
    """
    Format groups as CSV.

    Args:
        groups: List of group objects
        show_member_count: Whether to include member count column

    Returns:
        CSV string
    """
    output = StringIO()
    fieldnames = ['name', 'groupId']
    if show_member_count:
        fieldnames.append('memberCount')

    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()

    for group in groups:
        row = {
            'name': group.get('name', ''),
            'groupId': group.get('groupId', '')
        }
        if show_member_count:
            row['memberCount'] = group.get('memberCount', '')
        writer.writerow(row)

    return output.getvalue()


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description='List JIRA groups with optional filtering',
        epilog='''
Examples:
  %(prog)s                              # List all groups
  %(prog)s --query "developers"         # Filter by name
  %(prog)s --include-members            # Include member counts (slower)
  %(prog)s --show-system                # Highlight system groups
  %(prog)s --output json                # JSON output
  %(prog)s --output csv > groups.csv    # Export to CSV
''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--query', '-q', default='',
                        help='Filter groups by name (partial match)')
    parser.add_argument('--include-members', '-m', action='store_true',
                        help='Include member counts (slower)')
    parser.add_argument('--show-system', '-s', action='store_true',
                        help='Highlight system/built-in groups')
    parser.add_argument('--max-results', type=int, default=50,
                        help='Maximum results to return (default: 50)')
    parser.add_argument('--output', '-o', choices=['table', 'json', 'csv'],
                        default='table', help='Output format (default: table)')
    parser.add_argument('--profile', help='JIRA profile to use')

    args = parser.parse_args(argv)

    try:
        client = get_jira_client(args.profile)

        # Get groups
        if args.include_members:
            groups = list_groups_with_member_counts(
                client,
                query=args.query,
                max_results=args.max_results
            )
        else:
            groups = list_groups(
                client,
                query=args.query,
                max_results=args.max_results
            )

        # Format output
        if not groups:
            query_info = f' matching "{args.query}"' if args.query else ''
            print(f'No groups found{query_info}')
            sys.exit(0)

        query_info = f' matching "{args.query}"' if args.query else ''
        print(f'Found {len(groups)} group(s){query_info}\n')

        if args.output == 'json':
            print(format_groups_json(groups))
        elif args.output == 'csv':
            print(format_groups_csv(groups, show_member_count=args.include_members))
        else:
            print(format_groups_table(
                groups,
                show_member_count=args.include_members,
                highlight_system=args.show_system
            ))

        client.close()

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
