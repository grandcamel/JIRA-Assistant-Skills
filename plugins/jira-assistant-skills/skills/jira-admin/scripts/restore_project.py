#!/usr/bin/env python3
"""
Restore an archived or deleted JIRA project.

Restores projects that have been archived or moved to trash.
Deleted projects can be restored within 60 days.

Requires JIRA administrator permissions.

Examples:
    # Restore an archived project
    python restore_project.py PROJ

    # Restore a deleted project from trash
    python restore_project.py OLD

    # Skip confirmation
    python restore_project.py PROJ --yes
"""

import argparse
import json
import sys
from typing import Any

# Add shared lib to path
from jira_assistant_skills_lib import (
    JiraError,
    ValidationError,
    get_jira_client,
    print_error,
    validate_project_key,
)


def restore_project(project_key: str, client=None) -> dict[str, Any]:
    """
    Restore an archived or deleted project.

    Args:
        project_key: Project key to restore
        client: JiraClient instance (optional)

    Returns:
        Restored project data

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
        result = client.restore_project(project_key)
        return result

    finally:
        if should_close:
            client.close()


def format_output(project: dict[str, Any], output_format: str = "text") -> str:
    """Format restore result for output."""
    if output_format == "json":
        return json.dumps(project, indent=2)

    # Text output
    lines = [
        f"Project {project.get('key', 'Unknown')} restored successfully.",
        "",
        f"  Key:  {project.get('key', 'N/A')}",
        f"  Name: {project.get('name', 'N/A')}",
        f"  Type: {project.get('projectTypeKey', 'N/A')}",
    ]

    if project.get("lead"):
        lead = project.get("lead", {})
        lines.append(f"  Lead: {lead.get('displayName', 'N/A')}")

    lines.extend(
        [
            "",
            "The project is now active and editable.",
            "",
            f"URL: {project.get('self', 'N/A').replace('/rest/api/3/project/', '/browse/')}",
        ]
    )

    return "\n".join(lines)


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Restore an archived or deleted JIRA project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Restore an archived project
  %(prog)s PROJ

  # Restore a deleted project from trash
  %(prog)s OLD

  # Skip confirmation
  %(prog)s PROJ --yes
        """,
    )

    # Required arguments
    parser.add_argument("project_key", help="Project key to restore (e.g., PROJ)")

    # Optional arguments
    parser.add_argument(
        "--yes", "-y", action="store_true", help="Skip confirmation prompt"
    )

    # Output options
    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args(argv)

    try:
        client = get_jira_client()

        # Confirmation prompt unless --yes
        if not args.yes:
            print(f"You are about to restore project {args.project_key}")
            print()
            print("This will make the project active and editable again.")
            print()
            response = input(
                "Are you sure you want to restore this project? (yes/no): "
            )
            if response.lower() not in ["yes", "y"]:
                print("Operation cancelled.")
                sys.exit(0)

        result = restore_project(project_key=args.project_key, client=client)

        print(format_output(result, args.output))

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except ValidationError as e:
        print_error(e)
        sys.exit(1)
    finally:
        if "client" in locals():
            client.close()


if __name__ == "__main__":
    main()
