#!/usr/bin/env python3
"""
Assign issue type scheme to a project.

Associates an issue type scheme with a company-managed project.
Requires 'Administer Jira' global permission.
"""

import argparse
import sys
from pathlib import Path

# Add shared lib to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import JiraError, print_error


def assign_issue_type_scheme(
    scheme_id: str,
    project_id: str,
    client=None,
    profile: str = None,
    dry_run: bool = False
) -> bool:
    """
    Assign issue type scheme to a project.

    Args:
        scheme_id: Issue type scheme ID
        project_id: Project ID
        client: JiraClient instance (for testing)
        profile: Configuration profile name
        dry_run: If True, simulate without making changes

    Returns:
        True if successful

    Raises:
        JiraError: On API failure

    Note:
        Only works for company-managed (classic) projects.
        Will fail if project has issues using types not in the scheme.
    """
    if dry_run:
        return True

    if client is None:
        client = get_jira_client(profile=profile)

    try:
        client.assign_issue_type_scheme(
            scheme_id=scheme_id,
            project_id=project_id
        )
        return True
    finally:
        if client:
            client.close()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Assign issue type scheme to a project',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Assign scheme to project
  python assign_issue_type_scheme.py --scheme-id 10001 --project-id 10000

  # Dry run (simulate assignment)
  python assign_issue_type_scheme.py --scheme-id 10001 --project-id 10000 --dry-run

  # Force without confirmation
  python assign_issue_type_scheme.py --scheme-id 10001 --project-id 10000 --force

  # Use specific profile
  python assign_issue_type_scheme.py --scheme-id 10001 --project-id 10000 --profile production

Note:
  Requires 'Administer Jira' global permission.
  Only works for company-managed (classic) projects.
  Will fail if project has issues using types not in the new scheme.
"""
    )

    parser.add_argument(
        '--scheme-id',
        required=True,
        help='Issue type scheme ID to assign'
    )
    parser.add_argument(
        '--project-id',
        required=True,
        help='Project ID to assign the scheme to'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate assignment without making changes'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Skip confirmation prompt'
    )
    parser.add_argument(
        '--profile',
        help='Configuration profile to use'
    )

    args = parser.parse_args()

    try:
        # Confirmation prompt
        if not args.force and not args.dry_run:
            confirm = input(
                f"Assign scheme {args.scheme_id} to project {args.project_id}? "
                "This may affect existing issues. [y/N]: "
            )
            if confirm.lower() != 'y':
                print("Assignment cancelled.")
                return

        if args.dry_run:
            print(f"[DRY RUN] Would assign scheme {args.scheme_id} to project {args.project_id}")
        else:
            assign_issue_type_scheme(
                scheme_id=args.scheme_id,
                project_id=args.project_id,
                profile=args.profile
            )
            print(f"Scheme {args.scheme_id} assigned to project {args.project_id} successfully.")

    except JiraError as e:
        print_error(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
