#!/usr/bin/env python3
"""
List project role memberships.

Shows which users and groups are assigned to each role in a project.

Examples:
    # List all roles and their members for a project
    python list_project_roles.py --project DEMO

    # Show specific role members
    python list_project_roles.py --project DEMO --role Administrators

    # JSON output
    python list_project_roles.py --project DEMO --output json
"""

import argparse
import sys
from typing import Any

from jira_assistant_skills_lib import (
    JiraError,
    NotFoundError,
    format_json,
    get_csv_string,
    get_jira_client,
    print_error,
    print_info,
    validate_project_key,
)


def get_project_roles_for_project(client, project_key: str) -> dict[str, str]:
    """
    Get all roles available for a project with their URLs.

    Args:
        client: JiraClient instance
        project_key: Project key

    Returns:
        Dict mapping role name to role URL
    """
    project_key = validate_project_key(project_key)
    return client.get(
        f"/rest/api/3/project/{project_key}/role",
        operation=f"get roles for project {project_key}",
    )


def get_project_role_actors(client, project_key: str, role_id: int) -> dict[str, Any]:
    """
    Get actors (users/groups) in a project role.

    Args:
        client: JiraClient instance
        project_key: Project key
        role_id: Role ID

    Returns:
        Role data with actors list
    """
    project_key = validate_project_key(project_key)
    return client.get(
        f"/rest/api/3/project/{project_key}/role/{role_id}",
        operation=f"get role {role_id} for project {project_key}",
    )


def extract_role_id_from_url(url: str) -> int | None:
    """Extract role ID from role URL."""
    try:
        # URL format: .../project/{key}/role/{id}
        parts = url.rstrip("/").split("/")
        return int(parts[-1])
    except (IndexError, ValueError):
        return None


def list_project_roles(
    client,
    project_key: str,
    role_name: str | None = None,
) -> list[dict[str, Any]]:
    """
    List project roles with their members.

    Args:
        client: JiraClient instance
        project_key: Project key
        role_name: Filter to specific role (optional)

    Returns:
        List of role dicts with actors
    """
    # Get all roles for the project
    roles_dict = get_project_roles_for_project(client, project_key)

    result = []

    for name, url in roles_dict.items():
        # Skip if filtering by role name and doesn't match
        if role_name and name.lower() != role_name.lower():
            continue

        role_id = extract_role_id_from_url(url)
        if role_id is None:
            continue

        # Get role details with actors
        role_data = get_project_role_actors(client, project_key, role_id)

        actors = role_data.get("actors", [])

        # Parse actors into users and groups
        users = []
        groups = []
        for actor in actors:
            actor_type = actor.get("type", "")
            display_name = actor.get("displayName", "Unknown")
            actor_user = actor.get("actorUser", {})
            actor_group = actor.get("actorGroup", {})

            if actor_type == "atlassian-user-role-actor":
                users.append(
                    {
                        "displayName": display_name,
                        "accountId": actor_user.get("accountId", ""),
                        "emailAddress": actor_user.get("emailAddress", ""),
                    }
                )
            elif actor_type == "atlassian-group-role-actor":
                groups.append(
                    {
                        "displayName": display_name,
                        "name": actor_group.get("name", display_name),
                        "groupId": actor_group.get("groupId", ""),
                    }
                )

        result.append(
            {
                "id": role_id,
                "name": name,
                "description": role_data.get("description", ""),
                "users": users,
                "groups": groups,
                "totalActors": len(actors),
            }
        )

    # Check if role was requested but not found
    if role_name and not result:
        raise NotFoundError("Role", f"'{role_name}' in project {project_key}")

    # Sort by role name
    result.sort(key=lambda r: r["name"])

    return result


def format_roles_output(
    roles: list[dict[str, Any]],
    output_format: str = "table",
    project_key: str | None = None,
) -> str:
    """
    Format roles for output.

    Args:
        roles: List of role dicts
        output_format: Output format ('table', 'json', 'csv')
        project_key: Project key for header

    Returns:
        Formatted string
    """
    if not roles:
        return "No roles found."

    if output_format == "json":
        return format_json(roles)

    # Build output lines for table format
    lines = []

    if project_key:
        lines.append(f"Project Roles for: {project_key}")
        lines.append("=" * 60)
        lines.append("")

    for role in roles:
        lines.append(f"Role: {role['name']} (ID: {role['id']})")
        if role.get("description"):
            lines.append(f"  Description: {role['description']}")
        lines.append(f"  Total members: {role['totalActors']}")

        # List users
        users = role.get("users", [])
        if users:
            lines.append("  Users:")
            for user in users:
                email = user.get("emailAddress", "")
                email_str = f" <{email}>" if email else ""
                lines.append(f"    - {user['displayName']}{email_str}")

        # List groups
        groups = role.get("groups", [])
        if groups:
            lines.append("  Groups:")
            for group in groups:
                lines.append(f"    - {group['displayName']}")

        if not users and not groups:
            lines.append("  (No members)")

        lines.append("")

    return "\n".join(lines)


def format_roles_csv(roles: list[dict[str, Any]], project_key: str) -> str:
    """Format roles as CSV with one row per actor."""
    data = []

    for role in roles:
        # Add users
        for user in role.get("users", []):
            data.append(
                {
                    "Project": project_key,
                    "Role": role["name"],
                    "RoleID": role["id"],
                    "ActorType": "User",
                    "DisplayName": user.get("displayName", ""),
                    "Identifier": user.get("emailAddress") or user.get("accountId", ""),
                }
            )

        # Add groups
        for group in role.get("groups", []):
            data.append(
                {
                    "Project": project_key,
                    "Role": role["name"],
                    "RoleID": role["id"],
                    "ActorType": "Group",
                    "DisplayName": group.get("displayName", ""),
                    "Identifier": group.get("name", ""),
                }
            )

        # Add empty row if no actors
        if not role.get("users") and not role.get("groups"):
            data.append(
                {
                    "Project": project_key,
                    "Role": role["name"],
                    "RoleID": role["id"],
                    "ActorType": "",
                    "DisplayName": "(No members)",
                    "Identifier": "",
                }
            )

    return get_csv_string(
        data,
        columns=["Project", "Role", "RoleID", "ActorType", "DisplayName", "Identifier"],
    )


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="List project role memberships",
        epilog="""
Examples:
  %(prog)s --project DEMO
  %(prog)s --project DEMO --role Administrators
  %(prog)s --project DEMO --output json
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--project", "-p", required=True, help="Project key")
    parser.add_argument("--role", "-r", help="Filter to specific role name")
    parser.add_argument(
        "--output",
        "-o",
        choices=["table", "json", "csv"],
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument("--profile", help="JIRA profile to use")

    args = parser.parse_args(argv)

    try:
        client = get_jira_client(profile=args.profile)

        roles = list_project_roles(
            client,
            project_key=args.project,
            role_name=args.role,
        )

        if args.output == "csv":
            output = format_roles_csv(roles, args.project)
        else:
            output = format_roles_output(
                roles,
                output_format=args.output,
                project_key=args.project,
            )
        print(output)

        # Print summary for table output
        if args.output == "table" and roles:
            total_users = sum(len(r.get("users", [])) for r in roles)
            total_groups = sum(len(r.get("groups", [])) for r in roles)
            print_info(
                f"Total: {len(roles)} roles, {total_users} users, {total_groups} groups"
            )

        client.close()

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(130)


if __name__ == "__main__":
    main()
