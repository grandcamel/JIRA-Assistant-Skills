#!/usr/bin/env python3
"""
Get issue type scheme mappings.

Lists which issue types are in which schemes.
Requires 'Administer Jira' global permission.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import JiraError, print_error
from formatters import format_table


def get_issue_type_scheme_mappings(
    client=None,
    profile: Optional[str] = None,
    start_at: int = 0,
    max_results: int = 50,
    scheme_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Get issue type scheme mappings.

    Args:
        client: JiraClient instance (for testing)
        profile: Configuration profile name
        start_at: Starting index for pagination
        max_results: Maximum results per page
        scheme_ids: Filter by scheme IDs

    Returns:
        Paginated response with mappings

    Raises:
        JiraError: On API failure
    """
    if client is None:
        client = get_jira_client(profile=profile)

    try:
        result = client.get_issue_type_scheme_items(
            start_at=start_at,
            max_results=max_results,
            scheme_ids=scheme_ids
        )
        return result
    finally:
        if client:
            client.close()


def format_mappings(response: Dict[str, Any], output_format: str = 'table') -> str:
    """Format mappings for display."""
    if output_format == 'json':
        return json.dumps(response, indent=2)

    mappings = response.get('values', [])
    if not mappings:
        return "No mappings found."

    headers = ['Scheme ID', 'Issue Type ID']
    rows = []

    for mapping in mappings:
        rows.append([
            mapping.get('issueTypeSchemeId', ''),
            mapping.get('issueTypeId', '')
        ])

    return format_table(headers, rows)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Get issue type scheme mappings',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all mappings
  python get_issue_type_scheme_mappings.py

  # Filter by scheme ID
  python get_issue_type_scheme_mappings.py --scheme-ids 10000 10001

  # With pagination
  python get_issue_type_scheme_mappings.py --start-at 0 --max-results 100

  # Output as JSON
  python get_issue_type_scheme_mappings.py --format json
"""
    )

    parser.add_argument(
        '--scheme-ids',
        nargs='+',
        help='Filter by scheme IDs'
    )
    parser.add_argument(
        '--start-at',
        type=int,
        default=0,
        help='Starting index (default: 0)'
    )
    parser.add_argument(
        '--max-results',
        type=int,
        default=50,
        help='Maximum results (default: 50)'
    )
    parser.add_argument(
        '--format',
        choices=['table', 'json'],
        default='table',
        help='Output format (default: table)'
    )
    parser.add_argument(
        '--profile',
        help='Configuration profile to use'
    )

    args = parser.parse_args()

    try:
        response = get_issue_type_scheme_mappings(
            profile=args.profile,
            start_at=args.start_at,
            max_results=args.max_results,
            scheme_ids=args.scheme_ids
        )

        output = format_mappings(response, args.format)
        print(output)

        if args.format == 'table':
            total = response.get('total', len(response.get('values', [])))
            shown = len(response.get('values', []))
            print(f"\nShowing {shown} of {total} mapping(s)")

    except JiraError as e:
        print_error(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
