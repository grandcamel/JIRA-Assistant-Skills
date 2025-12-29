#!/usr/bin/env python3
"""
Assign a JIRA permission scheme to projects.

Assigns a permission scheme to one or more projects.

Examples:
    # Assign to a single project
    python assign_permission_scheme.py --project PROJ --scheme 10050

    # Assign to multiple projects
    python assign_permission_scheme.py --projects PROJ,DEV,QA --scheme 10050

    # Use scheme name instead of ID
    python assign_permission_scheme.py --project PROJ --scheme "Custom Scheme"

    # Show current scheme
    python assign_permission_scheme.py --project PROJ --show-current

    # Dry run
    python assign_permission_scheme.py --project PROJ --scheme 10050 --dry-run
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add shared lib to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError, ValidationError
from jira_assistant_skills_lib import format_json, format_table


def resolve_scheme_id(client, scheme_id_or_name: str) -> int:
    """
    Resolve a scheme reference to its ID.

    Args:
        client: JIRA client instance
        scheme_id_or_name: Scheme ID (numeric) or name

    Returns:
        Scheme ID as integer

    Raises:
        ValidationError: If scheme not found by name
    """
    # Try to parse as ID
    try:
        scheme_id = int(scheme_id_or_name)
        return scheme_id
    except ValueError:
        pass

    # Look up by name
    response = client.get_permission_schemes()
    schemes = response.get('permissionSchemes', [])

    for scheme in schemes:
        if scheme.get('name', '').lower() == scheme_id_or_name.lower():
            return scheme['id']

    raise ValidationError(
        f"Permission scheme not found: '{scheme_id_or_name}'. "
        "Use list_permission_schemes.py to see available schemes."
    )


def get_current_scheme(client, project_key: str) -> Dict[str, Any]:
    """
    Get the current permission scheme for a project.

    Args:
        client: JIRA client instance
        project_key: Project key

    Returns:
        Current permission scheme
    """
    return client.get_project_permission_scheme(project_key)


def get_current_schemes(
    client,
    project_keys: List[str]
) -> Dict[str, Dict[str, Any]]:
    """
    Get current permission schemes for multiple projects.

    Args:
        client: JIRA client instance
        project_keys: List of project keys

    Returns:
        Dict mapping project keys to their schemes
    """
    result = {}
    for key in project_keys:
        result[key] = get_current_scheme(client, key)
    return result


def assign_permission_scheme(
    client,
    project_key: str,
    scheme_id: int,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Assign a permission scheme to a project.

    Args:
        client: JIRA client instance
        project_key: Project key
        scheme_id: Permission scheme ID
        dry_run: If True, don't actually assign

    Returns:
        Assigned scheme (or preview if dry-run)
    """
    if dry_run:
        current = get_current_scheme(client, project_key)
        return {
            'project_key': project_key,
            'current': current,
            'new_id': scheme_id
        }

    return client.assign_permission_scheme_to_project(project_key, scheme_id)


def assign_permission_scheme_to_projects(
    client,
    project_keys: List[str],
    scheme_id: int,
    dry_run: bool = False
) -> List[Dict[str, Any]]:
    """
    Assign a permission scheme to multiple projects.

    Args:
        client: JIRA client instance
        project_keys: List of project keys
        scheme_id: Permission scheme ID
        dry_run: If True, don't actually assign

    Returns:
        List of assignment results
    """
    results = []
    for key in project_keys:
        result = assign_permission_scheme(client, key, scheme_id, dry_run=dry_run)
        results.append(result)
    return results


def preview_assignment(
    client,
    project_key: str,
    scheme_id: int
) -> Dict[str, Any]:
    """
    Preview an assignment without making changes.

    Args:
        client: JIRA client instance
        project_key: Project key
        scheme_id: Target scheme ID

    Returns:
        Preview with current and new scheme info
    """
    current = get_current_scheme(client, project_key)
    new_scheme = client.get_permission_scheme(scheme_id)

    return {
        'project_key': project_key,
        'current': current,
        'new': new_scheme
    }


def format_current_schemes(schemes: Dict[str, Dict[str, Any]]) -> str:
    """Format current scheme assignments."""
    data = []
    for key, scheme in schemes.items():
        data.append({
            'Project': key,
            'Scheme ID': scheme.get('id', ''),
            'Scheme Name': scheme.get('name', '')
        })
    return format_table(data, columns=['Project', 'Scheme ID', 'Scheme Name'])


def format_assignment_result(
    results: List[Dict[str, Any]],
    scheme_name: str,
    dry_run: bool = False
) -> str:
    """Format assignment results."""
    lines = []

    if dry_run:
        lines.append("=== DRY RUN ===")
        lines.append(f"Would assign scheme: {scheme_name}")
        lines.append("")

    for result in results:
        if 'project_key' in result:
            # Preview format
            key = result['project_key']
            current = result.get('current', {})
            lines.append(f"  {key}: {current.get('name', 'Unknown')} -> {scheme_name}")
        else:
            # Actual result
            lines.append(f"  Assigned: {result.get('name', 'Unknown')} (ID: {result.get('id')})")

    if dry_run:
        lines.append("")
        lines.append("No changes made (dry-run mode)")

    return '\n'.join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Assign a JIRA permission scheme to projects',
        epilog='''
Examples:
  %(prog)s --project PROJ --scheme 10050
  %(prog)s --projects PROJ,DEV,QA --scheme 10050
  %(prog)s --project PROJ --scheme "Custom Scheme"
  %(prog)s --project PROJ --show-current
  %(prog)s --project PROJ --scheme 10050 --dry-run
'''
    )
    parser.add_argument(
        '--project', '-P',
        help='Single project key'
    )
    parser.add_argument(
        '--projects',
        help='Comma-separated project keys'
    )
    parser.add_argument(
        '--scheme', '-s',
        help='Permission scheme ID or name'
    )
    parser.add_argument(
        '--show-current',
        action='store_true',
        help='Show current scheme assignment(s) only'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview assignment without making changes'
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

    # Validate arguments
    if not args.project and not args.projects:
        parser.error("Either --project or --projects is required")

    if not args.show_current and not args.scheme:
        parser.error("Either --scheme or --show-current is required")

    try:
        client = get_jira_client(profile=args.profile)

        # Get project keys
        if args.projects:
            project_keys = [k.strip() for k in args.projects.split(',')]
        else:
            project_keys = [args.project]

        # Show current schemes
        if args.show_current:
            schemes = get_current_schemes(client, project_keys)
            if args.output == 'json':
                print(format_json(schemes))
            else:
                print(format_current_schemes(schemes))
            return

        # Resolve scheme
        scheme_id = resolve_scheme_id(client, args.scheme)
        scheme_info = client.get_permission_scheme(scheme_id)
        scheme_name = scheme_info.get('name', f'ID {scheme_id}')

        # Assign scheme
        results = assign_permission_scheme_to_projects(
            client,
            project_keys=project_keys,
            scheme_id=scheme_id,
            dry_run=args.dry_run
        )

        if args.output == 'json':
            print(format_json(results))
        else:
            output = format_assignment_result(results, scheme_name, dry_run=args.dry_run)
            print(output)

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(130)


if __name__ == '__main__':
    main()
