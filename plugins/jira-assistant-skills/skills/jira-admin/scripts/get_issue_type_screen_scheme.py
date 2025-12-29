#!/usr/bin/env python3
"""
Get detailed information about a specific issue type screen scheme.

Shows scheme details, issue type mappings, and associated projects.
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add shared lib to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError
from jira_assistant_skills_lib import format_json, format_table


def get_issue_type_screen_scheme(scheme_id: int,
                                  client=None,
                                  show_mappings: bool = False,
                                  show_projects: bool = False) -> Dict[str, Any]:
    """
    Get detailed information about a specific issue type screen scheme.

    Args:
        scheme_id: Issue type screen scheme ID
        client: JiraClient instance
        show_mappings: Include issue type to screen scheme mappings
        show_projects: Include associated projects

    Returns:
        Issue type screen scheme object with optional details
    """
    if client is None:
        from config_manager import get_jira_client
        client = get_jira_client()

    scheme = client.get_issue_type_screen_scheme(scheme_id)

    if show_mappings:
        mappings_result = client.get_issue_type_screen_scheme_mappings(
            scheme_ids=[scheme_id]
        )
        mappings = []
        for m in mappings_result.get('values', []):
            if str(m.get('issueTypeScreenSchemeId')) == str(scheme_id):
                mappings.append({
                    'issue_type_id': m.get('issueTypeId'),
                    'screen_scheme_id': m.get('screenSchemeId')
                })
        scheme['mappings'] = mappings

    if show_projects:
        project_result = client.get_project_issue_type_screen_schemes()
        project_ids = []
        for mapping in project_result.get('values', []):
            itss = mapping.get('issueTypeScreenScheme', {})
            if str(itss.get('id', '')) == str(scheme_id):
                project_ids = mapping.get('projectIds', [])
                break
        scheme['project_ids'] = project_ids

    return scheme


def format_scheme_output(scheme: Dict[str, Any],
                         output_format: str = 'text') -> str:
    """
    Format issue type screen scheme details for output.

    Args:
        scheme: Issue type screen scheme object
        output_format: Output format ('text', 'json')

    Returns:
        Formatted output string
    """
    if output_format == 'json':
        return format_json(scheme)

    lines = []
    lines.append(f"Issue Type Screen Scheme: {scheme.get('name', 'Unknown')}")
    lines.append(f"ID: {scheme.get('id', 'N/A')}")

    description = scheme.get('description')
    if description:
        lines.append(f"Description: {description}")

    mappings = scheme.get('mappings', [])
    if mappings:
        lines.append("\nIssue Type to Screen Scheme Mappings:")
        for m in mappings:
            issue_type = m.get('issue_type_id', 'unknown')
            screen_scheme = m.get('screen_scheme_id', 'unknown')
            issue_type_label = 'Default' if issue_type == 'default' else f"Issue Type {issue_type}"
            lines.append(f"  {issue_type_label} -> Screen Scheme {screen_scheme}")

    project_ids = scheme.get('project_ids', [])
    if project_ids:
        lines.append(f"\nAssociated Projects: {len(project_ids)}")
        for pid in project_ids[:10]:  # Show first 10
            lines.append(f"  - Project ID: {pid}")
        if len(project_ids) > 10:
            lines.append(f"  ... and {len(project_ids) - 10} more")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Get detailed information about a JIRA issue type screen scheme',
        epilog='''
Examples:
    # Get basic scheme info
    python get_issue_type_screen_scheme.py 10000

    # Include issue type mappings
    python get_issue_type_screen_scheme.py 10000 --mappings

    # Include project associations
    python get_issue_type_screen_scheme.py 10000 --projects

    # Include all details
    python get_issue_type_screen_scheme.py 10000 --mappings --projects

    # JSON output
    python get_issue_type_screen_scheme.py 10000 --output json
'''
    )

    parser.add_argument('scheme_id', type=int,
                        help='Issue type screen scheme ID')
    parser.add_argument('--mappings', '-m', dest='show_mappings', action='store_true',
                        help='Show issue type to screen scheme mappings')
    parser.add_argument('--projects', '-P', dest='show_projects', action='store_true',
                        help='Show associated projects')
    parser.add_argument('--output', '-o', choices=['text', 'json'], default='text',
                        help='Output format (default: text)')
    parser.add_argument('--profile', '-p', help='JIRA profile to use')

    args = parser.parse_args()

    try:
        client = get_jira_client(args.profile)

        scheme = get_issue_type_screen_scheme(
            scheme_id=args.scheme_id,
            client=client,
            show_mappings=args.show_mappings,
            show_projects=args.show_projects
        )

        output = format_scheme_output(scheme, args.output)
        print(output)

    except JiraError as e:
        print_error(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
