#!/usr/bin/env python3
"""
Get comments on a JIRA issue.

Usage:
    python get_comments.py PROJ-123
    python get_comments.py PROJ-123 --id 10001
    python get_comments.py PROJ-123 --limit 10 --order asc
"""

import argparse
import json
import sys
from typing import Any

from jira_assistant_skills_lib import (
    JiraError,
    adf_to_text,
    get_jira_client,
    print_error,
    validate_issue_key,
)


def get_comments(
    issue_key: str,
    limit: int = 50,
    offset: int = 0,
    order: str = "desc",
    profile: str | None = None,
) -> dict[str, Any]:
    """
    Get all comments on an issue.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        limit: Maximum number of comments to return
        offset: Starting index for pagination
        order: Sort order ('asc' for oldest first, 'desc' for newest first)
        profile: JIRA profile to use

    Returns:
        Comments data with 'comments', 'total', 'startAt', 'maxResults'
    """
    issue_key = validate_issue_key(issue_key)

    order_by = "+created" if order == "asc" else "-created"

    client = get_jira_client(profile)
    result = client.get_comments(
        issue_key, max_results=limit, start_at=offset, order_by=order_by
    )
    client.close()

    return result


def get_comment_by_id(
    issue_key: str, comment_id: str, profile: str | None = None
) -> dict[str, Any]:
    """
    Get a specific comment by ID.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        comment_id: Comment ID
        profile: JIRA profile to use

    Returns:
        Comment data
    """
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client(profile)
    result = client.get_comment(issue_key, comment_id)
    client.close()

    return result


def format_comment_body(body: dict[str, Any], max_length: int = 50) -> str:
    """
    Extract and format comment body from ADF.

    Args:
        body: Comment body in ADF format
        max_length: Maximum length of preview

    Returns:
        Plain text preview of comment
    """
    text = adf_to_text(body)
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text


def format_comments_table(comments: list[dict[str, Any]]) -> str:
    """
    Format comments as a table.

    Args:
        comments: List of comment objects

    Returns:
        Formatted table string
    """
    from datetime import datetime

    from tabulate import tabulate

    rows = []
    for comment in comments:
        comment_id = comment.get("id", "N/A")
        author = comment.get("author", {}).get("displayName", "Unknown")
        created = comment.get("created", "")

        # Format date
        if created:
            try:
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                date_str = dt.strftime("%Y-%m-%d %H:%M")
            except:
                date_str = created[:16]
        else:
            date_str = "N/A"

        # Extract body text
        body = comment.get("body", {})
        body_preview = format_comment_body(body, max_length=60)

        # Check visibility
        visibility = comment.get("visibility")
        if visibility:
            vis_type = visibility.get("type", "")
            vis_value = visibility.get("value", "")
            visibility_str = f" [{vis_type}: {vis_value}]"
            body_preview += visibility_str

        rows.append([comment_id, author, date_str, body_preview])

    headers = ["ID", "Author", "Date", "Body"]
    return tabulate(rows, headers=headers, tablefmt="simple")


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Get comments on a JIRA issue",
        epilog="""
Examples:
  %(prog)s PROJ-123                   # Get all comments
  %(prog)s PROJ-123 --id 10001        # Get specific comment
  %(prog)s PROJ-123 --limit 10        # Get first 10 comments
  %(prog)s PROJ-123 --order asc       # Oldest first
  %(prog)s PROJ-123 --output json     # JSON output
        """,
    )

    parser.add_argument("issue_key", help="Issue key (e.g., PROJ-123)")
    parser.add_argument("--id", help="Get specific comment by ID")
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of comments to return (default: 50)",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Starting index for pagination (default: 0)",
    )
    parser.add_argument(
        "--order",
        choices=["asc", "desc"],
        default="desc",
        help="Sort order: asc (oldest first) or desc (newest first, default)",
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument("--profile", "-p", help="JIRA profile to use")

    args = parser.parse_args(argv)

    try:
        if args.id:
            # Get specific comment
            result = get_comment_by_id(args.issue_key, args.id, args.profile)

            if args.output == "json":
                print(json.dumps(result, indent=2))
            else:
                print(f"Comment {result['id']} on {args.issue_key}:\n")
                author = result.get("author", {}).get("displayName", "Unknown")
                created = result.get("created", "N/A")[:16]
                print(f"  Author: {author}")
                print(f"  Created: {created}")

                visibility = result.get("visibility")
                if visibility:
                    vis_type = visibility.get("type", "")
                    vis_value = visibility.get("value", "")
                    print(f"  Visibility: {vis_type} - {vis_value}")
                else:
                    print("  Visibility: Public")

                print()
                body = result.get("body", {})
                body_text = adf_to_text(body)
                print(f"  {body_text}")

        else:
            # Get all comments
            result = get_comments(
                args.issue_key, args.limit, args.offset, args.order, args.profile
            )

            if args.output == "json":
                print(json.dumps(result, indent=2))
            else:
                total = result.get("total", 0)
                comments = result.get("comments", [])

                print(f"Comments on {args.issue_key} ({total} total):\n")

                if not comments:
                    print("No comments found.")
                else:
                    table = format_comments_table(comments)
                    print(table)

                    if len(comments) < total:
                        print(
                            f"\nShowing {len(comments)} of {total} comments. Use --limit and --offset to see more."
                        )

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
