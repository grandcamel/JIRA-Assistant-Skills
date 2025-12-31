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


from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError
from jira_assistant_skills_lib import validate_issue_key
from jira_assistant_skills_lib import print_success
from jira_assistant_skills_lib import markdown_to_adf, text_to_adf


def add_comment(issue_key: str, body: str, format_type: str = 'text',
               profile: str = None) -> dict:
    """
    Add a public comment to an issue.

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


def add_comment_with_visibility(issue_key: str, body: str, format_type: str = 'text',
                                visibility_type: str = None, visibility_value: str = None,
                                profile: str = None) -> dict:
    """
    Add a comment with visibility restrictions.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        body: Comment body
        format_type: Format ('text', 'markdown', or 'adf')
        visibility_type: 'role' or 'group' (None for public)
        visibility_value: Role or group name
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
    result = client.add_comment_with_visibility(
        issue_key,
        comment_body,
        visibility_type=visibility_type,
        visibility_value=visibility_value
    )
    client.close()

    return result


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description='Add a comment to a JIRA issue',
        epilog='''
Examples:
  %(prog)s PROJ-123 --body "Working on this"
  %(prog)s PROJ-123 --body "Internal note" --visibility-role Administrators
  %(prog)s PROJ-123 --body "Dev note" --visibility-group jira-developers
        '''
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
    parser.add_argument('--visibility-role',
                       help='Restrict visibility to a role (e.g., Administrators)')
    parser.add_argument('--visibility-group',
                       help='Restrict visibility to a group (e.g., jira-developers)')
    parser.add_argument('--profile',
                       help='JIRA profile to use (default: from config)')

    args = parser.parse_args(argv)

    try:
        # Determine visibility settings
        visibility_type = None
        visibility_value = None

        if args.visibility_role and args.visibility_group:
            print_error("Error: Cannot specify both --visibility-role and --visibility-group")
            sys.exit(1)

        if args.visibility_role:
            visibility_type = 'role'
            visibility_value = args.visibility_role
        elif args.visibility_group:
            visibility_type = 'group'
            visibility_value = args.visibility_group

        # Add comment with or without visibility
        if visibility_type:
            result = add_comment_with_visibility(
                issue_key=args.issue_key,
                body=args.body,
                format_type=args.format,
                visibility_type=visibility_type,
                visibility_value=visibility_value,
                profile=args.profile
            )
        else:
            result = add_comment(
                issue_key=args.issue_key,
                body=args.body,
                format_type=args.format,
                profile=args.profile
            )

        comment_id = result.get('id', '')
        print_success(f"Added comment to {args.issue_key} (ID: {comment_id})")

        # Show visibility info if present
        visibility = result.get('visibility')
        if visibility:
            vis_type = visibility.get('type', '')
            vis_value = visibility.get('value', '')
            print(f"\nVisibility: {vis_value} ({vis_type})")
            print(f"Note: This comment is only visible to users with the {vis_value} {vis_type}.")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
