#!/usr/bin/env python3
"""
Get screen configuration for a project.

Shows the complete 3-tier screen hierarchy for a project:
1. Issue Type Screen Scheme (project level)
2. Screen Schemes (per issue type)
3. Screens (per operation: create/edit/view)
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import print_error, JiraError
from formatters import format_json


def get_project_screens(project_key: str,
                        client=None,
                        issue_type: Optional[str] = None,
                        operation: Optional[str] = None,
                        show_issue_types: bool = False,
                        show_full_hierarchy: bool = False,
                        show_available_fields: bool = False) -> Dict[str, Any]:
    """
    Get screen configuration for a project.

    Args:
        project_key: Project key (e.g., 'PROJ')
        client: JiraClient instance
        issue_type: Filter by issue type name
        operation: Filter by operation (create, edit, view)
        show_issue_types: Include issue type mappings
        show_full_hierarchy: Include complete screen details
        show_available_fields: Include fields that can be added

    Returns:
        Project screen configuration
    """
    if client is None:
        from config_manager import get_jira_client
        client = get_jira_client()

    # Get project info
    project = client.get_project(project_key)

    result = {
        'project': {
            'id': project.get('id'),
            'key': project.get('key'),
            'name': project.get('name')
        }
    }

    # Get issue type screen scheme for the project
    project_id = project.get('id')
    itss_result = client.get_project_issue_type_screen_schemes(
        project_ids=[project_id]
    )

    itss = None
    for mapping in itss_result.get('values', []):
        if project_id in mapping.get('projectIds', []):
            itss = mapping.get('issueTypeScreenScheme')
            break

    if not itss:
        result['issue_type_screen_scheme'] = None
        return result

    result['issue_type_screen_scheme'] = {
        'id': itss.get('id'),
        'name': itss.get('name'),
        'description': itss.get('description')
    }

    # Get issue type to screen scheme mappings
    if show_issue_types or show_full_hierarchy or issue_type:
        mappings_result = client.get_issue_type_screen_scheme_mappings(
            scheme_ids=[itss.get('id')]
        )

        mappings = []
        for m in mappings_result.get('values', []):
            mapping_entry = {
                'issue_type_id': m.get('issueTypeId'),
                'screen_scheme_id': m.get('screenSchemeId')
            }

            # Get screen scheme details if showing full hierarchy
            if show_full_hierarchy:
                try:
                    ss = client.get_screen_scheme(int(m.get('screenSchemeId')))
                    mapping_entry['screen_scheme'] = {
                        'id': ss.get('id'),
                        'name': ss.get('name'),
                        'screens': ss.get('screens', {})
                    }

                    # Get screen details for each operation
                    if operation:
                        screen_id = ss.get('screens', {}).get(operation)
                        if screen_id:
                            screen = client.get_screen(int(screen_id))
                            mapping_entry['screen'] = {
                                'id': screen.get('id'),
                                'name': screen.get('name'),
                                'operation': operation
                            }

                            if show_available_fields:
                                available = client.get_screen_available_fields(int(screen_id))
                                mapping_entry['available_fields'] = available
                except Exception:
                    pass

            mappings.append(mapping_entry)

        # Filter by issue type if specified
        if issue_type:
            # Try to match by name (would need issue type API call)
            # For now, just include all mappings
            pass

        result['mappings'] = mappings

    return result


def format_output(result: Dict[str, Any],
                  output_format: str = 'text') -> str:
    """
    Format project screen configuration for output.

    Args:
        result: Project screen configuration
        output_format: Output format ('text', 'json')

    Returns:
        Formatted output string
    """
    if output_format == 'json':
        return format_json(result)

    lines = []
    project = result.get('project', {})
    lines.append(f"Project: {project.get('name')} ({project.get('key')})")
    lines.append(f"Project ID: {project.get('id')}")

    itss = result.get('issue_type_screen_scheme')
    if itss:
        lines.append(f"\nIssue Type Screen Scheme:")
        lines.append(f"  Name: {itss.get('name')}")
        lines.append(f"  ID: {itss.get('id')}")
        if itss.get('description'):
            lines.append(f"  Description: {itss.get('description')}")

    mappings = result.get('mappings', [])
    if mappings:
        lines.append(f"\nIssue Type Mappings ({len(mappings)}):")
        for m in mappings:
            issue_type_id = m.get('issue_type_id', 'unknown')
            issue_type_label = 'Default' if issue_type_id == 'default' else f"Issue Type {issue_type_id}"

            ss = m.get('screen_scheme')
            if ss:
                lines.append(f"\n  {issue_type_label}:")
                lines.append(f"    Screen Scheme: {ss.get('name')} (ID: {ss.get('id')})")
                screens = ss.get('screens', {})
                for op in ['default', 'create', 'edit', 'view']:
                    screen_id = screens.get(op)
                    if screen_id:
                        lines.append(f"      {op.capitalize()}: Screen {screen_id}")
            else:
                lines.append(f"  {issue_type_label} -> Screen Scheme {m.get('screen_scheme_id')}")

            screen = m.get('screen')
            if screen:
                lines.append(f"    Current Screen: {screen.get('name')} (ID: {screen.get('id')})")

            available = m.get('available_fields')
            if available:
                lines.append(f"    Available Fields ({len(available)}):")
                for f in available[:5]:
                    lines.append(f"      - {f.get('name')} ({f.get('id')})")
                if len(available) > 5:
                    lines.append(f"      ... and {len(available) - 5} more")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Get screen configuration for a JIRA project',
        epilog='''
Examples:
    # Get project screen configuration
    python get_project_screens.py PROJ

    # Show issue type mappings
    python get_project_screens.py PROJ --issue-types

    # Show full hierarchy with screen details
    python get_project_screens.py PROJ --full

    # Filter by operation (create screens only)
    python get_project_screens.py PROJ --full --operation create

    # Show available fields for screens
    python get_project_screens.py PROJ --full --operation create --available-fields

    # JSON output
    python get_project_screens.py PROJ --output json
'''
    )

    parser.add_argument('project_key',
                        help='Project key (e.g., PROJ)')
    parser.add_argument('--issue-type', '-t',
                        help='Filter by issue type name')
    parser.add_argument('--operation', '-O',
                        choices=['create', 'edit', 'view'],
                        help='Filter by operation type')
    parser.add_argument('--issue-types', '-i', dest='show_issue_types', action='store_true',
                        help='Show issue type mappings')
    parser.add_argument('--full', '-F', dest='show_full_hierarchy', action='store_true',
                        help='Show complete screen hierarchy')
    parser.add_argument('--available-fields', '-a', dest='show_available_fields', action='store_true',
                        help='Show fields available to add to screens')
    parser.add_argument('--output', '-o', choices=['text', 'json'], default='text',
                        help='Output format (default: text)')
    parser.add_argument('--profile', '-p', help='JIRA profile to use')

    args = parser.parse_args()

    try:
        client = get_jira_client(args.profile)

        result = get_project_screens(
            project_key=args.project_key,
            client=client,
            issue_type=args.issue_type,
            operation=args.operation,
            show_issue_types=args.show_issue_types,
            show_full_hierarchy=args.show_full_hierarchy,
            show_available_fields=args.show_available_fields
        )

        output = format_output(result, args.output)
        print(output)

    except JiraError as e:
        print_error(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
