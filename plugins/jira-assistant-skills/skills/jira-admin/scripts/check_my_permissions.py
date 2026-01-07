#!/usr/bin/env python3
"""
Check current user's permissions on a project.

Queries the /rest/api/3/mypermissions endpoint to show which permissions
the current user has on a specific project.

Examples:
    # Check all permissions on a project
    python check_my_permissions.py --project DEMO

    # Check specific permission
    python check_my_permissions.py --project DEMO --permission DELETE_ISSUES

    # Check multiple permissions
    python check_my_permissions.py --project DEMO --permission DELETE_ISSUES,BROWSE_PROJECTS

    # JSON output
    python check_my_permissions.py --project DEMO --output json

    # Show only permissions user has
    python check_my_permissions.py --project DEMO --only-have

    # Show only permissions user lacks
    python check_my_permissions.py --project DEMO --only-missing
"""

import argparse
import sys
from typing import Any

from jira_assistant_skills_lib import (
    JiraError,
    format_json,
    format_table,
    get_csv_string,
    get_jira_client,
    print_error,
    print_info,
    print_success,
    print_warning,
    validate_project_key,
)

# Common permissions to check if none specified
DEFAULT_PERMISSIONS = [
    "BROWSE_PROJECTS",
    "CREATE_ISSUES",
    "EDIT_ISSUES",
    "DELETE_ISSUES",
    "ASSIGN_ISSUES",
    "ASSIGNABLE_USER",
    "RESOLVE_ISSUES",
    "CLOSE_ISSUES",
    "TRANSITION_ISSUES",
    "SCHEDULE_ISSUES",
    "MOVE_ISSUES",
    "SET_ISSUE_SECURITY",
    "MANAGE_WATCHERS",
    "ADD_COMMENTS",
    "EDIT_ALL_COMMENTS",
    "DELETE_ALL_COMMENTS",
    "CREATE_ATTACHMENTS",
    "DELETE_ALL_ATTACHMENTS",
    "WORK_ON_ISSUES",
    "LINK_ISSUES",
    "VIEW_VOTERS_AND_WATCHERS",
    "ADMINISTER_PROJECTS",
]


def get_my_permissions(
    client,
    project_key: str | None = None,
    permissions: list[str] | None = None,
) -> dict[str, Any]:
    """
    Get current user's permissions.

    Args:
        client: JiraClient instance
        project_key: Project key to check permissions for
        permissions: List of permission keys to check (optional)

    Returns:
        Dict containing permissions with havePermission boolean
    """
    params = {}
    if project_key:
        params["projectKey"] = project_key
    if permissions:
        params["permissions"] = ",".join(permissions)

    return client.get(
        "/rest/api/3/mypermissions",
        params=params,
        operation="get my permissions",
    )


def check_permissions(
    client,
    project_key: str,
    permissions: list[str] | None = None,
    only_have: bool = False,
    only_missing: bool = False,
) -> list[dict[str, Any]]:
    """
    Check user's permissions on a project.

    Args:
        client: JiraClient instance
        project_key: Project key to check
        permissions: Specific permissions to check (or use defaults)
        only_have: If True, only show permissions user has
        only_missing: If True, only show permissions user lacks

    Returns:
        List of permission dicts with havePermission status
    """
    # Validate project key
    project_key = validate_project_key(project_key)

    # Use defaults if no specific permissions requested
    check_perms = permissions or DEFAULT_PERMISSIONS

    # Get permissions
    response = get_my_permissions(
        client, project_key=project_key, permissions=check_perms
    )
    permissions_dict = response.get("permissions", {})

    # Convert to list and add key field
    result = []
    for key, data in permissions_dict.items():
        perm = {
            "key": key,
            "name": data.get("name", key),
            "description": data.get("description", ""),
            "havePermission": data.get("havePermission", False),
        }
        result.append(perm)

    # Filter if requested
    if only_have:
        result = [p for p in result if p["havePermission"]]
    elif only_missing:
        result = [p for p in result if not p["havePermission"]]

    # Sort by key
    result.sort(key=lambda p: p["key"])

    return result


def format_permissions_output(
    permissions: list[dict[str, Any]],
    output_format: str = "table",
    project_key: str | None = None,
) -> str:
    """
    Format permissions for output.

    Args:
        permissions: List of permission dicts
        output_format: Output format ('table', 'json', 'csv')
        project_key: Project key for header

    Returns:
        Formatted string
    """
    if not permissions:
        return "No permissions to display."

    if output_format == "json":
        return format_json(permissions)

    # Prepare data for table/CSV
    data = []
    for perm in permissions:
        have = perm.get("havePermission", False)
        status = "\u2713" if have else "\u2717"  # checkmark or x

        desc = perm.get("description", "")
        if len(desc) > 40:
            desc = desc[:37] + "..."

        data.append(
            {
                "Permission": perm.get("key", ""),
                "Status": status,
                "Name": perm.get("name", ""),
                "Description": desc,
            }
        )

    if output_format == "csv":
        return get_csv_string(
            data, columns=["Permission", "Status", "Name", "Description"]
        )

    # Add header for table output
    header = ""
    if project_key:
        header = f"Permissions for project: {project_key}\n\n"

    return header + format_table(
        data, columns=["Permission", "Status", "Name", "Description"]
    )


def print_summary(permissions: list[dict[str, Any]], project_key: str) -> None:
    """Print a summary of permission status."""
    have = sum(1 for p in permissions if p.get("havePermission"))
    missing = len(permissions) - have

    print()
    if missing == 0:
        print_success(f"You have all {have} checked permissions on {project_key}")
    elif have == 0:
        print_warning(
            f"You have none of the {len(permissions)} checked permissions on {project_key}"
        )
    else:
        print_info(
            f"Summary: {have} permissions granted, {missing} missing on {project_key}"
        )


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check current user's permissions on a project",
        epilog="""
Examples:
  %(prog)s --project DEMO
  %(prog)s --project DEMO --permission DELETE_ISSUES
  %(prog)s --project DEMO --permission DELETE_ISSUES,BROWSE_PROJECTS
  %(prog)s --project DEMO --only-missing
  %(prog)s --project DEMO --output json
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--project", "-p", required=True, help="Project key to check permissions for"
    )
    parser.add_argument(
        "--permission",
        "-P",
        help="Specific permission(s) to check (comma-separated)",
    )
    parser.add_argument(
        "--only-have",
        action="store_true",
        help="Only show permissions user has",
    )
    parser.add_argument(
        "--only-missing",
        action="store_true",
        help="Only show permissions user lacks",
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["table", "json", "csv"],
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument(
        "--no-summary",
        action="store_true",
        help="Skip summary line",
    )
    parser.add_argument("--profile", help="JIRA profile to use")

    args = parser.parse_args(argv)

    # Validate mutually exclusive options
    if args.only_have and args.only_missing:
        parser.error("--only-have and --only-missing are mutually exclusive")

    try:
        client = get_jira_client(profile=args.profile)

        # Parse permissions if provided
        permissions = None
        if args.permission:
            permissions = [p.strip().upper() for p in args.permission.split(",")]

        result = check_permissions(
            client,
            project_key=args.project,
            permissions=permissions,
            only_have=args.only_have,
            only_missing=args.only_missing,
        )

        output = format_permissions_output(
            result, output_format=args.output, project_key=args.project
        )
        print(output)

        # Print summary unless suppressed or JSON output
        if not args.no_summary and args.output == "table":
            print_summary(result, args.project)

        client.close()

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(130)


if __name__ == "__main__":
    main()
