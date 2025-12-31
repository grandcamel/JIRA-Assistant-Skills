#!/usr/bin/env python3
"""
List all screen schemes in JIRA.

Provides paginated listing with filtering capabilities.
"""

import sys
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add shared lib to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError
from jira_assistant_skills_lib import format_table, format_json


def list_screen_schemes(client=None,
                        filter_pattern: Optional[str] = None,
                        fetch_all: bool = False,
                        max_results: int = 100) -> List[Dict[str, Any]]:
    """
    List all screen schemes in JIRA.

    Args:
        client: JiraClient instance
        filter_pattern: Filter schemes by name pattern (case-insensitive)
        fetch_all: If True, fetch all pages of results
        max_results: Maximum results per page

    Returns:
        List of screen scheme objects
    """
    if client is None:
        from jira_assistant_skills_lib import get_jira_client
        client = get_jira_client()

    schemes = []
    start_at = 0

    while True:
        result = client.get_screen_schemes(
            start_at=start_at,
            max_results=max_results,
            query_string=filter_pattern
        )

        page_schemes = result.get('values', [])
        schemes.extend(page_schemes)

        # Check if we need to fetch more pages
        if not fetch_all or result.get('isLast', True):
            break

        total = result.get('total', 0)
        if start_at + len(page_schemes) >= total:
            break

        start_at += len(page_schemes)

    # Apply local filtering if filter_pattern wasn't sent to API
    if filter_pattern:
        schemes = [s for s in schemes if filter_pattern.lower() in s.get('name', '').lower()]

    return schemes


def format_schemes_output(schemes: List[Dict[str, Any]],
                          show_screens: bool = False,
                          output_format: str = 'text') -> str:
    """
    Format screen schemes for output.

    Args:
        schemes: List of screen scheme objects
        show_screens: Include screen mappings in output
        output_format: Output format ('text', 'json')

    Returns:
        Formatted output string
    """
    if output_format == 'json':
        return format_json(schemes)

    if not schemes:
        return "No screen schemes found."

    # Prepare data for table
    data = []
    columns = ['ID', 'Name', 'Description']

    if show_screens:
        columns.extend(['Default', 'Create', 'Edit', 'View'])

    for scheme in schemes:
        row = {
            'ID': scheme.get('id', ''),
            'Name': scheme.get('name', ''),
            'Description': (scheme.get('description', '') or '')[:40]
        }

        if show_screens:
            screens = scheme.get('screens', {})
            row['Default'] = screens.get('default', 'N/A')
            row['Create'] = screens.get('create', '-')
            row['Edit'] = screens.get('edit', '-')
            row['View'] = screens.get('view', '-')

        data.append(row)

    return format_table(data, columns=columns)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description='List all screen schemes in JIRA',
        epilog='''
Examples:
    # List all screen schemes
    python list_screen_schemes.py

    # Filter by name
    python list_screen_schemes.py --filter "Default"

    # Show screen mappings
    python list_screen_schemes.py --show-screens

    # JSON output
    python list_screen_schemes.py --output json

    # Fetch all pages
    python list_screen_schemes.py --all
'''
    )

    parser.add_argument('--filter', '-f', dest='filter_pattern',
                        help='Filter schemes by name pattern (case-insensitive)')
    parser.add_argument('--show-screens', '-s', action='store_true',
                        help='Show screen mappings (default/create/edit/view)')
    parser.add_argument('--all', '-a', dest='fetch_all', action='store_true',
                        help='Fetch all pages of results')
    parser.add_argument('--output', '-o', choices=['text', 'json'], default='text',
                        help='Output format (default: text)')
    parser.add_argument('--profile', '-p', help='JIRA profile to use')

    args = parser.parse_args(argv)

    try:
        client = get_jira_client(args.profile)

        schemes = list_screen_schemes(
            client=client,
            filter_pattern=args.filter_pattern,
            fetch_all=args.fetch_all
        )

        output = format_schemes_output(schemes, args.show_screens, args.output)
        print(output)

        if args.output == 'text' and schemes:
            print(f"\nTotal: {len(schemes)} screen scheme(s)")

    except JiraError as e:
        print_error(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
