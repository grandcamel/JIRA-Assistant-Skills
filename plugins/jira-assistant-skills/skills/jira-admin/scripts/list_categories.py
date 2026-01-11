#!/usr/bin/env python3
"""
List all JIRA project categories.

Project categories are used to group and organize projects.

Examples:
    # List all categories
    python list_categories.py

    # JSON output
    python list_categories.py --output json
"""

import argparse
import json
import sys
from typing import Any

# Add shared lib to path
from jira_assistant_skills_lib import JiraError, get_jira_client, print_error


def list_categories(output_format: str = "table", client=None) -> list[dict[str, Any]]:
    """
    List all project categories.

    Args:
        output_format: Output format (table, json)
        client: JiraClient instance (optional)

    Returns:
        List of category objects

    Raises:
        JiraError: If API call fails
    """
    # Create client if not provided
    should_close = False
    if client is None:
        client = get_jira_client()
        should_close = True

    try:
        result = client.get_project_categories()
        return result

    finally:
        if should_close:
            client.close()


def format_output(
    categories: list[dict[str, Any]], output_format: str = "table"
) -> str:
    """Format categories for output."""
    if output_format == "json":
        return json.dumps(categories, indent=2)

    if not categories:
        return "No project categories found."

    # Table format
    lines = ["Project Categories:", "=" * 60, ""]

    headers = ["ID", "Name", "Description"]

    # Try to use tabulate if available
    try:
        from tabulate import tabulate

        rows = []
        for cat in categories:
            desc = cat.get("description", "-")[:40] if cat.get("description") else "-"
            rows.append([cat.get("id", "-"), cat.get("name", "-"), desc])
        lines.append(tabulate(rows, headers=headers, tablefmt="grid"))
    except ImportError:
        # Simple format
        lines.append(f"{'ID':<10} {'Name':<25} {'Description':<30}")
        lines.append("-" * 65)
        for cat in categories:
            desc = cat.get("description", "-")[:30] if cat.get("description") else "-"
            lines.append(
                f"{cat.get('id', '-'):<10} {cat.get('name', '-'):<25} {desc:<30}"
            )

    lines.append("")
    lines.append(f"Total: {len(categories)} categories")

    return "\n".join(lines)


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="List all JIRA project categories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all categories
  %(prog)s

  # JSON output
  %(prog)s --output json
        """,
    )

    # Output options
    parser.add_argument(
        "--output",
        "-o",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)",
    )

    args = parser.parse_args(argv)

    try:
        client = get_jira_client()

        result = list_categories(output_format=args.output, client=client)

        print(format_output(result, args.output))

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    finally:
        if "client" in locals():
            client.close()


if __name__ == "__main__":
    main()
