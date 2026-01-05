#!/usr/bin/env python3
"""
Get JSM service desk queue details.

Usage:
    python get_queue.py --service-desk 1 --queue-id 5
    python get_queue.py --service-desk 1 --queue-id 5 --output json
"""

import argparse
import json
import sys
from typing import Any

from jira_assistant_skills_lib import JiraError, get_jira_client, print_error


def get_queue(
    service_desk_id: int, queue_id: int, profile: str | None = None
) -> dict[str, Any]:
    """Get queue details."""
    with get_jira_client(profile) as client:
        return client.get_queue(service_desk_id, queue_id)


def format_queue_text(queue: dict[str, Any]) -> str:
    """Format queue as text."""
    lines = []
    lines.append(f"\nQueue: {queue.get('name')}")
    lines.append("=" * 80)
    lines.append(f"ID: {queue.get('id')}")
    lines.append(f"JQL: {queue.get('jql', 'N/A')}")
    return "\n".join(lines)


def format_queue_json(queue: dict[str, Any]) -> str:
    """Format queue as JSON."""
    return json.dumps(queue, indent=2)


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Get JSM service desk queue details")
    parser.add_argument(
        "--service-desk", type=int, required=True, help="Service desk ID"
    )
    parser.add_argument("--queue-id", type=int, required=True, help="Queue ID")
    parser.add_argument("--output", choices=["text", "json"], default="text")
    parser.add_argument("--profile", help="JIRA profile to use")

    args = parser.parse_args(argv)

    try:
        queue = get_queue(args.service_desk, args.queue_id, args.profile)

        if args.output == "json":
            print(format_queue_json(queue))
        else:
            print(format_queue_text(queue))

        return 0

    except JiraError as e:
        print_error(f"Failed to get queue: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
