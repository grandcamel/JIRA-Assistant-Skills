#!/usr/bin/env python3
"""
Get JSM request status history.

Usage:
    python get_request_status.py SD-101
    python get_request_status.py SD-101 --show-durations
    python get_request_status.py SD-101 --output json
"""

import argparse
import json
import sys
import time
from typing import Any

from jira_assistant_skills_lib import (
    JiraError,
    NotFoundError,
    get_jira_client,
    print_error,
)


def get_status_history(issue_key: str) -> dict[str, Any]:
    """
    Get request status history.

    Args:
        issue_key: Request key

    Returns:
        Status history data

    Raises:
        NotFoundError: If request doesn't exist
    """
    with get_jira_client() as client:
        return client.get_request_status(issue_key)


def format_duration(millis: int) -> str:
    """Format milliseconds to human-readable duration."""
    hours = millis // 3600000
    minutes = (millis % 3600000) // 60000

    if hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"


def calculate_durations(statuses: list[dict[str, Any]]) -> dict[str, int]:
    """
    Calculate time spent in each status.

    Args:
        statuses: List of status history entries

    Returns:
        Dictionary mapping status names to duration in milliseconds
    """
    durations = {}
    current_time = int(time.time() * 1000)

    for i, status in enumerate(statuses):
        status_name = status["status"]
        start_time = status["statusDate"]["epochMillis"]

        if i + 1 < len(statuses):
            end_time = statuses[i + 1]["statusDate"]["epochMillis"]
        else:
            # Current status - use now
            end_time = current_time

        duration = end_time - start_time
        durations[status_name] = duration

    return durations


def calculate_metrics(statuses: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Calculate status change metrics.

    Args:
        statuses: List of status history entries

    Returns:
        Dictionary with metrics
    """
    if not statuses:
        return {}

    durations = calculate_durations(statuses)
    total_time = sum(durations.values())

    # Time to first response (first status change)
    time_to_first_response = None
    if len(statuses) > 1:
        time_to_first_response = (
            statuses[1]["statusDate"]["epochMillis"]
            - statuses[0]["statusDate"]["epochMillis"]
        )

    # Time to resolution (if resolved)
    time_to_resolution = None
    last_status = statuses[-1]
    if last_status.get("statusCategory") == "DONE":
        time_to_resolution = total_time

    return {
        "total_time": total_time,
        "status_changes": len(statuses),
        "time_to_first_response": time_to_first_response,
        "time_to_resolution": time_to_resolution,
    }


def format_timeline(
    statuses: list[dict[str, Any]], show_durations: bool = False
) -> str:
    """Format status history as timeline."""
    if not statuses:
        return "No status history found."

    lines = []
    header = f"\n{'Status':<25} {'Category':<15} {'Changed':<25}"
    if show_durations:
        header += f" {'Duration'}"
    lines.append(header)

    lines.append("-" * 80)

    durations = calculate_durations(statuses) if show_durations else {}

    for status in statuses:
        status_name = status.get("status", "N/A")
        category = status.get("statusCategory", "N/A")
        changed = status.get("statusDate", {}).get("friendly", "N/A")

        line = f"{status_name:<25} {category:<15} {changed:<25}"

        if show_durations and status_name in durations:
            duration = format_duration(durations[status_name])
            line += f" {duration}"

        lines.append(line)

    # Add metrics
    if show_durations:
        metrics = calculate_metrics(statuses)

        lines.append("")
        lines.append(f"Total Time: {format_duration(metrics['total_time'])}")
        if metrics.get("time_to_first_response"):
            lines.append(
                f"Time to First Response: {format_duration(metrics['time_to_first_response'])}"
            )
        if metrics.get("time_to_resolution"):
            lines.append(
                f"Time to Resolution: {format_duration(metrics['time_to_resolution'])}"
            )
        lines.append(f"Status Changes: {metrics['status_changes']}")

    return "\n".join(lines)


def format_json(statuses: list[dict[str, Any]]) -> str:
    """Format status history as JSON."""
    return json.dumps(statuses, indent=2)


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Get JSM request status history",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Basic usage:
    %(prog)s SD-101

  With durations:
    %(prog)s SD-101 --show-durations

  JSON output:
    %(prog)s SD-101 --output json
        """,
    )

    parser.add_argument("request_key", help="Request key (e.g., SD-101)")
    parser.add_argument(
        "--show-durations", action="store_true", help="Show time spent in each status"
    )
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args(argv)

    try:
        history = get_status_history(args.request_key)

        statuses = history.get("values", [])

        if args.output == "json":
            print(format_json(statuses))
        else:
            print(f"Status History for {args.request_key}:")
            print(format_timeline(statuses, show_durations=args.show_durations))

        return 0

    except NotFoundError as e:
        print_error(f"Request not found: {e}")
        return 1
    except JiraError as e:
        print_error(f"Failed to get status history: {e}")
        return 1
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
