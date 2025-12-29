#!/usr/bin/env python3
"""
Update a JIRA permission scheme.

Updates a permission scheme's name, description, or grants. Can add or remove
individual permission grants.

Examples:
    # Update name
    python update_permission_scheme.py 10000 --name "Updated Name"

    # Update description
    python update_permission_scheme.py 10000 --description "New description"

    # Add a grant
    python update_permission_scheme.py 10000 --add-grant "LINK_ISSUES:group:developers"

    # Remove a grant by ID
    python update_permission_scheme.py 10000 --remove-grant 10103

    # Remove a grant by specification
    python update_permission_scheme.py 10000 --remove-grant "EDIT_ISSUES:group:testers"
"""

import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add shared lib to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError, ValidationError
from jira_assistant_skills_lib import format_json
from jira_assistant_skills_lib import (
    parse_grant_string,
    find_grant_by_spec
)


def update_permission_scheme(
    client,
    scheme_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update a permission scheme's metadata.

    Args:
        client: JIRA client instance
        scheme_id: Permission scheme ID
        name: New name (optional)
        description: New description (optional)

    Returns:
        Updated scheme
    """
    return client.update_permission_scheme(
        scheme_id,
        name=name,
        description=description
    )


def add_grants(
    client,
    scheme_id: int,
    grants: List[str],
    dry_run: bool = False
) -> List[Dict[str, Any]]:
    """
    Add permission grants to a scheme.

    Args:
        client: JIRA client instance
        scheme_id: Permission scheme ID
        grants: List of grant strings
        dry_run: If True, don't actually add grants

    Returns:
        List of created grant objects
    """
    results = []

    for grant_str in grants:
        permission, holder_type, holder_param = parse_grant_string(grant_str)

        if dry_run:
            # Return preview
            results.append({
                'permission': permission,
                'holder': {
                    'type': holder_type,
                    'parameter': holder_param
                }
            })
        else:
            result = client.create_permission_grant(
                scheme_id=scheme_id,
                permission=permission,
                holder_type=holder_type,
                holder_parameter=holder_param
            )
            results.append(result)

    return results


def remove_grants(
    client,
    scheme_id: int,
    grant_ids: List[int],
    dry_run: bool = False
) -> None:
    """
    Remove permission grants by ID.

    Args:
        client: JIRA client instance
        scheme_id: Permission scheme ID
        grant_ids: List of grant IDs to remove
        dry_run: If True, don't actually remove grants
    """
    for grant_id in grant_ids:
        if not dry_run:
            client.delete_permission_grant(scheme_id, grant_id)


def find_and_remove_grant(
    client,
    scheme_id: int,
    grant_spec: str,
    dry_run: bool = False
) -> bool:
    """
    Find and remove a grant by specification.

    Args:
        client: JIRA client instance
        scheme_id: Permission scheme ID
        grant_spec: Grant specification (PERMISSION:holder_type[:parameter])
        dry_run: If True, don't actually remove grant

    Returns:
        True if grant was found (and removed if not dry-run)

    Raises:
        ValidationError: If grant not found
    """
    # Get current scheme with grants
    scheme = client.get_permission_scheme(scheme_id, expand='permissions')
    grants = scheme.get('permissions', [])

    # Parse the specification
    permission, holder_type, holder_param = parse_grant_string(grant_spec)

    # Find matching grant
    matching_grant = find_grant_by_spec(grants, permission, holder_type, holder_param)

    if not matching_grant:
        raise ValidationError(
            f"Grant not found: {grant_spec}. "
            "Use get_permission_scheme.py to view current grants."
        )

    if not dry_run:
        client.delete_permission_grant(scheme_id, matching_grant['id'])

    return True


def format_update_result(
    scheme: Optional[Dict[str, Any]] = None,
    added_grants: Optional[List[Dict[str, Any]]] = None,
    removed_grants: Optional[List[str]] = None,
    output_format: str = 'table'
) -> str:
    """
    Format update results for output.

    Args:
        scheme: Updated scheme object (if metadata was updated)
        added_grants: List of added grants
        removed_grants: List of removed grant descriptions
        output_format: Output format

    Returns:
        Formatted string
    """
    if output_format == 'json':
        result = {}
        if scheme:
            result['scheme'] = scheme
        if added_grants:
            result['added_grants'] = added_grants
        if removed_grants:
            result['removed_grants'] = removed_grants
        return format_json(result)

    lines = []

    if scheme:
        lines.append(f"Updated scheme: {scheme.get('name', 'Unknown')} (ID: {scheme.get('id')})")
        lines.append(f"  Description: {scheme.get('description', '')}")

    if added_grants:
        lines.append(f"\nAdded {len(added_grants)} grant(s):")
        for grant in added_grants:
            perm = grant.get('permission', 'UNKNOWN')
            holder = grant.get('holder', {})
            holder_type = holder.get('type', 'unknown')
            param = holder.get('parameter', '')
            if param:
                lines.append(f"  + {perm}: {holder_type}:{param}")
            else:
                lines.append(f"  + {perm}: {holder_type}")

    if removed_grants:
        lines.append(f"\nRemoved {len(removed_grants)} grant(s):")
        for grant in removed_grants:
            lines.append(f"  - {grant}")

    return '\n'.join(lines) if lines else "No changes made."


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Update a JIRA permission scheme',
        epilog='''
Examples:
  %(prog)s 10000 --name "Updated Name"
  %(prog)s 10000 --description "New description"
  %(prog)s 10000 --add-grant "LINK_ISSUES:group:developers"
  %(prog)s 10000 --remove-grant 10103
  %(prog)s 10000 --remove-grant "EDIT_ISSUES:group:testers"
  %(prog)s 10000 --add-grant "LINK_ISSUES:anyone" --dry-run
'''
    )
    parser.add_argument(
        'scheme_id',
        type=int,
        help='Permission scheme ID to update'
    )
    parser.add_argument(
        '--name', '-n',
        help='New name for the scheme'
    )
    parser.add_argument(
        '--description', '-d',
        help='New description for the scheme'
    )
    parser.add_argument(
        '--add-grant', '-a',
        action='append',
        dest='add_grants',
        metavar='GRANT',
        help='Add a permission grant (format: PERMISSION:holder_type[:parameter])'
    )
    parser.add_argument(
        '--remove-grant', '-r',
        action='append',
        dest='remove_grants',
        metavar='GRANT_ID_OR_SPEC',
        help='Remove a grant by ID or specification'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without making them'
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

        updated_scheme = None
        added = None
        removed = []

        # Update metadata
        if args.name or args.description:
            if args.dry_run:
                updated_scheme = {
                    'id': args.scheme_id,
                    'name': args.name or '(unchanged)',
                    'description': args.description or '(unchanged)'
                }
            else:
                updated_scheme = update_permission_scheme(
                    client,
                    scheme_id=args.scheme_id,
                    name=args.name,
                    description=args.description
                )

        # Add grants
        if args.add_grants:
            added = add_grants(
                client,
                scheme_id=args.scheme_id,
                grants=args.add_grants,
                dry_run=args.dry_run
            )

        # Remove grants
        if args.remove_grants:
            for grant_str in args.remove_grants:
                # Try to parse as ID first
                try:
                    grant_id = int(grant_str)
                    if not args.dry_run:
                        remove_grants(client, args.scheme_id, [grant_id])
                    removed.append(f"ID {grant_id}")
                except ValueError:
                    # It's a specification
                    find_and_remove_grant(
                        client,
                        scheme_id=args.scheme_id,
                        grant_spec=grant_str,
                        dry_run=args.dry_run
                    )
                    removed.append(grant_str)

        if args.dry_run:
            print("=== DRY RUN ===")
            print()

        output = format_update_result(
            scheme=updated_scheme,
            added_grants=added,
            removed_grants=removed if removed else None,
            output_format=args.output
        )
        print(output)

        if args.dry_run:
            print()
            print("No changes made (dry-run mode)")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(130)


if __name__ == '__main__':
    main()
