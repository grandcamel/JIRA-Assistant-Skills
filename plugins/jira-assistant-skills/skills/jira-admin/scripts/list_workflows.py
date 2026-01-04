#!/usr/bin/env python3
"""
List all workflows in a JIRA instance.

Provides workflow discovery with filtering, pagination, and multiple output formats.
Requires 'Administer Jira' global permission.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add shared lib to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError
from jira_assistant_skills_lib import format_table


def list_workflows(
    client,
    details: bool = False,
    name_filter: Optional[str] = None,
    scope: Optional[str] = None,
    show_usage: bool = False,
    max_results: int = 50,
    start_at: int = 0,
    fetch_all: bool = False
) -> Dict[str, Any]:
    """
    List all workflows with optional filtering and details.

    Args:
        client: JiraClient instance
        details: If True, include statuses and transitions (uses search endpoint)
        name_filter: Filter by workflow name (case-insensitive)
        scope: Filter by scope ('global' or 'project')
        show_usage: Include workflow scheme usage information
        max_results: Maximum results per page
        start_at: Starting index for pagination
        fetch_all: Fetch all pages of results

    Returns:
        Dict with 'workflows' list, 'total', 'has_more'
    """
    all_workflows = []
    current_start = start_at
    has_more = True

    while has_more:
        if details:
            # Use search endpoint for full details including transitions/statuses
            expand = 'transitions,statuses'
            response = client.search_workflows(
                workflow_name=name_filter,
                expand=expand,
                start_at=current_start,
                max_results=max_results
            )
            workflows_data = response.get('values', [])
            is_paginated = True
        else:
            # Use basic list endpoint - returns a list directly, not paginated
            response = client.get_workflows(
                start_at=current_start,
                max_results=max_results
            )
            # get_workflows returns a list directly, not a paginated response
            if isinstance(response, list):
                workflows_data = response
                is_paginated = False
            else:
                workflows_data = response.get('values', [])
                is_paginated = True

        # Process each workflow
        for wf_data in workflows_data:
            workflow = _parse_workflow(wf_data, details)

            # Apply client-side filters if needed
            if name_filter and name_filter.lower() not in workflow['name'].lower():
                continue

            if scope:
                wf_scope = workflow.get('scope_type', 'GLOBAL')
                if scope.lower() == 'global' and wf_scope != 'GLOBAL':
                    continue
                if scope.lower() == 'project' and wf_scope != 'PROJECT':
                    continue

            all_workflows.append(workflow)

        # Check if more pages exist
        if is_paginated:
            total = response.get('total', len(workflows_data))
            is_last = response.get('isLast', True)
            if fetch_all and not is_last:
                current_start += max_results
            else:
                has_more = False
        else:
            # Non-paginated response (basic list) returns all results at once
            total = len(workflows_data)
            is_last = True
            has_more = False

    # Add usage information if requested
    if show_usage:
        for workflow in all_workflows:
            try:
                entity_id = workflow.get('entity_id')
                if entity_id:
                    schemes = client.get_workflow_schemes_for_workflow(
                        entity_id, max_results=100
                    )
                    workflow['scheme_count'] = schemes.get('total', 0)
                    workflow['schemes'] = [
                        s.get('name', 'Unknown') for s in schemes.get('values', [])
                    ]
            except JiraError:
                workflow['scheme_count'] = 0
                workflow['schemes'] = []

    return {
        'workflows': all_workflows,
        'total': len(all_workflows) if fetch_all else total,
        'has_more': not is_last if not fetch_all else False
    }


def _parse_workflow(wf_data: Dict[str, Any], include_details: bool = False) -> Dict[str, Any]:
    """Parse workflow data from API response."""
    # Handle both basic and detailed response formats
    if 'id' in wf_data and isinstance(wf_data['id'], dict):
        # Basic format: id is object with name and entityId
        workflow = {
            'name': wf_data['id'].get('name', 'Unknown'),
            'entity_id': wf_data['id'].get('entityId', ''),
            'description': wf_data.get('description', ''),
            'is_default': wf_data.get('isDefault', False)
        }
    else:
        # Search format or other
        workflow = {
            'name': wf_data.get('name', wf_data.get('id', {}).get('name', 'Unknown')),
            'entity_id': wf_data.get('entityId', wf_data.get('id', {}).get('entityId', '')),
            'description': wf_data.get('description', ''),
            'is_default': wf_data.get('isDefault', False)
        }

    # Handle scope
    scope = wf_data.get('scope', {})
    workflow['scope_type'] = scope.get('type', 'GLOBAL')
    if scope.get('project'):
        workflow['scope_project'] = scope['project'].get('key', '')

    # Handle version
    version = wf_data.get('version', {})
    workflow['version'] = version.get('versionNumber', 1) if version else 1

    # Handle dates
    workflow['created'] = wf_data.get('created', '')
    workflow['updated'] = wf_data.get('updated', '')

    # Handle statuses and transitions for detailed view
    if include_details:
        statuses = wf_data.get('statuses', [])
        transitions = wf_data.get('transitions', [])
        workflow['status_count'] = len(statuses)
        workflow['transition_count'] = len(transitions)
        workflow['statuses'] = statuses
        workflow['transitions'] = transitions

    return workflow


def format_workflows_table(workflows: List[Dict[str, Any]]) -> str:
    """Format workflows as a human-readable table."""
    if not workflows:
        return "No workflows found."

    # Prepare data for format_table (list of dicts with desired keys)
    table_data = []
    columns = ['name', 'scope', 'default', 'description']
    headers = ['Name', 'Type', 'Default', 'Description']

    has_details = any('status_count' in wf for wf in workflows)
    has_usage = any('scheme_count' in wf for wf in workflows)

    if has_details:
        columns.extend(['status_count', 'transition_count'])
        headers.extend(['Statuses', 'Transitions'])

    if has_usage:
        columns.append('scheme_count')
        headers.append('Schemes')

    for wf in workflows:
        scope = 'Global' if wf.get('scope_type') == 'GLOBAL' else 'Project'
        default = 'Yes' if wf.get('is_default') else 'No'
        description = wf.get('description', '')[:50]
        if len(wf.get('description', '')) > 50:
            description += '...'

        row = {
            'name': wf['name'],
            'scope': scope,
            'default': default,
            'description': description
        }

        if has_details:
            row['status_count'] = str(wf.get('status_count', '-'))
            row['transition_count'] = str(wf.get('transition_count', '-'))

        if has_usage:
            row['scheme_count'] = str(wf.get('scheme_count', '-'))

        table_data.append(row)

    output = format_table(table_data, columns=columns, headers=headers)
    output += f"\n\nTotal: {len(workflows)} workflows"
    return output


def format_workflows_json(workflows: List[Dict[str, Any]]) -> str:
    """Format workflows as JSON."""
    return json.dumps(workflows, indent=2, default=str)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description='List all workflows in a JIRA instance',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all workflows
  python list_workflows.py

  # Include full details (statuses, transitions)
  python list_workflows.py --details

  # Filter by name
  python list_workflows.py --filter "Development"

  # Filter by scope
  python list_workflows.py --scope global
  python list_workflows.py --scope project

  # Show which schemes use each workflow
  python list_workflows.py --show-usage

  # JSON output
  python list_workflows.py --output json

  # With profile
  python list_workflows.py --profile production

Note: Requires 'Administer Jira' global permission.
        """
    )

    parser.add_argument(
        '--details', '-d',
        action='store_true',
        help='Include full details (statuses, transitions)'
    )
    parser.add_argument(
        '--filter', '-f',
        dest='name_filter',
        help='Filter workflows by name (case-insensitive)'
    )
    parser.add_argument(
        '--scope', '-s',
        choices=['global', 'project'],
        help='Filter by workflow scope'
    )
    parser.add_argument(
        '--show-usage', '-u',
        action='store_true',
        help='Show which workflow schemes use each workflow'
    )
    parser.add_argument(
        '--output', '-o',
        choices=['table', 'json'],
        default='table',
        help='Output format (default: table)'
    )
    parser.add_argument(
        '--max-results',
        type=int,
        default=50,
        help='Maximum results per page (default: 50)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        dest='fetch_all',
        help='Fetch all pages of results'
    )
    parser.add_argument(
        '--profile', '-p',
        help='Configuration profile to use'
    )

    args = parser.parse_args(argv)

    try:
        client = get_jira_client(profile=args.profile)

        result = list_workflows(
            client=client,
            details=args.details,
            name_filter=args.name_filter,
            scope=args.scope,
            show_usage=args.show_usage,
            max_results=args.max_results,
            fetch_all=args.fetch_all
        )

        if args.output == 'json':
            print(format_workflows_json(result['workflows']))
        else:
            print(format_workflows_table(result['workflows']))
            if result['has_more']:
                print(f"\n(Showing first {len(result['workflows'])} of {result['total']} workflows. Use --all to fetch all.)")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    finally:
        if 'client' in locals():
            client.close()


if __name__ == '__main__':
    main()
