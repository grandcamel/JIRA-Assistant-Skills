#!/usr/bin/env python3
"""
List all available JIRA permissions.

Lists all permission keys that can be used when creating permission grants
in permission schemes.

Examples:
    # List all permissions
    python list_permissions.py

    # Filter by type
    python list_permissions.py --type PROJECT
    python list_permissions.py --type GLOBAL

    # Search by name or description
    python list_permissions.py --search "issue"

    # JSON output
    python list_permissions.py --output json
"""

import argparse
import sys
from typing import Any

# Add shared lib to path
from jira_assistant_skills_lib import (
    JiraError,
    format_json,
    format_table,
    get_csv_string,
    get_jira_client,
    print_error,
)


def list_permissions(
    client, permission_type: str | None = None, search: str | None = None
) -> list[dict[str, Any]]:
    """
    List all available permissions.

    Args:
        client: JIRA client instance
        permission_type: Filter by type ('PROJECT' or 'GLOBAL')
        search: Search term for name or description

    Returns:
        List of permission objects sorted by key
    """
    response = client.get_all_permissions()
    permissions_dict = response.get("permissions", {})

    # Convert dict to list
    permissions = list(permissions_dict.values())

    # Filter by type
    if permission_type:
        type_upper = permission_type.upper()
        permissions = [p for p in permissions if p.get("type") == type_upper]

    # Filter by search term
    if search:
        search_lower = search.lower()
        permissions = [
            p
            for p in permissions
            if (
                search_lower in p.get("key", "").lower()
                or search_lower in p.get("name", "").lower()
                or search_lower in p.get("description", "").lower()
            )
        ]

    # Sort by key
    permissions.sort(key=lambda p: p.get("key", ""))

    return permissions


def group_by_type(permissions: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """
    Group permissions by type.

    Args:
        permissions: List of permission objects

    Returns:
        Dict mapping type to list of permissions
    """
    grouped = {}
    for perm in permissions:
        perm_type = perm.get("type", "OTHER")
        if perm_type not in grouped:
            grouped[perm_type] = []
        grouped[perm_type].append(perm)
    return grouped


def format_permissions(
    permissions: list[dict[str, Any]], output_format: str = "table"
) -> str:
    """
    Format permissions for output.

    Args:
        permissions: List of permission objects
        output_format: Output format ('table', 'json', 'csv')

    Returns:
        Formatted string
    """
    if not permissions:
        return "No permissions found."

    if output_format == "json":
        return format_json(permissions)

    # Prepare data for table/CSV
    data = []
    for perm in permissions:
        desc = perm.get("description", "")
        if len(desc) > 50:
            desc = desc[:47] + "..."

        data.append(
            {
                "Key": perm.get("key", ""),
                "Name": perm.get("name", ""),
                "Type": perm.get("type", ""),
                "Description": desc,
            }
        )

    if output_format == "csv":
        return get_csv_string(data, columns=["Key", "Name", "Type", "Description"])

    return format_table(data, columns=["Key", "Name", "Type", "Description"])


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="List all available JIRA permissions",
        epilog="""
Examples:
  %(prog)s
  %(prog)s --type PROJECT
  %(prog)s --type GLOBAL
  %(prog)s --search "issue"
  %(prog)s --output json
""",
    )
    parser.add_argument(
        "--type", "-t", choices=["PROJECT", "GLOBAL"], help="Filter by permission type"
    )
    parser.add_argument(
        "--search", "-s", help="Search by name or description (case-insensitive)"
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["table", "json", "csv"],
        default="table",
        help="Output format (default: table)",
    )

    args = parser.parse_args(argv)

    try:
        client = get_jira_client()

        permissions = list_permissions(
            client, permission_type=args.type, search=args.search
        )

        output = format_permissions(permissions, output_format=args.output)
        print(output)

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(130)


if __name__ == "__main__":
    main()
