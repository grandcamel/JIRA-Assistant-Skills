#!/usr/bin/env python3
"""
List all notification schemes in JIRA.

Lists available notification schemes with optional filtering and event count display.

Usage:
    python list_notification_schemes.py
    python list_notification_schemes.py --output json
    python list_notification_schemes.py --filter "default"
    python list_notification_schemes.py --show-events
    python list_notification_schemes.py --profile production
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Dict, Any, Optional, List


from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError, handle_errors
from jira_assistant_skills_lib import format_table, print_info


def list_notification_schemes(
    client=None,
    filter_name: Optional[str] = None,
    show_events: bool = False,
    max_results: int = 50,
    fetch_all: bool = False,
    profile: Optional[str] = None
) -> Dict[str, Any]:
    """
    List all notification schemes.

    Args:
        client: JiraClient instance (optional, created if not provided)
        filter_name: Filter schemes by name (case-insensitive)
        show_events: If True, include event count per scheme
        max_results: Maximum results per API call
        fetch_all: If True, fetch all pages of results
        profile: JIRA profile to use

    Returns:
        Dict with 'schemes' list and 'total' count
    """
    close_client = False
    if client is None:
        client = get_jira_client(profile)
        close_client = True

    try:
        all_schemes = []
        start_at = 0
        expand = 'notificationSchemeEvents' if show_events else None

        while True:
            result = client.get_notification_schemes(
                start_at=start_at,
                max_results=max_results,
                expand=expand
            )

            schemes = result.get('values', [])
            all_schemes.extend(schemes)

            # Check if we need to fetch more pages
            total = result.get('total', len(schemes))
            is_last = result.get('isLast', True)

            if not fetch_all or is_last or start_at + len(schemes) >= total:
                break

            start_at += len(schemes)

        # Apply name filter if specified
        if filter_name:
            filter_lower = filter_name.lower()
            all_schemes = [
                s for s in all_schemes
                if filter_lower in s.get('name', '').lower()
            ]

        # Format schemes with event count if requested
        formatted_schemes = []
        for scheme in all_schemes:
            formatted = {
                'id': scheme.get('id', 'N/A'),
                'name': scheme.get('name', 'N/A'),
                'description': scheme.get('description', '')
            }
            if show_events:
                events = scheme.get('notificationSchemeEvents', [])
                formatted['events'] = len(events)
            formatted_schemes.append(formatted)

        return {
            'schemes': formatted_schemes,
            'total': len(formatted_schemes)
        }

    finally:
        if close_client and hasattr(client, 'close'):
            client.close()


def format_text_output(result: Dict[str, Any], show_events: bool = False) -> str:
    """
    Format result as human-readable text.

    Args:
        result: Result dict from list_notification_schemes
        show_events: If True, include event count column

    Returns:
        Formatted text string
    """
    schemes = result.get('schemes', [])
    total = result.get('total', 0)

    if total == 0:
        return "No notification schemes found."

    output = ["Available Notification Schemes:", ""]

    if show_events:
        columns = ['id', 'name', 'description', 'events']
        headers = ['ID', 'Name', 'Description', 'Events']
    else:
        columns = ['id', 'name', 'description']
        headers = ['ID', 'Name', 'Description']

    table = format_table(schemes, columns=columns, headers=headers)
    output.append(table)
    output.append("")
    output.append(f"Total: {total} notification scheme(s)")

    return '\n'.join(output)


def format_json_output(result: Dict[str, Any]) -> str:
    """
    Format result as JSON.

    Args:
        result: Result dict from list_notification_schemes

    Returns:
        JSON string
    """
    return json.dumps(result, indent=2)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='List notification schemes in JIRA',
        epilog='''
Examples:
    python list_notification_schemes.py
    python list_notification_schemes.py --output json
    python list_notification_schemes.py --filter "default"
    python list_notification_schemes.py --show-events
    python list_notification_schemes.py --profile production
        '''
    )
    parser.add_argument('--output', '-o', choices=['text', 'json'], default='text',
                        help='Output format (default: text)')
    parser.add_argument('--filter', '-f', dest='filter_name',
                        help='Filter schemes by name (case-insensitive)')
    parser.add_argument('--show-events', '-e', action='store_true',
                        help='Show number of events configured per scheme')
    parser.add_argument('--all', '-a', dest='fetch_all', action='store_true',
                        help='Fetch all pages of results')
    parser.add_argument('--profile', '-p', help='JIRA profile to use')

    args = parser.parse_args()

    try:
        result = list_notification_schemes(
            filter_name=args.filter_name,
            show_events=args.show_events,
            fetch_all=args.fetch_all,
            profile=args.profile
        )

        if args.output == 'json':
            print(format_json_output(result))
        else:
            print(format_text_output(result, show_events=args.show_events))

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
