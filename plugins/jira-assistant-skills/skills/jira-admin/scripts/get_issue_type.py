#!/usr/bin/env python3
"""
Get issue type details from JIRA.

Retrieves detailed information about a specific issue type by ID.
Requires 'Administer Jira' global permission for some features.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add shared lib to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import JiraError, print_error


def get_issue_type(
    issue_type_id: str,
    client=None,
    profile: Optional[str] = None,
    show_alternatives: bool = False
) -> Dict[str, Any]:
    """
    Get issue type details by ID.

    Args:
        issue_type_id: Issue type ID
        client: JiraClient instance (for testing)
        profile: Configuration profile name
        show_alternatives: If True, also fetch alternative types

    Returns:
        Issue type details dictionary

    Raises:
        JiraError: On API failure
        NotFoundError: If issue type not found
    """
    if client is None:
        client = get_jira_client(profile=profile)

    try:
        issue_type = client.get_issue_type(issue_type_id)

        if show_alternatives:
            alternatives = client.get_issue_type_alternatives(issue_type_id)
            issue_type['alternatives'] = alternatives

        return issue_type
    finally:
        if client:
            client.close()


def format_issue_type(issue_type: Dict[str, Any], output_format: str = 'detail') -> str:
    """Format issue type for display."""
    if output_format == 'json':
        return json.dumps(issue_type, indent=2)

    lines = []
    lines.append(f"Issue Type: {issue_type.get('name', 'Unknown')}")
    lines.append("=" * 50)
    lines.append(f"ID:          {issue_type.get('id', '')}")
    lines.append(f"Name:        {issue_type.get('name', '')}")
    lines.append(f"Description: {issue_type.get('description', '') or 'None'}")
    lines.append(f"Subtask:     {'Yes' if issue_type.get('subtask') else 'No'}")
    lines.append(f"Hierarchy:   {issue_type.get('hierarchyLevel', 0)}")

    # Scope information
    scope = issue_type.get('scope', {})
    scope_type = scope.get('type', 'GLOBAL')
    lines.append(f"Scope:       {scope_type}")
    if scope_type == 'PROJECT' and 'project' in scope:
        lines.append(f"Project ID:  {scope['project'].get('id', '')}")

    # Avatar
    if issue_type.get('avatarId'):
        lines.append(f"Avatar ID:   {issue_type.get('avatarId')}")

    # Entity ID
    if issue_type.get('entityId'):
        lines.append(f"Entity ID:   {issue_type.get('entityId')}")

    # Icon URL
    if issue_type.get('iconUrl'):
        lines.append(f"Icon URL:    {issue_type.get('iconUrl')}")

    # Alternatives
    if issue_type.get('alternatives'):
        lines.append("")
        lines.append("Alternative Issue Types:")
        lines.append("-" * 30)
        for alt in issue_type['alternatives']:
            lines.append(f"  - {alt.get('name', '')} (ID: {alt.get('id', '')})")

    return '\n'.join(lines)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Get issue type details from JIRA',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get issue type by ID
  python get_issue_type.py 10000

  # Get issue type with alternatives (for deletion)
  python get_issue_type.py 10000 --show-alternatives

  # Output as JSON
  python get_issue_type.py 10000 --format json

  # Use specific profile
  python get_issue_type.py 10000 --profile production
"""
    )

    parser.add_argument(
        'issue_type_id',
        help='Issue type ID to retrieve'
    )
    parser.add_argument(
        '--show-alternatives',
        action='store_true',
        help='Show alternative issue types (for migration/deletion)'
    )
    parser.add_argument(
        '--format',
        choices=['detail', 'json'],
        default='detail',
        help='Output format (default: detail)'
    )
    parser.add_argument(
        '--profile',
        help='Configuration profile to use'
    )

    args = parser.parse_args()

    try:
        issue_type = get_issue_type(
            issue_type_id=args.issue_type_id,
            profile=args.profile,
            show_alternatives=args.show_alternatives
        )

        output = format_issue_type(issue_type, args.format)
        print(output)

    except JiraError as e:
        print_error(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
