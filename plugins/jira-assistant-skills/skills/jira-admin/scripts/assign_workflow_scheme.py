#!/usr/bin/env python3
"""
Assign a workflow scheme to a project.

Assigns workflow schemes to projects with optional status mapping.
This is an asynchronous operation that may take time to complete.
Requires 'Administer Jira' global permission.
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import print_error, JiraError, NotFoundError, ValidationError


def get_current_scheme(client, project_key: str) -> Dict[str, Any]:
    """
    Get the current workflow scheme for a project.

    Args:
        client: JiraClient instance
        project_key: Project key

    Returns:
        Dict with current scheme info
    """
    response = client.get_workflow_scheme_for_project(project_key)
    scheme = response.get('workflowScheme', {})
    return {
        'id': scheme.get('id'),
        'name': scheme.get('name', 'Unknown'),
        'description': scheme.get('description', '')
    }


def assign_workflow_scheme(
    client,
    project_key: str,
    scheme_id: Optional[int] = None,
    scheme_name: Optional[str] = None,
    status_mappings: Optional[List[Dict[str, Any]]] = None,
    dry_run: bool = False,
    confirm: bool = False,
    wait: bool = True,
    poll_interval: int = 2,
    max_wait: int = 300
) -> Dict[str, Any]:
    """
    Assign a workflow scheme to a project.

    Args:
        client: JiraClient instance
        project_key: Project key
        scheme_id: Workflow scheme ID
        scheme_name: Workflow scheme name (alternative to ID)
        status_mappings: Optional status migration mappings
        dry_run: If True, show what would change without making changes
        confirm: Must be True to make actual changes
        wait: If True, wait for async operation to complete
        poll_interval: Seconds between status polls
        max_wait: Maximum seconds to wait

    Returns:
        Dict with operation result

    Raises:
        ValidationError: If parameters invalid or confirm not set
        NotFoundError: If scheme or project not found
    """
    # Validate parameters
    if scheme_id is None and not scheme_name:
        raise ValidationError("Either scheme_id or scheme_name must be provided")

    if not dry_run and not confirm:
        raise ValidationError(
            "Workflow scheme assignment requires explicit confirmation. "
            "Use --confirm to proceed or --dry-run to preview changes."
        )

    # Resolve scheme ID from name if needed
    if scheme_name and scheme_id is None:
        response = client.get_workflow_schemes(max_results=100)
        schemes = response.get('values', [])

        for s in schemes:
            if s.get('name', '').lower() == scheme_name.lower():
                scheme_id = s.get('id')
                break

        if scheme_id is None:
            raise NotFoundError(f"Workflow scheme '{scheme_name}' not found")

    # Dry run - just show what would change
    if dry_run:
        try:
            current = get_current_scheme(client, project_key)
        except JiraError:
            current = {'id': None, 'name': 'None/Default'}

        new_scheme = client.get_workflow_scheme(scheme_id)

        return {
            'dry_run': True,
            'project_key': project_key,
            'current_scheme': current,
            'new_scheme': {
                'id': scheme_id,
                'name': new_scheme.get('name', 'Unknown'),
                'description': new_scheme.get('description', '')
            }
        }

    # Perform assignment
    response = client.assign_workflow_scheme_to_project(
        project_key_or_id=project_key,
        workflow_scheme_id=str(scheme_id),
        status_mappings=status_mappings
    )

    task_id = response.get('taskId')

    result = {
        'success': False,
        'task_id': task_id,
        'project_key': project_key,
        'scheme_id': scheme_id
    }

    # Wait for task if requested
    if wait and task_id:
        elapsed = 0
        while elapsed < max_wait:
            task_status = client.get_task_status(task_id)
            status = task_status.get('status', '')

            if status == 'COMPLETE':
                result['success'] = True
                result['message'] = task_status.get('message', 'Completed')
                break
            elif status in ('FAILED', 'CANCELLED'):
                result['success'] = False
                result['message'] = task_status.get('message', 'Failed')
                break

            time.sleep(poll_interval)
            elapsed += poll_interval
        else:
            result['message'] = f'Timed out after {max_wait} seconds. Check task {task_id} manually.'
    else:
        result['success'] = True
        result['message'] = f'Assignment started. Task ID: {task_id}'

    return result


def format_result(result: Dict[str, Any]) -> str:
    """Format assignment result as human-readable text."""
    lines = []

    if result.get('dry_run'):
        lines.append("DRY RUN - No changes will be made")
        lines.append("=" * 40)
        lines.append(f"Project: {result['project_key']}")
        lines.append("")
        lines.append("Current Workflow Scheme:")
        current = result.get('current_scheme', {})
        lines.append(f"  ID:   {current.get('id', 'N/A')}")
        lines.append(f"  Name: {current.get('name', 'Unknown')}")
        lines.append("")
        lines.append("New Workflow Scheme:")
        new = result.get('new_scheme', {})
        lines.append(f"  ID:   {new.get('id', 'N/A')}")
        lines.append(f"  Name: {new.get('name', 'Unknown')}")
        lines.append("")
        lines.append("To apply this change, remove --dry-run and add --confirm")
    else:
        if result.get('success'):
            lines.append("SUCCESS: Workflow scheme assigned")
        else:
            lines.append("FAILED: Workflow scheme assignment failed")

        lines.append(f"Project: {result.get('project_key', 'Unknown')}")
        lines.append(f"Scheme ID: {result.get('scheme_id', 'Unknown')}")
        lines.append(f"Task ID: {result.get('task_id', 'N/A')}")

        if result.get('message'):
            lines.append(f"Message: {result['message']}")

    return "\n".join(lines)


def format_result_json(result: Dict[str, Any]) -> str:
    """Format assignment result as JSON."""
    return json.dumps(result, indent=2, default=str)


def main():
    parser = argparse.ArgumentParser(
        description='Assign a workflow scheme to a project',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show current workflow scheme for a project
  python assign_workflow_scheme.py --project PROJ --show-current

  # Dry run - show what would change
  python assign_workflow_scheme.py --project PROJ --scheme-id 10100 --dry-run

  # Assign workflow scheme (requires confirmation)
  python assign_workflow_scheme.py --project PROJ --scheme-id 10100 --confirm

  # Assign by scheme name
  python assign_workflow_scheme.py --project PROJ --scheme "Software Development Scheme" --confirm

  # With status migration mappings from file
  python assign_workflow_scheme.py --project PROJ --scheme-id 10100 \\
    --mappings mappings.json --confirm

  # Don't wait for completion
  python assign_workflow_scheme.py --project PROJ --scheme-id 10100 \\
    --confirm --no-wait

Note: This is an experimental API endpoint.
      Requires 'Administer Jira' global permission.
        """
    )

    parser.add_argument(
        '--project', '-p',
        required=True,
        dest='project_key',
        help='Project key'
    )
    parser.add_argument(
        '--scheme-id',
        type=int,
        help='Workflow scheme ID'
    )
    parser.add_argument(
        '--scheme', '-s',
        dest='scheme_name',
        help='Workflow scheme name'
    )
    parser.add_argument(
        '--mappings', '-m',
        help='JSON file with status migration mappings'
    )
    parser.add_argument(
        '--show-current',
        action='store_true',
        help='Show current workflow scheme and exit'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would change without making changes'
    )
    parser.add_argument(
        '--confirm',
        action='store_true',
        help='Confirm the assignment (required for actual changes)'
    )
    parser.add_argument(
        '--no-wait',
        action='store_true',
        help="Don't wait for operation to complete"
    )
    parser.add_argument(
        '--output', '-o',
        choices=['text', 'json'],
        default='text',
        help='Output format (default: text)'
    )
    parser.add_argument(
        '--profile',
        help='Configuration profile to use'
    )

    args = parser.parse_args()

    # Load status mappings from file if provided
    status_mappings = None
    if args.mappings:
        try:
            with open(args.mappings, 'r') as f:
                status_mappings = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading mappings file: {e}", file=sys.stderr)
            sys.exit(1)

    try:
        client = get_jira_client(profile=args.profile)

        # Show current and exit if requested
        if args.show_current:
            current = get_current_scheme(client, args.project_key)
            if args.output == 'json':
                print(json.dumps(current, indent=2))
            else:
                print(f"Current Workflow Scheme for {args.project_key}:")
                print(f"  ID:          {current.get('id', 'N/A')}")
                print(f"  Name:        {current.get('name', 'Unknown')}")
                print(f"  Description: {current.get('description', '-')}")
            sys.exit(0)

        result = assign_workflow_scheme(
            client=client,
            project_key=args.project_key,
            scheme_id=args.scheme_id,
            scheme_name=args.scheme_name,
            status_mappings=status_mappings,
            dry_run=args.dry_run,
            confirm=args.confirm,
            wait=not args.no_wait
        )

        if args.output == 'json':
            print(format_result_json(result))
        else:
            print(format_result(result))

        # Exit with error if not successful (and not dry run)
        if not result.get('dry_run') and not result.get('success'):
            sys.exit(1)

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    finally:
        if 'client' in locals():
            client.close()


if __name__ == '__main__':
    main()
