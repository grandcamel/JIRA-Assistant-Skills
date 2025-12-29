#!/usr/bin/env python3
"""
Reorder issue types within an issue type scheme.

Moves an issue type to a new position within the scheme.
Requires 'Administer Jira' global permission.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Add shared lib to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import JiraError, print_error


def reorder_issue_types_in_scheme(
    scheme_id: str,
    issue_type_id: str,
    after: Optional[str] = None,
    client=None,
    profile: str = None
) -> bool:
    """
    Reorder issue types in a scheme.

    Args:
        scheme_id: Scheme ID
        issue_type_id: Issue type ID to move
        after: Issue type ID to position after (None = move to first)
        client: JiraClient instance (for testing)
        profile: Configuration profile name

    Returns:
        True if successful

    Raises:
        JiraError: On API failure
    """
    if client is None:
        client = get_jira_client(profile=profile)

    try:
        client.reorder_issue_types_in_scheme(
            scheme_id=scheme_id,
            issue_type_id=issue_type_id,
            after=after
        )
        return True
    finally:
        if client:
            client.close()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Reorder issue types within an issue type scheme',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Move issue type to first position
  python reorder_issue_types_in_scheme.py --scheme-id 10001 --issue-type-id 10003

  # Move issue type after another
  python reorder_issue_types_in_scheme.py --scheme-id 10001 --issue-type-id 10003 --after 10001

  # Use specific profile
  python reorder_issue_types_in_scheme.py --scheme-id 10001 --issue-type-id 10003 --profile production

Note:
  Requires 'Administer Jira' global permission.
  Omitting --after moves the issue type to the first position.
"""
    )

    parser.add_argument(
        '--scheme-id',
        required=True,
        help='Issue type scheme ID'
    )
    parser.add_argument(
        '--issue-type-id',
        required=True,
        help='Issue type ID to move'
    )
    parser.add_argument(
        '--after',
        help='Issue type ID to position after (omit for first position)'
    )
    parser.add_argument(
        '--profile',
        help='Configuration profile to use'
    )

    args = parser.parse_args()

    try:
        reorder_issue_types_in_scheme(
            scheme_id=args.scheme_id,
            issue_type_id=args.issue_type_id,
            after=args.after,
            profile=args.profile
        )

        if args.after:
            print(f"Issue type {args.issue_type_id} moved after {args.after} in scheme {args.scheme_id}.")
        else:
            print(f"Issue type {args.issue_type_id} moved to first position in scheme {args.scheme_id}.")

    except JiraError as e:
        print_error(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
