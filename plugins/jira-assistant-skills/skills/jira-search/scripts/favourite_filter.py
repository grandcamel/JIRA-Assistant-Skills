#!/usr/bin/env python3
"""
Manage filter favourites.

Add or remove filters from your favourites list.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add shared library to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import JiraError, print_error


def add_favourite(client, filter_id: str) -> Dict[str, Any]:
    """
    Add filter to favourites.

    Args:
        client: JIRA client
        filter_id: Filter ID

    Returns:
        Updated filter object
    """
    return client.add_filter_favourite(filter_id)


def remove_favourite(client, filter_id: str) -> None:
    """
    Remove filter from favourites.

    Args:
        client: JIRA client
        filter_id: Filter ID
    """
    client.remove_filter_favourite(filter_id)


def toggle_favourite(client, filter_id: str) -> tuple:
    """
    Toggle filter favourite status.

    Args:
        client: JIRA client
        filter_id: Filter ID

    Returns:
        Tuple of (action, filter_data)
    """
    # Get current status
    filter_data = client.get_filter(filter_id)
    is_favourite = filter_data.get('favourite', False)

    if is_favourite:
        remove_favourite(client, filter_id)
        return ('removed', filter_data)
    else:
        result = add_favourite(client, filter_id)
        return ('added', result)


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Manage filter favourites.',
        epilog='''
Examples:
  %(prog)s 10042 --add             # Add to favourites
  %(prog)s 10042 --remove          # Remove from favourites
  %(prog)s 10042                   # Toggle favourite status
        '''
    )

    parser.add_argument('filter_id',
                        help='Filter ID')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--add', '-a', action='store_true',
                       help='Add to favourites')
    group.add_argument('--remove', '-r', action='store_true',
                       help='Remove from favourites')

    parser.add_argument('--output', '-o', choices=['text', 'json'],
                        default='text', help='Output format (default: text)')
    parser.add_argument('--profile', '-p',
                        help='JIRA profile to use')

    args = parser.parse_args(argv)

    try:
        client = get_jira_client(args.profile)

        if args.add:
            result = add_favourite(client, args.filter_id)
            filter_name = result.get('name', args.filter_id)

            if args.output == 'json':
                print(json.dumps({'action': 'added', 'filter': result}, indent=2))
            else:
                print(f'Filter {args.filter_id} "{filter_name}" added to favourites.')

        elif args.remove:
            # Get filter info first for the name
            filter_data = client.get_filter(args.filter_id)
            filter_name = filter_data.get('name', args.filter_id)

            remove_favourite(client, args.filter_id)

            if args.output == 'json':
                print(json.dumps({'action': 'removed', 'filter_id': args.filter_id},
                                indent=2))
            else:
                print(f'Filter {args.filter_id} "{filter_name}" removed from favourites.')

        else:
            # Toggle
            action, filter_data = toggle_favourite(client, args.filter_id)
            filter_name = filter_data.get('name', args.filter_id)

            if args.output == 'json':
                print(json.dumps({'action': action, 'filter_id': args.filter_id},
                                indent=2))
            else:
                if action == 'added':
                    print(f'Filter {args.filter_id} "{filter_name}" added to favourites.')
                else:
                    print(f'Filter {args.filter_id} "{filter_name}" removed from favourites.')

        # Show current favourite count
        if args.output != 'json':
            favourites = client.get_favourite_filters()
            print(f"\nCurrent favourites: {len(favourites)}")

    except JiraError as e:
        print_error(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
