#!/usr/bin/env python3
"""
Get project components in JIRA.

Usage:
    python get_components.py PROJ
    python get_components.py PROJ --output json
    python get_components.py --id 10000
    python get_components.py --id 10000 --counts
"""

import argparse
import json
import sys
from typing import Any

from jira_assistant_skills_lib import (
    JiraError,
    format_table,
    get_jira_client,
    print_error,
)


def get_components(project: str, profile: str | None = None) -> list[dict[str, Any]]:
    """
    Get all components for a project.

    Args:
        project: Project key (e.g., PROJ)
        profile: JIRA profile to use

    Returns:
        List of component data
    """
    client = get_jira_client(profile)
    result = client.get_components(project)
    client.close()

    return result


def get_component_by_id(
    component_id: str, profile: str | None = None
) -> dict[str, Any]:
    """
    Get a specific component by ID.

    Args:
        component_id: Component ID
        profile: JIRA profile to use

    Returns:
        Component data
    """
    client = get_jira_client(profile)
    result = client.get_component(component_id)
    client.close()

    return result


def filter_by_lead(
    components: list[dict[str, Any]], lead_name: str
) -> list[dict[str, Any]]:
    """
    Filter components by lead name.

    Args:
        components: List of components
        lead_name: Lead display name to filter by

    Returns:
        Filtered list of components
    """
    return [c for c in components if c.get("lead", {}).get("displayName") == lead_name]


def get_component_issue_counts(
    component_id: str, profile: str | None = None
) -> dict[str, Any]:
    """
    Get issue counts for a component.

    Args:
        component_id: Component ID
        profile: JIRA profile to use

    Returns:
        Issue counts
    """
    client = get_jira_client(profile)
    result = client.get_component_issue_counts(component_id)
    client.close()

    return result


def display_components_table(components: list[dict[str, Any]]) -> None:
    """
    Display components in table format.

    Args:
        components: List of components
    """
    if not components:
        print("No components found.")
        return

    # Prepare table data
    table_data = []
    for component in components:
        lead = component.get("lead", {})
        table_data.append(
            {
                "id": component.get("id", ""),
                "name": component.get("name", ""),
                "description": (component.get("description", "") or "")[:40],
                "lead": lead.get("displayName", "") if lead else "",
            }
        )

    print(
        format_table(
            table_data,
            columns=["id", "name", "description", "lead"],
            headers=["ID", "Name", "Description", "Lead"],
        )
    )


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Get project components in JIRA",
        epilog="""
Examples:
  %(prog)s PROJ
  %(prog)s PROJ --output json
  %(prog)s --id 10000
  %(prog)s --id 10000 --counts
        """,
    )

    parser.add_argument("project", nargs="?", help="Project key (e.g., PROJ)")
    parser.add_argument("--id", help="Get specific component by ID")
    parser.add_argument(
        "--counts",
        action="store_true",
        help="Show issue counts for the component (requires --id)",
    )
    parser.add_argument(
        "--output",
        "-O",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument("--profile", "-p", help="JIRA profile to use")

    args = parser.parse_args(argv)

    # Validate arguments
    if args.id:
        # Get specific component
        if args.project:
            print_error("Error: Cannot specify both project and --id")
            sys.exit(1)
    else:
        # Get project components
        if not args.project:
            print_error("Error: Must specify either project or --id")
            sys.exit(1)

    if args.counts and not args.id:
        print_error("Error: --counts requires --id")
        sys.exit(1)

    try:
        if args.id:
            # Get specific component
            component = get_component_by_id(args.id, args.profile)

            if args.counts:
                # Get issue counts
                counts = get_component_issue_counts(args.id, args.profile)

                print(f"Component: {component['name']} (ID: {component['id']})")
                print(f"\nIssue Count: {counts['issueCount']}")
            else:
                # Show component details
                if args.output == "json":
                    print(json.dumps(component, indent=2))
                else:
                    print(f"Component: {component['name']} (ID: {component['id']})")
                    if component.get("description"):
                        print(f"Description: {component['description']}")
                    if component.get("lead"):
                        lead_name = component["lead"].get("displayName", "")
                        print(f"Lead: {lead_name}")
                    if component.get("assigneeType"):
                        print(f"Assignee Type: {component['assigneeType']}")
        else:
            # Get project components
            components = get_components(args.project, args.profile)

            # Output
            if args.output == "json":
                print(json.dumps(components, indent=2))
            else:
                print(f"Components for project {args.project}:\n")
                display_components_table(components)
                print(f"\nTotal: {len(components)} component(s)")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
