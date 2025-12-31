#!/usr/bin/env python3
"""
Delete a comment from a JIRA issue.

Usage:
    python delete_comment.py PROJ-123 --id 10001
    python delete_comment.py PROJ-123 --id 10001 --yes
    python delete_comment.py PROJ-123 --id 10001 --dry-run
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, Any, Optional


from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError
from jira_assistant_skills_lib import validate_issue_key
from jira_assistant_skills_lib import adf_to_text


def delete_comment(issue_key: str, comment_id: str, profile: str = None) -> None:
    """
    Delete a comment.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        comment_id: Comment ID to delete
        profile: JIRA profile to use

    Raises:
        JiraError or subclass on failure
    """
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client(profile)
    client.delete_comment(issue_key, comment_id)
    client.close()


def delete_comment_with_confirm(issue_key: str, comment_id: str, profile: str = None) -> bool:
    """
    Delete a comment with confirmation prompt.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        comment_id: Comment ID to delete
        profile: JIRA profile to use

    Returns:
        True if deleted, False if cancelled
    """
    issue_key = validate_issue_key(issue_key)

    # Get comment details first
    client = get_jira_client(profile)
    comment = client.get_comment(issue_key, comment_id)

    # Show comment preview
    author = comment.get('author', {}).get('displayName', 'Unknown')
    created = comment.get('created', 'N/A')[:16]
    body = comment.get('body', {})
    body_text = adf_to_text(body)

    # Limit body preview
    if len(body_text) > 100:
        body_preview = body_text[:100] + '...'
    else:
        body_preview = body_text

    print(f"Delete comment {comment_id} from {issue_key}?\n")
    print("Comment preview:")
    print(f"  Author: {author}")
    print(f"  Date: {created}")
    print(f"  Body: {body_preview}")
    print()

    confirmation = input("Type 'yes' to confirm: ")

    if confirmation.lower() == 'yes':
        client.delete_comment(issue_key, comment_id)
        client.close()
        return True
    else:
        client.close()
        return False


def delete_comment_dry_run(issue_key: str, comment_id: str, profile: str = None) -> Dict[str, Any]:
    """
    Show what would be deleted without actually deleting.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        comment_id: Comment ID
        profile: JIRA profile to use

    Returns:
        Comment data that would be deleted
    """
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client(profile)
    comment = client.get_comment(issue_key, comment_id)
    client.close()

    return comment


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Delete a comment from a JIRA issue',
        epilog='''
Examples:
  %(prog)s PROJ-123 --id 10001              # Delete with confirmation
  %(prog)s PROJ-123 --id 10001 --yes        # Skip confirmation
  %(prog)s PROJ-123 --id 10001 --dry-run    # Show what would be deleted
        '''
    )

    parser.add_argument('issue_key',
                       help='Issue key (e.g., PROJ-123)')
    parser.add_argument('--id', required=True,
                       help='Comment ID to delete')
    parser.add_argument('--yes', '-y', action='store_true',
                       help='Skip confirmation prompt')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be deleted without deleting')
    parser.add_argument('--profile', '-p',
                       help='JIRA profile to use')

    args = parser.parse_args(argv)

    try:
        if args.dry_run:
            # Dry run mode
            comment = delete_comment_dry_run(args.issue_key, args.id, args.profile)

            author = comment.get('author', {}).get('displayName', 'Unknown')
            created = comment.get('created', 'N/A')[:16]
            body = comment.get('body', {})
            body_text = adf_to_text(body)

            print(f"[DRY RUN] Would delete comment {comment['id']} from {args.issue_key}:\n")
            print(f"  Author: {author}")
            print(f"  Date: {created}")
            print(f"  Body: {body_text[:200]}")
            print()
            print("No changes made (dry-run mode).")

        elif args.yes:
            # Delete without confirmation
            delete_comment(args.issue_key, args.id, args.profile)
            print(f"Comment {args.id} deleted from {args.issue_key}.")

        else:
            # Delete with confirmation
            deleted = delete_comment_with_confirm(args.issue_key, args.id, args.profile)

            if deleted:
                print(f"\nComment {args.id} deleted from {args.issue_key}.")
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
