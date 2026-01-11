#!/usr/bin/env python3
"""
Generate time reports from JIRA worklogs.

Aggregates time logged across issues by user, project, date, etc.
"""

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

# Add shared lib to path
from jira_assistant_skills_lib import (
    JiraError,
    format_seconds,
    get_jira_client,
    parse_relative_date,
    print_error,
)


def generate_report(
    client,
    project: str | None = None,
    author: str | None = None,
    since: str | None = None,
    until: str | None = None,
    group_by: str | None = None,
) -> dict[str, Any]:
    """
    Generate a time report.

    Args:
        client: JiraClient instance
        project: Project key to filter by
        author: Author email/accountId to filter by
        since: Start date for filtering
        until: End date for filtering
        group_by: Grouping option (issue, day, user)

    Returns:
        Report data dict with entries, totals, and grouping
    """
    # Build JQL query
    jql_parts = []
    if project:
        jql_parts.append(f"project = {project}")
    jql_parts.append("timespent > 0")

    jql = " AND ".join(jql_parts) if jql_parts else "timespent > 0"

    # Parse date filters
    since_dt = None
    until_dt = None
    if since:
        since_dt = parse_relative_date(since)
    if until:
        until_dt = parse_relative_date(until)
        # Include the entire end date
        until_dt = until_dt.replace(hour=23, minute=59, second=59)

    # Fetch issues with worklogs
    search_result = client.search_issues(jql, fields=["summary"], max_results=100)
    issues = search_result.get("issues", [])

    # Collect all worklog entries
    entries = []
    for issue in issues:
        issue_key = issue["key"]
        issue_summary = issue["fields"].get("summary", "")

        worklogs_result = client.get_worklogs(issue_key)
        worklogs = worklogs_result.get("worklogs", [])

        for worklog in worklogs:
            # Parse started date
            started_str = worklog.get("started", "")
            try:
                started_dt = datetime.fromisoformat(
                    started_str.replace("+0000", "+00:00").replace("Z", "+00:00")
                )
                started_dt = started_dt.replace(
                    tzinfo=None
                )  # Remove timezone for comparison
            except (ValueError, AttributeError):
                continue

            # Apply date filters
            if since_dt and started_dt.date() < since_dt.date():
                continue
            if until_dt and started_dt.date() > until_dt.date():
                continue

            # Apply author filter
            worklog_author = worklog.get("author", {})
            author_email = worklog_author.get("emailAddress", "")
            author_id = worklog_author.get("accountId", "")

            if author and author not in (author_email, author_id):
                continue

            entries.append(
                {
                    "issue_key": issue_key,
                    "issue_summary": issue_summary,
                    "worklog_id": worklog.get("id"),
                    "author": worklog_author.get("displayName", author_email),
                    "author_email": author_email,
                    "started": started_str,
                    "started_date": started_dt.strftime("%Y-%m-%d"),
                    "time_spent": worklog.get("timeSpent", ""),
                    "time_seconds": worklog.get("timeSpentSeconds", 0),
                }
            )

    # Calculate totals
    total_seconds = sum(e["time_seconds"] for e in entries)

    # Build result
    result = {
        "entries": entries,
        "entry_count": len(entries),
        "total_seconds": total_seconds,
        "total_formatted": format_seconds(total_seconds) if total_seconds else "0m",
        "filters": {
            "project": project,
            "author": author,
            "since": since,
            "until": until,
        },
    }

    # Apply grouping
    if group_by:
        result["group_by"] = group_by
        result["grouped"] = _group_entries(entries, group_by)

    return result


def _group_entries(entries: list[dict], group_by: str) -> dict[str, Any]:
    """Group entries by the specified field."""
    grouped = defaultdict(lambda: {"entries": [], "total_seconds": 0})

    for entry in entries:
        if group_by == "issue":
            key = entry["issue_key"]
        elif group_by == "day":
            key = entry["started_date"]
        elif group_by == "user":
            key = entry["author"]
        else:
            key = "all"

        grouped[key]["entries"].append(entry)
        grouped[key]["total_seconds"] += entry["time_seconds"]

    # Add formatted totals
    for key in grouped:
        grouped[key]["total_formatted"] = format_seconds(grouped[key]["total_seconds"])
        grouped[key]["entry_count"] = len(grouped[key]["entries"])

    return dict(grouped)


