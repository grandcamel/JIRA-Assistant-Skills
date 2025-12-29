#!/usr/bin/env python3
"""
List available issue link types in JIRA.

Usage:
    python get_link_types.py
    python get_link_types.py --output json
    python get_link_types.py --filter "block"
"""

import sys
import argparse
import json
from pathlib import Path


from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError


def get_link_types(filter_pattern: str = None, profile: str = None) -> list:
    """
    Get all available issue link types.

    Args:
        filter_pattern: Optional pattern to filter link types by name
        profile: JIRA profile to use

    Returns:
        List of link type objects
    """
    client = get_jira_client(profile)
    link_types = client.get_link_types()
    client.close()

    if filter_pattern:
        pattern_lower = filter_pattern.lower()
        link_types = [
            lt for lt in link_types
            if pattern_lower in lt['name'].lower() or
               pattern_lower in lt.get('inward', '').lower() or
               pattern_lower in lt.get('outward', '').lower()
        ]

    return link_types


def format_link_types(link_types: list, output_format: str = 'text') -> str:
    """
    Format link types for output.

    Args:
        link_types: List of link type objects
        output_format: 'text' or 'json'

    Returns:
        Formatted string
    """
    if output_format == 'json':
        return json.dumps(link_types, indent=2)

    if not link_types:
        return "No link types found."

    # Calculate column widths
    name_width = max(len(lt['name']) for lt in link_types)
    outward_width = max(len(lt.get('outward', '')) for lt in link_types)
    inward_width = max(len(lt.get('inward', '')) for lt in link_types)

    # Minimum widths
    name_width = max(name_width, 4)
    outward_width = max(outward_width, 7)
    inward_width = max(inward_width, 6)

    # Build header
    lines = []
    lines.append("Available Link Types:")
    lines.append("")
    header = f"{'Name':<{name_width}}  {'Outward':<{outward_width}}  {'Inward':<{inward_width}}"
    lines.append(header)
    lines.append("─" * name_width + "  " + "─" * outward_width + "  " + "─" * inward_width)

    # Build rows
    for lt in link_types:
        row = f"{lt['name']:<{name_width}}  {lt.get('outward', ''):<{outward_width}}  {lt.get('inward', ''):<{inward_width}}"
        lines.append(row)

    lines.append("")
    lines.append(f"Total: {len(link_types)} link type(s)")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='List available issue link types',
        epilog='Example: python get_link_types.py --filter "block"'
    )

    parser.add_argument('--filter', '-f',
                       help='Filter link types by name pattern (case-insensitive)')
    parser.add_argument('--output', '-o',
                       choices=['text', 'json'],
                       default='text',
                       help='Output format (default: text)')
    parser.add_argument('--profile',
                       help='JIRA profile to use (default: from config)')

    args = parser.parse_args()

    try:
        link_types = get_link_types(
            filter_pattern=args.filter,
            profile=args.profile
        )
        output = format_link_types(link_types, output_format=args.output)
        print(output)

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
