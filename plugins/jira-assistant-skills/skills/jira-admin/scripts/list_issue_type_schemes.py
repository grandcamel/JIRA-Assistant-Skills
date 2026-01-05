#!/usr/bin/env python3
"""
List all issue type schemes in JIRA.

Lists schemes with pagination and filtering options.
Requires 'Administer Jira' global permission.
"""

import argparse
import json
import sys
from typing import Any

# Add shared lib to path
from jira_assistant_skills_lib import (
    JiraError,
    format_table,
    get_jira_client,
    print_error,
)


def list_issue_type_schemes(
    client=None,
    profile: str | None = None,
    start_at: int = 0,
    max_results: int = 50,
    scheme_ids: list[str] | None = None,
    order_by: str | None = None,
) -> dict[str, Any]:
    """
    List issue type schemes with pagination.

    Args:
        client: JiraClient instance (for testing)
        profile: Configuration profile name
        start_at: Starting index for pagination
        max_results: Maximum results per page
        scheme_ids: Filter by specific scheme IDs
        order_by: Order by field (e.g., 'name', '-name')

    Returns:
        Paginated response with schemes

    Raises:
        JiraError: On API failure
    """
    if client is None:
        client = get_jira_client(profile=profile)

    try:
        result = client.get_issue_type_schemes(
            start_at=start_at,
            max_results=max_results,
            scheme_ids=scheme_ids,
            order_by=order_by,
        )
        return result
    finally:
        if client:
            client.close()


def format_schemes(response: dict[str, Any], output_format: str = "table") -> str:
    """Format schemes for display."""
    if output_format == "json":
        return json.dumps(response, indent=2)

    schemes = response.get("values", [])
    if not schemes:
        return "No issue type schemes found."

    headers = ["ID", "Name", "Description", "Default Type ID", "Is Default"]
    rows = []

    for scheme in schemes:
        rows.append(
            [
                scheme.get("id", ""),
                scheme.get("name", ""),
                (scheme.get("description", "") or "")[:40],
                scheme.get("defaultIssueTypeId", "None"),
                "Yes" if scheme.get("isDefault") else "No",
            ]
        )

    return format_table(headers, rows)


def main(argv: list[str] | None = None):
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="List all issue type schemes in JIRA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all schemes
  python list_issue_type_schemes.py

  # List with pagination
  python list_issue_type_schemes.py --start-at 0 --max-results 25

  # Filter by specific IDs
  python list_issue_type_schemes.py --scheme-ids 10000 10001

  # Output as JSON
  python list_issue_type_schemes.py --format json

  # Use specific profile
  python list_issue_type_schemes.py --profile production
""",
    )

    parser.add_argument(
        "--start-at",
        type=int,
        default=0,
        help="Starting index for pagination (default: 0)",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=50,
        help="Maximum results per page (default: 50)",
    )
    parser.add_argument("--scheme-ids", nargs="+", help="Filter by scheme IDs")
    parser.add_argument(
        "--order-by",
        choices=["name", "-name", "id", "-id"],
        help="Order results by field (prefix with - for descending)",
    )
    parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument("--profile", help="Configuration profile to use")

    args = parser.parse_args(argv)

    try:
        response = list_issue_type_schemes(
            profile=args.profile,
            start_at=args.start_at,
            max_results=args.max_results,
            scheme_ids=args.scheme_ids,
            order_by=args.order_by,
        )

        output = format_schemes(response, args.format)
        print(output)

        if args.format == "table":
            total = response.get("total", len(response.get("values", [])))
            shown = len(response.get("values", []))
            print(f"\nShowing {shown} of {total} scheme(s)")

    except JiraError as e:
        print_error(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
