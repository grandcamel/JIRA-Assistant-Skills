#!/usr/bin/env python3
"""
Send notification about a JIRA issue.

Usage:
    python send_notification.py PROJ-123 --watchers
    python send_notification.py PROJ-123 --assignee --reporter --subject "Action Required"
    python send_notification.py PROJ-123 --user accountId1 --group developers
"""

import argparse
import sys
from typing import Any

from jira_assistant_skills_lib import (
    JiraError,
    get_jira_client,
    print_error,
    validate_issue_key,
)


def send_notification(
    issue_key: str,
    subject: str | None = None,
    body: str | None = None,
    watchers: bool = False,
    assignee: bool = False,
    reporter: bool = False,
    voters: bool = False,
    users: list[str] | None = None,
    groups: list[str] | None = None,
) -> None:
    """
    Send notification about an issue.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        subject: Notification subject
        body: Notification body
        watchers: Notify watchers
        assignee: Notify assignee
        reporter: Notify reporter
        voters: Notify voters
        users: List of account IDs to notify
        groups: List of group names to notify

    Raises:
        JiraError or subclass on failure
    """
    issue_key = validate_issue_key(issue_key)

    # Build recipients dict
    to = {
        "reporter": reporter,
        "assignee": assignee,
        "watchers": watchers,
        "voters": voters,
        "users": [],
        "groups": [],
    }

    if users:
        to["users"] = [{"accountId": user_id} for user_id in users]

    if groups:
        to["groups"] = [{"name": group_name} for group_name in groups]

    client = get_jira_client()
    client.notify_issue(issue_key, subject=subject, text_body=body, to=to)
    client.close()


def notify_dry_run(
    issue_key: str,
    subject: str | None = None,
    body: str | None = None,
    watchers: bool = False,
    assignee: bool = False,
    reporter: bool = False,
    voters: bool = False,
    users: list[str] | None = None,
    groups: list[str] | None = None,
) -> dict[str, Any]:
    """
    Show notification details without sending.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        subject: Notification subject
        body: Notification body
        watchers: Notify watchers
        assignee: Notify assignee
        reporter: Notify reporter
        voters: Notify voters
        users: List of account IDs to notify
        groups: List of group names to notify

    Returns:
        Notification details
    """
    issue_key = validate_issue_key(issue_key)

    return {
        "issue_key": issue_key,
        "subject": subject,
        "body": body,
        "recipients": {
            "reporter": reporter,
            "assignee": assignee,
            "watchers": watchers,
            "voters": voters,
            "users": users or [],
            "groups": groups or [],
        },
    }


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Send notification about a JIRA issue",
        epilog="""
Examples:
  %(prog)s PROJ-123 --watchers
  %(prog)s PROJ-123 --assignee --reporter --subject "Please review"
  %(prog)s PROJ-123 --user 5b10a2844c20165700ede21g --group developers
  %(prog)s PROJ-123 --watchers --dry-run
        """,
    )

    parser.add_argument("issue_key", help="Issue key (e.g., PROJ-123)")
    parser.add_argument(
        "--subject", "-s", help='Notification subject (default: "Issue Update")'
    )
    parser.add_argument("--body", "-b", help="Notification body")
    parser.add_argument("--watchers", action="store_true", help="Notify all watchers")
    parser.add_argument("--assignee", action="store_true", help="Notify assignee")
    parser.add_argument("--reporter", action="store_true", help="Notify reporter")
    parser.add_argument("--voters", action="store_true", help="Notify voters")
    parser.add_argument(
        "--user",
        action="append",
        dest="users",
        help="Notify specific user by account ID (can be repeated)",
    )
    parser.add_argument(
        "--group",
        action="append",
        dest="groups",
        help="Notify group by name (can be repeated)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be sent without sending"
    )

    args = parser.parse_args(argv)

    # Check if at least one recipient is specified
    if not any(
        [
            args.watchers,
            args.assignee,
            args.reporter,
            args.voters,
            args.users,
            args.groups,
        ]
    ):
        print_error(
            "Error: Must specify at least one recipient (--watchers, --assignee, --reporter, --voters, --user, or --group)"
        )
        sys.exit(1)

    # Set defaults
    subject = args.subject or f"Issue Update: {args.issue_key}"
    body = args.body or "This is a notification about this issue."

    try:
        if args.dry_run:
            # Dry run mode
            details = notify_dry_run(
                args.issue_key,
                subject=subject,
                body=body,
                watchers=args.watchers,
                assignee=args.assignee,
                reporter=args.reporter,
                voters=args.voters,
                users=args.users,
                groups=args.groups,
            )

            print(f"[DRY RUN] Would send notification for {args.issue_key}:\n")
            print(f"Subject: {details['subject']}")
            print(f"Body: {details['body']}\n")
            print("Recipients:")

            recipients = details["recipients"]
            if recipients["watchers"]:
                print("  - Watchers")
            if recipients["assignee"]:
                print("  - Assignee")
            if recipients["reporter"]:
                print("  - Reporter")
            if recipients["voters"]:
                print("  - Voters")
            if recipients["users"]:
                print(f"  - {len(recipients['users'])} specific user(s)")
            if recipients["groups"]:
                for group in recipients["groups"]:
                    print(f"  - Group: {group}")

            print("\nNo notification sent (dry-run mode).")

        else:
            # Send notification
            send_notification(
                args.issue_key,
                subject=subject,
                body=body,
                watchers=args.watchers,
                assignee=args.assignee,
                reporter=args.reporter,
                voters=args.voters,
                users=args.users,
                groups=args.groups,
            )

            print(f"Notification sent for {args.issue_key}:\n")
            print(f"Subject: {subject}")
            print(f"Body: {body}\n")
            print("Recipients:")
            if args.watchers:
                print("  - Watchers")
            if args.assignee:
                print("  - Assignee")
            if args.reporter:
                print("  - Reporter")
            if args.voters:
                print("  - Voters")
            if args.users:
                print(f"  - {len(args.users)} specific user(s)")
            if args.groups:
                for group in args.groups:
                    print(f"  - Group: {group}")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
