#!/usr/bin/env python3
"""
Update an existing comment on a JIRA issue.

Usage:
    python update_comment.py PROJ-123 --id 10001 --body "Updated text"
    python update_comment.py PROJ-123 --id 10001 --body "## Updated heading" --format markdown
"""

import argparse
import json
import sys
from typing import Any

from jira_assistant_skills_lib import (
    JiraError,
    adf_to_text,
    get_jira_client,
    markdown_to_adf,
    print_error,
    text_to_adf,
    validate_issue_key,
)


def update_comment(
    issue_key: str,
    comment_id: str,
    body: str,
    format_type: str = "text",
) -> dict[str, Any]:
    """
    Update an existing comment.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        comment_id: Comment ID to update
        body: New comment body
        format_type: Format ('text', 'markdown', or 'adf')

    Returns:
        Updated comment data
    """
    issue_key = validate_issue_key(issue_key)

    # Convert body to ADF format
    if format_type == "adf":
        comment_body = json.loads(body)
    elif format_type == "markdown":
        comment_body = markdown_to_adf(body)
    else:
        comment_body = text_to_adf(body)

    client = get_jira_client()
    result = client.update_comment(issue_key, comment_id, comment_body)
    client.close()

    return result


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Update an existing comment on a JIRA issue",
        epilog="""
Examples:
  %(prog)s PROJ-123 --id 10001 --body "Updated comment text"
  %(prog)s PROJ-123 --id 10001 --body "## New heading\n**Bold**" --format markdown
  %(prog)s PROJ-123 --id 10001 --body '{"type":"doc",...}' --format adf
        """,
    )

    parser.add_argument("issue_key", help="Issue key (e.g., PROJ-123)")
    parser.add_argument("--id", required=True, help="Comment ID to update")
    parser.add_argument("--body", "-b", required=True, help="New comment body")
    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "markdown", "adf"],
        default="text",
        help="Body format (default: text)",
    )

    args = parser.parse_args(argv)

    try:
        result = update_comment(
            issue_key=args.issue_key,
            comment_id=args.id,
            body=args.body,
            format_type=args.format,
        )

        print(f"Comment {result['id']} updated on {args.issue_key}.\n")

        # Show updated body
        print("Updated body:")
        body_text = adf_to_text(result.get("body", {}))
        print(f"  {body_text}\n")

        # Show author and last modified
        author = result.get("author", {}).get("displayName", "Unknown")
        updated = result.get("updated", "N/A")[:16]
        print(f"Author: {author}")
        print(f"Last modified: {updated}")

        # Show visibility if present
        visibility = result.get("visibility")
        if visibility:
            vis_type = visibility.get("type", "")
            vis_value = visibility.get("value", "")
            print(f"Visibility: {vis_type} - {vis_value}")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
