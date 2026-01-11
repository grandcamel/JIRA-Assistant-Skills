#!/usr/bin/env python3
"""
Add a comment to a JSM request with public/internal visibility.

This script adds comments to JSM requests using the Service Desk API,
which differs from standard JIRA comments by supporting customer portal visibility.
Public comments are visible to customers in the portal, while internal comments
are only visible to agents.
"""

import argparse
import sys

# Add shared lib to path
from jira_assistant_skills_lib import handle_errors


def get_jira_client():
    """Get JIRA client (overridable for testing)."""
    from jira_assistant_skills_lib import get_jira_client as _get_client

    return _get_client()


def format_comment_output(comment: dict, issue_key: str) -> None:
    """Format and print comment creation result."""
    comment_id = comment.get("id", "unknown")
    is_public = comment.get("public", True)
    body = comment.get("body", "")

    visibility = "Public (Customer Portal)" if is_public else "Internal (Agents Only)"

    print(f"\nAdded comment to {issue_key} (ID: {comment_id})")
    print(f"\nVisibility: {visibility}")
    print("Body:")
    for line in body.split("\n"):
        print(f"  {line}")

    if is_public:
        print("\nNote: This comment is visible to customers in the service portal.")
    else:
        print("\nNote: This comment is NOT visible to customers.")


@handle_errors
def main(args=None):
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Add comment to JSM request (public/internal)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add public (customer-visible) comment
  %(prog)s REQ-123 --body "Your issue has been resolved."

  # Add internal (agent-only) comment
  %(prog)s REQ-123 --body "Escalating to Tier 2" --internal

  # Multiline comment
  %(prog)s REQ-123 --body "Issue resolved.

Root cause: Database connection timeout.
Fix: Increased timeout to 30s."

  # From stdin
  echo "Waiting for vendor response" | %(prog)s REQ-123 --internal --body -
        """,
    )

    parser.add_argument("issue_key", help="Request key (e.g., REQ-123)")
    parser.add_argument("--body", required=True, help="Comment body (use - for stdin)")
    parser.add_argument(
        "--internal",
        action="store_true",
        help="Internal comment (agent-only, not visible to customers)",
    )

    parsed_args = parser.parse_args(args)

    # Read body from stdin if needed
    body = parsed_args.body
    if body == "-":
        body = sys.stdin.read()

    # Get JIRA client
    jira = get_jira_client()

    # Add comment with visibility flag
    public = not parsed_args.internal

    comment = jira.add_request_comment(parsed_args.issue_key, body, public=public)

    # Format and display output
    format_comment_output(comment, parsed_args.issue_key)

    return 0


if __name__ == "__main__":
    sys.exit(main())
