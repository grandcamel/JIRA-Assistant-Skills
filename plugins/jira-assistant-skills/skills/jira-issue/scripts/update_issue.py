#!/usr/bin/env python3
"""
Update a JIRA issue.

Usage:
    python update_issue.py PROJ-123 --summary "New summary"
    python update_issue.py PROJ-123 --priority High --labels "urgent,bug"
    python update_issue.py PROJ-123 --description "New description" --no-notify
"""

import argparse
import json
import sys

from jira_assistant_skills_lib import (
    JiraError,
    get_jira_client,
    markdown_to_adf,
    print_error,
    print_success,
    text_to_adf,
    validate_issue_key,
)


def update_issue(
    issue_key: str,
    summary: str | None = None,
    description: str | None = None,
    priority: str | None = None,
    assignee: str | None = None,
    labels: list | None = None,
    components: list | None = None,
    custom_fields: dict | None = None,
    notify_users: bool = True,
    profile: str | None = None,
) -> None:
    """
    Update a JIRA issue.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        summary: New summary
        description: New description (markdown supported)
        priority: New priority
        assignee: New assignee (account ID or email)
        labels: New labels (replaces existing)
        components: New components (replaces existing)
        custom_fields: Custom fields to update
        notify_users: Send notifications to watchers
        profile: JIRA profile to use
    """
    issue_key = validate_issue_key(issue_key)

    fields = {}

    if summary is not None:
        fields["summary"] = summary

    if description is not None:
        if description.strip().startswith("{"):
            fields["description"] = json.loads(description)
        elif "\n" in description or any(
            md in description for md in ["**", "*", "#", "`", "["]
        ):
            fields["description"] = markdown_to_adf(description)
        else:
            fields["description"] = text_to_adf(description)

    if priority is not None:
        fields["priority"] = {"name": priority}

    if assignee is not None:
        if assignee.lower() == "none" or assignee.lower() == "unassigned":
            fields["assignee"] = None
        elif assignee.lower() == "self":
            # Will resolve to current user's account ID
            client = get_jira_client(profile)
            account_id = client.get_current_user_id()
            fields["assignee"] = {"accountId": account_id}
            client.close()
        elif "@" in assignee:
            fields["assignee"] = {"emailAddress": assignee}
        else:
            fields["assignee"] = {"accountId": assignee}

    if labels is not None:
        fields["labels"] = labels

    if components is not None:
        fields["components"] = [{"name": comp} for comp in components]

    if custom_fields:
        fields.update(custom_fields)

    if not fields:
        raise ValueError("No fields specified for update")

    client = get_jira_client(profile)
    client.update_issue(issue_key, fields, notify_users=notify_users)
    client.close()


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Update a JIRA issue",
        epilog='Example: python update_issue.py PROJ-123 --summary "New title" --priority High',
    )

    parser.add_argument("issue_key", help="Issue key (e.g., PROJ-123)")
    parser.add_argument("--summary", "-s", help="New summary (title)")
    parser.add_argument(
        "--description", "-d", help="New description (supports markdown)"
    )
    parser.add_argument(
        "--priority", help="New priority (Highest, High, Medium, Low, Lowest)"
    )
    parser.add_argument(
        "--assignee", "-a", help='New assignee (account ID, email, "self", or "none")'
    )
    parser.add_argument(
        "--labels", "-l", help="Comma-separated labels (replaces existing)"
    )
    parser.add_argument(
        "--components", "-c", help="Comma-separated component names (replaces existing)"
    )
    parser.add_argument("--custom-fields", help="Custom fields as JSON string")
    parser.add_argument(
        "--no-notify", action="store_true", help="Do not send notifications to watchers"
    )
    parser.add_argument("--profile", help="JIRA profile to use (default: from config)")

    args = parser.parse_args(argv)

    try:
        labels = [l.strip() for l in args.labels.split(",")] if args.labels else None
        components = (
            [c.strip() for c in args.components.split(",")] if args.components else None
        )
        custom_fields = json.loads(args.custom_fields) if args.custom_fields else None

        update_issue(
            issue_key=args.issue_key,
            summary=args.summary,
            description=args.description,
            priority=args.priority,
            assignee=args.assignee,
            labels=labels,
            components=components,
            custom_fields=custom_fields,
            notify_users=not args.no_notify,
            profile=args.profile,
        )

        print_success(f"Updated issue: {args.issue_key}")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
