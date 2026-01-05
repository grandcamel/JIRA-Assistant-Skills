#!/usr/bin/env python3
"""
Remove an issue type from an issue type scheme.

Removes a single issue type from a scheme.
Requires 'Administer Jira' global permission.
"""

import argparse
import sys

# Add shared lib to path
from jira_assistant_skills_lib import JiraError, get_jira_client, print_error


def remove_issue_type_from_scheme(
    scheme_id: str, issue_type_id: str, client=None, profile: str | None = None
) -> bool:
    """
    Remove an issue type from a scheme.

    Args:
        scheme_id: Scheme ID
        issue_type_id: Issue type ID to remove
        client: JiraClient instance (for testing)
        profile: Configuration profile name

    Returns:
        True if successful

    Raises:
        JiraError: On API failure

    Note:
        Cannot remove the default issue type or the last issue type.
    """
    if client is None:
        client = get_jira_client(profile=profile)

    try:
        client.remove_issue_type_from_scheme(
            scheme_id=scheme_id, issue_type_id=issue_type_id
        )
        return True
    finally:
        if client:
            client.close()


def main(argv: list[str] | None = None):
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Remove an issue type from an issue type scheme",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Remove issue type from scheme
  python remove_issue_type_from_scheme.py --scheme-id 10001 --issue-type-id 10003

  # Force without confirmation
  python remove_issue_type_from_scheme.py --scheme-id 10001 --issue-type-id 10003 --force

  # Use specific profile
  python remove_issue_type_from_scheme.py --scheme-id 10001 --issue-type-id 10003 --profile production

Note:
  Requires 'Administer Jira' global permission.
  Cannot remove the default issue type from the scheme.
  Cannot remove the last issue type from the scheme.
""",
    )

    parser.add_argument("--scheme-id", required=True, help="Issue type scheme ID")
    parser.add_argument(
        "--issue-type-id", required=True, help="Issue type ID to remove"
    )
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--profile", help="Configuration profile to use")

    args = parser.parse_args(argv)

    try:
        # Confirmation prompt
        if not args.force:
            confirm = input(
                f"Remove issue type {args.issue_type_id} from scheme {args.scheme_id}? [y/N]: "
            )
            if confirm.lower() != "y":
                print("Removal cancelled.")
                return

        remove_issue_type_from_scheme(
            scheme_id=args.scheme_id,
            issue_type_id=args.issue_type_id,
            profile=args.profile,
        )

        print(f"Issue type {args.issue_type_id} removed from scheme {args.scheme_id}.")

    except JiraError as e:
        print_error(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
