#!/usr/bin/env python3
"""
List JSM organizations.

Usage:
    python list_organizations.py
    python list_organizations.py --output json
    python list_organizations.py --start 0 --limit 25
"""

import argparse
import json
import sys

from jira_assistant_skills_lib import JiraError, get_jira_client, print_error


def list_organizations_func(start: int = 0, limit: int = 50) -> dict:
    """
    List all organizations.

    Args:
        start: Starting index for pagination
        limit: Maximum results per page

    Returns:
        Organizations data
    """
    with get_jira_client() as client:
        return client.get_organizations(start=start, limit=limit)


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="List JSM organizations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  List all organizations:
    %(prog)s

  JSON output:
    %(prog)s --output json

  Pagination:
    %(prog)s --start 0 --limit 25
        """,
    )

    parser.add_argument(
        "--start",
        type=int,
        default=0,
        help="Starting index for pagination (default: 0)",
    )
    parser.add_argument(
        "--limit", type=int, default=50, help="Maximum results per page (default: 50)"
    )
    parser.add_argument(
        "--output",
        choices=["text", "json", "csv"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument("--count", action="store_true", help="Show only count")

    args = parser.parse_args(argv)

    try:
        data = list_organizations_func(start=args.start, limit=args.limit)

        organizations = data.get("values", [])

        if args.count:
            print(len(organizations))
            return 0

        if args.output == "json":
            print(json.dumps(organizations, indent=2))
        elif args.output == "csv":
            print("ID,Name")
            for org in organizations:
                print(f"{org.get('id')},{org.get('name')}")
        else:
            if not organizations:
                print("No organizations found.")
                return 0

            print("Organizations:\n")
            print(f"{'ID':<10} {'Name'}")
            print("-" * 60)
            for org in organizations:
                print(f"{org.get('id'):<10} {org.get('name')}")

            print(f"\nTotal: {len(organizations)} organization(s)")

        return 0

    except JiraError as e:
        print_error(f"Failed to list organizations: {e}")
        return 1
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
