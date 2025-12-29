#!/usr/bin/env python3
"""
Add a field to a JIRA screen.

Adds a field to a specific tab or the default tab.
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Add shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import print_error, JiraError, NotFoundError
from formatters import format_json, print_success


def add_field_to_screen(screen_id: int,
                        field_id: str,
                        tab_id: Optional[int] = None,
                        tab_name: Optional[str] = None,
                        client=None,
                        dry_run: bool = False) -> Dict[str, Any]:
    """
    Add a field to a screen tab.

    Args:
        screen_id: Screen ID
        field_id: Field ID to add (e.g., 'customfield_10016')
        tab_id: Tab ID to add field to (optional)
        tab_name: Tab name to add field to (alternative to tab_id)
        client: JiraClient instance
        dry_run: If True, validate but don't make changes

    Returns:
        Added field object or dry-run status
    """
    if client is None:
        from config_manager import get_jira_client
        client = get_jira_client()

    # If neither tab_id nor tab_name specified, use first tab
    if tab_id is None:
        tabs = client.get_screen_tabs(screen_id)
        if not tabs:
            raise NotFoundError(f"No tabs found for screen {screen_id}")

        if tab_name:
            # Find tab by name
            for tab in tabs:
                if tab.get('name', '').lower() == tab_name.lower():
                    tab_id = tab['id']
                    break
            if tab_id is None:
                raise NotFoundError(f"Tab '{tab_name}' not found on screen {screen_id}")
        else:
            # Use first tab
            tab_id = tabs[0]['id']

    if dry_run:
        # Validate field exists in available fields
        available = client.get_screen_available_fields(screen_id)
        available_ids = [f.get('id') for f in available]

        if field_id in available_ids:
            return {
                'dry_run': True,
                'action': 'add_field',
                'screen_id': screen_id,
                'tab_id': tab_id,
                'field_id': field_id,
                'status': 'would_succeed'
            }
        else:
            # Field might already be on screen or not exist
            return {
                'dry_run': True,
                'action': 'add_field',
                'screen_id': screen_id,
                'tab_id': tab_id,
                'field_id': field_id,
                'status': 'field_not_available',
                'note': 'Field may already be on screen or does not exist'
            }

    # Actually add the field
    result = client.add_field_to_screen_tab(screen_id, tab_id, field_id)
    return result


def main():
    parser = argparse.ArgumentParser(
        description='Add a field to a JIRA screen',
        epilog='''
Examples:
    # Add field to first tab
    python add_field_to_screen.py 1 customfield_10016

    # Add field to specific tab by ID
    python add_field_to_screen.py 1 customfield_10016 --tab 10001

    # Add field to specific tab by name
    python add_field_to_screen.py 1 customfield_10016 --tab-name "Custom Fields"

    # Dry run to validate
    python add_field_to_screen.py 1 customfield_10016 --dry-run

    # JSON output
    python add_field_to_screen.py 1 customfield_10016 --output json
'''
    )

    parser.add_argument('screen_id', type=int,
                        help='Screen ID')
    parser.add_argument('field_id',
                        help='Field ID to add (e.g., customfield_10016)')
    parser.add_argument('--tab', '-t', dest='tab_id', type=int,
                        help='Tab ID to add field to')
    parser.add_argument('--tab-name', dest='tab_name',
                        help='Tab name to add field to (alternative to --tab)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Validate without making changes')
    parser.add_argument('--output', '-o', choices=['text', 'json'], default='text',
                        help='Output format (default: text)')
    parser.add_argument('--profile', '-p', help='JIRA profile to use')

    args = parser.parse_args()

    try:
        client = get_jira_client(args.profile)

        result = add_field_to_screen(
            screen_id=args.screen_id,
            field_id=args.field_id,
            tab_id=args.tab_id,
            tab_name=args.tab_name,
            client=client,
            dry_run=args.dry_run
        )

        if args.output == 'json':
            print(format_json(result))
        else:
            if args.dry_run:
                status = result.get('status', 'unknown')
                if status == 'would_succeed':
                    print(f"[DRY RUN] Would add field '{args.field_id}' to screen {args.screen_id}")
                else:
                    print(f"[DRY RUN] {result.get('note', 'Field cannot be added')}")
            else:
                print_success(f"Added field '{result.get('name', args.field_id)}' to screen {args.screen_id}")

    except JiraError as e:
        print_error(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
