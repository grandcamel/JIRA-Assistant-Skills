#!/usr/bin/env python3
"""
List JIRA permission schemes.

Lists all permission schemes in the JIRA instance with optional filtering
and grant expansion.

Examples:
    # List all schemes
    python list_permission_schemes.py

    # List with grants shown
    python list_permission_schemes.py --show-grants

    # Filter by name
    python list_permission_schemes.py --filter "Development"

    # JSON output
    python list_permission_schemes.py --output json
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


def list_permission_schemes(
    client, name_filter: str | None = None, show_grants: bool = False
) -> list[dict[str, Any]]:
    """
    List all permission schemes.

    Args:
        client: JIRA client instance
        name_filter: Optional name filter (case-insensitive partial match)
        show_grants: If True, expand permissions in the response

    Returns:
        List of permission scheme objects
    """
    expand = "permissions" if show_grants else None
    response = client.get_permission_schemes(expand=expand)
    schemes = response.get("permissionSchemes", [])

    # Apply filter if specified
    if name_filter:
        filter_lower = name_filter.lower()
        schemes = [s for s in schemes if filter_lower in s.get("name", "").lower()]

    return schemes


def format_permission_schemes(
    schemes: list[dict[str, Any]],
    output_format: str = "table",
    show_grants: bool = False,
) -> str:
    """
    Format permission schemes for output.

    Args:
        schemes: List of permission scheme objects
        output_format: Output format ('table', 'json', 'csv')
        show_grants: If True, include grant information

    Returns:
        Formatted string
    """
    if not schemes:
        return "No permission schemes found."

    if output_format == "json":
        return format_json(schemes)

    # Prepare data for table/CSV
    data = []
    for scheme in schemes:
        row = {
            "ID": scheme.get("id", ""),
            "Name": scheme.get("name", ""),
            "Description": scheme.get("description", "")[:50] + "..."
            if scheme.get("description", "") and len(scheme.get("description", "")) > 50
            else scheme.get("description", ""),
        }

        if show_grants:
            permissions = scheme.get("permissions", [])
            row["Grants"] = len(permissions)

        data.append(row)

    if output_format == "csv":
        columns = ["ID", "Name", "Description"]
        if show_grants:
            columns.append("Grants")
        return get_csv_string(data, columns=columns)

    # Table format
    columns = ["ID", "Name", "Description"]
    if show_grants:
        columns.append("Grants")

    return format_table(data, columns=columns)


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="List JIRA permission schemes",
        epilog="""
Examples:
  %(prog)s
  %(prog)s --show-grants
  %(prog)s --filter "Development"
  %(prog)s --output json
  %(prog)s --output csv > schemes.csv
""",
    )
    parser.add_argument(
        "--filter",
        "-f",
        dest="name_filter",
        help="Filter schemes by name (case-insensitive partial match)",
    )
    parser.add_argument(
        "--show-grants",
        "-g",
        action="store_true",
        help="Include permission grant counts",
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

        schemes = list_permission_schemes(
            client, name_filter=args.name_filter, show_grants=args.show_grants
        )

        output = format_permission_schemes(
            schemes, output_format=args.output, show_grants=args.show_grants
        )
        print(output)

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(130)


if __name__ == "__main__":
    main()