def format_report_text(report: dict[str, Any], show_details: bool = True) -> str:
    """Format report as text output."""
    lines = []

    # Header
    filters = report.get("filters", {})
    if filters.get("author"):
        lines.append(f"Time Report: {filters['author']}")
    elif filters.get("project"):
        lines.append(f"Time Report: Project {filters['project']}")
    else:
        lines.append("Time Report")

    if filters.get("since") or filters.get("until"):
        period = f"{filters.get('since', '...')} to {filters.get('until', '...')}"
        lines.append(f"Period: {period}")

    lines.append("")

    # Grouped output
    if "grouped" in report:
        report.get("group_by", "unknown")
        for key, data in sorted(report["grouped"].items()):
            lines.append(
                f"{key}: {data['total_formatted']} ({data['entry_count']} entries)"
            )
    elif show_details and report["entries"]:
        # Detailed output
        lines.append(f"{'Issue':<12} {'Author':<15} {'Date':<12} {'Time':<8}")
        lines.append("-" * 50)
        for entry in report["entries"]:
            lines.append(
                f"{entry['issue_key']:<12} "
                f"{entry['author'][:15]:<15} "
                f"{entry['started_date']:<12} "
                f"{entry['time_spent']:<8}"
            )

    lines.append("")
    lines.append(
        f"Total: {report['total_formatted']} ({report['entry_count']} entries)"
    )

    return "\n".join(lines)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Generate time reports from JIRA worklogs.",
        epilog="""
Examples:
  %(prog)s --project PROJ
  %(prog)s --user currentUser() --period last-week
  %(prog)s --project PROJ --since 2025-01-01 --until 2025-01-31
  %(prog)s --project PROJ --group-by day
  %(prog)s --project PROJ --group-by user --output json
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--project", "-P", help="Project key to filter by")
    parser.add_argument("--user", "-u", help="User email or accountId to filter by")
    parser.add_argument(
        "--since", "-s", help="Start date (e.g., 2025-01-01, yesterday, last-week)"
    )
    parser.add_argument("--until", "-e", help="End date (e.g., 2025-01-31, today)")
    parser.add_argument(
        "--period",
        choices=[
            "today",
            "yesterday",
            "this-week",
            "last-week",
            "this-month",
            "last-month",
        ],
        help="Predefined time period",
    )
    parser.add_argument(
        "--group-by",
        "-g",
        choices=["issue", "day", "user"],
        help="Group results by field",
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json", "csv"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args(argv)

    # Handle period shortcuts
    if args.period:
        today = datetime.now().date()
        if args.period == "today":
            args.since = str(today)
            args.until = str(today)
        elif args.period == "yesterday":
            yesterday = today - timedelta(days=1)
            args.since = str(yesterday)
            args.until = str(yesterday)
        elif args.period == "this-week":
            start = today - timedelta(days=today.weekday())
            args.since = str(start)
            args.until = str(today)
        elif args.period == "last-week":
            start = today - timedelta(days=today.weekday() + 7)
            end = start + timedelta(days=6)
            args.since = str(start)
            args.until = str(end)
        elif args.period == "this-month":
            args.since = str(today.replace(day=1))
            args.until = str(today)
        elif args.period == "last-month":
            first_of_month = today.replace(day=1)
            last_month_end = first_of_month - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)
            args.since = str(last_month_start)
            args.until = str(last_month_end)

    try:
        # Get client
        client = get_jira_client()

        # Generate report
        report = generate_report(
            client,
            project=args.project,
            author=args.user,
            since=args.since,
            until=args.until,
            group_by=args.group_by,
        )

        # Output result
        if args.output == "json":
            print(json.dumps(report, indent=2))
        elif args.output == "csv":
            # CSV output
            print("Issue Key,Issue Summary,Author,Date,Time Spent,Seconds")
            for entry in report["entries"]:
                summary = entry["issue_summary"].replace('"', '""')
                print(
                    f'{entry["issue_key"]},"{summary}",{entry["author"]},{entry["started_date"]},{entry["time_spent"]},{entry["time_seconds"]}'
                )
        else:
            print(format_report_text(report))

        client.close()

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(1)


if __name__ == "__main__":
    main()
