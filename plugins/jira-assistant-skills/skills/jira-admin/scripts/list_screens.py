#!/usr/bin/env python3
"""
List all screens in JIRA.

Provides paginated listing of screens with filtering capabilities.
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


def list_screens(client=None,
                 filter_pattern: Optional[str] = None,
                 scope: Optional[List[str]] = None,
                 fetch_all: bool = False,
                 max_results: int = 100) -> List[Dict[str, Any]]:
    """
    List all screens in JIRA.

    Args:
        client: JiraClient instance (optional, will be created if not provided)
        filter_pattern: Filter screens by name pattern (case-insensitive)
        scope: Filter by scope type (PROJECT, TEMPLATE, GLOBAL)
        fetch_all: If True, fetch all pages of results
        max_results: Maximum results per page

    Returns:
        List of screen objects
    """
    if client is None:
        from config_manager import get_jira_client
        client = get_jira_client()

    screens = []
    start_at = 0

    while True:
        result = client.get_screens(
            start_at=start_at,
            max_results=max_results,
            scope=scope,
            query_string=filter_pattern
        )

        page_screens = result.get('values', [])
        screens.extend(page_screens)

        # Check if we need to fetch more pages
        if not fetch_all or result.get('isLast', True):
            break

        total = result.get('total', 0)
        if start_at + len(page_screens) >= total:
            break

        start_at += len(page_screens)

    # Apply local filtering if filter_pattern wasn't sent to API
    if filter_pattern:
        screens = [s for s in screens if filter_pattern.lower() in s.get('name', '').lower()]

    return screens


def format_screens_output(screens: List[Dict[str, Any]],
                          output_format: str = 'text') -> str:
    """
    Format screens for output.

    Args:
        screens: List of screen objects
        output_format: Output format ('text', 'json')

    Returns:
        Formatted output string
    """
    if output_format == 'json':
        return format_json(screens)

    if not screens:
        return "No screens found."

    # Prepare data for table
    data = []
    for screen in screens:
        scope_info = ""
        if screen.get('scope'):
            scope_type = screen['scope'].get('type', '')
            if scope_type == 'PROJECT':
                project = screen['scope'].get('project', {})
                scope_info = f"Project: {project.get('id', 'unknown')}"
            else:
                scope_info = scope_type

        data.append({
            'ID': screen.get('id', ''),
            'Name': screen.get('name', ''),
            'Description': (screen.get('description', '') or '')[:50],
            'Scope': scope_info
        })

    return format_table(data, columns=['ID', 'Name', 'Description', 'Scope'])


def main():
    parser = argparse.ArgumentParser(
        description='List all screens in JIRA',
        epilog='''
Examples:
    # List all screens
    python list_screens.py

    # Filter by name
    python list_screens.py --filter "Default"

    # Filter by scope
    python list_screens.py --scope PROJECT

    # JSON output
    python list_screens.py --output json

    # Fetch all pages (for large instances)
    python list_screens.py --all
'''
    )

    parser.add_argument('--filter', '-f', dest='filter_pattern',
                        help='Filter screens by name pattern (case-insensitive)')
    parser.add_argument('--scope', '-s', action='append',
                        choices=['PROJECT', 'TEMPLATE', 'GLOBAL'],
                        help='Filter by scope type (can be specified multiple times)')
    parser.add_argument('--all', '-a', dest='fetch_all', action='store_true',
                        help='Fetch all pages of results')
    parser.add_argument('--output', '-o', choices=['text', 'json'], default='text',
                        help='Output format (default: text)')
    parser.add_argument('--profile', '-p', help='JIRA profile to use')

    args = parser.parse_args()

    try:
        client = get_jira_client(args.profile)

        screens = list_screens(
            client=client,
            filter_pattern=args.filter_pattern,
            scope=args.scope,
            fetch_all=args.fetch_all
        )

        output = format_screens_output(screens, args.output)
        print(output)

        if args.output == 'text' and screens:
            print(f"\nTotal: {len(screens)} screen(s)")

    except JiraError as e:
        print_error(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
