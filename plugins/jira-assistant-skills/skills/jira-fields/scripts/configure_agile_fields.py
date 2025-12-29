#!/usr/bin/env python3
"""
Configure Agile fields for a company-managed JIRA project.

This script adds Story Points, Epic Link, and Sprint fields to project screens.
Requires JIRA Administrator permissions.

Usage:
    python configure_agile_fields.py PROJ
    python configure_agile_fields.py PROJ --dry-run
    python configure_agile_fields.py PROJ --story-points customfield_10016
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add shared lib to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError, ValidationError
from jira_assistant_skills_lib import format_json, print_info, print_success, print_warning


def find_agile_fields(client) -> Dict[str, str]:
    """Find Agile field IDs in the instance."""
    fields = client.get('/rest/api/3/field')

    agile_fields = {
        'story_points': None,
        'epic_link': None,
        'sprint': None,
        'epic_name': None
    }

    for field in fields:
        name = field.get('name', '').lower()
        fid = field.get('id', '')

        if 'story point' in name and agile_fields['story_points'] is None:
            agile_fields['story_points'] = fid
        elif 'epic link' in name and agile_fields['epic_link'] is None:
            agile_fields['epic_link'] = fid
        elif name == 'sprint' and agile_fields['sprint'] is None:
            agile_fields['sprint'] = fid
        elif 'epic name' in name and agile_fields['epic_name'] is None:
            agile_fields['epic_name'] = fid

    return agile_fields


def find_project_screens(client, project_key: str) -> List[Dict[str, Any]]:
    """Find screens used by a project."""
    # Get project ID
    project = client.get(f'/rest/api/3/project/{project_key}')
    project_id = project.get('id')

    # Get issue type screen scheme for project
    schemes = client.get('/rest/api/3/issuetypescreenscheme/project',
                         params={'projectId': project_id})

    screens = []

    # If no scheme found, project uses default
    if not schemes.get('values'):
        # Get default screen
        all_screens = client.get('/rest/api/3/screens')
        for screen in all_screens.get('values', []):
            if 'Default' in screen.get('name', ''):
                screens.append({
                    'id': screen.get('id'),
                    'name': screen.get('name')
                })
        return screens

    # Get screens from scheme
    for scheme_mapping in schemes.get('values', []):
        scheme = scheme_mapping.get('issueTypeScreenScheme', {})
        scheme_id = scheme.get('id')

        # Get screen scheme items
        items = client.get(f'/rest/api/3/issuetypescreenscheme/{scheme_id}/mapping')

        for item in items.get('values', []):
            screen_scheme_id = item.get('screenSchemeId')
            if screen_scheme_id:
                # Get screen scheme
                screen_scheme = client.get(f'/rest/api/3/screenscheme/{screen_scheme_id}')

                # Get screens from screen scheme
                for operation, screen_id in screen_scheme.get('screens', {}).items():
                    if screen_id:
                        try:
                            screen = client.get(f'/rest/api/3/screens/{screen_id}')
                            screens.append({
                                'id': screen.get('id'),
                                'name': screen.get('name'),
                                'operation': operation
                            })
                        except JiraError:
                            pass

    return screens


def add_field_to_screen(client, screen_id: int, field_id: str, dry_run: bool = False) -> bool:
    """Add a field to a screen."""
    if dry_run:
        return True

    # Get screen tabs
    tabs = client.get(f'/rest/api/3/screens/{screen_id}/tabs')
    if not tabs:
        return False

    tab_id = tabs[0].get('id')

    # Check if field already on screen
    fields = client.get(f'/rest/api/3/screens/{screen_id}/tabs/{tab_id}/fields')
    for f in fields:
        if f.get('id') == field_id:
            return True  # Already present

    # Add field
    try:
        client.post(f'/rest/api/3/screens/{screen_id}/tabs/{tab_id}/fields',
                    data={'fieldId': field_id})
        return True
    except JiraError:
        return False


def configure_agile_fields(project_key: str,
                           story_points_id: str = None,
                           epic_link_id: str = None,
                           sprint_id: str = None,
                           dry_run: bool = False,
                           profile: str = None,
                           client=None) -> Dict[str, Any]:
    """
    Configure Agile fields for a project.

    Args:
        project_key: Project key
        story_points_id: Custom Story Points field ID (optional, auto-detect)
        epic_link_id: Custom Epic Link field ID (optional, auto-detect)
        sprint_id: Custom Sprint field ID (optional, auto-detect)
        dry_run: If True, show what would be done without making changes
        profile: JIRA profile to use
        client: JiraClient instance (for testing)

    Returns:
        Configuration result

    Raises:
        ValidationError: If project is team-managed
        JiraError: If API call fails
    """
    if not client:
        client = get_jira_client(profile)
        should_close = True
    else:
        should_close = False

    try:
        # Check project type
        project = client.get(f'/rest/api/3/project/{project_key}')

        if project.get('style') == 'next-gen':
            raise ValidationError(
                f"Project {project_key} is team-managed (next-gen). "
                "Field configuration must be done in the project settings UI."
            )

        result = {
            'project': project_key,
            'dry_run': dry_run,
            'fields_found': {},
            'screens_found': [],
            'fields_added': []
        }

        # Find Agile fields
        agile_fields = find_agile_fields(client)

        # Use provided IDs or auto-detected
        field_mapping = {
            'story_points': story_points_id or agile_fields.get('story_points'),
            'epic_link': epic_link_id or agile_fields.get('epic_link'),
            'sprint': sprint_id or agile_fields.get('sprint')
        }

        result['fields_found'] = {k: v for k, v in field_mapping.items() if v}

        if not any(field_mapping.values()):
            raise ValidationError(
                "No Agile fields found in JIRA instance. "
                "Create Story Points, Epic Link, and Sprint fields first."
            )

        # Find project screens
        screens = find_project_screens(client, project_key)
        result['screens_found'] = [s['name'] for s in screens]

        if not screens:
            # Use default screen
            screens = [{'id': 1, 'name': 'Default Screen'}]

        # Add fields to screens
        for screen in screens:
            screen_id = screen['id']
            screen_name = screen['name']

            for field_type, field_id in field_mapping.items():
                if field_id:
                    success = add_field_to_screen(client, screen_id, field_id, dry_run)
                    if success:
                        result['fields_added'].append({
                            'field': field_type,
                            'field_id': field_id,
                            'screen': screen_name,
                            'screen_id': screen_id
                        })

        return result

    finally:
        if should_close:
            client.close()


def main():
    parser = argparse.ArgumentParser(
        description='Configure Agile fields for a company-managed JIRA project',
        epilog='Example: python configure_agile_fields.py PROJ'
    )

    parser.add_argument('project',
                        help='Project key')
    parser.add_argument('--story-points',
                        help='Custom Story Points field ID')
    parser.add_argument('--epic-link',
                        help='Custom Epic Link field ID')
    parser.add_argument('--sprint',
                        help='Custom Sprint field ID')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='Show what would be done without making changes')
    parser.add_argument('--profile',
                        help='JIRA profile to use')
    parser.add_argument('--output', '-o',
                        choices=['text', 'json'],
                        default='text',
                        help='Output format')

    args = parser.parse_args()

    try:
        result = configure_agile_fields(
            project_key=args.project,
            story_points_id=args.story_points,
            epic_link_id=args.epic_link,
            sprint_id=args.sprint,
            dry_run=args.dry_run,
            profile=args.profile
        )

        if args.output == 'json':
            print(format_json(result))
        else:
            if args.dry_run:
                print_info("DRY RUN - No changes made")
                print()

            print(f"Project: {result['project']}")
            print()

            print("Agile Fields Found:")
            for field_type, field_id in result['fields_found'].items():
                print(f"  {field_type}: {field_id}")
            print()

            print(f"Screens Found: {len(result['screens_found'])}")
            for screen in result['screens_found']:
                print(f"  - {screen}")
            print()

            if result['fields_added']:
                action = "Would add" if args.dry_run else "Added"
                print(f"{action} fields:")
                for item in result['fields_added']:
                    print(f"  {item['field']} ({item['field_id']}) -> {item['screen']}")

                if not args.dry_run:
                    print()
                    print_success("Agile fields configured successfully!")
            else:
                print("No fields to add (already configured or no fields found)")

    except ValidationError as e:
        print_error(e)
        sys.exit(1)
    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
