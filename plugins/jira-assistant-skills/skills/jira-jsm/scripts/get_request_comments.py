#!/usr/bin/env python3
"""
Get comments for a JSM request with visibility information.

This script retrieves comments from JSM requests, showing public/internal visibility.
Public comments are visible to customers in the portal, while internal comments
are only visible to agents.
"""

import sys
import argparse
import json
from pathlib import Path
from datetime import datetime

# Add shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import handle_errors


def get_jira_client(profile=None):
    """Get JIRA client (overridable for testing)."""
    from config_manager import get_jira_client as _get_client
    return _get_client(profile)


def format_visibility(is_public: bool) -> str:
    """Format visibility as clear indicator."""
    return "👁️  PUBLIC  " if is_public else "🔒 INTERNAL"


def format_comments_table(comments: list) -> None:
    """Format comments as table with visibility indicators."""
    if not comments:
        print("No comments found.")
        return

    # Count public vs internal
    public_count = sum(1 for c in comments if c.get('public', True))
    internal_count = len(comments) - public_count

    print(f"\nComments ({len(comments)} total: {public_count} public, {internal_count} internal):\n")

    print(f"{'ID':<10} {'Author':<20} {'Date':<20} {'Visibility':<12} {'Body'}")
    print("─" * 100)

    for comment in comments:
        comment_id = comment.get('id', 'unknown')
        author = comment.get('author', {}).get('displayName', 'Unknown')
        created = comment.get('created', '')
        is_public = comment.get('public', True)
        body = comment.get('body', '').replace('\n', ' ')[:50]  # First 50 chars

        # Format date
        try:
            dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
            date_str = dt.strftime('%Y-%m-%d %H:%M')
        except:
            date_str = created[:16] if created else 'Unknown'

        visibility = "PUBLIC  " if is_public else "INTERNAL"

        print(f"{comment_id:<10} {author:<20} {date_str:<20} {visibility:<12} {body}...")

    print("\nLegend:")
    print("  PUBLIC    - Visible in customer portal")
    print("  INTERNAL  - Agent-only, not visible to customers")


@handle_errors
def main(args=None):
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Get JSM request comments with visibility info',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # All comments
  %(prog)s REQ-123

  # Public comments only
  %(prog)s REQ-123 --public-only

  # Internal comments only
  %(prog)s REQ-123 --internal-only

  # Specific comment
  %(prog)s REQ-123 --id 10001

  # JSON output
  %(prog)s REQ-123 --output json
        """
    )

    parser.add_argument('issue_key',
                        help='Request key (e.g., REQ-123)')
    parser.add_argument('--public-only', action='store_true',
                        help='Show only public (customer-visible) comments')
    parser.add_argument('--internal-only', action='store_true',
                        help='Show only internal (agent-only) comments')
    parser.add_argument('--id',
                        help='Get specific comment by ID')
    parser.add_argument('--output', choices=['text', 'json'], default='text',
                        help='Output format (default: text)')
    parser.add_argument('--all-pages', action='store_true',
                        help='Fetch all pages (default: first 100)')
    parser.add_argument('--profile',
                        help='JIRA profile to use')

    parsed_args = parser.parse_args(args)

    # Get JIRA client
    jira = get_jira_client(parsed_args.profile)

    # Get specific comment by ID
    if parsed_args.id:
        comment = jira.get_request_comment(parsed_args.issue_key, parsed_args.id, expand=None)
        if parsed_args.output == 'json':
            print(json.dumps(comment, indent=2))
        else:
            format_comments_table([comment])
        return 0

    # Determine visibility filter
    public_filter = None
    if parsed_args.public_only:
        public_filter = True
    elif parsed_args.internal_only:
        public_filter = False

    # Get comments
    if parsed_args.all_pages:
        # Fetch all pages
        all_comments = []
        start = 0
        limit = 100
        while True:
            response = jira.get_request_comments(
                parsed_args.issue_key,
                public=public_filter,
                start=start,
                limit=limit
            )
            comments = response.get('values', [])
            all_comments.extend(comments)

            if response.get('isLastPage', True):
                break
            start += limit

        comments_data = all_comments
    else:
        # Single page
        response = jira.get_request_comments(
            parsed_args.issue_key,
            public=public_filter,
            start=0,
            limit=100
        )
        comments_data = response.get('values', [])

    # Output
    if parsed_args.output == 'json':
        print(json.dumps(comments_data, indent=2))
    else:
        format_comments_table(comments_data)

    return 0


if __name__ == '__main__':
    sys.exit(main())
