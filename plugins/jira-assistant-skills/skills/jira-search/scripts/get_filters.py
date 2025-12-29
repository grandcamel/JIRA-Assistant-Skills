#!/usr/bin/env python3
"""
List and search saved filters.

Shows filters owned by the current user, favourite filters,
or search for filters by name, owner, or project.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add shared library to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import JiraError, print_error
from jira_assistant_skills_lib import format_table


def get_my_filters(client, expand: str = None) -> List[Dict[str, Any]]:
    """
    Get current user's filters.

    Args:
        client: JIRA client
        expand: Optional expansions

    Returns:
        List of filter objects
    """
    return client.get_my_filters(expand=expand)


def get_favourite_filters(client, expand: str = None) -> List[Dict[str, Any]]:
    """
    Get current user's favourite filters.

    Args:
        client: JIRA client
        expand: Optional expansions

    Returns:
        List of filter objects
    """
    return client.get_favourite_filters(expand=expand)


def search_filters(client, filter_name: str = None,
                   account_id: str = None,
                   project_key: str = None,
                   expand: str = None,
                   max_results: int = 50) -> Dict[str, Any]:
    """
    Search for filters.

    Args:
        client: JIRA client
        filter_name: Filter name to search for
        account_id: Filter by owner
        project_key: Filter by project
        expand: Expansions
        max_results: Max results

    Returns:
        Search result with values array
    """
    return client.search_filters(
        filter_name=filter_name,
        account_id=account_id,
        project_key=project_key,
        expand=expand,
        max_results=max_results
    )


def get_filter_by_id(client, filter_id: str,
                     expand: str = None) -> Dict[str, Any]:
    """
    Get a specific filter by ID.

    Args:
        client: JIRA client
        filter_id: Filter ID
        expand: Optional expansions

    Returns:
        Filter object
    """
    return client.get_filter(filter_id, expand=expand)


def format_filters_text(filters: List[Dict[str, Any]]) -> str:
    """
    Format filters as table.

    Args:
        filters: List of filter objects

    Returns:
        Formatted table string
    """
    if not filters:
        return "No filters found"

    data = []
    for f in filters:
        jql = f.get('jql', '')
        if len(jql) > 40:
            jql = jql[:37] + '...'

        data.append({
            'ID': f.get('id', ''),
            'Name': f.get('name', ''),
            'Favourite': 'Yes' if f.get('favourite') else 'No',
            'Owner': f.get('owner', {}).get('displayName', ''),
            'JQL': jql
        })

    # Sort by name
    data.sort(key=lambda x: x['Name'].lower())

    table = format_table(data, columns=['ID', 'Name', 'Favourite', 'Owner', 'JQL'])

    # Count favourites
    fav_count = sum(1 for f in filters if f.get('favourite'))

    return f"{table}\n\nTotal: {len(filters)} filters ({fav_count} favourites)"


def format_filter_detail(filter_data: Dict[str, Any]) -> str:
    """
    Format single filter with full details.

    Args:
        filter_data: Filter object

    Returns:
        Formatted string
    """
    lines = []

    lines.append(f"ID:          {filter_data.get('id', 'N/A')}")
    lines.append(f"Name:        {filter_data.get('name', 'N/A')}")

    owner = filter_data.get('owner', {})
    lines.append(f"Owner:       {owner.get('displayName', 'N/A')}")

    lines.append(f"Favourite:   {'Yes' if filter_data.get('favourite') else 'No'}")

    fav_count = filter_data.get('favouritedCount', 0)
    lines.append(f"Favourited:  {fav_count} users")

    description = filter_data.get('description')
    lines.append(f"Description: {description if description else '(none)'}")

    lines.append("")
    lines.append(f"JQL: {filter_data.get('jql', 'N/A')}")

    # Share permissions
    permissions = filter_data.get('sharePermissions', [])
    if permissions:
        lines.append("")
        lines.append("Shared With:")
        for p in permissions:
            ptype = p.get('type', '')
            if ptype == 'project':
                proj = p.get('project', {})
                lines.append(f"  - Project: {proj.get('name', proj.get('key', '?'))}")
            elif ptype == 'group':
                grp = p.get('group', {})
                lines.append(f"  - Group: {grp.get('name', '?')}")
            elif ptype == 'global':
                lines.append("  - Global (all users)")
            elif ptype == 'loggedin':
                lines.append("  - Logged-in users")

    # URLs
    lines.append("")
    view_url = filter_data.get('viewUrl', '')
    if view_url:
        lines.append(f"View URL: {view_url}")

    return "\n".join(lines)


def format_filters_json(filters: List[Dict[str, Any]]) -> str:
    """
    Format filters as JSON.

    Args:
        filters: List of filter objects

    Returns:
        JSON string
    """
    return json.dumps(filters, indent=2)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='List and search saved filters.',
        epilog='''
Examples:
  %(prog)s --my                    # List your filters
  %(prog)s --favourites            # List favourite filters
  %(prog)s --search "bugs"         # Search by name
  %(prog)s --search "*" --owner self   # Your filters via search
  %(prog)s --search "*" --project PROJ # Filters for project
  %(prog)s --id 10042              # Get specific filter
  %(prog)s --my --output json      # JSON output
        '''
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--my', '-m', action='store_true',
                       help='List your own filters')
    group.add_argument('--favourites', '-f', action='store_true',
                       help='List favourite filters')
    group.add_argument('--search', '-s',
                       help='Search filters by name')
    group.add_argument('--id', '-i',
                       help='Get specific filter by ID')

    parser.add_argument('--owner',
                        help='Filter by owner (account ID or "self")')
    parser.add_argument('--project',
                        help='Filter by project key')
    parser.add_argument('--output', '-o', choices=['text', 'json'],
                        default='text', help='Output format (default: text)')
    parser.add_argument('--profile', '-p',
                        help='JIRA profile to use')

    args = parser.parse_args()

    try:
        client = get_jira_client(args.profile)

        if args.my:
            filters = get_my_filters(client)
            if args.output == 'json':
                print(format_filters_json(filters))
            else:
                print("My Filters:\n")
                print(format_filters_text(filters))

        elif args.favourites:
            filters = get_favourite_filters(client)
            if args.output == 'json':
                print(format_filters_json(filters))
            else:
                print("Favourite Filters:\n")
                print(format_filters_text(filters))

        elif args.search:
            # Handle "self" owner
            account_id = None
            if args.owner:
                if args.owner.lower() == 'self':
                    account_id = client.get_current_user_id()
                else:
                    account_id = args.owner

            result = search_filters(
                client,
                filter_name=args.search if args.search != '*' else None,
                account_id=account_id,
                project_key=args.project
            )
            filters = result.get('values', [])

            if args.output == 'json':
                print(format_filters_json(filters))
            else:
                print("Search Results:\n")
                print(format_filters_text(filters))

        elif args.id:
            filter_data = get_filter_by_id(client, args.id)

            if args.output == 'json':
                print(json.dumps(filter_data, indent=2))
            else:
                print("Filter Details:\n")
                print(format_filter_detail(filter_data))

    except JiraError as e:
        print_error(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
