#!/usr/bin/env python3
"""
Get epic details and progress from JIRA.

Usage:
    python get_epic.py PROJ-100
    python get_epic.py PROJ-100 --with-children
    python get_epic.py PROJ-100 --output json
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Optional, Dict, List

# Add shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

# Imports from shared library
from config_manager import get_jira_client, get_agile_fields
from error_handler import print_error, JiraError, ValidationError
from validators import validate_issue_key
from formatters import print_success


def get_epic(epic_key: str,
             with_children: bool = False,
             profile: str = None,
             client=None) -> Dict:
    """
    Get epic details and optionally calculate progress.

    Args:
        epic_key: Epic key to retrieve
        with_children: Fetch child issues and calculate progress
        profile: JIRA profile to use
        client: JiraClient instance (for testing)

    Returns:
        Epic data with optional children and progress stats:
        - key, fields: Standard JIRA issue data
        - children: List of child issues (if with_children=True)
        - progress: {total, done, percentage} (if with_children=True)
        - story_points: {total, done, percentage} (if with_children=True)

    Raises:
        JiraError: If epic doesn't exist or API error
        ValidationError: If epic_key is invalid
    """
    # Validate epic key
    epic_key = validate_issue_key(epic_key)

    # Initialize client
    if not client:
        client = get_jira_client(profile)
        should_close = True
    else:
        should_close = False

    try:
        # Get Agile field IDs from configuration
        agile_fields = get_agile_fields(profile)
        story_points_field = agile_fields['story_points']
        epic_name_field = agile_fields['epic_name']

        # Fetch epic details
        epic = client.get_issue(epic_key)

        result = {
            'key': epic['key'],
            'fields': epic['fields'],
            '_agile_fields': agile_fields  # Store for use in formatting
        }

        # Fetch children if requested
        if with_children:
            # Search for issues with this epic link
            # Note: Epic Link field may vary per instance
            jql = f'\"Epic Link\" = {epic_key} OR parent = {epic_key}'
            search_results = client.search_issues(
                jql,
                fields=['key', 'summary', 'status', 'issuetype', story_points_field],
                max_results=1000
            )

            children = search_results.get('issues', [])
            result['children'] = children

            # Calculate progress
            total_issues = len(children)
            done_issues = sum(
                1 for issue in children
                if issue['fields']['status']['name'].lower() in ['done', 'closed', 'resolved']
            )

            result['progress'] = {
                'total': total_issues,
                'done': done_issues,
                'percentage': int((done_issues / total_issues * 100) if total_issues > 0 else 0)
            }

            # Calculate story points
            total_points = 0
            done_points = 0

            for issue in children:
                points = issue['fields'].get(story_points_field)
                if points is not None:
                    total_points += points
                    if issue['fields']['status']['name'].lower() in ['done', 'closed', 'resolved']:
                        done_points += points

            if total_points > 0:
                result['story_points'] = {
                    'total': total_points,
                    'done': done_points,
                    'percentage': int((done_points / total_points * 100))
                }

        return result

    finally:
        if should_close:
            client.close()


def format_epic_output(epic_data: Dict, format: str = 'text') -> str:
    """
    Format epic data for output.

    Args:
        epic_data: Epic data from get_epic()
        format: Output format ('text' or 'json')

    Returns:
        Formatted string
    """
    if format == 'json':
        # Remove internal fields before JSON output
        output = {k: v for k, v in epic_data.items() if not k.startswith('_')}
        return json.dumps(output, indent=2)

    # Get field IDs from result or use defaults
    agile_fields = epic_data.get('_agile_fields', {})
    epic_name_field = agile_fields.get('epic_name', 'customfield_10011')

    # Text format
    lines = []
    lines.append(f"Epic: {epic_data['key']}")
    lines.append(f"Summary: {epic_data['fields']['summary']}")

    # Epic Name if available
    epic_name = epic_data['fields'].get(epic_name_field)
    if epic_name:
        lines.append(f"Epic Name: {epic_name}")

    # Status
    status = epic_data['fields']['status']['name']
    lines.append(f"Status: {status}")

    # Progress if available
    if 'progress' in epic_data:
        prog = epic_data['progress']
        lines.append(f"Progress: {prog['done']}/{prog['total']} issues ({prog['percentage']}%)")

    # Story points if available
    if 'story_points' in epic_data:
        sp = epic_data['story_points']
        lines.append(f"Story Points: {sp['done']}/{sp['total']} ({sp['percentage']}%)")

    # Children if available
    if 'children' in epic_data and epic_data['children']:
        lines.append("")
        lines.append("Children:")
        for child in epic_data['children']:
            status = child['fields']['status']['name']
            summary = child['fields']['summary']
            lines.append(f"  {child['key']} [{status}] - {summary}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Get epic details and progress from JIRA',
        epilog='Example: python get_epic.py PROJ-100 --with-children'
    )

    parser.add_argument('epic_key',
                       help='Epic key (e.g., PROJ-100)')
    parser.add_argument('--with-children', '-c',
                       action='store_true',
                       help='Fetch child issues and calculate progress')
    parser.add_argument('--output', '-o',
                       choices=['text', 'json'],
                       default='text',
                       help='Output format (default: text)')
    parser.add_argument('--profile',
                       help='JIRA profile to use (default: from config)')

    args = parser.parse_args()

    try:
        result = get_epic(
            epic_key=args.epic_key,
            with_children=args.with_children,
            profile=args.profile
        )

        output = format_epic_output(result, format=args.output)
        print(output)

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except ValidationError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
