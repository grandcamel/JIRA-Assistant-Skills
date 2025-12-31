#!/usr/bin/env python3
"""
List custom fields in JIRA instance.

Usage:
    python list_fields.py
    python list_fields.py --filter "epic"
    python list_fields.py --agile
    python list_fields.py --output json
"""

import sys
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add shared lib to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError
from jira_assistant_skills_lib import format_table, format_json, print_info

# Known Agile field name patterns
AGILE_PATTERNS = ['epic', 'sprint', 'story', 'point', 'rank', 'velocity', 'backlog']


def list_fields(filter_pattern: str = None,
                agile_only: bool = False,
                custom_only: bool = True,
                profile: str = None,
                client=None) -> List[Dict[str, Any]]:
    """
    List fields from JIRA instance.

    Args:
        filter_pattern: Filter fields by name pattern (case-insensitive)
        agile_only: If True, only show Agile-related fields
        custom_only: If True, only show custom fields (default: True)
        profile: JIRA profile to use
        client: JiraClient instance (for testing)

    Returns:
        List of field dictionaries

    Raises:
        JiraError: If API call fails
    """
    if not client:
        client = get_jira_client(profile)
        should_close = True
    else:
        should_close = False

    try:
        fields = client.get('/rest/api/3/field')

        result = []
        for field in fields:
            # Filter by custom
            if custom_only and not field.get('custom', False):
                continue

            name = field.get('name', '')
            field_id = field.get('id', '')

            # Filter by pattern
            if filter_pattern and filter_pattern.lower() not in name.lower():
                continue

            # Filter by Agile patterns
            if agile_only:
                is_agile = any(pattern in name.lower() for pattern in AGILE_PATTERNS)
                if not is_agile:
                    continue

            schema = field.get('schema', {})
            result.append({
                'id': field_id,
                'name': name,
                'type': schema.get('type', 'unknown'),
                'custom': field.get('custom', False),
                'searchable': field.get('searchable', False),
                'navigable': field.get('navigable', False)
            })

        # Sort by name
        result.sort(key=lambda x: x['name'].lower())
        return result

    finally:
        if should_close:
            client.close()


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description='List custom fields in JIRA instance',
        epilog='Example: python list_fields.py --agile'
    )

    parser.add_argument('--filter', '-f',
                        help='Filter fields by name pattern')
    parser.add_argument('--agile', '-a', action='store_true',
                        help='Show only Agile-related fields')
    parser.add_argument('--all', action='store_true',
                        help='Show all fields (not just custom)')
    parser.add_argument('--profile',
                        help='JIRA profile to use')
    parser.add_argument('--output', '-o',
                        choices=['text', 'json'],
                        default='text',
                        help='Output format')

    args = parser.parse_args(argv)

    try:
        fields = list_fields(
            filter_pattern=args.filter,
            agile_only=args.agile,
            custom_only=not args.all,
            profile=args.profile
        )

        if args.output == 'json':
            print(format_json(fields))
        else:
            if not fields:
                print("No fields found matching criteria")
            else:
                print_info(f"Found {len(fields)} field(s)")
                print()
                print(format_table(
                    fields,
                    columns=['id', 'name', 'type'],
                    headers=['Field ID', 'Name', 'Type']
                ))

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
