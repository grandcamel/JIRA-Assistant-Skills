#!/usr/bin/env python3
"""
Search workflows with various filters.

Search and filter workflows by name, status, scope, and other criteria.
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


def search_workflows(
    client,
    name: Optional[str] = None,
    status: Optional[str] = None,
    scope: Optional[str] = None,
    is_active: Optional[bool] = None,
    order_by: Optional[str] = None,
    expand: Optional[str] = None,
    max_results: int = 50,
    start_at: int = 0
) -> Dict[str, Any]:
    """
    Search workflows with various filters.

    Args:
        client: JiraClient instance
        name: Filter by workflow name (partial match)
        status: Filter by workflows containing this status name
        scope: Filter by scope ('global' or 'project')
        is_active: Filter by active status
        order_by: Sort field ('name', 'created', 'updated')
        expand: Fields to expand ('transitions', 'transitions.rules', 'statuses')
        max_results: Maximum results per page
        start_at: Starting index for pagination

    Returns:
        Dict with 'workflows' list and metadata
    """
    # Build expand parameter
    expand_param = expand
    if status and not expand_param:
        expand_param = 'statuses'
    elif status and expand_param and 'statuses' not in expand_param:
        expand_param = f"{expand_param},statuses"

    # Call search API
    response = client.search_workflows(
        workflow_name=name,
        is_active=is_active,
        order_by=order_by,
        expand=expand_param,
        start_at=start_at,
        max_results=max_results
    )

    workflows_data = response.get('values', [])

    # Parse workflows
    workflows = []
    for wf_data in workflows_data:
        workflow = _parse_workflow(wf_data)

        # Client-side filter by scope
        if scope:
            wf_scope = workflow.get('scope_type', 'GLOBAL')
            if scope.lower() == 'global' and wf_scope != 'GLOBAL':
                continue
            if scope.lower() == 'project' and wf_scope != 'PROJECT':
                continue

        # Client-side filter by status
        if status:
            status_names = [s.get('name', '') for s in workflow.get('statuses', [])]
            if status not in status_names:
                continue

        workflows.append(workflow)

    return {
        'workflows': workflows,
        'total': response.get('total', len(workflows)),
        'has_more': not response.get('isLast', True)
    }


def _parse_workflow(wf_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse workflow data from API response."""
    # Handle different response formats
    if 'id' in wf_data and isinstance(wf_data['id'], dict):
        name = wf_data['id'].get('name', 'Unknown')
        entity_id = wf_data['id'].get('entityId', '')
    else:
        name = wf_data.get('name', 'Unknown')
        entity_id = wf_data.get('entityId', '')

    workflow = {
        'name': name,
        'entity_id': entity_id,
        'description': wf_data.get('description', ''),
        'is_default': wf_data.get('isDefault', False)
    }

    # Handle scope
    scope = wf_data.get('scope', {})
    workflow['scope_type'] = scope.get('type', 'GLOBAL')
    if scope.get('project'):
        workflow['scope_project'] = scope['project'].get('key', '')

    # Handle statuses if present
    statuses = wf_data.get('statuses', [])
    if statuses:
        workflow['statuses'] = statuses
        workflow['status_count'] = len(statuses)

    # Handle transitions if present
    transitions = wf_data.get('transitions', [])
    if transitions:
        workflow['transitions'] = transitions
        workflow['transition_count'] = len(transitions)

    return workflow


def format_search_results(workflows: List[Dict[str, Any]]) -> str:
    """Format search results as a human-readable table."""
    if not workflows:
        return "No workflows found matching the search criteria."

    # Prepare data for format_table
    table_data = []
    columns = ['name', 'scope', 'default', 'description']
    headers = ['Name', 'Scope', 'Default', 'Description']

    has_statuses = any('status_count' in wf for wf in workflows)
    has_transitions = any('transition_count' in wf for wf in workflows)

    if has_statuses:
        columns.append('status_count')
        headers.append('Statuses')

    if has_transitions:
        columns.append('transition_count')
        headers.append('Transitions')

    for wf in workflows:
        scope = 'Global' if wf.get('scope_type') == 'GLOBAL' else 'Project'
        default = 'Yes' if wf.get('is_default') else 'No'
        description = wf.get('description', '')[:40]
        if len(wf.get('description', '')) > 40:
            description += '...'

        row = {
            'name': wf['name'],
            'scope': scope,
            'default': default,
            'description': description
        }

        if has_statuses:
            row['status_count'] = str(wf.get('status_count', '-'))

        if has_transitions:
            row['transition_count'] = str(wf.get('transition_count', '-'))

        table_data.append(row)

    output = format_table(table_data, columns=columns, headers=headers)
    output += f"\n\nFound: {len(workflows)} workflows"
    return output


def format_search_json(workflows: List[Dict[str, Any]]) -> str:
    """Format search results as JSON."""
    return json.dumps(workflows, indent=2, default=str)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description='Search workflows with various filters',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search by name pattern
  python search_workflows.py --name "Development"

  # Find workflows containing a specific status
  python search_workflows.py --status "In Progress"

  # Filter by scope
  python search_workflows.py --scope global
  python search_workflows.py --scope project

  # Filter by active status
  python search_workflows.py --active
  python search_workflows.py --inactive

  # Expand transition details
  python search_workflows.py --expand transitions

  # Order results
  python search_workflows.py --order-by name
  python search_workflows.py --order-by created

  # Combined search
  python search_workflows.py --name "Software" --scope global --active

  # JSON output
  python search_workflows.py --name "Bug" --output json

Note: Requires 'Administer Jira' global permission.
        """
    )

    parser.add_argument(
        '--name', '-n',
        help='Filter workflows by name (partial match)'
    )
    parser.add_argument(
        '--status', '-s',
        help='Filter workflows containing this status'
    )
    parser.add_argument(
        '--scope',
        choices=['global', 'project'],
        help='Filter by workflow scope'
    )
    parser.add_argument(
        '--active',
        action='store_true',
        dest='is_active',
        help='Only show active workflows'
    )
    parser.add_argument(
        '--inactive',
        action='store_true',
        dest='is_inactive',
        help='Only show inactive workflows'
    )
    parser.add_argument(
        '--order-by',
        choices=['name', 'created', 'updated'],
        help='Sort results by field'
    )
    parser.add_argument(
        '--expand', '-e',
        help='Fields to expand (transitions, transitions.rules, statuses)'
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
        help='Maximum results (default: 50)'
    )
    parser.add_argument(
        '--profile', '-p',
        help='Configuration profile to use'
    )

    args = parser.parse_args(argv)

    # Determine active filter
    is_active = None
    if args.is_active:
        is_active = True
    elif args.is_inactive:
        is_active = False

    try:
        client = get_jira_client(profile=args.profile)

        result = search_workflows(
            client=client,
            name=args.name,
            status=args.status,
            scope=args.scope,
            is_active=is_active,
            order_by=args.order_by,
            expand=args.expand,
            max_results=args.max_results
        )

        if args.output == 'json':
            print(format_search_json(result['workflows']))
        else:
            print(format_search_results(result['workflows']))

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    finally:
        if 'client' in locals():
            client.close()


if __name__ == '__main__':
    main()
