#!/usr/bin/env python3
"""
Manage filter sharing permissions.

Share filters with projects, groups, roles, or specific users.
"""

import argparse
import json
import sys
from typing import Any

# Add shared library to path
from jira_assistant_skills_lib import JiraError, get_jira_client, print_error


def share_with_project(client, filter_id: str, project_key: str) -> dict[str, Any]:
    """
    Share filter with all project members.

    Args:
        client: JIRA client
        filter_id: Filter ID
        project_key: Project key

    Returns:
        New permission object
    """
    permission = {
        "type": "project",
        "projectId": project_key,  # JIRA accepts key or ID
    }
    return client.add_filter_permission(filter_id, permission)


def share_with_project_role(
    client, filter_id: str, project_key: str, role_name: str
) -> dict[str, Any]:
    """
    Share filter with a specific project role.

    Args:
        client: JIRA client
        filter_id: Filter ID
        project_key: Project key
        role_name: Role name (e.g., 'Developers')

    Returns:
        New permission object
    """
    # First, get the role ID from the project roles
    roles = client.get(f"/rest/api/3/project/{project_key}/role")
    role_id = None
    for name, url in roles.items():
        if name.lower() == role_name.lower():
            # Extract role ID from URL
            role_id = url.split("/")[-1]
            break

    if not role_id:
        raise JiraError(f"Role '{role_name}' not found in project {project_key}")

    permission = {
        "type": "projectRole",
        "projectId": project_key,
        "projectRoleId": role_id,
    }
    return client.add_filter_permission(filter_id, permission)


def share_with_group(client, filter_id: str, group_name: str) -> dict[str, Any]:
    """
    Share filter with a group.

    Args:
        client: JIRA client
        filter_id: Filter ID
        group_name: Group name

    Returns:
        New permission object
    """
    permission = {"type": "group", "groupname": group_name}
    return client.add_filter_permission(filter_id, permission)


def share_globally(client, filter_id: str) -> dict[str, Any]:
    """
    Share filter with all authenticated users.

    Args:
        client: JIRA client
        filter_id: Filter ID

    Returns:
        New permission object
    """
    permission = {"type": "global"}
    return client.add_filter_permission(filter_id, permission)


def share_with_user(client, filter_id: str, account_id: str) -> dict[str, Any]:
    """
    Share filter with a specific user.

    Args:
        client: JIRA client
        filter_id: Filter ID
        account_id: User's account ID

    Returns:
        New permission object
    """
    permission = {"type": "user", "accountId": account_id}
    return client.add_filter_permission(filter_id, permission)


def unshare(client, filter_id: str, permission_id: str) -> None:
    """
    Remove a share permission.

    Args:
        client: JIRA client
        filter_id: Filter ID
        permission_id: Permission ID to remove
    """
    client.delete_filter_permission(filter_id, permission_id)


def list_permissions(client, filter_id: str) -> list[dict[str, Any]]:
    """
    List current share permissions.

    Args:
        client: JIRA client
        filter_id: Filter ID

    Returns:
        List of permission objects
    """
    return client.get_filter_permissions(filter_id)


def format_permission(perm: dict[str, Any]) -> str:
    """Format a permission for display."""
    perm_type = perm.get("type", "unknown")

    if perm_type == "project":
        project = perm.get("project", {})
        return f"Project: {project.get('key', project.get('name', 'Unknown'))}"
    elif perm_type == "projectRole":
        project = perm.get("project", {})
        role = perm.get("role", {})
        return f"Role: {role.get('name', 'Unknown')} in {project.get('key', 'Unknown')}"
    elif perm_type == "group":
        group = perm.get("group", {})
        return f"Group: {group.get('name', 'Unknown')}"
    elif perm_type == "user":
        user = perm.get("user", {})
        return f"User: {user.get('displayName', user.get('accountId', 'Unknown'))}"
    elif perm_type == "global":
        return "All authenticated users"
    else:
        return f"Unknown type: {perm_type}"


def handle_list_permissions(client, args) -> None:
    """
    Handle listing filter permissions.

    Args:
        client: JIRA client
        args: Parsed command-line arguments
    """
    permissions = list_permissions(client, args.filter_id)

    if args.output == "json":
        print(json.dumps(permissions, indent=2))
    else:
        if not permissions:
            print(f"Filter {args.filter_id} has no share permissions (private).")
        else:
            print(f"Share permissions for filter {args.filter_id}:")
            print()
            print(f"{'ID':<10} {'Type':<15} {'Shared With':<40}")
            print("-" * 65)
            for perm in permissions:
                perm_id = perm.get("id", "N/A")
                perm_type = perm.get("type", "unknown")
                shared_with = format_permission(perm)
                print(f"{perm_id:<10} {perm_type:<15} {shared_with:<40}")


