#!/usr/bin/env python3
"""
Create a JIRA permission scheme.

Creates a new permission scheme, optionally with initial grants or by cloning
an existing scheme.

Examples:
    # Create empty scheme
    python create_permission_scheme.py --name "New Scheme" --description "Description"

    # Create with grants
    python create_permission_scheme.py --name "New Scheme" \\
      --grant "BROWSE_PROJECTS:anyone" \\
      --grant "CREATE_ISSUES:group:jira-developers"

    # Create from template
    python create_permission_scheme.py --name "New Scheme" --template grants.json

    # Clone existing scheme
    python create_permission_scheme.py --name "Cloned Scheme" --clone 10000

    # Dry run
    python create_permission_scheme.py --name "Test" --grant "BROWSE_PROJECTS:anyone" --dry-run
"""

import argparse
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import print_error, JiraError, ValidationError
from formatters import format_json
from permission_helpers import (
    parse_grant_string,
    build_grant_payload,
    VALID_HOLDER_TYPES
)


def parse_grants(grant_strings: List[str]) -> List[Dict[str, Any]]:
    """
    Parse grant strings into API-ready format.

    Args:
        grant_strings: List of grant strings in format PERMISSION:holder_type[:parameter]

    Returns:
        List of permission grant objects

    Raises:
        ValidationError: If any grant string is invalid
    """
    grants = []
    for grant_str in grant_strings:
        permission, holder_type, holder_param = parse_grant_string(grant_str)
        grants.append(build_grant_payload(permission, holder_type, holder_param))
    return grants


def load_template(file_path: str) -> List[str]:
    """
    Load grant strings from a template file.

    Args:
        file_path: Path to JSON template file

    Returns:
        List of grant strings

    Raises:
        ValidationError: If file is invalid
        FileNotFoundError: If file doesn't exist
    """
    try:
        with open(file_path, 'r') as f:
            template = json.load(f)

        if not isinstance(template, list):
            raise ValidationError(f"Template must be a JSON array of grant strings")

        return template
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON in template file: {e}")


def create_permission_scheme(
    client,
    name: str,
    description: Optional[str] = None,
    grants: Optional[List[str]] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Create a new permission scheme.

    Args:
        client: JIRA client instance
        name: Name for the new scheme
        description: Optional description
        grants: Optional list of grant strings
        dry_run: If True, don't actually create, just return preview

    Returns:
        Created scheme or preview

    Raises:
        ValidationError: If name is empty or grants are invalid
    """
    if not name or not name.strip():
        raise ValidationError("Scheme name cannot be empty")

    permissions = []
    if grants:
        permissions = parse_grants(grants)

    if dry_run:
        # Return preview without creating
        preview = {
            'name': name,
            'description': description or '',
            'permissions': permissions
        }
        return preview

    return client.create_permission_scheme(
        name=name,
        description=description,
        permissions=permissions if permissions else None
    )


def clone_permission_scheme(
    client,
    source_id: int,
    new_name: str,
    description: Optional[str] = None,
    additional_grants: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Clone an existing permission scheme.

    Args:
        client: JIRA client instance
        source_id: ID of scheme to clone
        new_name: Name for the new scheme
        description: Optional description (uses source's if not provided)
        additional_grants: Optional additional grant strings to add

    Returns:
        Created scheme
    """
    # Get the source scheme
    source = client.get_permission_scheme(source_id, expand='permissions')

    # Extract grants from source
    permissions = []
    for grant in source.get('permissions', []):
        permissions.append({
            'permission': grant.get('permission'),
            'holder': grant.get('holder', {})
        })

    # Add additional grants
    if additional_grants:
        for grant_str in additional_grants:
            permission, holder_type, holder_param = parse_grant_string(grant_str)
            permissions.append(build_grant_payload(permission, holder_type, holder_param))

    # Use source description if not provided
    if description is None:
        description = source.get('description', '')

    return client.create_permission_scheme(
        name=new_name,
        description=description,
        permissions=permissions
    )


def format_created_scheme(scheme: Dict[str, Any], output_format: str = 'table') -> str:
    """
    Format created scheme for output.

    Args:
        scheme: Created scheme object
        output_format: Output format ('table', 'json')

    Returns:
        Formatted string
    """
    if output_format == 'json':
        return format_json(scheme)

    lines = []
    lines.append(f"Created permission scheme: {scheme.get('name', 'Unknown')}")
    lines.append(f"ID: {scheme.get('id', 'N/A')}")

    description = scheme.get('description', '')
    if description:
        lines.append(f"Description: {description}")

    permissions = scheme.get('permissions', [])
    lines.append(f"Grants: {len(permissions)}")

    return '\n'.join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Create a JIRA permission scheme',
        epilog='''
Examples:
  %(prog)s --name "New Scheme" --description "Description"
  %(prog)s --name "New Scheme" --grant "BROWSE_PROJECTS:anyone"
  %(prog)s --name "New Scheme" --template grants.json
  %(prog)s --name "Cloned Scheme" --clone 10000
  %(prog)s --name "Test" --grant "BROWSE_PROJECTS:anyone" --dry-run
'''
    )
    parser.add_argument(
        '--name', '-n',
        required=True,
        help='Name for the new scheme'
    )
    parser.add_argument(
        '--description', '-d',
        help='Description for the scheme'
    )
    parser.add_argument(
        '--grant', '-g',
        action='append',
        dest='grants',
        help='Permission grant (format: PERMISSION:holder_type[:parameter]). Can be repeated.'
    )
    parser.add_argument(
        '--template', '-t',
        help='JSON file containing grant strings'
    )
    parser.add_argument(
        '--clone', '-c',
        type=int,
        dest='clone_id',
        help='Clone grants from existing scheme ID'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview without creating'
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

        # Collect grants from all sources
        all_grants = args.grants or []

        if args.template:
            template_grants = load_template(args.template)
            all_grants.extend(template_grants)

        if args.clone_id:
            # Clone mode
            scheme = clone_permission_scheme(
                client,
                source_id=args.clone_id,
                new_name=args.name,
                description=args.description,
                additional_grants=all_grants if all_grants else None
            )
        else:
            # Create mode
            scheme = create_permission_scheme(
                client,
                name=args.name,
                description=args.description,
                grants=all_grants if all_grants else None,
                dry_run=args.dry_run
            )

        if args.dry_run:
            print("=== DRY RUN ===")
            print("Would create permission scheme:")
            print()

        output = format_created_scheme(scheme, output_format=args.output)
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
