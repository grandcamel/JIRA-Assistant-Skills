#!/usr/bin/env python3
"""
Get issue type scheme details from JIRA.

Retrieves detailed information about a specific scheme by ID.
Requires 'Administer Jira' global permission.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import JiraError, NotFoundError, print_error


def get_issue_type_scheme(
    scheme_id: str,
    client=None,
    profile: Optional[str] = None,
    include_items: bool = False
) -> Dict[str, Any]:
    """
    Get issue type scheme details by ID.

    Args:
        scheme_id: Scheme ID
        client: JiraClient instance (for testing)
        profile: Configuration profile name
        include_items: If True, include issue type mappings

    Returns:
        Scheme details dictionary

    Raises:
        NotFoundError: If scheme not found
        JiraError: On API failure
    """
    if client is None:
        client = get_jira_client(profile=profile)

    try:
        # Get scheme by filtering
        result = client.get_issue_type_schemes(scheme_ids=[scheme_id])
        schemes = result.get('values', [])

        if not schemes:
            raise NotFoundError('Issue type scheme', scheme_id)

        scheme = schemes[0]

        # Get issue type mappings if requested
        if include_items:
            items_result = client.get_issue_type_scheme_items(
                scheme_ids=[scheme_id]
            )
            scheme['items'] = [
                item for item in items_result.get('values', [])
                if item.get('issueTypeSchemeId') == scheme_id
            ]

        return scheme
    finally:
        if client:
            client.close()


def format_scheme(scheme: Dict[str, Any], output_format: str = 'detail') -> str:
    """Format scheme for display."""
    if output_format == 'json':
        return json.dumps(scheme, indent=2)

    lines = []
    lines.append(f"Issue Type Scheme: {scheme.get('name', 'Unknown')}")
    lines.append("=" * 50)
    lines.append(f"ID:              {scheme.get('id', '')}")
    lines.append(f"Name:            {scheme.get('name', '')}")
    lines.append(f"Description:     {scheme.get('description', '') or 'None'}")
    lines.append(f"Default Type ID: {scheme.get('defaultIssueTypeId', 'None')}")
    lines.append(f"Is Default:      {'Yes' if scheme.get('isDefault') else 'No'}")

    # Issue type mappings
    if 'items' in scheme and scheme['items']:
        lines.append("")
        lines.append("Issue Types in Scheme:")
        lines.append("-" * 30)
        for item in scheme['items']:
            lines.append(f"  - Type ID: {item.get('issueTypeId', '')}")

    return '\n'.join(lines)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Get issue type scheme details from JIRA',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get scheme by ID
  python get_issue_type_scheme.py 10000

  # Include issue type mappings
  python get_issue_type_scheme.py 10000 --include-items

  # Output as JSON
  python get_issue_type_scheme.py 10000 --format json

  # Use specific profile
  python get_issue_type_scheme.py 10000 --profile production
"""
    )

    parser.add_argument(
        'scheme_id',
        help='Issue type scheme ID to retrieve'
    )
    parser.add_argument(
        '--include-items',
        action='store_true',
        help='Include issue type mappings'
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
        scheme = get_issue_type_scheme(
            scheme_id=args.scheme_id,
            profile=args.profile,
            include_items=args.include_items
        )

        output = format_scheme(scheme, args.format)
        print(output)

    except JiraError as e:
        print_error(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
