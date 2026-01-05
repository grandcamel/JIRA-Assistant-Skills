#!/usr/bin/env python3
"""
Get and display a JIRA issue.

Usage:
    python get_issue.py PROJ-123
    python get_issue.py PROJ-123 --detailed
    python get_issue.py PROJ-123 --show-links
    python get_issue.py PROJ-123 --show-time
    python get_issue.py PROJ-123 --output json
"""

import argparse
import sys

from jira_assistant_skills_lib import (
    JiraError,
    format_issue,
    format_json,
    get_jira_client,
    print_error,
    validate_issue_key,
)


def get_issue(
    issue_key: str, fields: list | None = None, profile: str | None = None
) -> dict:
    """
    Get a JIRA issue.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        fields: Specific fields to retrieve (default: all)
        profile: JIRA profile to use

    Returns:
        Issue data dictionary
    """
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client(profile)
    issue = client.get_issue(issue_key, fields=fields)
    client.close()

    return issue


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Get and display a JIRA issue",
        epilog="Example: python get_issue.py PROJ-123 --detailed",
    )

    parser.add_argument("issue_key", help="Issue key (e.g., PROJ-123)")
    parser.add_argument(
        "--fields", "-f", help="Comma-separated list of fields to retrieve"
    )
    parser.add_argument(
        "--detailed",
        "-d",
        action="store_true",
        help="Show detailed information including description",
    )
    parser.add_argument(
        "--show-links",
        "-l",
        action="store_true",
        help="Show issue links (blocks, relates to, etc.)",
    )
    parser.add_argument(
        "--show-time", "-t", action="store_true", help="Show time tracking information"
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument("--profile", help="JIRA profile to use (default: from config)")

    args = parser.parse_args(argv)

    try:
        fields = [f.strip() for f in args.fields.split(",")] if args.fields else None

        # If --show-links, ensure issuelinks is included and show detailed
        show_detailed = args.detailed or args.show_links or args.show_time
        if args.show_links and fields is None:
            fields = None  # Get all fields including issuelinks
        elif args.show_links and fields is not None and "issuelinks" not in fields:
            fields.append("issuelinks")

        # If --show-time, ensure timetracking is included
        if args.show_time and fields is not None and "timetracking" not in fields:
            fields.append("timetracking")

        issue = get_issue(issue_key=args.issue_key, fields=fields, profile=args.profile)

        if args.output == "json":
            print(format_json(issue))
        else:
            print(format_issue(issue, detailed=show_detailed))

            # Show time tracking if requested
            if args.show_time:
                tt = issue.get("fields", {}).get("timetracking", {})
                if tt:
                    print("\nTime Tracking:")
                    if tt.get("originalEstimate"):
                        print(f"  Original Estimate:  {tt.get('originalEstimate')}")
                    if tt.get("remainingEstimate"):
                        print(f"  Remaining Estimate: {tt.get('remainingEstimate')}")
                    if tt.get("timeSpent"):
                        print(f"  Time Spent:         {tt.get('timeSpent')}")
                else:
                    print("\nTime Tracking: Not configured or no data")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
