#!/usr/bin/env python3
"""
Log time to multiple JIRA issues at once.

Bulk time logging for meetings, sprint activities, etc.
"""

import argparse
import json
import sys
from typing import Any

# Add shared lib to path
from jira_assistant_skills_lib import (
    AuthenticationError,
    JiraError,
    ValidationError,
    format_seconds,
    get_jira_client,
    parse_time_string,
    print_error,
    text_to_adf,
    validate_issue_key,
    validate_time_format,
)


def bulk_log_time(
    client,
    issues: list[str] | None = None,
    jql: str | None = None,
    time_spent: str | None = None,
    comment: str | None = None,
    started: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Log time to multiple issues.

    Args:
        client: JiraClient instance
        issues: List of issue keys
        jql: JQL query to find issues
        time_spent: Time to log per issue
        comment: Optional comment for all worklogs
        started: Optional start time
        dry_run: If True, preview without logging

    Returns:
        Result dict with success/failure counts
    """
    # Get issues from JQL if specified
    if jql:
        search_result = client.search_issues(jql, fields=["summary"], max_results=100)
        issues = [issue["key"] for issue in search_result.get("issues", [])]

    if not issues:
        return {
            "success_count": 0,
            "failure_count": 0,
            "total_seconds": 0,
            "entries": [],
            "failures": [],
            "dry_run": dry_run,
            "would_log_count": 0,
        }

    # Validate time format
    if not validate_time_format(time_spent):
        raise ValidationError(
            f"Invalid time format: '{time_spent}'. Use format like '2h', '1d 4h', '30m'"
        )

    time_seconds = parse_time_string(time_spent)

    # Prepare comment ADF if provided
    comment_adf = None
    if comment:
        comment_adf = text_to_adf(comment)

    # Dry run - just preview
    if dry_run:
        preview = []
        for issue_key in issues:
            try:
                issue = client.get_issue(issue_key)
                preview.append(
                    {
                        "issue": issue_key,
                        "summary": issue.get("fields", {}).get("summary", ""),
                        "time_to_log": time_spent,
                    }
                )
            except JiraError:
                preview.append(
                    {
                        "issue": issue_key,
                        "summary": "(unable to fetch)",
                        "time_to_log": time_spent,
                    }
                )

        return {
            "dry_run": True,
            "would_log_count": len(issues),
            "would_log_seconds": time_seconds * len(issues),
            "would_log_formatted": format_seconds(time_seconds * len(issues)),
            "preview": preview,
        }

    # Actually log time
    successes = []
    failures = []

    for issue_key in issues:
        try:
            worklog = client.add_worklog(
                issue_key=issue_key,
                time_spent=time_spent,
                started=started,
                comment=comment_adf,
            )
            successes.append(
                {
                    "issue": issue_key,
                    "worklog_id": worklog.get("id"),
                    "time_spent": time_spent,
                }
            )
        except (JiraError, AuthenticationError) as e:
            failures.append({"issue": issue_key, "error": str(e)})

    total_seconds = time_seconds * len(successes)

    return {
        "success_count": len(successes),
        "failure_count": len(failures),
        "total_seconds": total_seconds,
        "total_formatted": format_seconds(total_seconds),
        "entries": successes,
        "failures": failures,
        "dry_run": False,
    }


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Log time to multiple JIRA issues at once.",
        epilog="""
Examples:
  %(prog)s --issues PROJ-1,PROJ-2,PROJ-3 --time 30m --comment "Sprint planning"
  %(prog)s --jql "project=PROJ AND sprint=456" --time 15m --comment "Daily standup"
  %(prog)s --issues PROJ-1,PROJ-2 --time 1h --dry-run
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--issues", "-i", help="Comma-separated list of issue keys")
    parser.add_argument("--jql", "-j", help="JQL query to find issues")
    parser.add_argument(
        "--time", "-t", required=True, help="Time to log per issue (e.g., 30m, 1h)"
    )
    parser.add_argument("--comment", "-c", help="Comment to add to all worklogs")
    parser.add_argument("--started", "-s", help="Start time for all worklogs")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview without logging"
    )
    parser.add_argument(
        "--yes", "-y", action="store_true", help="Skip confirmation prompt"
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

    # Validate that either issues or jql is specified
    if not args.issues and not args.jql:
        parser.error("Either --issues or --jql must be specified")

    # Parse issues list
    issues = None
    if args.issues:
        issues = [k.strip() for k in args.issues.split(",")]
        for key in issues:
            validate_issue_key(key)

    try:
        # Get client
        client = get_jira_client(args.profile)

        # Perform bulk log
        result = bulk_log_time(
            client,
            issues=issues,
            jql=args.jql,
            time_spent=args.time,
            comment=args.comment,
            started=args.started,
            dry_run=args.dry_run,
        )

        # Output result
        if args.output == "json":
            print(json.dumps(result, indent=2))
        else:
            if result.get("dry_run"):
                print("Bulk Time Logging Preview (dry-run):")
                for item in result.get("preview", []):
                    print(
                        f"  {item['issue']}: +{item['time_to_log']} ({item['summary'][:40]})"
                    )
                print()
                print(
                    f"Would log {result['would_log_formatted']} total to {result['would_log_count']} issues."
                )
                print("Run without --dry-run to apply.")
            else:
                print("Bulk Time Logging Complete:")
                print(f"  Successful: {result['success_count']} issues")
                if result["failure_count"] > 0:
                    print(f"  Failed: {result['failure_count']} issues")
                    for failure in result["failures"]:
                        print(f"    - {failure['issue']}: {failure['error']}")
                print(f"  Total logged: {result['total_formatted']}")

        client.close()

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(1)


if __name__ == "__main__":
    main()
