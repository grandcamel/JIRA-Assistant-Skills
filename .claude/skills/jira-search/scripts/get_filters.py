#!/usr/bin/env python3
"""
List saved JIRA filters.

Usage:
    python get_filters.py
    python get_filters.py --output json
"""

import sys
import argparse
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import print_error, JiraError
from formatters import format_table, format_json


def get_filters(profile: str = None) -> list:
    """
    Get list of saved filters accessible to user.

    Args:
        profile: JIRA profile to use

    Returns:
        List of filter objects
    """
    client = get_jira_client(profile)
    response = client.get('/rest/api/3/filter/my', operation="get filters")
    client.close()

    return response if isinstance(response, list) else []


def main():
    parser = argparse.ArgumentParser(
        description='List saved JIRA filters',
        epilog='Example: python get_filters.py'
    )

    parser.add_argument('--output', '-o',
                       choices=['text', 'json'],
                       default='text',
                       help='Output format (default: text)')
    parser.add_argument('--profile',
                       help='JIRA profile to use (default: from config)')

    args = parser.parse_args()

    try:
        filters = get_filters(profile=args.profile)

        if args.output == 'json':
            print(format_json(filters))
        else:
            if not filters:
                print("No saved filters found")
            else:
                data = [
                    {
                        'ID': f.get('id'),
                        'Name': f.get('name'),
                        'Favourite': 'Yes' if f.get('favourite') else 'No',
                        'Owner': f.get('owner', {}).get('displayName', '')
                    }
                    for f in filters
                ]
                print(format_table(data))

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
