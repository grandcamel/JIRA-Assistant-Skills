#!/usr/bin/env python3
"""
Get detailed information about a JIRA permission scheme.

Retrieves a single permission scheme by ID or name, displaying all
permission grants and their holders.

Examples:
    # Get by ID
    python get_permission_scheme.py 10000

    # Get by name
    python get_permission_scheme.py "Default Software Scheme"

    # Export grants as template
    python get_permission_scheme.py 10000 --export-template grants.json

    # JSON output
    python get_permission_scheme.py 10000 --output json
"""

import argparse
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add shared lib to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError, ValidationError
from jira_assistant_skills_lib import format_json
from jira_assistant_skills_lib import (
    format_grant_for_export,
    get_holder_display,
    find_scheme_by_name
)


def get_permission_scheme(
    client,
    scheme_id_or_name: str,
    fuzzy: bool = False
) -> Dict[str, Any]:
    """
    Get a permission scheme by ID or name.

    Args:
        client: JIRA client instance
        scheme_id_or_name: Scheme ID (numeric) or name (string)
        fuzzy: If True, allow partial name matching

    Returns:
        Permission scheme object with grants

    Raises:
        ValidationError: If scheme not found by name
        NotFoundError: If scheme not found by ID
    """
    # Try to parse as ID first
    try:
        scheme_id = int(scheme_id_or_name)
        return client.get_permission_scheme(
            scheme_id,
            expand='permissions,user,group,projectRole'
        )
    except ValueError:
        pass

    # Look up by name
    response = client.get_permission_schemes()
    schemes = response.get('permissionSchemes', [])

    scheme = find_scheme_by_name(schemes, scheme_id_or_name, fuzzy=fuzzy)

    if not scheme:
        raise ValidationError(
            f"Permission scheme not found: '{scheme_id_or_name}'. "
            "Use --list to see available schemes."
        )

    # Get the full scheme with permissions
    return client.get_permission_scheme(
        scheme['id'],
        expand='permissions,user,group,projectRole'
    )


def group_grants_by_permission(grants: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group permission grants by permission key.

    Args:
        grants: List of permission grant objects

    Returns:
        Dict mapping permission keys to lists of grants
    """
    grouped = {}
    for grant in grants:
        permission = grant.get('permission', 'UNKNOWN')
        if permission not in grouped:
            grouped[permission] = []
        grouped[permission].append(grant)
    return grouped


def group_grants_by_holder(grants: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group permission grants by holder.

    Args:
        grants: List of permission grant objects

    Returns:
        Dict mapping holder keys to lists of grants
    """
    grouped = {}
    for grant in grants:
        holder = grant.get('holder', {})
        holder_type = holder.get('type', 'unknown')
        parameter = holder.get('parameter', '')

        if parameter:
            key = f"{holder_type}:{parameter}"
        else:
            key = holder_type

        if key not in grouped:
            grouped[key] = []
        grouped[key].append(grant)
    return grouped


def export_grants_template(scheme: Dict[str, Any]) -> List[str]:
    """
    Export permission grants as a template list.

    Args:
        scheme: Permission scheme object with grants

    Returns:
        List of grant strings in format PERMISSION:holder_type[:parameter]
    """
    grants = scheme.get('permissions', [])
    return [format_grant_for_export(grant) for grant in grants]


def format_permission_scheme(
    scheme: Dict[str, Any],
    output_format: str = 'table',
    group_by: Optional[str] = None
) -> str:
    """
    Format a permission scheme for output.

    Args:
        scheme: Permission scheme object
        output_format: Output format ('table', 'json')
        group_by: How to group grants ('permission' or 'holder')

    Returns:
        Formatted string
    """
    if output_format == 'json':
        return format_json(scheme)

    # Table format
    lines = []
    lines.append(f"Permission Scheme: {scheme.get('name', 'Unknown')}")
    lines.append(f"ID: {scheme.get('id', 'N/A')}")

    description = scheme.get('description', '')
    if description:
        lines.append(f"Description: {description}")

    grants = scheme.get('permissions', [])
    lines.append(f"\nPermission Grants ({len(grants)}):")
    lines.append("-" * 60)

    if not grants:
        lines.append("  No grants configured")
        return '\n'.join(lines)

    if group_by == 'holder':
        grouped = group_grants_by_holder(grants)
        for holder_key, holder_grants in sorted(grouped.items()):
            lines.append(f"\n  {holder_key}:")
            for grant in holder_grants:
                permission = grant.get('permission', 'UNKNOWN')
                lines.append(f"    - {permission}")
    else:
        # Default: group by permission
        grouped = group_grants_by_permission(grants)
        for permission, perm_grants in sorted(grouped.items()):
            holders = [get_holder_display(g.get('holder', {})) for g in perm_grants]
            lines.append(f"  {permission}:")
            for holder in holders:
                lines.append(f"    - {holder}")

    return '\n'.join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Get detailed information about a JIRA permission scheme',
        epilog='''
Examples:
  %(prog)s 10000
  %(prog)s "Default Software Scheme"
  %(prog)s 10000 --output json
  %(prog)s 10000 --export-template grants.json
  %(prog)s "Software" --fuzzy
'''
    )
    parser.add_argument(
        'scheme',
        help='Permission scheme ID or name'
    )
    parser.add_argument(
        '--fuzzy', '-F',
        action='store_true',
        help='Allow partial name matching'
    )
    parser.add_argument(
        '--group-by', '-g',
        choices=['permission', 'holder'],
        default='permission',
        help='How to group grants (default: permission)'
    )
    parser.add_argument(
        '--export-template', '-e',
        metavar='FILE',
        help='Export grants as template to file'
    )
    parser.add_argument(
        '--output', '-o',
        choices=['table', 'json'],
        default='table',
        help='Output format (default: table)'
    )
    parser.add_argument(
        '--profile', '-p',
        help='JIRA profile to use'
    )

    args = parser.parse_args()

    try:
        client = get_jira_client(profile=args.profile)

        scheme = get_permission_scheme(
            client,
            args.scheme,
            fuzzy=args.fuzzy
        )

        if args.export_template:
            template = export_grants_template(scheme)
            with open(args.export_template, 'w') as f:
                json.dump(template, f, indent=2)
            print(f"Exported {len(template)} grants to {args.export_template}")
        else:
            output = format_permission_scheme(
                scheme,
                output_format=args.output,
                group_by=args.group_by
            )
            print(output)

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(130)


if __name__ == '__main__':
    main()
