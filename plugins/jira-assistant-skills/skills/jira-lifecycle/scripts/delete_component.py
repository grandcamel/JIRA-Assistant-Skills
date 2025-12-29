#!/usr/bin/env python3
"""
Delete a project component in JIRA.

Usage:
    python delete_component.py --id 10000
    python delete_component.py --id 10000 --yes
    python delete_component.py --id 10000 --move-to 10001
    python delete_component.py --id 10000 --dry-run
"""

import sys
import argparse
from pathlib import Path
from typing import Optional, Dict, Any


from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError
from jira_assistant_skills_lib import print_success


def delete_component(component_id: str, move_issues_to: str = None,
                    profile: str = None) -> None:
    """
    Delete a component.

    Args:
        component_id: Component ID to delete
        move_issues_to: Optional component ID to move issues to
        profile: JIRA profile to use
    """
    client = get_jira_client(profile)

    kwargs = {}
    if move_issues_to:
        kwargs['moveIssuesTo'] = move_issues_to

    client.delete_component(component_id, **kwargs)
    client.close()


def delete_component_with_confirmation(component_id: str, move_issues_to: str = None,
                                       profile: str = None) -> bool:
    """
    Delete a component with confirmation prompt.

    Args:
        component_id: Component ID to delete
        move_issues_to: Optional component ID to move issues to
        profile: JIRA profile to use

    Returns:
        True if deleted, False if cancelled
    """
    # Get component details first
    client = get_jira_client(profile)
    component = client.get_component(component_id)

    # Show component preview
    name = component.get('name', 'Unknown')
    description = component.get('description', '')

    print(f"Delete component {component_id}?")
    print(f"\n  Name: {name}")
    if description:
        print(f"  Description: {description}")
    if move_issues_to:
        print(f"  Move issues to component: {move_issues_to}")
    print()

    confirmation = input("Type 'yes' to confirm: ")

    if confirmation.lower() == 'yes':
        kwargs = {}
        if move_issues_to:
            kwargs['moveIssuesTo'] = move_issues_to

        client.delete_component(component_id, **kwargs)
        client.close()
        return True
    else:
        client.close()
        return False


def delete_component_dry_run(component_id: str, profile: str = None) -> Dict[str, Any]:
    """
    Show what component would be deleted without deleting.

    Args:
        component_id: Component ID
        profile: JIRA profile to use

    Returns:
        Component data that would be deleted
    """
    client = get_jira_client(profile)
    component = client.get_component(component_id)
    client.close()

    return component


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Delete a project component in JIRA',
        epilog='''
Examples:
  %(prog)s --id 10000                    # Delete with confirmation
  %(prog)s --id 10000 --yes              # Skip confirmation
  %(prog)s --id 10000 --move-to 10001    # Move issues before deletion
  %(prog)s --id 10000 --dry-run          # Show what would be deleted
        '''
    )

    parser.add_argument('--id',
                       required=True,
                       help='Component ID to delete')
    parser.add_argument('--move-to',
                       help='Component ID to move issues to before deletion')
    parser.add_argument('--yes', '-y', action='store_true',
                       help='Skip confirmation prompt')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be deleted without deleting')
    parser.add_argument('--profile', '-p',
                       help='JIRA profile to use')

    args = parser.parse_args()

    try:
        if args.dry_run:
            # Dry run mode
            component = delete_component_dry_run(args.id, args.profile)

            print(f"[DRY RUN] Would delete component {args.id}:\n")
            print(f"  Name: {component['name']}")
            if component.get('description'):
                print(f"  Description: {component['description']}")
            if args.move_to:
                print(f"  Move issues to: {args.move_to}")
            print("\nNo component deleted (dry-run mode).")

        elif args.yes:
            # Delete without confirmation
            delete_component(args.id, args.move_to, args.profile)
            print_success(f"Deleted component {args.id}")

        else:
            # Delete with confirmation
            deleted = delete_component_with_confirmation(
                args.id,
                args.move_to,
                args.profile
            )

            if deleted:
                print_success(f"\nDeleted component {args.id}")
            else:
                print("\nDeletion cancelled.")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
