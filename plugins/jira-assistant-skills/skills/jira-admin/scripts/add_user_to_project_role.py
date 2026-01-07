#!/usr/bin/env python3
"""
Add a user to a project role.

Supports:
- Adding by account ID or email lookup
- Role by name or ID
- Dry-run mode for preview

Examples:
    # Add user by email to Administrators role
    python add_user_to_project_role.py --project DEMO --role Administrators --user user@example.com

    # Add user by account ID
    python add_user_to_project_role.py --project DEMO --role Developers --account-id 5b10ac8d82e05b22cc7d4ef5

    # Dry-run preview
    python add_user_to_project_role.py --project DEMO --role Administrators --user user@example.com --dry-run
"""

import argparse
import sys
from typing import Any

from jira_assistant_skills_lib import (
    JiraError,
    NotFoundError,
    format_json,
    get_jira_client,
    print_error,
    print_success,
    validate_project_key,
)


def get_project_roles_for_project(client, project_key: str) -> dict[str, str]:
    """Get all roles available for a project with their URLs."""
    project_key = validate_project_key(project_key)
    return client.get(
        f"/rest/api/3/project/{project_key}/role",
        operation=f"get roles for project {project_key}",
    )


def extract_role_id_from_url(url: str) -> int | None:
    """Extract role ID from role URL."""
    try:
        parts = url.rstrip("/").split("/")
        return int(parts[-1])
    except (IndexError, ValueError):
        return None


def resolve_role_id(client, project_key: str, role_identifier: str) -> tuple[int, str]:
    """
    Resolve role name or ID to role ID.

    Args:
        client: JiraClient instance
        project_key: Project key
        role_identifier: Role name or ID

    Returns:
        Tuple of (role_id, role_name)

    Raises:
        NotFoundError: If role not found
    """
    # Try as ID first
    try:
        role_id = int(role_identifier)
        # Verify it exists by getting the role
        role_data = client.get(
            f"/rest/api/3/project/{project_key}/role/{role_id}",
            operation=f"get role {role_id}",
        )
        return role_id, role_data.get("name", str(role_id))
    except ValueError:
        pass  # Not an ID, try as name

    # Try as name
    roles_dict = get_project_roles_for_project(client, project_key)

    for name, url in roles_dict.items():
        if name.lower() == role_identifier.lower():
            role_id = extract_role_id_from_url(url)
            if role_id:
                return role_id, name

    raise NotFoundError("Role", f"'{role_identifier}' in project {project_key}")


def resolve_user_account_id(client, user_identifier: str) -> tuple[str, str]:
    """
    Resolve user email or account ID to account ID.

    Args:
        client: JiraClient instance
        user_identifier: Email or account ID

    Returns:
        Tuple of (account_id, display_info)

    Raises:
        NotFoundError: If user not found
    """
    # If it looks like an email, search for user
    if "@" in user_identifier:
        users = client.search_users(query=user_identifier, max_results=10)

        # Find exact email match
        for user in users:
            if user.get("emailAddress", "").lower() == user_identifier.lower():
                return user["accountId"], user.get("displayName", user_identifier)

        # No exact match found
        raise NotFoundError("User", f"with email {user_identifier}")

    # Assume it's an account ID
    return user_identifier, user_identifier


def add_user_to_project_role(
    client,
    project_key: str,
    role_id: int,
    account_id: str,
) -> dict[str, Any]:
    """
    Add a user to a project role.

    Args:
        client: JiraClient instance
        project_key: Project key
        role_id: Role ID
        account_id: User's account ID

    Returns:
        Updated role data
    """
    project_key = validate_project_key(project_key)

    data = {"user": [account_id]}

    return client.post(
        f"/rest/api/3/project/{project_key}/role/{role_id}",
        data=data,
        operation=f"add user to role {role_id} in project {project_key}",
    )


def format_dry_run_preview(
    project_key: str,
    role_name: str,
    role_id: int,
    user_info: str,
    account_id: str,
) -> str:
    """Format dry-run preview message."""
    lines = [
        "DRY RUN - Preview of adding user to project role:",
        "=" * 55,
        f"Project:      {project_key}",
        f"Role:         {role_name} (ID: {role_id})",
        f"User:         {user_info}",
        f"Account ID:   {account_id}",
        "",
        "This is a dry run. No changes will be made.",
        "Remove --dry-run to add the user to the role.",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Add a user to a project role",
        epilog="""
Examples:
  %(prog)s --project DEMO --role Administrators --user user@example.com
  %(prog)s --project DEMO --role Developers --account-id 5b10ac8d82e05b22cc7d4ef5
  %(prog)s --project DEMO --role Administrators --user user@example.com --dry-run
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--project", "-p", required=True, help="Project key")
    parser.add_argument("--role", "-r", required=True, help="Role name or ID")

    # User identification (mutually exclusive)
    user_group = parser.add_mutually_exclusive_group(required=True)
    user_group.add_argument("--user", "-u", help="User email address")
    user_group.add_argument("--account-id", "-a", help="User account ID")

    parser.add_argument(
        "--dry-run", "-n", action="store_true", help="Preview without making changes"
    )
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
        client = get_jira_client(profile=args.profile)

        # Resolve role
        role_id, role_name = resolve_role_id(client, args.project, args.role)

        # Resolve user
        if args.account_id:
            account_id = args.account_id
            user_info = account_id
        else:
            account_id, user_info = resolve_user_account_id(client, args.user)

        # Dry run mode
        if args.dry_run:
            print(
                format_dry_run_preview(
                    project_key=args.project,
                    role_name=role_name,
                    role_id=role_id,
                    user_info=user_info,
                    account_id=account_id,
                )
            )
            client.close()
            sys.exit(0)

        # Add user to role
        result = add_user_to_project_role(
            client,
            project_key=args.project,
            role_id=role_id,
            account_id=account_id,
        )

        # Output
        if args.output == "json":
            print(format_json(result))
        else:
            print_success(
                f"Added '{user_info}' to role '{role_name}' in project {args.project}"
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
