#!/usr/bin/env python3
"""
Check field availability for a JIRA project.

Usage:
    python check_project_fields.py PROJ
    python check_project_fields.py PROJ --type Story
    python check_project_fields.py PROJ --check-agile
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add shared lib to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError
from jira_assistant_skills_lib import format_table, format_json, print_info, print_success, print_warning

# Agile field patterns and expected fields
AGILE_FIELDS = {
    'sprint': ['sprint'],
    'story_points': ['story point', 'story points', 'story point estimate'],
    'epic_link': ['epic link'],
    'epic_name': ['epic name'],
    'rank': ['rank']
}


def check_project_fields(project_key: str,
                         issue_type: str = None,
                         check_agile: bool = False,
                         profile: str = None,
                         client=None) -> Dict[str, Any]:
    """
    Check field availability for a project.

    Args:
        project_key: Project key
        issue_type: Optional issue type to check
        check_agile: If True, specifically check Agile field availability
        profile: JIRA profile to use
        client: JiraClient instance (for testing)

    Returns:
        Dictionary with project info and available fields

    Raises:
        JiraError: If API call fails
    """
    if not client:
        client = get_jira_client(profile)
        should_close = True
    else:
        should_close = False

    try:
        # Get project info
        project = client.get(f'/rest/api/3/project/{project_key}')

        result = {
            'project_key': project.get('key'),  # Top-level for convenience
            'project': {
                'key': project.get('key'),
                'name': project.get('name'),
                'id': project.get('id'),
                'style': project.get('style', 'classic'),  # 'next-gen' or 'classic'
                'simplified': project.get('simplified', False),
                'project_type': project.get('projectTypeKey')
            },
            'is_team_managed': project.get('style') == 'next-gen',
            'fields': {},
            'issue_types': []
        }

        # Get create meta to see available fields
        params = {'projectKeys': project_key, 'expand': 'projects.issuetypes.fields'}
        if issue_type:
            params['issuetypeNames'] = issue_type

        meta = client.get('/rest/api/3/issue/createmeta', params=params)

        for proj in meta.get('projects', []):
            for itype in proj.get('issuetypes', []):
                type_info = {
                    'name': itype.get('name'),
                    'id': itype.get('id'),
                    'fields': []
                }

                for fid, finfo in itype.get('fields', {}).items():
                    field = {
                        'id': fid,
                        'name': finfo.get('name'),
                        'required': finfo.get('required', False)
                    }
                    type_info['fields'].append(field)

                    # Track unique fields
                    if fid not in result['fields']:
                        result['fields'][fid] = finfo.get('name')

                result['issue_types'].append(type_info)

        # Check Agile field availability
        if check_agile:
            result['agile_fields'] = {}
            all_fields = {v.lower(): k for k, v in result['fields'].items()}

            for agile_type, patterns in AGILE_FIELDS.items():
                found = None
                for pattern in patterns:
                    for field_name, field_id in all_fields.items():
                        if pattern in field_name:
                            found = {'id': field_id, 'name': result['fields'][field_id]}
                            break
                    if found:
                        break
                result['agile_fields'][agile_type] = found

        return result

    finally:
        if should_close:
            client.close()


def main():
    parser = argparse.ArgumentParser(
        description='Check field availability for a JIRA project',
        epilog='Example: python check_project_fields.py PROJ --check-agile'
    )

    parser.add_argument('project',
                        help='Project key')
    parser.add_argument('--type', '-t',
                        help='Specific issue type to check')
    parser.add_argument('--check-agile', '-a', action='store_true',
                        help='Check Agile field availability')
    parser.add_argument('--profile',
                        help='JIRA profile to use')
    parser.add_argument('--output', '-o',
                        choices=['text', 'json'],
                        default='text',
                        help='Output format')

    args = parser.parse_args()

    try:
        result = check_project_fields(
            project_key=args.project,
            issue_type=args.type,
            check_agile=args.check_agile,
            profile=args.profile
        )

        if args.output == 'json':
            print(format_json(result))
        else:
            # Project info
            proj = result['project']
            print_info(f"Project: {proj['key']} ({proj['name']})")
            print(f"Type: {proj['project_type']}")
            print(f"Style: {'Team-managed (next-gen)' if result['is_team_managed'] else 'Company-managed (classic)'}")
            print()

            # Issue types
            print(f"Issue Types: {len(result['issue_types'])}")
            for itype in result['issue_types']:
                print(f"  - {itype['name']} ({len(itype['fields'])} fields)")
            print()

            # Agile fields
            if args.check_agile:
                print("Agile Field Availability:")
                for field_type, field_info in result.get('agile_fields', {}).items():
                    if field_info:
                        print_success(f"  {field_type}: {field_info['name']} ({field_info['id']})")
                    else:
                        print_warning(f"  {field_type}: NOT AVAILABLE")

                # Provide guidance
                print()
                if result['is_team_managed']:
                    print("Note: This is a team-managed project.")
                    print("  - Field configuration is done in project settings UI")
                    print("  - Some Agile fields may need to be enabled via project settings")
                else:
                    print("Note: This is a company-managed project.")
                    print("  - Use configure_agile_fields.py to add missing fields")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
