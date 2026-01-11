#!/usr/bin/env python3
"""
Add issue types to an issue type scheme.

Adds one or more issue types to an existing scheme.
Requires 'Administer Jira' global permission.
"""

import argparse
import sys

# Add shared lib to path
from jira_assistant_skills_lib import (
    JiraError,
    ValidationError,
    get_jira_client,
    print_error,
)


def add_issue_types_to_scheme(
    scheme_id: str,
    issue_type_ids: list[str],
    client=None,
) -> bool:
    """
    Add issue types to a scheme.

    Args:
        scheme_id: Scheme ID
        issue_type_ids: List of issue type IDs to add
        client: JiraClient instance (for testing)

    Returns:
        True if successful

    Raises:
        ValidationError: If issue_type_ids is empty
        JiraError: On API failure
    """
    if not issue_type_ids:
        raise ValidationError("At least one issue type ID is required")

    if client is None:
        client = get_jira_client()

    try:
        client.add_issue_types_to_scheme(
            scheme_id=scheme_id, issue_type_ids=issue_type_ids
        )
        return True
    finally:
        if client:
            client.close()


def main(argv: list[str] | None = None):
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Add issue types to an issue type scheme",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add single issue type
  python add_issue_types_to_scheme.py --scheme-id 10001 --issue-type-ids 10003

  # Add multiple issue types
  python add_issue_types_to_scheme.py --scheme-id 10001 --issue-type-ids 10003 10004 10005

  # Use specific profile
  python add_issue_types_to_scheme.py --scheme-id 10001 --issue-type-ids 10003

Note:
  Requires 'Administer Jira' global permission.
  Issue types must not already be in the scheme.
""",
    )

    parser.add_argument("--scheme-id", required=True, help="Issue type scheme ID")
    parser.add_argument(
        "--issue-type-ids", nargs="+", required=True, help="Issue type IDs to add"
    )

    args = parser.parse_args(argv)

    try:
        add_issue_types_to_scheme(
            scheme_id=args.scheme_id,
            issue_type_ids=args.issue_type_ids,
        )

        print(
            f"Added {len(args.issue_type_ids)} issue type(s) to scheme {args.scheme_id}."
        )

    except (ValidationError, JiraError) as e:
        print_error(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
