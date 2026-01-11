#!/usr/bin/env python3
"""
Get activity/changelog for a JIRA issue.

Usage:
    python get_activity.py PROJ-123
    python get_activity.py PROJ-123 --limit 10 --offset 0
    python get_activity.py PROJ-123 --output json
    python get_activity.py PROJ-123 --field status
    python get_activity.py PROJ-123 --field-type custom
"""

import argparse
import json
import sys
from typing import Any

from jira_assistant_skills_lib import (
    JiraError,
    format_table,
    get_jira_client,
    print_error,
    validate_issue_key,
)


def get_activity(
    issue_key: str, limit: int = 100, offset: int = 0
) -> dict[str, Any]:
    """
    Get activity/changelog for an issue.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        limit: Maximum number of changelog entries to return
        offset: Starting position (for pagination)

    Returns:
        Changelog data with values, total, etc.
    """
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client()
    result = client.get_changelog(issue_key, max_results=limit, start_at=offset)
    client.close()

    return result


def parse_changelog(
    changelog_data: dict[str, Any],
    field_filter: list[str] | None = None,
    field_type_filter: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Parse changelog into simplified format with optional filtering.

    Args:
        changelog_data: Raw changelog data from API
        field_filter: List of field names to include (e.g., ['status', 'assignee'])
        field_type_filter: List of field types to include (e.g., ['custom', 'jira'])

    Returns:
        List of parsed changes with type, field, from, to, author, date
    """
    parsed = []

    for entry in changelog_data.get("values", []):
        author = entry.get("author", {}).get("displayName", "Unknown")
        created = entry.get("created", "")

        for item in entry.get("items", []):
            field = item.get("field", "")
            field_type = item.get("fieldtype", "")
            from_string = item.get("fromString") or ""
            to_string = item.get("toString") or ""

            # Apply field name filter
            if field_filter:
                if field.lower() not in [f.lower() for f in field_filter]:
                    continue

            # Apply field type filter
            if field_type_filter:
                if field_type.lower() not in [ft.lower() for ft in field_type_filter]:
                    continue

            # Determine change type based on field
            change_type = field

            parsed.append(
                {
                    "type": change_type,
                    "field": field,
                    "field_type": field_type,
                    "from": from_string,
                    "to": to_string,
                    "author": author,
                    "created": created,
                }
            )

    return parsed


def display_activity_table(changes: list[dict[str, Any]]) -> None:
    """
    Display activity in table format.

    Args:
        changes: List of parsed changes
    """
    if not changes:
        print("No activity found.")
        return

    # Prepare table data - add formatted date to each change
    table_data = []
    for change in changes:
        table_data.append(
            {
                "date": change.get("created", "")[:16],
                "author": change.get("author", ""),
                "field": change.get("field", ""),
                "from": change.get("from", "") or "(none)",
                "to": change.get("to", "") or "(none)",
            }
        )

    print(
        format_table(
            table_data,
            columns=["date", "author", "field", "from", "to"],
            headers=["Date", "Author", "Field", "From", "To"],
        )
    )


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Get activity/changelog for a JIRA issue",
        epilog="""
Examples:
  %(prog)s PROJ-123
  %(prog)s PROJ-123 --limit 10
  %(prog)s PROJ-123 --output json
  %(prog)s PROJ-123 --field status
  %(prog)s PROJ-123 --field status --field assignee
  %(prog)s PROJ-123 --field-type custom
  %(prog)s PROJ-123 --field-type jira

Field types:
  jira    - Built-in JIRA fields (status, assignee, priority, etc.)
  custom  - Custom fields (story points, etc.)
        """,
    )

    parser.add_argument("issue_key", help="Issue key (e.g., PROJ-123)")
    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=100,
        help="Maximum number of changelog entries (default: 100)",
    )
    parser.add_argument(
        "--offset",
        "-o",
        type=int,
        default=0,
        help="Starting position for pagination (default: 0)",
    )
    parser.add_argument(
        "--field",
        "-f",
        action="append",
        dest="fields",
        help="Filter by field name (can be repeated)",
    )
    parser.add_argument(
        "--field-type",
        "-t",
        action="append",
        dest="field_types",
        choices=["jira", "custom"],
        help="Filter by field type: jira (built-in) or custom",
    )
    parser.add_argument(
        "--output",
        "-O",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)",
    )

    args = parser.parse_args(argv)

    try:
        # Get activity
        changelog = get_activity(
            args.issue_key, limit=args.limit, offset=args.offset
        )

        # Parse changelog with filters
        changes = parse_changelog(
            changelog, field_filter=args.fields, field_type_filter=args.field_types
        )

        # Output
        if args.output == "json":
            print(json.dumps(changes, indent=2))
        else:
            # Build filter description
            filter_desc = ""
            if args.fields:
                filter_desc += f" (fields: {', '.join(args.fields)})"
            if args.field_types:
                filter_desc += f" (types: {', '.join(args.field_types)})"

            print(f"Activity for {args.issue_key}{filter_desc}:\n")
            display_activity_table(changes)

            # Show pagination info
            total = changelog.get("total", 0)
            raw_count = len(parse_changelog(changelog))  # Unfiltered count
            showing = len(changes)

            if args.fields or args.field_types:
                print(
                    f"\nShowing {showing} filtered changes (from {raw_count} in range)."
                )
            if total > args.limit:
                print(
                    f"Use --offset {args.offset + args.limit} to see more (total: {total})."
                )

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
