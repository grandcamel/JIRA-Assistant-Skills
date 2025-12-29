#!/usr/bin/env python3
"""
List all tabs for a specific screen.

Shows tab IDs and names, optionally with field counts.
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


def list_screen_tabs(screen_id: int,
                     client=None,
                     show_field_count: bool = False) -> List[Dict[str, Any]]:
    """
    List all tabs for a screen.

    Args:
        screen_id: Screen ID
        client: JiraClient instance
        show_field_count: Include field count for each tab

    Returns:
        List of tab objects
    """
    if client is None:
        from config_manager import get_jira_client
        client = get_jira_client()

    tabs = client.get_screen_tabs(screen_id)

    if show_field_count:
        for tab in tabs:
            fields = client.get_screen_tab_fields(screen_id, tab['id'])
            tab['field_count'] = len(fields)

    return tabs


def format_tabs_output(tabs: List[Dict[str, Any]],
                       screen_name: str = '',
                       output_format: str = 'text') -> str:
    """
    Format tabs for output.

    Args:
        tabs: List of tab objects
        screen_name: Name of the screen (for display)
        output_format: Output format ('text', 'json')

    Returns:
        Formatted output string
    """
    if output_format == 'json':
        return format_json(tabs)

    if not tabs:
        return "No tabs found for this screen."

    header = f"Tabs for screen: {screen_name}\n" if screen_name else ""

    # Prepare data for table
    data = []
    columns = ['ID', 'Name']

    for tab in tabs:
        row = {
            'ID': tab.get('id', ''),
            'Name': tab.get('name', '')
        }
        if 'field_count' in tab:
            row['Fields'] = tab['field_count']
            if 'Fields' not in columns:
                columns.append('Fields')
        data.append(row)

    return header + format_table(data, columns=columns)


def main():
    parser = argparse.ArgumentParser(
        description='List all tabs for a JIRA screen',
        epilog='''
Examples:
    # List tabs for screen 1
    python list_screen_tabs.py 1

    # Include field counts
    python list_screen_tabs.py 1 --field-count

    # JSON output
    python list_screen_tabs.py 1 --output json
'''
    )

    parser.add_argument('screen_id', type=int,
                        help='Screen ID')
    parser.add_argument('--field-count', '-c', dest='show_field_count', action='store_true',
                        help='Include field count for each tab')
    parser.add_argument('--output', '-o', choices=['text', 'json'], default='text',
                        help='Output format (default: text)')
    parser.add_argument('--profile', '-p', help='JIRA profile to use')

    args = parser.parse_args()

    try:
        client = get_jira_client(args.profile)

        # Get screen name for display
        try:
            screen = client.get_screen(args.screen_id)
            screen_name = screen.get('name', f'Screen {args.screen_id}')
        except Exception:
            screen_name = f'Screen {args.screen_id}'

        tabs = list_screen_tabs(
            screen_id=args.screen_id,
            client=client,
            show_field_count=args.show_field_count
        )

        output = format_tabs_output(tabs, screen_name, args.output)
        print(output)

        if args.output == 'text' and tabs:
            print(f"\nTotal: {len(tabs)} tab(s)")

    except JiraError as e:
        print_error(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
