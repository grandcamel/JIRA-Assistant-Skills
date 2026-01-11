#!/usr/bin/env python3
"""
Get issue type scheme for a project.

Retrieves the issue type scheme assigned to a specific project.
Requires 'Administer Jira' global permission.
"""

import argparse
import json
import sys
from typing import Any

# Add shared lib to path
from jira_assistant_skills_lib import (
    JiraError,
    NotFoundError,
    get_jira_client,
    print_error,
)


def get_project_issue_type_scheme(project_id: str, client=None) -> dict[str, Any]:
    """
    Get issue type scheme assigned to a project.

    Args:
        project_id: Project ID
        client: JiraClient instance (for testing)

    Returns:
        Scheme assignment with issueTypeScheme and projectIds

    Raises:
        NotFoundError: If no scheme found for project
        JiraError: On API failure
    """
    if client is None:
        client = get_jira_client()

    try:
        result = client.get_issue_type_scheme_for_projects(project_ids=[project_id])

        values = result.get("values", [])
        if not values:
            raise NotFoundError("Issue type scheme for project", project_id)

        return values[0]
    finally:
        if client:
            client.close()


def format_project_scheme(
    assignment: dict[str, Any], output_format: str = "detail"
) -> str:
    """Format project scheme assignment for display."""
    if output_format == "json":
        return json.dumps(assignment, indent=2)

    scheme = assignment.get("issueTypeScheme", {})
    project_ids = assignment.get("projectIds", [])

    lines = []
    lines.append("Project Issue Type Scheme")
    lines.append("=" * 40)
    lines.append(f"Scheme ID:       {scheme.get('id', '')}")
    lines.append(f"Scheme Name:     {scheme.get('name', '')}")
    lines.append(f"Description:     {scheme.get('description', '') or 'None'}")
    lines.append(f"Default Type ID: {scheme.get('defaultIssueTypeId', 'None')}")
    lines.append(f"Is Default:      {'Yes' if scheme.get('isDefault') else 'No'}")
    lines.append(f"Project IDs:     {', '.join(project_ids)}")

    return "\n".join(lines)


def main(argv: list[str] | None = None):
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Get issue type scheme for a project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get scheme for project
  python get_project_issue_type_scheme.py 10000

  # Output as JSON
  python get_project_issue_type_scheme.py 10000 --format json

  # Use specific profile
  python get_project_issue_type_scheme.py 10000
""",
    )

    parser.add_argument("project_id", help="Project ID to query")
    parser.add_argument(
        "--format",
        choices=["detail", "json"],
        default="detail",
        help="Output format (default: detail)",
    )

    args = parser.parse_args(argv)

    try:
        assignment = get_project_issue_type_scheme(project_id=args.project_id)

        output = format_project_scheme(assignment, args.format)
        print(output)

    except JiraError as e:
        print_error(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
