#!/usr/bin/env python3
"""
List manually-triggered automation rules.

Lists all automation rules that can be triggered manually.

Usage:
    python list_manual_rules.py
    python list_manual_rules.py --context issue
    python list_manual_rules.py --context alert
    python list_manual_rules.py --output json
    python list_manual_rules.py --profile development
"""

import argparse
import json
import sys
from typing import Any

# Add shared lib to path
from jira_assistant_skills_lib import (
    AutomationError,
    JiraError,
    format_table,
    get_automation_client,
    print_error,
)


def list_manual_rules(
    client=None,
    context_type: str = "issue",
    limit: int = 50,
    fetch_all: bool = False,
    profile: str | None = None,
) -> list[dict[str, Any]]:
    """
    List manually-triggered automation rules.

    Args:
        client: AutomationClient instance (optional, created if not provided)
        context_type: Context type ('issue', 'alert', etc.)
        limit: Maximum results per page
        fetch_all: If True, fetch all pages
        profile: JIRA profile to use

    Returns:
        List of manual rule summaries
    """
    if client is None:
        client = get_automation_client(profile)

    all_rules = []
    cursor = None

    while True:
        response = client.get_manual_rules(
            context_type=context_type, limit=limit, cursor=cursor
        )

        rules = response.get("values", [])
        all_rules.extend(rules)

        # Check for pagination
        if not fetch_all or not response.get("hasMore", False):
            break

        # Get next cursor
        links = response.get("links", {})
        next_link = links.get("next", "")
        if "?cursor=" in next_link:
            cursor = next_link.split("?cursor=")[-1]
        else:
            break

    return all_rules


def format_rule_summary(rule: dict[str, Any]) -> dict[str, str]:
    """Format a manual rule for display."""
    return {
        "ID": str(rule.get("id", "")),
        "Name": rule.get("name", "Unnamed"),
        "Description": (rule.get("description", "")[:50] + "...")
        if len(rule.get("description", "")) > 50
        else rule.get("description", ""),
        "Context": rule.get("contextType", "N/A"),
    }


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="List manually-triggered automation rules",
        epilog="""
Examples:
    # List all manual rules
    python list_manual_rules.py

    # List for specific context type
    python list_manual_rules.py --context issue
    python list_manual_rules.py --context alert

    # Fetch all pages
    python list_manual_rules.py --all

    # Output as JSON
    python list_manual_rules.py --output json

    # Use specific profile
    python list_manual_rules.py --profile development
        """,
    )

    parser.add_argument(
        "--context", "-c", default="issue", help="Context type (default: issue)"
    )
    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=50,
        help="Maximum results per page (default: 50)",
    )
    parser.add_argument(
        "--all",
        "-a",
        action="store_true",
        dest="fetch_all",
        help="Fetch all pages of results",
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["table", "json", "csv"],
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument("--profile", help="JIRA profile to use")

    args = parser.parse_args(argv)

    try:
        rules = list_manual_rules(
            context_type=args.context,
            limit=args.limit,
            fetch_all=args.fetch_all,
            profile=args.profile,
        )

        if not rules:
            print(f"No manual rules found for context '{args.context}'.")
            return

        if args.output == "json":
            print(json.dumps(rules, indent=2))
        elif args.output == "csv":
            headers = ["ID", "Name", "Description", "Context"]
            print(",".join(headers))
            for rule in rules:
                formatted = format_rule_summary(rule)
                row = [f'"{formatted[h]}"' for h in headers]
                print(",".join(row))
        else:
            print(f"\nManual Rules ({len(rules)} found, context: {args.context})")
            print("=" * 80)

            rows = [format_rule_summary(rule) for rule in rules]
            if rows:
                table = format_table(rows)
                print(table)

    except (JiraError, AutomationError) as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
