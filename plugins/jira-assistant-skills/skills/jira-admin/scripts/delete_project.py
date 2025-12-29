#!/usr/bin/env python3
"""
Delete a JIRA project.

Deletes a project and optionally all its data. By default, projects go to trash
and can be restored within 60 days.

Requires JIRA administrator permissions.

Examples:
    # Delete with confirmation prompt
    python delete_project.py PROJ

    # Skip confirmation
    python delete_project.py PROJ --yes

    # Dry run to preview
    python delete_project.py PROJ --dry-run

    # Permanent deletion (no trash)
    python delete_project.py PROJ --no-undo --yes
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any

# Add shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import JiraError, ValidationError, print_error
from validators import validate_project_key


def delete_project(
    project_key: str,
    enable_undo: bool = True,
    force: bool = False,
    dry_run: bool = False,
    client=None
) -> Optional[Dict[str, Any]]:
    """
    Delete a JIRA project.

    Args:
        project_key: Project key to delete
        enable_undo: If True, project goes to trash (default True)
        force: Skip confirmation prompt
        dry_run: Preview deletion without executing
        client: JiraClient instance (optional)

    Returns:
        Project data if dry_run, None otherwise

    Raises:
        ValidationError: If project key is invalid
        JiraError: If API call fails
    """
    # Validate project key
    project_key = validate_project_key(project_key)

    # Create client if not provided
    should_close = False
    if client is None:
        client = get_jira_client()
        should_close = True

    try:
        # Get project info for display/dry-run
        project = client.get_project(project_key)

        if dry_run:
            return project

        # Delete the project
        client.delete_project(project_key, enable_undo=enable_undo)

        return None

    finally:
        if should_close:
            client.close()


def delete_project_async(
    project_key: str,
    client=None
) -> str:
    """
    Delete a large project asynchronously.

    Args:
        project_key: Project key to delete
        client: JiraClient instance (optional)

    Returns:
        Task ID for polling status

    Raises:
        ValidationError: If project key is invalid
        JiraError: If API call fails
    """
    # Validate project key
    project_key = validate_project_key(project_key)

    # Create client if not provided
    should_close = False
    if client is None:
        client = get_jira_client()
        should_close = True

    try:
        return client.delete_project_async(project_key)
    finally:
        if should_close:
            client.close()


def poll_task_status(task_id: str, client=None) -> Dict[str, Any]:
    """
    Poll async task status.

    Args:
        task_id: Task ID to poll
        client: JiraClient instance (optional)

    Returns:
        Task status data

    Raises:
        JiraError: If API call fails
    """
    # Create client if not provided
    should_close = False
    if client is None:
        client = get_jira_client()
        should_close = True

    try:
        return client.get_task_status(task_id)
    finally:
        if should_close:
            client.close()


def format_dry_run(project: Dict[str, Any]) -> str:
    """Format dry run output."""
    lines = [
        "DRY RUN - Would delete the following project:",
        "",
        f"  Key:         {project.get('key')}",
        f"  Name:        {project.get('name')}",
        f"  Type:        {project.get('projectTypeKey', 'N/A')}",
        f"  ID:          {project.get('id')}",
    ]

    # Lead
    lead = project.get('lead')
    if lead:
        lines.append(f"  Lead:        {lead.get('displayName', 'N/A')}")

    # Category
    category = project.get('projectCategory')
    if category:
        lines.append(f"  Category:    {category.get('name', 'N/A')}")

    lines.append("")
    lines.append("No changes made. Remove --dry-run to delete.")

    return "\n".join(lines)


def confirm_deletion(project_key: str, project_name: str, enable_undo: bool) -> bool:
    """
    Prompt user to confirm deletion.

    Args:
        project_key: Project key
        project_name: Project name
        enable_undo: Whether undo is enabled

    Returns:
        True if confirmed, False otherwise
    """
    print(f"\nYou are about to delete project: {project_key} - {project_name}")

    if enable_undo:
        print("The project will be moved to trash and can be restored within 60 days.")
    else:
        print("WARNING: This will PERMANENTLY delete the project!")

    print("\nThis will delete all issues, boards, sprints, and related data.")

    response = input("\nAre you sure you want to continue? (yes/no): ")
    return response.lower().strip() in ('yes', 'y')


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Delete a JIRA project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Delete with confirmation prompt
  %(prog)s PROJ

  # Skip confirmation
  %(prog)s PROJ --yes

  # Dry run to preview
  %(prog)s PROJ --dry-run

  # Permanent deletion (no trash)
  %(prog)s PROJ --no-undo --yes

Warning:
  Deleting a project removes all issues, boards, sprints, and other data.
  By default, projects go to trash and can be restored within 60 days.
        """
    )

    # Required arguments
    parser.add_argument(
        "project_key",
        help="Project key to delete (e.g., PROJ)"
    )

    # Options
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompt"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview deletion without executing"
    )
    parser.add_argument(
        "--no-undo",
        action="store_true",
        help="Permanently delete (skip trash)"
    )
    parser.add_argument(
        "--async",
        dest="async_delete",
        action="store_true",
        help="Use async deletion for large projects"
    )

    # Output options
    parser.add_argument(
        "--output", "-o",
        choices=['text', 'json'],
        default='text',
        help="Output format (default: text)"
    )
    parser.add_argument(
        "--profile",
        help="Configuration profile to use"
    )

    args = parser.parse_args()

    try:
        client = get_jira_client(profile=args.profile)

        # Handle dry run
        if args.dry_run:
            project = delete_project(
                project_key=args.project_key,
                dry_run=True,
                client=client
            )
            if args.output == 'json':
                print(json.dumps({'dry_run': True, 'project': project}, indent=2))
            else:
                print(format_dry_run(project))
            sys.exit(0)

        # Get project info for confirmation
        project = client.get_project(args.project_key)

        # Confirm unless --yes
        if not args.yes:
            if not confirm_deletion(
                args.project_key,
                project.get('name', ''),
                not args.no_undo
            ):
                print("Deletion cancelled.")
                sys.exit(0)

        # Handle async deletion
        if args.async_delete:
            task_id = delete_project_async(
                project_key=args.project_key,
                client=client
            )
            if args.output == 'json':
                print(json.dumps({'task_id': task_id, 'status': 'started'}, indent=2))
            else:
                print(f"Async deletion started. Task ID: {task_id}")
                print("Use the task ID to check deletion status.")
            sys.exit(0)

        # Standard deletion
        delete_project(
            project_key=args.project_key,
            enable_undo=not args.no_undo,
            force=True,
            client=client
        )

        if args.output == 'json':
            print(json.dumps({
                'deleted': True,
                'project_key': args.project_key,
                'in_trash': not args.no_undo
            }, indent=2))
        else:
            if args.no_undo:
                print(f"Project {args.project_key} permanently deleted.")
            else:
                print(f"Project {args.project_key} moved to trash.")
                print("It can be restored within 60 days.")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except ValidationError as e:
        print_error(e)
        sys.exit(1)
    finally:
        if 'client' in locals():
            client.close()


if __name__ == "__main__":
    main()
