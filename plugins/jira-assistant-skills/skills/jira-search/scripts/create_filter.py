#!/usr/bin/env python3
"""
Create a saved filter.

Creates a new JIRA filter with the specified JQL query, optionally
sharing it with projects, groups, or globally.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add shared library to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import JiraError, print_error


def build_project_permission(project_id: str) -> Dict[str, Any]:
    """
    Build project share permission.

    Args:
        project_id: Project ID or key

    Returns:
        Permission object
    """
    return {
        'type': 'project',
        'project': {'id': project_id}
    }


def build_group_permission(group_name: str) -> Dict[str, Any]:
    """
    Build group share permission.

    Args:
        group_name: Group name

    Returns:
        Permission object
    """
    return {
        'type': 'group',
        'group': {'name': group_name}
    }


def build_global_permission() -> Dict[str, Any]:
    """
    Build global share permission.

    Returns:
        Permission object
    """
    return {'type': 'global'}


def create_filter(client, name: str, jql: str,
                  description: str = None,
                  favourite: bool = False,
                  share_permissions: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create a new filter.

    Args:
        client: JIRA client
        name: Filter name
        jql: JQL query string
        description: Optional description
        favourite: Mark as favourite
        share_permissions: List of permission objects

    Returns:
        Created filter object
    """
    return client.create_filter(
        name=name,
        jql=jql,
        description=description,
        favourite=favourite,
        share_permissions=share_permissions
    )


def format_filter_text(filter_data: Dict[str, Any]) -> str:
    """
    Format created filter for display.

    Args:
        filter_data: Filter object from API

    Returns:
        Formatted string
    """
    lines = ["Filter created successfully:", ""]

    lines.append(f"  ID:          {filter_data.get('id', 'N/A')}")
    lines.append(f"  Name:        {filter_data.get('name', 'N/A')}")
    lines.append(f"  JQL:         {filter_data.get('jql', 'N/A')}")

    description = filter_data.get('description')
    lines.append(f"  Description: {description if description else '(none)'}")

    lines.append(f"  Favourite:   {'Yes' if filter_data.get('favourite') else 'No'}")

    # Sharing info
    permissions = filter_data.get('sharePermissions', [])
    if permissions:
        share_info = []
        for p in permissions:
            ptype = p.get('type', '')
            if ptype == 'project':
                proj = p.get('project', {})
                share_info.append(f"Project: {proj.get('key', proj.get('id', '?'))}")
            elif ptype == 'group':
                grp = p.get('group', {})
                share_info.append(f"Group: {grp.get('name', '?')}")
            elif ptype == 'global':
                share_info.append("Global (all users)")
            elif ptype == 'loggedin':
                share_info.append("Logged-in users")
        lines.append(f"  Shared:      {', '.join(share_info)}")
    else:
        lines.append("  Shared:      Private (only you)")

    lines.append("")
    view_url = filter_data.get('viewUrl', '')
    if view_url:
        lines.append(f"  View URL: {view_url}")

    lines.append("")
    lines.append(f"To run this filter: python jql_search.py --filter {filter_data.get('id')}")

    return "\n".join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Create a saved filter.',
        epilog='''
Examples:
  %(prog)s --name "My Bugs" --jql "project = PROJ AND type = Bug"
  %(prog)s --name "Sprint Issues" --jql "sprint in openSprints()" --description "Active sprint work"
  %(prog)s --name "Team Bugs" --jql "..." --favourite
  %(prog)s --name "Project Bugs" --jql "..." --share-project 10000
  %(prog)s --name "Dev Bugs" --jql "..." --share-group developers
  %(prog)s --name "Public View" --jql "..." --share-global
        '''
    )

    parser.add_argument('--name', '-n', required=True,
                        help='Filter name')
    parser.add_argument('--jql', '-j', required=True,
                        help='JQL query string')
    parser.add_argument('--description', '-d',
                        help='Filter description')
    parser.add_argument('--favourite', '-f', action='store_true',
                        help='Mark as favourite')
    parser.add_argument('--share-project',
                        help='Share with project (ID or key)')
    parser.add_argument('--share-group',
                        help='Share with group')
    parser.add_argument('--share-global', action='store_true',
                        help='Share with all users')
    parser.add_argument('--output', '-o', choices=['text', 'json'],
                        default='text', help='Output format (default: text)')
    parser.add_argument('--profile', '-p',
                        help='JIRA profile to use')

    args = parser.parse_args()

    # Build permissions
    permissions = []
    if args.share_project:
        permissions.append(build_project_permission(args.share_project))
    if args.share_group:
        permissions.append(build_group_permission(args.share_group))
    if args.share_global:
        permissions.append(build_global_permission())

    try:
        client = get_jira_client(args.profile)

        result = create_filter(
            client,
            name=args.name,
            jql=args.jql,
            description=args.description,
            favourite=args.favourite,
            share_permissions=permissions if permissions else None
        )

        if args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            print(format_filter_text(result))

    except JiraError as e:
        print_error(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
