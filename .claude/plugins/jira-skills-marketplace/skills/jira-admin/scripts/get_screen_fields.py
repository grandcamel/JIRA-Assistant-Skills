#!/usr/bin/env python3
"""
Get all fields on a screen or specific tab.

Lists fields with their IDs and names, optionally filtered by type.
"""

import sys
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import print_error, JiraError
from formatters import format_table, format_json


def get_screen_fields(screen_id: int,
                      tab_id: Optional[int] = None,
                      client=None,
                      field_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get all fields on a screen or specific tab.

    Args:
        screen_id: Screen ID
        tab_id: Tab ID (if None, gets fields from all tabs)
        client: JiraClient instance
        field_type: Filter by type ('custom', 'system', or None for all)

    Returns:
        List of field objects
    """
    if client is None:
        from config_manager import get_jira_client
        client = get_jira_client()

    fields = []

    if tab_id is not None:
        # Get fields from specific tab
        fields = client.get_screen_tab_fields(screen_id, tab_id)
    else:
        # Get fields from all tabs
        tabs = client.get_screen_tabs(screen_id)
        for tab in tabs:
            tab_fields = client.get_screen_tab_fields(screen_id, tab['id'])
            for field in tab_fields:
                field['tab_id'] = tab['id']
                field['tab_name'] = tab.get('name', '')
            fields.extend(tab_fields)

    # Filter by type
    if field_type:
        if field_type == 'custom':
            fields = [f for f in fields if f.get('id', '').startswith('customfield_')]
        elif field_type == 'system':
            fields = [f for f in fields if not f.get('id', '').startswith('customfield_')]

    return fields


def format_fields_output(fields: List[Dict[str, Any]],
                         output_format: str = 'text',
                         show_tab: bool = False) -> str:
    """
    Format fields for output.

    Args:
        fields: List of field objects
        output_format: Output format ('text', 'json')
        show_tab: Include tab information in output

    Returns:
        Formatted output string
    """
    if output_format == 'json':
        return format_json(fields)

    if not fields:
        return "No fields found."

    # Prepare data for table
    data = []
    columns = ['Field ID', 'Name']
    if show_tab:
        columns.insert(0, 'Tab')

    for field in fields:
        field_id = field.get('id', '')
        field_type = 'Custom' if field_id.startswith('customfield_') else 'System'

        row = {
            'Field ID': field_id,
            'Name': field.get('name', ''),
            'Type': field_type
        }

        if show_tab:
            row['Tab'] = field.get('tab_name', '')

        data.append(row)

    if 'Type' not in columns:
        columns.append('Type')

    return format_table(data, columns=columns)


def main():
    parser = argparse.ArgumentParser(
        description='Get all fields on a JIRA screen',
        epilog='''
Examples:
    # Get all fields from all tabs
    python get_screen_fields.py 1

    # Get fields from specific tab
    python get_screen_fields.py 1 --tab 10000

    # Filter to custom fields only
    python get_screen_fields.py 1 --type custom

    # Filter to system fields only
    python get_screen_fields.py 1 --type system

    # JSON output
    python get_screen_fields.py 1 --output json
'''
    )

    parser.add_argument('screen_id', type=int,
                        help='Screen ID')
    parser.add_argument('--tab', '-t', dest='tab_id', type=int,
                        help='Tab ID (if not specified, gets fields from all tabs)')
    parser.add_argument('--type', choices=['custom', 'system'],
                        help='Filter by field type')
    parser.add_argument('--output', '-o', choices=['text', 'json'], default='text',
                        help='Output format (default: text)')
    parser.add_argument('--profile', '-p', help='JIRA profile to use')

    args = parser.parse_args()

    try:
        client = get_jira_client(args.profile)

        fields = get_screen_fields(
            screen_id=args.screen_id,
            tab_id=args.tab_id,
            client=client,
            field_type=args.type
        )

        # Show tab column if getting fields from all tabs
        show_tab = args.tab_id is None
        output = format_fields_output(fields, args.output, show_tab=show_tab)
        print(output)

        if args.output == 'text' and fields:
            print(f"\nTotal: {len(fields)} field(s)")

    except JiraError as e:
        print_error(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
