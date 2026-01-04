#!/usr/bin/env python3
"""
List all issue types in JIRA.

Lists global and project-scoped issue types with filtering options.
Requires 'Browse Projects' permission.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add shared lib to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import JiraError, print_error
from jira_assistant_skills_lib import format_table


def list_issue_types(
    client=None,
    profile: Optional[str] = None,
    subtask_only: bool = False,
    standard_only: bool = False,
    hierarchy_level: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    List issue types with optional filtering.

    Args:
        client: JiraClient instance (for testing)
        profile: Configuration profile name
        subtask_only: If True, return only subtask types
        standard_only: If True, return only non-subtask types
        hierarchy_level: Filter by specific hierarchy level

    Returns:
        List of issue type dictionaries

    Raises:
        JiraError: On API failure
    """
    if client is None:
        client = get_jira_client(profile=profile)

    try:
        issue_types = client.get_issue_types()

        # Apply filters
        if subtask_only:
            issue_types = [t for t in issue_types if t.get('subtask', False)]
        elif standard_only:
            issue_types = [t for t in issue_types if not t.get('subtask', False)]

        if hierarchy_level is not None:
            issue_types = [
                t for t in issue_types
                if t.get('hierarchyLevel') == hierarchy_level
            ]

        return issue_types
    finally:
        if client:
            client.close()


def format_issue_types(
    issue_types: List[Dict[str, Any]],
    output_format: str = 'table'
) -> str:
    """Format issue types for display."""
    if output_format == 'json':
        return json.dumps(issue_types, indent=2)

    if not issue_types:
        return "No issue types found."

    # Prepare table data as list of dicts for format_table
    columns = ['id', 'name', 'description', 'subtask', 'hierarchy', 'scope']
    headers = ['ID', 'Name', 'Description', 'Subtask', 'Hierarchy', 'Scope']
    rows = []

    for issue_type in issue_types:
        scope_type = issue_type.get('scope', {}).get('type', 'GLOBAL') if issue_type.get('scope') else 'GLOBAL'
        rows.append({
            'id': issue_type.get('id', ''),
            'name': issue_type.get('name', ''),
            'description': (issue_type.get('description', '') or '')[:50],
            'subtask': 'Yes' if issue_type.get('subtask') else 'No',
            'hierarchy': str(issue_type.get('hierarchyLevel', 0)),
            'scope': scope_type
        })

    return format_table(rows, columns=columns, headers=headers)


def main(argv: list[str] | None = None):
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='List all issue types in JIRA',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all issue types
  python list_issue_types.py

  # List only subtask types
  python list_issue_types.py --subtask-only

  # List only standard (non-subtask) types
  python list_issue_types.py --standard-only

  # List only epic-level types (hierarchy 1)
  python list_issue_types.py --hierarchy 1

  # Output as JSON
  python list_issue_types.py --format json

  # Use specific profile
  python list_issue_types.py --profile production
"""
    )

    parser.add_argument(
        '--subtask-only',
        action='store_true',
        help='Show only subtask types'
    )
    parser.add_argument(
        '--standard-only',
        action='store_true',
        help='Show only standard (non-subtask) types'
    )
    parser.add_argument(
        '--hierarchy',
        type=int,
        metavar='LEVEL',
        help='Filter by hierarchy level (-1=subtask, 0=standard, 1=epic, etc.)'
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

    args = parser.parse_args(argv)

    try:
        issue_types = list_issue_types(
            profile=args.profile,
            subtask_only=args.subtask_only,
            standard_only=args.standard_only,
            hierarchy_level=args.hierarchy
        )

        output = format_issue_types(issue_types, args.format)
        print(output)

        if args.format == 'table' and issue_types:
            print(f"\nTotal: {len(issue_types)} issue type(s)")

    except JiraError as e:
        print_error(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
