#!/usr/bin/env python3
"""
Get JQL field value suggestions for autocomplete.

Provides suggestions for field values like status, project, assignee, etc.
to help build accurate JQL queries.

Features caching for improved performance - suggestions are cached for
1 hour by default.
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


def get_suggestions(
    client,
    field_name: str,
    prefix: str = "",
    use_cache: bool = True,
    refresh_cache: bool = False,
) -> list[dict[str, Any]]:
    """
    Get autocomplete suggestions for a field value with caching.

    Args:
        client: JIRA client
        field_name: Field to get suggestions for
        prefix: Partial value to filter suggestions
        use_cache: Use cached data if available (default: True)
        refresh_cache: Force refresh from API (default: False)

    Returns:
        List of suggestion objects with value and displayName
    """
    if use_cache:
        cache = get_autocomplete_cache()
        return cache.get_suggestions(
            field_name, prefix, client, force_refresh=refresh_cache
        )
    else:
        result = client.get_jql_suggestions(field_name, prefix)
        return result.get("results", [])


def format_value_for_jql(value: str) -> str:
    """
    Format a value for use in JQL.

    Args:
        value: Raw value

    Returns:
        Properly quoted value for JQL
    """
    # Values with spaces need quotes
    if " " in value:
        return f'"{value}"'
    return value


def format_suggestions_text(field_name: str, suggestions: list[dict[str, Any]]) -> str:
    """
    Format suggestions as human-readable table.

    Args:
        field_name: Field name for context
        suggestions: List of suggestion objects

    Returns:
        Formatted string
    """
    if not suggestions:
        return f"No suggestions found for '{field_name}'\n\nThis field may be a free-text field or have no configured values."

    # Prepare data for table
    data = []
    for s in suggestions:
        value = s.get("value", "")
        display = s.get("displayName", value)
        data.append({"Value": format_value_for_jql(value), "Display Name": display})

    # Sort by display name
    data.sort(key=lambda x: x["Display Name"].lower())

    table = format_table(data, columns=["Value", "Display Name"])

    # Add usage example
    if suggestions:
        example_value = format_value_for_jql(suggestions[0].get("value", ""))
        example = f"\nUsage: {field_name} = {example_value}"
    else:
        example = ""

    return f"Suggestions for '{field_name}':\n\n{table}{example}"


def format_suggestions_json(suggestions: list[dict[str, Any]]) -> str:
    """
    Format suggestions as JSON.

    Args:
        suggestions: List of suggestion objects

    Returns:
        JSON string
    """
    return json.dumps(suggestions, indent=2)


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Get JQL field value suggestions for autocomplete.",
        epilog="""
Examples:
  %(prog)s --field project           # Get project suggestions
  %(prog)s --field status            # Get status suggestions
  %(prog)s --field status --prefix "In"  # Filter by prefix
  %(prog)s --field assignee --prefix "john"
  %(prog)s --field customfield_10000
  %(prog)s --field priority --output json
        """,
    )

    parser.add_argument(
        "--field", "-f", required=True, help="Field name to get suggestions for"
    )
    parser.add_argument(
        "--prefix", "-x", default="", help="Filter suggestions by prefix"
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

    try:
        client = get_jira_client()

        suggestions = get_suggestions(
            client,
            args.field,
            args.prefix,
            use_cache=not args.no_cache,
            refresh_cache=args.refresh,
        )

        if args.output == "json":
            print(format_suggestions_json(suggestions))
        else:
            print(format_suggestions_text(args.field, suggestions))

    except JiraError as e:
        print_error(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
