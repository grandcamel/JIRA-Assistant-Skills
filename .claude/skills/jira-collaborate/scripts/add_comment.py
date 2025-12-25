#!/usr/bin/env python3
"""
Add a comment to a JIRA issue.

Usage:
    python add_comment.py PROJ-123 --body "Comment text"
    python add_comment.py PROJ-123 --body "## Heading\n**Bold**" --format markdown
"""

import sys
import argparse
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import print_error, JiraError
from validators import validate_issue_key
from formatters import print_success
from adf_helper import markdown_to_adf, text_to_adf


def add_comment(issue_key: str, body: str, format_type: str = 'text',
               profile: str = None) -> dict:
    """
    Add a comment to an issue.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        body: Comment body
        format_type: Format ('text', 'markdown', or 'adf')
        profile: JIRA profile to use

    Returns:
        Created comment data
    """
    issue_key = validate_issue_key(issue_key)

    if format_type == 'adf':
        comment_body = json.loads(body)
    elif format_type == 'markdown':
        comment_body = markdown_to_adf(body)
    else:
        comment_body = text_to_adf(body)

    client = get_jira_client(profile)
    result = client.add_comment(issue_key, comment_body)
    client.close()

    return result


def main():
    parser = argparse.ArgumentParser(
        description='Add a comment to a JIRA issue',
        epilog='Example: python add_comment.py PROJ-123 --body "Working on this"'
    )

    parser.add_argument('issue_key',
                       help='Issue key (e.g., PROJ-123)')
    parser.add_argument('--body', '-b',
                       required=True,
                       help='Comment body')
    parser.add_argument('--format', '-f',
                       choices=['text', 'markdown', 'adf'],
                       default='text',
                       help='Body format (default: text)')
    parser.add_argument('--profile',
                       help='JIRA profile to use (default: from config)')

    args = parser.parse_args()

    try:
        result = add_comment(
            issue_key=args.issue_key,
            body=args.body,
            format_type=args.format,
            profile=args.profile
        )

        comment_id = result.get('id', '')
        print_success(f"Added comment to {args.issue_key} (ID: {comment_id})")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
