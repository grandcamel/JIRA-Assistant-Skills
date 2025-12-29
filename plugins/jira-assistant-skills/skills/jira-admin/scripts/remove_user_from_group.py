#!/usr/bin/env python3
"""
Remove a user from a JIRA group.

Supports:
- Removing by account ID or email lookup
- Group by name or group ID
- Confirmation requirement for safety
- Dry-run mode for preview
- Idempotent operation (removing non-member succeeds)
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Add shared lib to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError, ValidationError, NotFoundError


def remove_user_from_group(client, account_id: str,
                           group_name: Optional[str] = None,
                           group_id: Optional[str] = None,
                           confirmed: bool = False,
                           dry_run: bool = False) -> None:
    """
    Remove a user from a group.

    Args:
        client: JiraClient instance
        account_id: User's account ID
        group_name: Group name
        group_id: Group ID (preferred for GDPR compliance)
        confirmed: Must be True to proceed with removal
        dry_run: If True, preview only without removing

    Raises:
        ValidationError: If not confirmed
    """
    if dry_run:
        return

    if not confirmed:
        raise ValidationError(
            "Removing user from group requires confirmation. "
            "Use --confirm to proceed or --dry-run to preview."
        )

    client.remove_user_from_group(
        account_id=account_id,
        group_name=group_name,
        group_id=group_id
    )


def remove_user_by_email(client, email: str,
                         group_name: Optional[str] = None,
                         group_id: Optional[str] = None,
                         confirmed: bool = False,
                         dry_run: bool = False) -> str:
    """
    Remove a user from a group by email lookup.

    Args:
        client: JiraClient instance
        email: User's email address
        group_name: Group name
        group_id: Group ID (preferred for GDPR compliance)
        confirmed: Must be True to proceed
        dry_run: If True, preview only without removing

    Returns:
        The account ID of the removed user

    Raises:
        NotFoundError: If user with email not found
        ValidationError: If not confirmed
    """
    # Look up user by email
    users = client.search_users(query=email, max_results=10)

    # Find exact email match
    matched_user = None
    for user in users:
        if user.get('emailAddress', '').lower() == email.lower():
            matched_user = user
            break

    if not matched_user:
        raise NotFoundError("User", f"with email {email}")

    remove_user_from_group(
        client,
        account_id=matched_user['accountId'],
        group_name=group_name,
        group_id=group_id,
        confirmed=confirmed,
        dry_run=dry_run
    )

    return matched_user['accountId']


def format_dry_run_preview(account_id: Optional[str] = None,
                           email: Optional[str] = None,
                           group_name: Optional[str] = None,
                           group_id: Optional[str] = None) -> str:
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
    lines.append("DRY RUN - Preview of removing user from group:")
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
    lines.append("Remove --dry-run and add --confirm to remove the user from the group.")
    return '\n'.join(lines)


def format_success_message(account_id: str, group_name: Optional[str] = None,
                           group_id: Optional[str] = None) -> str:
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
    return f"User '{account_id}' removed from group '{group_identifier}' successfully."


def main():
    parser = argparse.ArgumentParser(
        description='Remove a user from a JIRA group',
        epilog='''
Examples:
  %(prog)s john@example.com --group "jira-developers" --confirm
  %(prog)s --account-id 5b10ac8d82e05b22cc7d4ef5 --group "jira-developers" --confirm
  %(prog)s john@example.com --group-id abc123 --confirm
  %(prog)s john@example.com --group "mobile-team" --dry-run
''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # User identification
    parser.add_argument('email', nargs='?', help='User email address')
    parser.add_argument('--account-id', '-a', help='User account ID (alternative to email)')

    # Group identification
    parser.add_argument('--group', '-g', dest='group_name', help='Group name')
    parser.add_argument('--group-id', '-i', help='Group ID (alternative to name)')

    # Options
    parser.add_argument('--confirm', '-y', action='store_true',
                        help='Confirm removal (required)')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='Preview without removing')
    parser.add_argument('--profile', help='JIRA profile to use')

    args = parser.parse_args()

    # Validate user identification
    if not args.email and not args.account_id:
        parser.error('Either email or --account-id is required')

    # Validate group identification
    if not args.group_name and not args.group_id:
        parser.error('Either --group or --group-id is required')

    try:
        # Dry run mode
        if args.dry_run:
            print(format_dry_run_preview(
                account_id=args.account_id,
                email=args.email,
                group_name=args.group_name,
                group_id=args.group_id
            ))
            sys.exit(0)

        # Require confirmation
        if not args.confirm:
            print("Error: Removing user from group requires confirmation.", file=sys.stderr)
            print("Use --confirm to proceed or --dry-run to preview.", file=sys.stderr)
            sys.exit(1)

        client = get_jira_client(args.profile)

        # Remove user from group
        if args.account_id:
            remove_user_from_group(
                client,
                account_id=args.account_id,
                group_name=args.group_name,
                group_id=args.group_id,
                confirmed=args.confirm
            )
            account_id = args.account_id
        else:
            account_id = remove_user_by_email(
                client,
                email=args.email,
                group_name=args.group_name,
                group_id=args.group_id,
                confirmed=args.confirm
            )

        # Output
        print(format_success_message(
            account_id=account_id,
            group_name=args.group_name,
            group_id=args.group_id
        ))

        client.close()

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
