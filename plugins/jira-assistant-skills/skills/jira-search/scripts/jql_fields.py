#!/usr/bin/env python3
"""
List JQL searchable fields and their valid operators.

Shows all fields available for JQL queries, including system fields
and custom fields, along with their supported operators.

Features caching for improved performance - field definitions are
cached for 1 day by default.
"""

import argparse
import json
import sys
from typing import Any

# Add shared library to path
from jira_assistant_skills_lib import (
    JiraError,
    format_table,
    get_autocomplete_cache,
    get_jira_client,
    print_error,
)


def get_fields(
    client,
    name_filter: str | None = None,
    custom_only: bool = False,
    system_only: bool = False,
    use_cache: bool = True,
    refresh_cache: bool = False,
) -> list[dict[str, Any]]:
    """
    Get JQL searchable fields with caching support.

    Args:
        client: JIRA client
        name_filter: Filter fields by name (case-insensitive substring match)
        custom_only: Only return custom fields
        system_only: Only return system fields
        use_cache: Use cached data if available (default: True)
        refresh_cache: Force refresh from API (default: False)

    Returns:
        List of field objects
    """
    if use_cache:
        cache = get_autocomplete_cache()
        fields = cache.get_fields(client, force_refresh=refresh_cache)
    else:
        data = client.get_jql_autocomplete()
        fields = data.get("visibleFieldNames", [])

    # Apply filters
    if name_filter:
        name_lower = name_filter.lower()
        fields = [
            f
            for f in fields
            if name_lower in f.get("value", "").lower()
            or name_lower in f.get("displayName", "").lower()
        ]

    if custom_only:
        fields = [f for f in fields if f.get("cfid") is not None]
    elif system_only:
        fields = [f for f in fields if f.get("cfid") is None]

    return fields


def format_fields_text(fields: list[dict[str, Any]]) -> str:
    """
    Format fields as human-readable table.

    Args:
        fields: List of field objects

    Returns:
        Formatted table string
    """
    if not fields:
        return "No fields found"

    # Prepare data for table
    data = []
    for field in fields:
        operators = field.get("operators", [])
        # Truncate operators if too long
        ops_str = ", ".join(operators)
        if len(ops_str) > 40:
            ops_str = ops_str[:37] + "..."

        data.append(
            {
                "Field": field.get("value", ""),
                "Display Name": field.get("displayName", ""),
                "Type": "Custom" if field.get("cfid") else "System",
                "Operators": ops_str,
            }
        )

    # Sort by display name
    data.sort(key=lambda x: x["Display Name"].lower())

    # Count stats
    custom_count = sum(1 for f in fields if f.get("cfid"))
    system_count = len(fields) - custom_count

    table = format_table(data, columns=["Field", "Display Name", "Type", "Operators"])
    return f"JQL Fields:\n\n{table}\n\nTotal: {len(fields)} fields ({system_count} system, {custom_count} custom)"


def format_fields_json(fields: list[dict[str, Any]]) -> str:
    """
    Format fields as JSON.

    Args:
        fields: List of field objects

    Returns:
        JSON string
    """
    return json.dumps(fields, indent=2)


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="List JQL searchable fields and their operators.",
        epilog="""
Examples:
  %(prog)s                       # List all fields
  %(prog)s --filter status       # Filter fields containing "status"
  %(prog)s --custom-only         # Show only custom fields
  %(prog)s --system-only         # Show only system fields
  %(prog)s --output json         # Output as JSON
        """,
    )

    parser.add_argument(
        "--filter",
        "-f",
        dest="name_filter",
        help="Filter fields by name (case-insensitive)",
    )
    parser.add_argument(
        "--custom-only", action="store_true", help="Show only custom fields"
    )
    parser.add_argument(
        "--system-only", action="store_true", help="Show only system fields"
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--no-cache", action="store_true", help="Bypass cache and fetch from API"
    )
    parser.add_argument(
        "--refresh", action="store_true", help="Force refresh cache from API"
    )

    args = parser.parse_args(argv)

    # Validate mutually exclusive options
    if args.custom_only and args.system_only:
        print(
            "Error: --custom-only and --system-only are mutually exclusive",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        client = get_jira_client()

        fields = get_fields(
            client,
            name_filter=args.name_filter,
            custom_only=args.custom_only,
            system_only=args.system_only,
            use_cache=not args.no_cache,
            refresh_cache=args.refresh,
        )

        if args.output == "json":
            print(format_fields_json(fields))
        else:
            print(format_fields_text(fields))

    except JiraError as e:
        print_error(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
