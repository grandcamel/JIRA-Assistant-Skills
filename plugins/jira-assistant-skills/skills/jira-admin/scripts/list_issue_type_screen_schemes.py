#!/usr/bin/env python3
"""
List all issue type screen schemes in JIRA.

Provides paginated listing with filtering capabilities.
"""

import argparse
import sys
from typing import Any

# Add shared lib to path
from jira_assistant_skills_lib import (
    JiraError,
    format_json,
    format_table,
    get_jira_client,
    print_error,
)


def list_issue_type_screen_schemes(
    client=None,
    filter_pattern: str | None = None,
    show_projects: bool = False,
    fetch_all: bool = False,
    max_results: int = 100,
) -> list[dict[str, Any]]:
    """
    List all issue type screen schemes in JIRA.

    Args:
        client: JiraClient instance
        filter_pattern: Filter schemes by name pattern (case-insensitive)
        show_projects: Include project associations
        fetch_all: If True, fetch all pages of results
        max_results: Maximum results per page

    Returns:
        List of issue type screen scheme objects
    """
    if client is None:
        from jira_assistant_skills_lib import get_jira_client

        client = get_jira_client()

    schemes = []
    start_at = 0

    while True:
        result = client.get_issue_type_screen_schemes(
            start_at=start_at, max_results=max_results
        )

        page_schemes = result.get("values", [])
        schemes.extend(page_schemes)

        # Check if we need to fetch more pages
        if not fetch_all or result.get("isLast", True):
            break

        total = result.get("total", 0)
        if start_at + len(page_schemes) >= total:
            break

        start_at += len(page_schemes)

    # Apply local filtering
    if filter_pattern:
        schemes = [
            s for s in schemes if filter_pattern.lower() in s.get("name", "").lower()
        ]

    # Add project associations if requested
    if show_projects:
        project_mappings = client.get_project_issue_type_screen_schemes()
        for scheme in schemes:
            scheme_id = str(scheme.get("id", ""))
            for mapping in project_mappings.get("values", []):
                itss = mapping.get("issueTypeScreenScheme", {})
                if str(itss.get("id", "")) == scheme_id:
                    scheme["project_ids"] = mapping.get("projectIds", [])
                    break

    return schemes


def format_schemes_output(
    schemes: list[dict[str, Any]], output_format: str = "text"
) -> str:
    """
    Format issue type screen schemes for output.

    Args:
        schemes: List of issue type screen scheme objects
        output_format: Output format ('text', 'json')

    Returns:
        Formatted output string
    """
    if output_format == "json":
        return format_json(schemes)

    if not schemes:
        return "No issue type screen schemes found."

    # Prepare data for table
    data = []
    columns = ["ID", "Name", "Description"]

    # Check if any scheme has project info
    has_projects = any(s.get("project_ids") for s in schemes)
    if has_projects:
        columns.append("Projects")

    for scheme in schemes:
        row = {
            "ID": scheme.get("id", ""),
            "Name": scheme.get("name", ""),
            "Description": (scheme.get("description", "") or "")[:40],
        }

        if has_projects:
            project_ids = scheme.get("project_ids", [])
            row["Projects"] = str(len(project_ids)) if project_ids else "0"

        data.append(row)

    return format_table(data, columns=columns)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="List all issue type screen schemes in JIRA",
        epilog="""
Examples:
    # List all issue type screen schemes
    python list_issue_type_screen_schemes.py

    # Filter by name
    python list_issue_type_screen_schemes.py --filter "Default"

    # Show project associations
    python list_issue_type_screen_schemes.py --projects

    # JSON output
    python list_issue_type_screen_schemes.py --output json

    # Fetch all pages
    python list_issue_type_screen_schemes.py --all
""",
    )

    parser.add_argument(
        "--filter",
        "-f",
        dest="filter_pattern",
        help="Filter schemes by name pattern (case-insensitive)",
    )
    parser.add_argument(
        "--projects",
        dest="show_projects",
        action="store_true",
        help="Show project associations",
    )
    parser.add_argument(
        "--all",
        "-a",
        dest="fetch_all",
        action="store_true",
        help="Fetch all pages of results",
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument("--profile", "-p", help="JIRA profile to use")

    args = parser.parse_args(argv)

    try:
        client = get_jira_client(args.profile)

        schemes = list_issue_type_screen_schemes(
            client=client,
            filter_pattern=args.filter_pattern,
            show_projects=args.show_projects,
            fetch_all=args.fetch_all,
        )

        output = format_schemes_output(schemes, args.output)
        print(output)

        if args.output == "text" and schemes:
            print(f"\nTotal: {len(schemes)} issue type screen scheme(s)")

    except JiraError as e:
        print_error(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
