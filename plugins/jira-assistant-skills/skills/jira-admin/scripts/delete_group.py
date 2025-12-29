#!/usr/bin/env python3
"""
Delete a JIRA group.

Supports:
- Deleting by group name or group ID
- Confirmation requirement for safety
- Dry-run mode for preview
- System group protection
- Swap group for reassigning issues
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Add shared lib to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError, ValidationError


# Protected system groups that should not be deleted
SYSTEM_GROUPS = [
    'jira-administrators',
    'jira-users',
    'jira-software-users',
    'site-admins',
    'atlassian-addons-admin'
]


def check_system_group_protection(group_name: str) -> None:
    """
    Check if a group is a protected system group.

    Args:
        group_name: Group name to check

    Raises:
        ValidationError: If the group is a protected system group
    """
    if group_name.lower() in [g.lower() for g in SYSTEM_GROUPS]:
        raise ValidationError(
            f"Cannot delete protected system group '{group_name}'. "
            "System groups are required for JIRA to function properly."
        )


def format_dry_run_preview(group_name: str, group_id: Optional[str] = None,
                           swap_group: Optional[str] = None) -> str:
    """
    Format dry-run preview message.

    Args:
        group_name: Group name to delete
        group_id: Group ID (if specified)
        swap_group: Group to reassign issues to

    Returns:
        Preview message
    """
    lines = []
    lines.append("DRY RUN - Preview of group deletion:")
    lines.append("=" * 50)
    if group_name:
        lines.append(f"Group Name: {group_name}")
    if group_id:
        lines.append(f"Group ID:   {group_id}")
    if swap_group:
        lines.append(f"Swap Group: {swap_group} (issues will be reassigned)")
    lines.append("")
    lines.append("This is a dry run. No group will be deleted.")
    lines.append("Remove --dry-run and add --confirm to delete the group.")
    return '\n'.join(lines)


def delete_group(client, group_name: Optional[str] = None,
                 group_id: Optional[str] = None,
                 swap_group: Optional[str] = None,
                 swap_group_id: Optional[str] = None,
                 confirmed: bool = False,
                 dry_run: bool = False) -> None:
    """
    Delete a group.

    Args:
        client: JiraClient instance
        group_name: Group name to delete
        group_id: Group ID to delete
        swap_group: Group name to reassign issues to
        swap_group_id: Group ID to reassign issues to
        confirmed: Must be True to proceed with deletion
        dry_run: If True, preview only without deleting

    Raises:
        ValidationError: If not confirmed or if group is protected
    """
    # Check for system group protection
    if group_name:
        check_system_group_protection(group_name)

    # Dry run mode - just return
    if dry_run:
        return

    # Require confirmation
    if not confirmed:
        raise ValidationError(
            "Group deletion requires confirmation. "
            "Use --confirm to proceed or --dry-run to preview."
        )

    # Delete the group
    client.delete_group(
        group_name=group_name,
        group_id=group_id,
        swap_group=swap_group,
        swap_group_id=swap_group_id
    )


def main():
    parser = argparse.ArgumentParser(
        description='Delete a JIRA group',
        epilog='''
Examples:
  %(prog)s "old-team" --confirm           # Delete with confirmation
  %(prog)s "old-team" --dry-run           # Preview only
  %(prog)s --group-id abc123 --confirm    # Delete by group ID
  %(prog)s "old-team" --swap "new-team" --confirm  # Reassign issues
''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('group_name', nargs='?', help='Group name to delete')
    parser.add_argument('--group-id', '-i', help='Group ID to delete (alternative to name)')
    parser.add_argument('--swap', metavar='GROUP',
                        help='Group to reassign issues to')
    parser.add_argument('--swap-id', metavar='GROUP_ID',
                        help='Group ID to reassign issues to')
    parser.add_argument('--confirm', '-y', action='store_true',
                        help='Confirm deletion (required)')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='Preview without deleting')
    parser.add_argument('--profile', help='JIRA profile to use')

    args = parser.parse_args()

    # Require either group name or group ID
    if not args.group_name and not args.group_id:
        parser.error('Either group_name or --group-id is required')

    try:
        # Check system group protection first
        if args.group_name:
            check_system_group_protection(args.group_name)

        # Dry run mode
        if args.dry_run:
            print(format_dry_run_preview(
                group_name=args.group_name,
                group_id=args.group_id,
                swap_group=args.swap
            ))
            sys.exit(0)

        # Require confirmation
        if not args.confirm:
            print("Error: Group deletion requires confirmation.", file=sys.stderr)
            print("Use --confirm to proceed or --dry-run to preview.", file=sys.stderr)
            sys.exit(1)

        client = get_jira_client(args.profile)

        # Delete group
        delete_group(
            client,
            group_name=args.group_name,
            group_id=args.group_id,
            swap_group=args.swap,
            swap_group_id=args.swap_id,
            confirmed=args.confirm,
            dry_run=args.dry_run
        )

        group_identifier = args.group_name or args.group_id
        print(f"Group '{group_identifier}' deleted successfully.")

        if args.swap:
            print(f"Issues have been reassigned to '{args.swap}'.")

        client.close()

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
