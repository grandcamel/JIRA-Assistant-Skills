#!/usr/bin/env python3
"""
Get issues in JSM service desk queue.

Usage:
    python get_queue_issues.py --service-desk 1 --queue-id 1
    python get_queue_issues.py --service-desk 1 --queue-id 1 --limit 10
    python get_queue_issues.py --service-desk 1 --queue-id 1 --output json
"""

import argparse
import json
import sys
from typing import Any

from jira_assistant_skills_lib import JiraError, get_jira_client, print_error


def get_queue_issues(
    service_desk_id: int,
    queue_id: int,
    start: int = 0,
    limit: int = 50,
    profile: str | None = None,
) -> dict[str, Any]:
    """Get issues in a queue."""
    with get_jira_client(profile) as client:
        return client.get_queue_issues(service_desk_id, queue_id, start, limit)


def format_issues_text(issues_data: dict[str, Any]) -> str:
    """Format issues as text."""
    lines = []
    issues = issues_data.get("values", [])
    total = issues_data.get("size", 0)

    lines.append(f"\nQueue Issues: {total} total")
    lines.append("=" * 80)
    lines.append("")

    for issue in issues:
        issue_key = issue.get("issueKey")
        fields = issue.get("fields", {})
        summary = fields.get("summary", "N/A")
        status = fields.get("status", {}).get("name", "N/A")

        lines.append(f"{issue_key}: {summary[:60]}")
        lines.append(f"  Status: {status}")

    return "\n".join(lines)


def format_issues_json(issues_data: dict[str, Any]) -> str:
    """Format issues as JSON."""
    return json.dumps(issues_data, indent=2)


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Get issues in JSM service desk queue")
    parser.add_argument(
        "--service-desk", type=int, required=True, help="Service desk ID"
    )
    parser.add_argument("--queue-id", type=int, required=True, help="Queue ID")
    parser.add_argument("--start", type=int, default=0, help="Starting index")
    parser.add_argument("--limit", type=int, default=50, help="Maximum results")
    parser.add_argument("--output", choices=["text", "json"], default="text")
    parser.add_argument("--profile", help="JIRA profile to use")

    args = parser.parse_args(argv)

    try:
        issues = get_queue_issues(
            args.service_desk, args.queue_id, args.start, args.limit, args.profile
        )

        if args.output == "json":
            print(format_issues_json(issues))
        else:
            print(format_issues_text(issues))

        return 0

    except JiraError as e:
        print_error(f"Failed to get queue issues: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