def handle_unshare(client, args) -> None:
    """
    Handle removing a share permission.

    Args:
        client: JIRA client
        args: Parsed command-line arguments
    """
    unshare(client, args.filter_id, args.unshare)

    if args.output == "json":
        print(
            json.dumps(
                {
                    "action": "removed",
                    "filter_id": args.filter_id,
                    "permission_id": args.unshare,
                },
                indent=2,
            )
        )
    else:
        print(f"Permission {args.unshare} removed from filter {args.filter_id}.")


def handle_share_project(client, args) -> None:
    """
    Handle sharing filter with a project or project role.

    Args:
        client: JIRA client
        args: Parsed command-line arguments
    """
    if args.role:
        result = share_with_project_role(
            client, args.filter_id, args.project, args.role
        )
        action_desc = f"project {args.project} role {args.role}"
    else:
        result = share_with_project(client, args.filter_id, args.project)
        action_desc = f"project {args.project}"

    if args.output == "json":
        print(json.dumps({"action": "shared", "permission": result}, indent=2))
    else:
        print(f"Filter {args.filter_id} shared with {action_desc}.")


def handle_share_group(client, args) -> None:
    """
    Handle sharing filter with a group.

    Args:
        client: JIRA client
        args: Parsed command-line arguments
    """
    result = share_with_group(client, args.filter_id, args.group)

    if args.output == "json":
        print(json.dumps({"action": "shared", "permission": result}, indent=2))
    else:
        print(f"Filter {args.filter_id} shared with group {args.group}.")


def handle_share_global(client, args) -> None:
    """
    Handle sharing filter globally with all authenticated users.

    Args:
        client: JIRA client
        args: Parsed command-line arguments
    """
    result = share_globally(client, args.filter_id)

    if args.output == "json":
        print(json.dumps({"action": "shared", "permission": result}, indent=2))
    else:
        print(f"Filter {args.filter_id} shared with all authenticated users.")


def handle_share_user(client, args) -> None:
    """
    Handle sharing filter with a specific user.

    Args:
        client: JIRA client
        args: Parsed command-line arguments
    """
    result = share_with_user(client, args.filter_id, args.user)

    if args.output == "json":
        print(json.dumps({"action": "shared", "permission": result}, indent=2))
    else:
        print(f"Filter {args.filter_id} shared with user {args.user}.")


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Manage filter sharing permissions.",
        epilog="""
Examples:
  %(prog)s 10042 --project PROJ           # Share with project
  %(prog)s 10042 --project PROJ --role Developers  # Share with role
  %(prog)s 10042 --group developers       # Share with group
  %(prog)s 10042 --global                 # Share globally
  %(prog)s 10042 --user accountId123      # Share with user
  %(prog)s 10042 --list                   # View permissions
  %(prog)s 10042 --unshare 456            # Remove permission
        """,
    )

    parser.add_argument("filter_id", help="Filter ID")

    # Share options (mutually exclusive)
    share_group = parser.add_mutually_exclusive_group()
    share_group.add_argument("--project", "-p", help="Share with project (project key)")
    share_group.add_argument("--group", "-g", help="Share with group")
    share_group.add_argument(
        "--global",
        dest="share_global",
        action="store_true",
        help="Share with all authenticated users",
    )
    share_group.add_argument(
        "--user", "-u", help="Share with specific user (account ID)"
    )
    share_group.add_argument(
        "--list", "-l", action="store_true", help="List current permissions"
    )
    share_group.add_argument("--unshare", help="Remove permission (permission ID)")

    # Additional options
    parser.add_argument("--role", "-r", help="Project role (used with --project)")
    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument("--profile", help="JIRA profile to use")

    args = parser.parse_args(argv)

    try:
        client = get_jira_client(args.profile)

        if args.list:
            handle_list_permissions(client, args)
        elif args.unshare:
            handle_unshare(client, args)
        elif args.project:
            handle_share_project(client, args)
        elif args.group:
            handle_share_group(client, args)
        elif args.share_global:
            handle_share_global(client, args)
        elif args.user:
            handle_share_user(client, args)
        else:
            parser.print_help()

    except JiraError as e:
        print_error(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
