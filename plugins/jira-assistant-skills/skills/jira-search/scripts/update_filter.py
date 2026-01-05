#!/usr/bin/env python3
"""
Update a saved filter.

Updates the name, JQL, or description of an existing filter.
"""

import argparse
import json
import sys
from typing import Any

# Add shared library to path
from jira_assistant_skills_lib import JiraError, get_jira_client, print_error


def update_filter(
    client,
    filter_id: str,
    name: str | None = None,
    jql: str | None = None,
    description: str | None = None,
    favourite: bool | None = None,
) -> dict[str, Any]:
    """
    Update a filter.

    Args:
        client: JIRA client
        filter_id: Filter ID
        name: New name
        jql: New JQL
        description: New description
        favourite: New favourite status

    Returns:
        Updated filter object
    """
    return client.update_filter(
        filter_id, name=name, jql=jql, description=description, favourite=favourite
    )


def format_update_result(filter_data: dict[str, Any], changes: dict[str, Any]) -> str:
    """
    Format update result for display.

    Args:
        filter_data: Updated filter object
        changes: What was changed

    Returns:
        Formatted string
    """
    lines = ["Filter updated successfully:", ""]

    lines.append(f"  ID:          {filter_data.get('id', 'N/A')}")
    lines.append(f"  Name:        {filter_data.get('name', 'N/A')}")
    lines.append(f"  JQL:         {filter_data.get('jql', 'N/A')}")

    description = filter_data.get("description")
    lines.append(f"  Description: {description if description else '(none)'}")

    lines.append("")

    # Show what was changed
    changed_fields = [k for k, v in changes.items() if v is not None]
    if changed_fields:
        lines.append(f"Changes: {', '.join(changed_fields)}")

    return "\n".join(lines)


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Update a saved filter.",
        epilog="""
Examples:
  %(prog)s 10042 --name "My Open Bugs"
  %(prog)s 10042 --jql "project = PROJ AND type = Bug AND status != Done"
  %(prog)s 10042 --description "All open bugs in the project"
  %(prog)s 10042 --name "New Name" --jql "..." --description "..."
        """,
    )

    parser.add_argument("filter_id", help="Filter ID to update")
    parser.add_argument("--name", "-n", help="New filter name")
    parser.add_argument("--jql", "-j", help="New JQL query")
    parser.add_argument("--description", "-d", help="New description")
    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument("--profile", "-p", help="JIRA profile to use")

    args = parser.parse_args(argv)

    # Check that at least one update field is provided
    if not any([args.name, args.jql, args.description]):
        parser.error("At least one of --name, --jql, or --description is required")

    try:
        client = get_jira_client(args.profile)

        changes = {"name": args.name, "jql": args.jql, "description": args.description}

        result = update_filter(
            client,
            args.filter_id,
            name=args.name,
            jql=args.jql,
            description=args.description,
        )

        if args.output == "json":
            print(json.dumps(result, indent=2))
        else:
            print(format_update_result(result, changes))

    except JiraError as e:
        print_error(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
