#!/usr/bin/env python3
"""
Delete an issue type scheme from JIRA.

Deletes a non-default scheme that is not assigned to any projects.
Requires 'Administer Jira' global permission.
"""

import argparse
import sys

# Add shared lib to path
from jira_assistant_skills_lib import JiraError, get_jira_client, print_error


def delete_issue_type_scheme(
    scheme_id: str, client=None, dry_run: bool = False
) -> bool:
    """
    Delete an issue type scheme.

    Args:
        scheme_id: Scheme ID to delete
        client: JiraClient instance (for testing)
        dry_run: If True, simulate without actual deletion

    Returns:
        True if successful

    Raises:
        JiraError: On API failure (e.g., scheme in use)
    """
    if dry_run:
        return True

    if client is None:
        client = get_jira_client()

    try:
        client.delete_issue_type_scheme(scheme_id)
        return True
    finally:
        if client:
            client.close()


def main(argv: list[str] | None = None):
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Delete an issue type scheme from JIRA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Delete issue type scheme
  python delete_issue_type_scheme.py 10002

  # Dry run (simulate deletion)
  python delete_issue_type_scheme.py 10002 --dry-run

  # Force delete without confirmation
  python delete_issue_type_scheme.py 10002 --force

  # Use specific profile
  python delete_issue_type_scheme.py 10002

Note:
  Requires 'Administer Jira' global permission.
  Cannot delete the default issue type scheme.
  Cannot delete schemes assigned to projects.
""",
    )

    parser.add_argument("scheme_id", help="Issue type scheme ID to delete")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate deletion without making changes",
    )
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompt")

    args = parser.parse_args(argv)

    try:
        # Confirmation prompt
        if not args.force and not args.dry_run:
            confirm = input(
                f"Are you sure you want to delete issue type scheme {args.scheme_id}? "
                "This cannot be undone. [y/N]: "
            )
            if confirm.lower() != "y":
                print("Deletion cancelled.")
                return

        # Perform deletion
        if args.dry_run:
            print(f"[DRY RUN] Would delete issue type scheme {args.scheme_id}")
        else:
            delete_issue_type_scheme(scheme_id=args.scheme_id)
            print(f"Issue type scheme {args.scheme_id} deleted successfully.")

    except JiraError as e:
        print_error(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
