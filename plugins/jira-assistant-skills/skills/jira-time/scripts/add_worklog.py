#!/usr/bin/env python3
"""
Add a worklog (time entry) to a JIRA issue.

Logs time spent working on an issue with optional comment,
start time, estimate adjustment, and visibility options.

Usage:
    python add_worklog.py PROJ-123 --time 2h
    python add_worklog.py PROJ-123 --time 2h --visibility-type role --visibility-value Developers
    python add_worklog.py PROJ-123 --time 2h --visibility-type group --visibility-value jira-users
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


def add_worklog(
    client,
    issue_key: str,
    time_spent: str,
    started: str | None = None,
    comment: str | None = None,
    adjust_estimate: str = "auto",
    new_estimate: str | None = None,
    reduce_by: str | None = None,
    visibility_type: str | None = None,
    visibility_value: str | None = None,
) -> dict[str, Any]:
    """
    Add a worklog to an issue.

    Args:
        client: JiraClient instance
        issue_key: Issue key (e.g., 'PROJ-123')
        time_spent: Time spent in JIRA format (e.g., '2h', '1d 4h')
        started: When work was started (ISO format, relative like 'yesterday')
        comment: Optional comment text
        adjust_estimate: How to adjust remaining estimate
        new_estimate: New remaining estimate (when adjust_estimate='new')
        reduce_by: Amount to reduce estimate (when adjust_estimate='manual')
        visibility_type: 'role' or 'group' to restrict visibility (None for public)
        visibility_value: Role or group name for visibility restriction

    Returns:
        Created worklog object

    Raises:
        ValidationError: If time format is invalid
        JiraError: If API call fails
    """
    # Validate time format
    if not time_spent or not time_spent.strip():
        raise ValidationError("Time spent cannot be empty")

    if not validate_time_format(time_spent):
        raise ValidationError(
            f"Invalid time format: '{time_spent}'. Use format like '2h', '1d 4h', '30m'"
        )

    # Validate visibility options
    if visibility_type and not visibility_value:
        raise ValidationError(
            "--visibility-value is required when --visibility-type is specified"
        )
    if visibility_value and not visibility_type:
        raise ValidationError(
            "--visibility-type is required when --visibility-value is specified"
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
    return client.add_worklog(
        issue_key=issue_key,
        time_spent=time_spent,
        started=started_iso,
        comment=comment_adf,
        adjust_estimate=adjust_estimate,
        new_estimate=new_estimate,
        reduce_by=reduce_by,
        visibility_type=visibility_type,
        visibility_value=visibility_value,
    )


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Add a worklog (time entry) to a JIRA issue.",
        epilog="""
Examples:
  %(prog)s PROJ-123 --time 2h
  %(prog)s PROJ-123 --time "1d 4h" --comment "Debugging auth issue"
  %(prog)s PROJ-123 --time 2h --started yesterday
  %(prog)s PROJ-123 --time 2h --started "2025-01-15 09:00"
  %(prog)s PROJ-123 --time 2h --adjust-estimate leave
  %(prog)s PROJ-123 --time 2h --adjust-estimate new --new-estimate 6h
  %(prog)s PROJ-123 --time 2h --visibility-type role --visibility-value Developers
  %(prog)s PROJ-123 --time 2h --visibility-type group --visibility-value jira-users

Visibility options:
  role   - Restrict to users with a specific project role (e.g., Developers, Administrators)
  group  - Restrict to members of a JIRA group (e.g., jira-users, jira-administrators)
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("issue_key", help="Issue key (e.g., PROJ-123)")
    parser.add_argument(
        "--time", "-t", required=True, help="Time spent (e.g., 2h, 1d 4h, 30m)"
    )
    parser.add_argument(
        "--started",
        "-s",
        help='When work was started (ISO format, or "yesterday", "today")',
    )
    parser.add_argument("--comment", "-c", help="Comment about the work done")
    parser.add_argument(
        "--adjust-estimate",
        choices=["auto", "leave", "new", "manual"],
        default="auto",
        help="How to adjust remaining estimate (default: auto)",
    )
    parser.add_argument(
        "--new-estimate", help="New remaining estimate (when --adjust-estimate=new)"
    )
    parser.add_argument(
        "--reduce-by", help="Amount to reduce estimate (when --adjust-estimate=manual)"
    )
    parser.add_argument(
        "--visibility-type",
        choices=["role", "group"],
        help="Restrict visibility to role or group",
    )
    parser.add_argument(
        "--visibility-value", help="Role or group name for visibility restriction"
    )
    parser.add_argument("--profile", "-p", help="JIRA profile to use")
    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args(argv)

    try:
        # Validate issue key
        validate_issue_key(args.issue_key)

        # Get client
        client = get_jira_client(args.profile)

        # Add worklog
        result = add_worklog(
            client,
            args.issue_key,
            args.time,
            started=args.started,
            comment=args.comment,
            adjust_estimate=args.adjust_estimate,
            new_estimate=args.new_estimate,
            reduce_by=args.reduce_by,
            visibility_type=args.visibility_type,
            visibility_value=args.visibility_value,
        )

        # Output result
        if args.output == "json":
            import json

            print(json.dumps(result, indent=2))
        else:
            print(f"Worklog added to {args.issue_key}:")
            print(f"  Worklog ID: {result.get('id')}")
            print(
                f"  Time logged: {result.get('timeSpent')} ({result.get('timeSpentSeconds')} seconds)"
            )
            if result.get("started"):
                print(f"  Started: {result.get('started')}")
            if result.get("comment"):
                # Extract text from ADF comment
                comment_content = result.get("comment", {}).get("content", [])
                if comment_content:
                    text_parts = []
                    for block in comment_content:
                        for content in block.get("content", []):
                            if content.get("type") == "text":
                                text_parts.append(content.get("text", ""))
                    if text_parts:
                        print(f"  Comment: {' '.join(text_parts)}")
            if result.get("visibility"):
                vis = result.get("visibility", {})
                vis_type = vis.get("type", "")
                vis_value = vis.get("value", "")
                print(f"  Visibility: {vis_type} = {vis_value}")

        client.close()

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(1)


if __name__ == "__main__":
    main()
