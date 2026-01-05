#!/usr/bin/env python3
"""
List JSM service requests with filtering.

Usage:
    python list_requests.py --service-desk 1
    python list_requests.py --service-desk "IT Support" --status "In Progress"
    python list_requests.py --service-desk 1 --jql 'reporter=currentUser()'
    python list_requests.py --service-desk 1 --output json
"""

import argparse
import json
import sys
from typing import Any

from jira_assistant_skills_lib import JiraError, get_jira_client, print_error


def list_service_requests(
    service_desk_id: str,
    status: str | None = None,
    request_type: str | None = None,
    jql: str | None = None,
    max_results: int = 50,
    start_at: int = 0,
    profile: str | None = None,
) -> dict[str, Any]:
    """
    List service requests.

    Args:
        service_desk_id: Service desk ID or project key
        status: Filter by status
        request_type: Filter by request type name
        jql: Custom JQL filter
        max_results: Maximum results to return
        start_at: Pagination offset
        profile: JIRA profile to use

    Returns:
        Search results with issues and total count
    """
    # Build JQL query
    jql_parts = []

    # Add service desk filter
    jql_parts.append(f'project="{service_desk_id}"')

    # Add status filter
    if status:
        jql_parts.append(f'status="{status}"')

    # Add custom JQL
    if jql:
        jql_parts.append(f"({jql})")

    final_jql = " AND ".join(jql_parts)

    with get_jira_client(profile) as client:
        return client.search_issues(
            jql=final_jql, max_results=max_results, start_at=start_at
        )


def format_table(issues: list[dict[str, Any]]) -> str:
    """Format issues as table."""
    if not issues:
        return "No requests found."

    lines = []
    lines.append(f"\n{'Key':<12} {'Summary':<40} {'Status':<20} {'Reporter'}")
    lines.append("-" * 100)

    for issue in issues:
        key = issue.get("key", "N/A")
        fields = issue.get("fields", {})

        summary = fields.get("summary", "N/A")
        if len(summary) > 37:
            summary = summary[:37] + "..."

        status = fields.get("status", {}).get("name", "N/A")

        reporter = fields.get("reporter", {})
        reporter_email = reporter.get("emailAddress", "N/A")

        lines.append(f"{key:<12} {summary:<40} {status:<20} {reporter_email}")

    return "\n".join(lines)


def format_json(issues: list[dict[str, Any]]) -> str:
    """Format issues as JSON."""
    return json.dumps(issues, indent=2)


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="List JSM service requests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  List all requests:
    %(prog)s --service-desk 1

  Filter by status:
    %(prog)s --service-desk 1 --status "In Progress"

  Multiple statuses:
    %(prog)s --service-desk 1 --jql 'status in ("In Progress", "Waiting for support")'

  Current user's requests:
    %(prog)s --service-desk 1 --jql 'reporter=currentUser()'

  Pagination:
    %(prog)s --service-desk 1 --max-results 50 --start-at 50

  JSON output:
    %(prog)s --service-desk 1 --output json
        """,
    )

    parser.add_argument(
        "--service-desk", required=True, help="Service desk ID or project key"
    )
    parser.add_argument("--status", help="Filter by status")
    parser.add_argument("--request-type", help="Filter by request type name")
    parser.add_argument("--jql", help="Additional JQL filter")
    parser.add_argument(
        "--max-results",
        type=int,
        default=50,
        help="Maximum results to return (default: 50)",
    )
    parser.add_argument(
        "--start-at", type=int, default=0, help="Pagination offset (default: 0)"
    )
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument("--profile", help="JIRA profile to use from config")

    args = parser.parse_args(argv)

    try:
        result = list_service_requests(
            service_desk_id=args.service_desk,
            status=args.status,
            request_type=args.request_type,
            jql=args.jql,
            max_results=args.max_results,
            start_at=args.start_at,
            profile=args.profile,
        )

        issues = result.get("issues", [])
        total = result.get("total", 0)

        if args.output == "json":
            print(format_json(issues))
        else:
            print(format_table(issues))
            print(f"\nTotal: {total} requests")

            if total > len(issues):
                shown = len(issues)
                remaining = total - shown - args.start_at
                if remaining > 0:
                    print(
                        f"Showing {shown} of {total} (use --start-at {args.start_at + shown} for next page)"
                    )

        return 0

    except JiraError as e:
        print_error(f"Failed to list requests: {e}")
        return 1
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
