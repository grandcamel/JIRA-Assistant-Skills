#!/usr/bin/env python3
"""
Add a user to a JIRA group.

Supports:
- Adding by account ID or email lookup
- Group by name or group ID
- Dry-run mode for preview
- Idempotent operation (adding already member succeeds)
"""

import argparse
import json
import sys
from typing import Any

# Add shared lib to path
from jira_assistant_skills_lib import (
    JiraError,
    NotFoundError,
    get_jira_client,
    print_error,
)


def add_user_to_group(
    client,
    account_id: str,
    group_name: str | None = None,
    group_id: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any] | None:
    """
    Add a user to a group.

    Args:
        client: JiraClient instance
        account_id: User's account ID
        group_name: Group name
        group_id: Group ID (preferred for GDPR compliance)
        dry_run: If True, preview only without adding

    Returns:
        Group object if successful, None for dry-run
    """
    if dry_run:
        return None

    return client.add_user_to_group(
        account_id=account_id, group_name=group_name, group_id=group_id
    )


def add_user_by_email(
    client,
    email: str,
    group_name: str | None = None,
    group_id: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any] | None:
    """
    Add a user to a group by email lookup.

    Args:
        client: JiraClient instance
        email: User's email address
        group_name: Group name
        group_id: Group ID (preferred for GDPR compliance)
        dry_run: If True, preview only without adding

    Returns:
        Group object if successful, None for dry-run

    Raises:
        NotFoundError: If user with email not found
    """
    # Look up user by email
    users = client.search_users(query=email, max_results=10)

    # Find exact email match
    matched_user = None
    for user in users:
        if user.get("emailAddress", "").lower() == email.lower():
            matched_user = user
            break

    if not matched_user:
        raise NotFoundError("User", f"with email {email}")

    return add_user_to_group(
        client,
        account_id=matched_user["accountId"],
        group_name=group_name,
        group_id=group_id,
        dry_run=dry_run,
    )


def format_dry_run_preview(
    account_id: str | None = None,
    email: str | None = None,
    group_name: str | None = None,
    group_id: str | None = None,
) -> str:
    """
    Format dry-run preview message.

    Args:
        account_id: User's account ID
        email: User's email
        group_name: Group name
        group_id: Group ID

    Returns:
        Preview message
    """
    lines = []
    lines.append("DRY RUN - Preview of adding user to group:")
    lines.append("=" * 50)
    if account_id:
        lines.append(f"Account ID:  {account_id}")
    if email:
        lines.append(f"Email:       {email}")
    if group_name:
        lines.append(f"Group Name:  {group_name}")
    if group_id:
        lines.append(f"Group ID:    {group_id}")
    lines.append("")
    lines.append("This is a dry run. No changes will be made.")
    lines.append("Remove --dry-run to add the user to the group.")
    return "\n".join(lines)


def format_success_message(
    account_id: str, group_name: str | None = None, group_id: str | None = None
) -> str:
    """
    Format success message.

    Args:
        account_id: User's account ID
        group_name: Group name
        group_id: Group ID

    Returns:
        Success message
    """
    group_identifier = group_name or group_id
    return f"User '{account_id}' added to group '{group_identifier}' successfully."


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Add a user to a JIRA group",
        epilog="""
Examples:
  %(prog)s john@example.com --group "jira-developers"
  %(prog)s --account-id 5b10ac8d82e05b22cc7d4ef5 --group "jira-developers"
  %(prog)s john@example.com --group-id abc123
  %(prog)s john@example.com --group "mobile-team" --dry-run
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # User identification
    parser.add_argument("email", nargs="?", help="User email address")
    parser.add_argument(
        "--account-id", "-a", help="User account ID (alternative to email)"
    )

    # Group identification
    parser.add_argument("--group", "-g", dest="group_name", help="Group name")
    parser.add_argument("--group-id", "-i", help="Group ID (alternative to name)")

    # Options
    parser.add_argument(
        "--dry-run", "-n", action="store_true", help="Preview without adding"
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument("--profile", help="JIRA profile to use")

    args = parser.parse_args(argv)

    # Validate user identification
    if not args.email and not args.account_id:
        parser.error("Either email or --account-id is required")

    # Validate group identification
    if not args.group_name and not args.group_id:
        parser.error("Either --group or --group-id is required")

    try:
        # Dry run mode
        if args.dry_run:
            print(
                format_dry_run_preview(
                    account_id=args.account_id,
                    email=args.email,
                    group_name=args.group_name,
                    group_id=args.group_id,
                )
            )
            sys.exit(0)

        client = get_jira_client(args.profile)

        # Add user to group
        if args.account_id:
            result = add_user_to_group(
                client,
                account_id=args.account_id,
                group_name=args.group_name,
                group_id=args.group_id,
            )
            account_id = args.account_id
        else:
            result = add_user_by_email(
                client,
                email=args.email,
                group_name=args.group_name,
                group_id=args.group_id,
            )
            # Look up the account ID for the message
            users = client.search_users(query=args.email, max_results=10)
            account_id = next(
                (
                    u["accountId"]
                    for u in users
                    if u.get("emailAddress", "").lower() == args.email.lower()
                ),
                args.email,
            )

        # Output
        if args.output == "json":
            print(json.dumps(result, indent=2))
        else:
            print(
                format_success_message(
                    account_id=account_id,
                    group_name=args.group_name,
                    group_id=args.group_id,
                )
            )

        client.close()

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
