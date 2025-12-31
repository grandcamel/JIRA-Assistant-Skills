#!/usr/bin/env python3
"""
Get detailed information about a specific screen.

Shows screen details, tabs, and optionally fields.
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add shared lib to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError
from jira_assistant_skills_lib import format_json


def get_screen(screen_id: int,
               client=None,
               show_tabs: bool = False,
               show_fields: bool = False) -> Dict[str, Any]:
    """
    Get detailed information about a specific screen.

    Args:
        screen_id: Screen ID
        client: JiraClient instance
        show_tabs: Include tab information
        show_fields: Include field information for each tab

    Returns:
        Screen object with optional tabs and fields
    """
    if client is None:
        from jira_assistant_skills_lib import get_jira_client
        client = get_jira_client()

    screen = client.get_screen(screen_id)

    if show_tabs:
        tabs = client.get_screen_tabs(screen_id)
        if show_fields:
            for tab in tabs:
                fields = client.get_screen_tab_fields(screen_id, tab['id'])
                tab['fields'] = fields
        screen['tabs'] = tabs

    return screen


def format_screen_output(screen: Dict[str, Any],
                         output_format: str = 'text') -> str:
    """
    Format screen details for output.

    Args:
        screen: Screen object with optional tabs and fields
        output_format: Output format ('text', 'json')

    Returns:
        Formatted output string
    """
    if output_format == 'json':
        return format_json(screen)

    lines = []
    lines.append(f"Screen: {screen.get('name', 'Unknown')}")
    lines.append(f"ID: {screen.get('id', 'N/A')}")

    description = screen.get('description')
    if description:
        lines.append(f"Description: {description}")

    scope = screen.get('scope')
    if scope:
        scope_type = scope.get('type', '')
        if scope_type == 'PROJECT':
            project = scope.get('project', {})
            lines.append(f"Scope: Project {project.get('id', 'unknown')}")
        else:
            lines.append(f"Scope: {scope_type}")

    tabs = screen.get('tabs', [])
    if tabs:
        lines.append(f"\nTabs ({len(tabs)}):")
        for tab in tabs:
            lines.append(f"\n  [{tab.get('id')}] {tab.get('name')}")
            fields = tab.get('fields', [])
            if fields:
                lines.append(f"  Fields ({len(fields)}):")
                for field in fields:
                    lines.append(f"    - {field.get('name')} ({field.get('id')})")

    return '\n'.join(lines)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description='Get detailed information about a JIRA screen',
        epilog='''
Examples:
    # Get basic screen info
    python get_screen.py 1

    # Include tabs
    python get_screen.py 1 --tabs

    # Include tabs and fields
    python get_screen.py 1 --tabs --fields

    # JSON output
    python get_screen.py 1 --tabs --fields --output json
'''
    )

    parser.add_argument('screen_id', type=int,
                        help='Screen ID')
    parser.add_argument('--tabs', '-t', dest='show_tabs', action='store_true',
                        help='Show screen tabs')
    parser.add_argument('--fields', '-f', dest='show_fields', action='store_true',
                        help='Show fields for each tab (requires --tabs)')
    parser.add_argument('--output', '-o', choices=['text', 'json'], default='text',
                        help='Output format (default: text)')
    parser.add_argument('--profile', '-p', help='JIRA profile to use')

    args = parser.parse_args(argv)

    # If --fields specified without --tabs, enable tabs
    if args.show_fields and not args.show_tabs:
        args.show_tabs = True

    try:
        client = get_jira_client(args.profile)

        screen = get_screen(
            screen_id=args.screen_id,
            client=client,
            show_tabs=args.show_tabs,
            show_fields=args.show_fields
        )

        output = format_screen_output(screen, args.output)
        print(output)

    except JiraError as e:
        print_error(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
