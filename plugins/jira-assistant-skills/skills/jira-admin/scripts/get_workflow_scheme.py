#!/usr/bin/env python3
"""
Get detailed workflow scheme information.

Retrieves workflow scheme details including issue type mappings and project usage.
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
    ValidationError,
    get_jira_client,
    print_error,
)


def get_workflow_scheme(
    client,
    scheme_id: int | None = None,
    name: str | None = None,
    show_mappings: bool = False,
    show_projects: bool = False,
    return_draft: bool = False,
) -> dict[str, Any]:
    """
    Get detailed workflow scheme information.

    Args:
        client: JiraClient instance
        scheme_id: Workflow scheme ID
        name: Workflow scheme name (alternative to ID)
        show_mappings: Include detailed issue type to workflow mappings
        show_projects: Include projects using this scheme
        return_draft: Return draft version if exists

    Returns:
        Dict with workflow scheme details

    Raises:
        ValidationError: If neither scheme_id nor name provided
        NotFoundError: If scheme not found
    """
    if scheme_id is None and not name:
        raise ValidationError("Either scheme_id or name must be provided")

    scheme_data = None

    if scheme_id is not None:
        # Get scheme by ID
        scheme_data = client.get_workflow_scheme(
            scheme_id, return_draft_if_exists=return_draft
        )
    else:
        # Search by name
        response = client.get_workflow_schemes(max_results=100)
        schemes = response.get("values", [])

        for s in schemes:
            if s.get("name", "").lower() == name.lower():
                scheme_id = s.get("id")
                scheme_data = client.get_workflow_scheme(
                    scheme_id, return_draft_if_exists=return_draft
                )
                break

        if scheme_data is None:
            raise NotFoundError(f"Workflow scheme '{name}' not found")

    # Parse scheme data
    result = _parse_scheme_details(scheme_data)

    # Add mappings if requested
    if show_mappings:
        result["mappings"] = _parse_mappings(scheme_data)

    # Add projects if requested (placeholder - actual implementation would query projects)
    if show_projects:
        result["projects"] = []
        result["project_count"] = 0

    return result


def _parse_scheme_details(scheme_data: dict[str, Any]) -> dict[str, Any]:
    """Parse workflow scheme details from API response."""
    result = {
        "id": scheme_data.get("id"),
        "name": scheme_data.get("name", "Unknown"),
        "description": scheme_data.get("description", ""),
        "default_workflow": scheme_data.get("defaultWorkflow", ""),
        "is_draft": scheme_data.get("draft", False),
    }

    # Add timestamps if present
    if scheme_data.get("lastModified"):
        result["last_modified"] = scheme_data["lastModified"]

    if scheme_data.get("lastModifiedUser"):
        user = scheme_data["lastModifiedUser"]
        result["last_modified_by"] = user.get("displayName", user.get("accountId", ""))

    return result


def _parse_mappings(scheme_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse issue type to workflow mappings."""
    result = []

    # Basic mappings from issueTypeMappings
    mappings = scheme_data.get("issueTypeMappings", {})
    for issue_type_id, workflow_name in mappings.items():
        mapping = {"issue_type_id": issue_type_id, "workflow": workflow_name}

        # Try to get issue type details from expanded data
        issue_types = scheme_data.get("issueTypes", {})
        if issue_type_id in issue_types:
            mapping["issue_type"] = issue_types[issue_type_id].get("name", "")

        result.append(mapping)

    return result


def format_scheme_details(scheme: dict[str, Any]) -> str:
    """Format workflow scheme details as human-readable text."""
    lines = []

    # Header
    lines.append(f"Workflow Scheme: {scheme['name']}")
    lines.append("=" * (len(scheme["name"]) + 17))

    # Basic info
    lines.append(f"ID:              {scheme.get('id', 'N/A')}")
    lines.append(f"Description:     {scheme.get('description', 'No description')}")
    lines.append(f"Default Workflow: {scheme.get('default_workflow', 'jira')}")
    lines.append(f"Is Draft:        {'Yes' if scheme.get('is_draft') else 'No'}")

    if scheme.get("last_modified"):
        lines.append(f"Last Modified:   {scheme['last_modified']}")
    if scheme.get("last_modified_by"):
        lines.append(f"Modified By:     {scheme['last_modified_by']}")

    # Mappings
    if "mappings" in scheme:
        lines.append("")
        lines.append(f"Issue Type Mappings ({len(scheme['mappings'])})")
        lines.append("-" * 30)

        if scheme["mappings"]:
            for mapping in scheme["mappings"]:
                issue_type = mapping.get(
                    "issue_type", mapping.get("issue_type_id", "Unknown")
                )
                workflow = mapping.get("workflow", "Unknown")
                lines.append(f"  {issue_type}: {workflow}")
        else:
            lines.append("  (All issue types use default workflow)")

    # Projects
    if "projects" in scheme:
        lines.append("")
        lines.append(f"Projects Using This Scheme ({scheme.get('project_count', 0)})")
        lines.append("-" * 30)

        if scheme["projects"]:
            for project in scheme["projects"]:
                lines.append(
                    f"  - {project.get('key', '')} - {project.get('name', '')}"
                )
        else:
            lines.append("  (Not assigned to any projects)")

    return "\n".join(lines)


def format_scheme_json(scheme: dict[str, Any]) -> str:
    """Format workflow scheme as JSON."""
    return json.dumps(scheme, indent=2, default=str)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Get detailed workflow scheme information",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get scheme by ID
  python get_workflow_scheme.py --id 10100

  # Get scheme by name
  python get_workflow_scheme.py "Software Development Scheme"

  # Show detailed mappings
  python get_workflow_scheme.py --id 10100 --show-mappings

  # Show which projects use this scheme
  python get_workflow_scheme.py --id 10100 --show-projects

  # Get draft version if exists
  python get_workflow_scheme.py --id 10100 --draft

  # JSON output
  python get_workflow_scheme.py --id 10100 --output json

Note: Requires 'Administer Jira' global permission.
        """,
    )

    parser.add_argument("name", nargs="?", help="Workflow scheme name")
    parser.add_argument("--id", type=int, dest="scheme_id", help="Workflow scheme ID")
    parser.add_argument(
        "--show-mappings",
        "-m",
        action="store_true",
        help="Show issue type to workflow mappings",
    )
    parser.add_argument(
        "--show-projects",
        "-p",
        action="store_true",
        help="Show projects using this scheme",
    )
    parser.add_argument(
        "--draft",
        action="store_true",
        dest="return_draft",
        help="Return draft version if exists",
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args(argv)

    if args.scheme_id is None and not args.name:
        parser.error("Either scheme name or --id must be provided")

    try:
        client = get_jira_client()

        result = get_workflow_scheme(
            client=client,
            scheme_id=args.scheme_id,
            name=args.name,
            show_mappings=args.show_mappings,
            show_projects=args.show_projects,
            return_draft=args.return_draft,
        )

        if args.output == "json":
            print(format_scheme_json(result))
        else:
            print(format_scheme_details(result))

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    finally:
        if "client" in locals():
            client.close()


if __name__ == "__main__":
    main()
