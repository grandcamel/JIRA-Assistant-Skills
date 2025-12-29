#!/usr/bin/env python3
"""
Get detailed information about a specific screen scheme.

Shows scheme details and screen mappings.
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Add shared lib to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError
from jira_assistant_skills_lib import format_json


def get_screen_scheme(scheme_id: int,
                      client=None,
                      show_screen_details: bool = False) -> Dict[str, Any]:
    """
    Get detailed information about a specific screen scheme.

    Args:
        scheme_id: Screen scheme ID
        client: JiraClient instance
        show_screen_details: Resolve screen IDs to names

    Returns:
        Screen scheme object with optional screen details
    """
    if client is None:
        from config_manager import get_jira_client
        client = get_jira_client()

    scheme = client.get_screen_scheme(scheme_id)

    if show_screen_details and scheme.get('screens'):
        # Resolve screen IDs to names
        screens_info = {}
        for operation, screen_id in scheme.get('screens', {}).items():
            if screen_id:
                try:
                    screen = client.get_screen(screen_id)
                    screens_info[operation] = {
                        'id': screen_id,
                        'name': screen.get('name', f'Screen {screen_id}')
                    }
                except Exception:
                    screens_info[operation] = {
                        'id': screen_id,
                        'name': f'Screen {screen_id}'
                    }
        scheme['screens_details'] = screens_info

    return scheme


def format_scheme_output(scheme: Dict[str, Any],
                         output_format: str = 'text') -> str:
    """
    Format screen scheme details for output.

    Args:
        scheme: Screen scheme object
        output_format: Output format ('text', 'json')

    Returns:
        Formatted output string
    """
    if output_format == 'json':
        return format_json(scheme)

    lines = []
    lines.append(f"Screen Scheme: {scheme.get('name', 'Unknown')}")
    lines.append(f"ID: {scheme.get('id', 'N/A')}")

    description = scheme.get('description')
    if description:
        lines.append(f"Description: {description}")

    screens = scheme.get('screens', {})
    screens_details = scheme.get('screens_details', {})

    if screens:
        lines.append("\nScreen Mappings:")
        for operation in ['default', 'create', 'edit', 'view']:
            screen_id = screens.get(operation)
            if screen_id:
                if screens_details and operation in screens_details:
                    name = screens_details[operation].get('name', '')
                    lines.append(f"  {operation.capitalize()}: {name} (ID: {screen_id})")
                else:
                    lines.append(f"  {operation.capitalize()}: Screen {screen_id}")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Get detailed information about a JIRA screen scheme',
        epilog='''
Examples:
    # Get basic scheme info
    python get_screen_scheme.py 1

    # Include screen names
    python get_screen_scheme.py 1 --details

    # JSON output
    python get_screen_scheme.py 1 --output json
'''
    )

    parser.add_argument('scheme_id', type=int,
                        help='Screen scheme ID')
    parser.add_argument('--details', '-d', dest='show_screen_details', action='store_true',
                        help='Resolve screen IDs to names')
    parser.add_argument('--output', '-o', choices=['text', 'json'], default='text',
                        help='Output format (default: text)')
    parser.add_argument('--profile', '-p', help='JIRA profile to use')

    args = parser.parse_args()

    try:
        client = get_jira_client(args.profile)

        scheme = get_screen_scheme(
            scheme_id=args.scheme_id,
            client=client,
            show_screen_details=args.show_screen_details
        )

        output = format_scheme_output(scheme, args.output)
        print(output)

    except JiraError as e:
        print_error(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
