#!/usr/bin/env python3
"""
Get activity/changelog for a JIRA issue.

Usage:
    python get_activity.py PROJ-123
    python get_activity.py PROJ-123 --limit 10 --offset 0
    python get_activity.py PROJ-123 --output json
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import print_error, JiraError
from validators import validate_issue_key
from formatters import format_table


def get_activity(issue_key: str, limit: int = 100, offset: int = 0,
                 profile: str = None) -> Dict[str, Any]:
    """
    Get activity/changelog for an issue.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        limit: Maximum number of changelog entries to return
        offset: Starting position (for pagination)
        profile: JIRA profile to use

    Returns:
        Changelog data with values, total, etc.
    """
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client(profile)
    result = client.get_changelog(issue_key, max_results=limit, start_at=offset)
    client.close()

    return result


def parse_changelog(changelog_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parse changelog into simplified format.

    Args:
        changelog_data: Raw changelog data from API

    Returns:
        List of parsed changes with type, field, from, to, author, date
    """
    parsed = []

    for entry in changelog_data.get('values', []):
        author = entry.get('author', {}).get('displayName', 'Unknown')
        created = entry.get('created', '')

        for item in entry.get('items', []):
            field = item.get('field', '')
            field_type = item.get('fieldtype', '')
            from_string = item.get('fromString') or ''
            to_string = item.get('toString') or ''

            # Determine change type based on field
            change_type = field

            parsed.append({
                'type': change_type,
                'field': field,
                'from': from_string,
                'to': to_string,
                'author': author,
                'created': created
            })

    return parsed


def display_activity_table(changes: List[Dict[str, Any]]) -> None:
    """
    Display activity in table format.

    Args:
        changes: List of parsed changes
    """
    if not changes:
        print("No activity found.")
        return

    # Prepare table data - add formatted date to each change
    table_data = []
    for change in changes:
        table_data.append({
            'date': change.get('created', '')[:16],
            'author': change.get('author', ''),
            'field': change.get('field', ''),
            'from': change.get('from', '') or '(none)',
            'to': change.get('to', '') or '(none)'
        })

    print(format_table(
        table_data,
        columns=['date', 'author', 'field', 'from', 'to'],
        headers=['Date', 'Author', 'Field', 'From', 'To']
    ))


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Get activity/changelog for a JIRA issue',
        epilog='''
Examples:
  %(prog)s PROJ-123
  %(prog)s PROJ-123 --limit 10
  %(prog)s PROJ-123 --output json
        '''
    )

    parser.add_argument('issue_key',
                       help='Issue key (e.g., PROJ-123)')
    parser.add_argument('--limit', '-l',
                       type=int,
                       default=100,
                       help='Maximum number of changelog entries (default: 100)')
    parser.add_argument('--offset', '-o',
                       type=int,
                       default=0,
                       help='Starting position for pagination (default: 0)')
    parser.add_argument('--output', '-O',
                       choices=['table', 'json'],
                       default='table',
                       help='Output format (default: table)')
    parser.add_argument('--profile', '-p',
                       help='JIRA profile to use')

    args = parser.parse_args()

    try:
        # Get activity
        changelog = get_activity(
            args.issue_key,
            limit=args.limit,
            offset=args.offset,
            profile=args.profile
        )

        # Parse changelog
        changes = parse_changelog(changelog)

        # Output
        if args.output == 'json':
            print(json.dumps(changes, indent=2))
        else:
            print(f"Activity for {args.issue_key}:\n")
            display_activity_table(changes)

            # Show pagination info
            total = changelog.get('total', 0)
            showing = len(changes)
            if total > showing:
                print(f"\nShowing {showing} of {total} total changes.")
                print(f"Use --offset {args.offset + args.limit} to see more.")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
