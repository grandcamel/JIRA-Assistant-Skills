#!/usr/bin/env python3
"""
Update an existing worklog (time entry) on a JIRA issue.

Modifies time spent, start time, or comment on an existing worklog.
"""

import argparse
import sys
from typing import Any

# Add shared lib to path
from jira_assistant_skills_lib import (
    JiraError,
    ValidationError,
    format_datetime_for_jira,
    get_jira_client,
    parse_relative_date,
    print_error,
    text_to_adf,
    validate_issue_key,
    validate_time_format,
)


def update_worklog(
    client,
    issue_key: str,
    worklog_id: str,
    time_spent: str | None = None,
    started: str | None = None,
    comment: str | None = None,
    adjust_estimate: str = "auto",
    new_estimate: str | None = None,
) -> dict[str, Any]:
    """
    Update an existing worklog.

    Args:
        client: JiraClient instance
        issue_key: Issue key (e.g., 'PROJ-123')
        worklog_id: Worklog ID to update
        time_spent: New time spent (optional)
        started: New start time (optional)
        comment: New comment text (optional)
        adjust_estimate: How to adjust remaining estimate
        new_estimate: New remaining estimate

    Returns:
        Updated worklog object

    Raises:
        ValidationError: If time format is invalid
        JiraError: If API call fails
    """
    # Validate time format if provided
    if time_spent and not validate_time_format(time_spent):
        raise ValidationError(
            f"Invalid time format: '{time_spent}'. Use format like '2h', '1d 4h', '30m'"
        )

    # Convert relative dates to ISO format
    started_iso = None
    if started:
        try:
            dt = parse_relative_date(started)
            started_iso = format_datetime_for_jira(dt)
        except ValueError as e:
            raise ValidationError(str(e))

    # Convert comment to ADF
    comment_adf = None
    if comment:
        comment_adf = text_to_adf(comment)

    # Call the API
    return client.update_worklog(
        issue_key=issue_key,
        worklog_id=worklog_id,
        time_spent=time_spent,
        started=started_iso if started_iso else started,
        comment=comment_adf,
        adjust_estimate=adjust_estimate,
        new_estimate=new_estimate,
    )


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Update an existing worklog (time entry) on a JIRA issue.",
        epilog="""
Examples:
  %(prog)s PROJ-123 --worklog-id 10045 --time 3h
  %(prog)s PROJ-123 --worklog-id 10045 --comment "Updated description"
  %(prog)s PROJ-123 --worklog-id 10045 --started "2025-01-15 10:00"
  %(prog)s PROJ-123 --worklog-id 10045 --time 3h --comment "Fixed the bug"
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("issue_key", help="Issue key (e.g., PROJ-123)")
    parser.add_argument(
        "--worklog-id", "-w", required=True, help="Worklog ID to update"
    )
    parser.add_argument("--time", "-t", help="New time spent (e.g., 3h, 1d 4h)")
    parser.add_argument("--started", "-s", help="New start time")
    parser.add_argument("--comment", "-c", help="New comment")
    parser.add_argument(
        "--adjust-estimate",
        choices=["auto", "leave", "new"],
        default="auto",
        help="How to adjust remaining estimate (default: auto)",
    )
    parser.add_argument(
        "--new-estimate", help="New remaining estimate (when --adjust-estimate=new)"
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args(argv)

    # Validate that at least one field is being updated
    if not any([args.time, args.started, args.comment]):
        parser.error(
            "At least one of --time, --started, or --comment must be specified"
        )

    try:
        # Validate issue key
        validate_issue_key(args.issue_key)

        # Get client
        client = get_jira_client()

        # Update worklog
        result = update_worklog(
            client,
            args.issue_key,
            args.worklog_id,
            time_spent=args.time,
            started=args.started,
            comment=args.comment,
            adjust_estimate=args.adjust_estimate,
            new_estimate=args.new_estimate,
        )

        # Output result
        if args.output == "json":
            import json

            print(json.dumps(result, indent=2))
        else:
            print(f"Worklog {args.worklog_id} updated on {args.issue_key}:")
            print(
                f"  Time logged: {result.get('timeSpent')} ({result.get('timeSpentSeconds')} seconds)"
            )
            if result.get("started"):
                print(f"  Started: {result.get('started')}")
            print(f"  Updated: {result.get('updated')}")

        client.close()

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(1)


if __name__ == "__main__":
    main()
