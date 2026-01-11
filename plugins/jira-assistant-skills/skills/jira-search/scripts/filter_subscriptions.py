#!/usr/bin/env python3
"""
View filter subscriptions.

Note: JIRA Cloud REST API has limited support for filter subscriptions.
Creating/editing subscriptions is only available via the JIRA UI.
"""

import argparse
import json
import sys
from typing import Any

# Add shared library to path
from jira_assistant_skills_lib import JiraError, get_jira_client, print_error


def get_subscriptions(client, filter_id: str) -> dict[str, Any]:
    """
    Get filter with subscription details.

    Args:
        client: JIRA client
        filter_id: Filter ID

    Returns:
        Filter object with subscriptions expanded
    """
    return client.get_filter(filter_id, expand="subscriptions")


def format_subscription(sub: dict[str, Any]) -> str:
    """Format a subscription for display."""
    user = sub.get("user", {})
    group = sub.get("group")

    if user:
        return user.get("emailAddress", user.get("displayName", "Unknown user"))
    elif group:
        return f"Group: {group.get('name', 'Unknown group')}"
    else:
        return "Unknown subscriber"


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="View filter subscriptions.",
        epilog="""
Examples:
  %(prog)s 10042                   # View subscriptions
  %(prog)s 10042 --output json     # JSON output

Note: Creating/editing subscriptions is only available via the JIRA UI.
        """,
    )

    parser.add_argument("filter_id", help="Filter ID")
    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args(argv)

    try:
        client = get_jira_client()

        filter_data = get_subscriptions(client, args.filter_id)
        subscriptions = filter_data.get("subscriptions", {})
        items = subscriptions.get("items", [])

        if args.output == "json":
            print(
                json.dumps(
                    {
                        "filter_id": args.filter_id,
                        "filter_name": filter_data.get("name"),
                        "subscriptions": items,
                    },
                    indent=2,
                )
            )
        else:
            filter_name = filter_data.get("name", "Unknown")
            print(f'Subscriptions for Filter {args.filter_id} "{filter_name}":')
            print()

            if not items:
                print("No subscriptions found.")
            else:
                print(f"{'ID':<10} {'Subscriber':<40}")
                print("-" * 50)
                for sub in items:
                    sub_id = sub.get("id", "N/A")
                    subscriber = format_subscription(sub)
                    print(f"{sub_id:<10} {subscriber:<40}")

            print()
            print(
                "Note: Creating/editing subscriptions is only available via the JIRA UI."
            )
            view_url = filter_data.get(
                "viewUrl",
                f"https://your-site.atlassian.net/issues/?filter={args.filter_id}",
            )
            print(f"See: {view_url} -> Subscribe")

    except JiraError as e:
        print_error(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
