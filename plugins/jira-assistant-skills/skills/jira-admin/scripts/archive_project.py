#!/usr/bin/env python3
"""
Archive a JIRA project.

Archived projects are read-only and cannot have issues created or edited.
They can be restored later using restore_project.py.

Requires JIRA administrator permissions.

Examples:
    # Archive a project (with confirmation)
    python archive_project.py PROJ

    # Archive without confirmation
    python archive_project.py PROJ --yes

    # Dry run - show what would happen
    python archive_project.py PROJ --dry-run
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Dict, Any

# Add shared lib to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import JiraError, ValidationError, print_error
from jira_assistant_skills_lib import validate_project_key


def archive_project(
    project_key: str,
    dry_run: bool = False,
    client=None
) -> Dict[str, Any]:
    """
    Archive a project.

    Args:
        project_key: Project key to archive
        dry_run: If True, don't actually archive, just show what would happen
        client: JiraClient instance (optional)

    Returns:
        Result dict with success status and project info

    Raises:
        ValidationError: If input validation fails
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
        if dry_run:
            # Get project info for dry-run display
            project = client.get_project(project_key)
            return {
                'success': True,
                'dry_run': True,
                'project_key': project_key,
                'project_name': project.get('name', 'Unknown'),
                'message': f"Would archive project {project_key}"
            }

        # Archive the project
        client.archive_project(project_key)

        return {
            'success': True,
            'dry_run': False,
            'project_key': project_key,
            'message': f"Project {project_key} archived successfully"
        }

    finally:
        if should_close:
            client.close()


def format_output(result: Dict[str, Any], project_key: str, output_format: str = "text") -> str:
    """Format archive result for output."""
    if output_format == "json":
        return json.dumps(result, indent=2)

    # Text output
    if result.get('dry_run'):
        lines = [
            "DRY RUN - No changes made",
            "",
            f"Would archive project: {project_key}",
        ]
        if result.get('project_name'):
            lines.append(f"  Name: {result.get('project_name')}")
        lines.extend([
            "",
            "Archived projects:",
            "  - Cannot have issues created or edited",
            "  - Can be browsed in read-only mode",
            "  - Can be restored later",
            "",
            "To actually archive, remove the --dry-run flag."
        ])
    else:
        lines = [
            f"Project {project_key} archived successfully.",
            "",
            "The project is now read-only.",
            "",
            f"To restore: python restore_project.py {project_key}"
        ]

    return "\n".join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Archive a JIRA project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Archive a project (with confirmation)
  %(prog)s PROJ

  # Archive without confirmation
  %(prog)s PROJ --yes

  # Dry run - show what would happen
  %(prog)s PROJ --dry-run
        """
    )

    # Required arguments
    parser.add_argument(
        "project_key",
        help="Project key to archive (e.g., PROJ)"
    )

    # Optional arguments
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompt"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without making changes"
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

        # Confirmation prompt unless --yes or --dry-run
        if not args.yes and not args.dry_run:
            # Get project info for confirmation
            try:
                project = client.get_project(args.project_key)
                project_name = project.get('name', 'Unknown')
            except JiraError:
                project_name = 'Unknown'

            print(f"WARNING: You are about to archive project {args.project_key} ({project_name})")
            print()
            print("Archived projects:")
            print("  - Cannot have issues created or edited")
            print("  - Can be browsed in read-only mode")
            print("  - Can be restored later")
            print()
            response = input("Are you sure you want to archive this project? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("Operation cancelled.")
                sys.exit(0)

        result = archive_project(
            project_key=args.project_key,
            dry_run=args.dry_run,
            client=client
        )

        print(format_output(result, args.project_key, args.output))

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
