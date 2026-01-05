#!/usr/bin/env python3
"""
List automation rules in JIRA.

Lists all automation rules with optional filtering by project scope,
state (enabled/disabled), and supports pagination.

Usage:
    python list_automation_rules.py
    python list_automation_rules.py --project PROJ
    python list_automation_rules.py --state enabled
    python list_automation_rules.py --state disabled
    python list_automation_rules.py --limit 10
    python list_automation_rules.py --output json
    python list_automation_rules.py --profile development
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


def list_automation_rules(
    client=None,
    project: str | None = None,
    state: str | None = None,
    limit: int = 50,
    fetch_all: bool = False,
    profile: str | None = None,
) -> list[dict[str, Any]]:
    """
    List automation rules with optional filtering.

    Args:
        client: AutomationClient instance (optional, created if not provided)
        project: Filter by project key
        state: Filter by state ('enabled' or 'disabled')
        limit: Maximum results per page (1-100)
        fetch_all: If True, fetch all pages of results
        profile: JIRA profile to use

    Returns:
        List of automation rule summaries
    """
    if client is None:
        client = get_automation_client(profile)

    all_rules = []
    cursor = None

    # Use search if we have filters
    use_search = project is not None or state is not None

    while True:
        if use_search:
            # Build scope filter from project key if provided
            scope = None
            if project:
                # Note: In production, we'd need to look up the project ARI
                # For now, we'll let the caller handle scope conversion
                scope = (
                    f"ari:cloud:jira:*:project/{project}"
                    if not project.startswith("ari:")
                    else project
                )

            response = client.search_rules(
                state=state.upper() if state else None,
                scope=scope,
                limit=limit,
                cursor=cursor,
            )
        else:
            response = client.get_rules(limit=limit, cursor=cursor)

        rules = response.get("values", [])
        all_rules.extend(rules)

        # Check for pagination
        if not fetch_all or not response.get("hasMore", False):
            break

        # Get next cursor from links
        links = response.get("links", {})
        next_link = links.get("next", "")
        if "?cursor=" in next_link:
            cursor = next_link.split("?cursor=")[-1]
        else:
            break

    return all_rules


def format_rule_summary(rule: dict[str, Any]) -> dict[str, str]:
    """Format a rule for display."""
    scope_resources = rule.get("ruleScope", {}).get("resources", [])
    scope = "Global" if not scope_resources else "Project"

    trigger = rule.get("trigger", {})
    trigger_type = trigger.get("type", "Unknown")
    # Simplify trigger type for display
    if ":" in trigger_type:
        trigger_display = trigger_type.split(":")[-1]
    else:
        trigger_display = trigger_type

    return {
        "ID": rule.get("id", "")[:50] + "..."
        if len(rule.get("id", "")) > 50
        else rule.get("id", ""),
        "Name": rule.get("name", "Unnamed"),
        "State": rule.get("state", "UNKNOWN"),
        "Scope": scope,
        "Trigger": trigger_display,
        "Updated": rule.get("updated", "")[:10] if rule.get("updated") else "N/A",
    }


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="List automation rules in JIRA",
        epilog="""
Examples:
    # List all rules
    python list_automation_rules.py

    # List rules for a specific project
    python list_automation_rules.py --project PROJ

    # List only enabled rules
    python list_automation_rules.py --state enabled

    # List only disabled rules
    python list_automation_rules.py --state disabled

    # Limit results
    python list_automation_rules.py --limit 10

    # Output as JSON
    python list_automation_rules.py --output json

    # Use specific profile
    python list_automation_rules.py --profile development
        """,
    )

    parser.add_argument("--project", "-p", help="Filter by project key")
    parser.add_argument(
        "--state", "-s", choices=["enabled", "disabled"], help="Filter by state"
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
        rules = list_automation_rules(
            project=args.project,
            state=args.state,
            limit=args.limit,
            fetch_all=args.fetch_all,
            profile=args.profile,
        )

        if not rules:
            print("No automation rules found.")
            return

        if args.output == "json":
            print(json.dumps(rules, indent=2))
        elif args.output == "csv":
            # CSV output
            headers = ["ID", "Name", "State", "Scope", "Trigger", "Updated"]
            print(",".join(headers))
            for rule in rules:
                formatted = format_rule_summary(rule)
                row = [f'"{formatted[h]}"' for h in headers]
                print(",".join(row))
        else:
            # Table output
            print(f"\nAutomation Rules ({len(rules)} found)")
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
