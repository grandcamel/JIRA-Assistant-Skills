#!/usr/bin/env python3
"""
Create a project component in JIRA.

Usage:
    python create_component.py PROJ --name "Backend API"
    python create_component.py PROJ --name "Frontend" --description "UI components"
    python create_component.py PROJ --name "Database" --lead 5b10a2844c20165700ede21g
    python create_component.py PROJ --name "Security" --assignee-type COMPONENT_LEAD
"""

import argparse
import sys
from typing import Any

from jira_assistant_skills_lib import (
    JiraError,
    get_jira_client,
    print_error,
    print_success,
)


def create_component(
    project: str,
    name: str,
    description: str | None = None,
    lead_account_id: str | None = None,
    assignee_type: str | None = None,
    profile: str | None = None,
) -> dict[str, Any]:
    """
    Create a project component.

    Args:
        project: Project key (e.g., PROJ)
        name: Component name
        description: Optional description
        lead_account_id: Optional component lead account ID
        assignee_type: Optional default assignee type (COMPONENT_LEAD, PROJECT_LEAD, PROJECT_DEFAULT, UNASSIGNED)
        profile: JIRA profile to use

    Returns:
        Created component data
    """
    client = get_jira_client(profile)
    result = client.create_component(
        project=project,
        name=name,
        description=description,
        lead_account_id=lead_account_id,
        assignee_type=assignee_type,
    )
    client.close()

    return result


def create_component_dry_run(
    project: str,
    name: str,
    description: str | None = None,
    lead_account_id: str | None = None,
    assignee_type: str | None = None,
) -> dict[str, Any]:
    """
    Show what component would be created without creating it.

    Args:
        project: Project key
        name: Component name
        description: Optional description
        lead_account_id: Optional lead account ID
        assignee_type: Optional assignee type

    Returns:
        Component data that would be created
    """
    component_data = {"project": project, "name": name}

    if description:
        component_data["description"] = description
    if lead_account_id:
        component_data["leadAccountId"] = lead_account_id
    if assignee_type:
        component_data["assigneeType"] = assignee_type

    return component_data


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create a project component in JIRA",
        epilog="""
Examples:
  %(prog)s PROJ --name "Backend API"
  %(prog)s PROJ --name "Frontend" --description "UI components"
  %(prog)s PROJ --name "Database" --lead 5b10a2844c20165700ede21g
  %(prog)s PROJ --name "Security" --assignee-type COMPONENT_LEAD --dry-run
        """,
    )

    parser.add_argument("project", help="Project key (e.g., PROJ)")
    parser.add_argument("--name", "-n", required=True, help="Component name")
    parser.add_argument("--description", "-d", help="Component description")
    parser.add_argument("--lead", "-l", help="Component lead account ID")
    parser.add_argument(
        "--assignee-type",
        "-a",
        choices=["COMPONENT_LEAD", "PROJECT_LEAD", "PROJECT_DEFAULT", "UNASSIGNED"],
        help="Default assignee type for issues in this component",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without creating",
    )
    parser.add_argument("--profile", "-p", help="JIRA profile to use")

    args = parser.parse_args(argv)

    try:
        if args.dry_run:
            # Dry run mode
            component_data = create_component_dry_run(
                project=args.project,
                name=args.name,
                description=args.description,
                lead_account_id=args.lead,
                assignee_type=args.assignee_type,
            )

            print(f"[DRY RUN] Would create component in project {args.project}:\n")
            print(f"  Name: {component_data['name']}")
            if component_data.get("description"):
                print(f"  Description: {component_data['description']}")
            if component_data.get("leadAccountId"):
                print(f"  Lead Account ID: {component_data['leadAccountId']}")
            if component_data.get("assigneeType"):
                print(f"  Assignee Type: {component_data['assigneeType']}")
            print("\nNo component created (dry-run mode).")

        else:
            # Create component
            component = create_component(
                project=args.project,
                name=args.name,
                description=args.description,
                lead_account_id=args.lead,
                assignee_type=args.assignee_type,
                profile=args.profile,
            )

            component_id = component.get("id", "")
            print_success(
                f"Created component '{args.name}' in project {args.project} (ID: {component_id})"
            )

            # Show component details
            if component.get("description"):
                print(f"\nDescription: {component['description']}")
            if component.get("lead"):
                lead_name = component["lead"].get("displayName", "")
                print(f"Lead: {lead_name}")
            if component.get("assigneeType"):
                print(f"Assignee Type: {component['assigneeType']}")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
