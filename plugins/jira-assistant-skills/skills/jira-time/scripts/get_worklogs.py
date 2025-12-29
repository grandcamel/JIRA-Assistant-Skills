#!/usr/bin/env python3
"""
Get worklogs (time entries) for a JIRA issue.

Lists all time logged against an issue with filtering and formatting options.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

# Add shared lib to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError
from jira_assistant_skills_lib import validate_issue_key
from jira_assistant_skills_lib import format_seconds, convert_to_jira_datetime_string


def get_worklogs(client, issue_key: str,
                 author_filter: Optional[str] = None,
                 since: Optional[str] = None,
                 until: Optional[str] = None) -> Dict[str, Any]:
    """
    Get worklogs for an issue with optional filtering.

    Args:
        client: JiraClient instance
        issue_key: Issue key (e.g., 'PROJ-123')
        author_filter: Filter by author email
        since: Only include worklogs started after this date
        until: Only include worklogs started before this date

    Returns:
        Dict with 'worklogs' list and 'total' count

    Raises:
        JiraError: If API call fails
    """
    result = client.get_worklogs(issue_key)
    worklogs = result.get('worklogs', [])

    # Apply filters
    filtered = worklogs

    if author_filter:
        filtered = [
            w for w in filtered
            if w.get('author', {}).get('emailAddress') == author_filter
            or w.get('author', {}).get('displayName') == author_filter
            or w.get('author', {}).get('accountId') == author_filter
        ]

    if since:
        filtered = [
            w for w in filtered
            if w.get('started', '') >= since
        ]

    if until:
        filtered = [
            w for w in filtered
            if w.get('started', '') <= until
        ]

    return {
        'worklogs': filtered,
        'total': len(filtered),
        'startAt': result.get('startAt', 0),
        'maxResults': result.get('maxResults', len(filtered))
    }


def format_worklogs_text(worklogs_result: Dict[str, Any], issue_key: str) -> str:
    """
    Format worklogs for text output.

    Args:
        worklogs_result: Result from get_worklogs
        issue_key: Issue key for display

    Returns:
        Formatted text output
    """
    worklogs = worklogs_result.get('worklogs', [])
    lines = [f"Worklogs for {issue_key}:", ""]

    if not worklogs:
        lines.append("No worklogs found.")
        return '\n'.join(lines)

    # Header
    lines.append(f"{'ID':<10} {'Author':<20} {'Started':<20} {'Time':<10} Comment")
    lines.append("-" * 80)

    total_seconds = 0
    for worklog in worklogs:
        worklog_id = worklog.get('id', '')
        author = worklog.get('author', {}).get('displayName', 'Unknown')
        started = worklog.get('started', '')[:19].replace('T', ' ')
        time_spent = worklog.get('timeSpent', '')
        time_seconds = worklog.get('timeSpentSeconds', 0)
        total_seconds += time_seconds

        # Extract comment text from ADF
        comment_text = ''
        comment = worklog.get('comment', {})
        if comment:
            for block in comment.get('content', []):
                for content in block.get('content', []):
                    if content.get('type') == 'text':
                        comment_text = content.get('text', '')[:30]
                        break

        lines.append(f"{worklog_id:<10} {author:<20} {started:<20} {time_spent:<10} {comment_text}")

    lines.append("-" * 80)
    lines.append(f"Total: {format_seconds(total_seconds)} ({len(worklogs)} entries)")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Get worklogs (time entries) for a JIRA issue.',
        epilog='''
Examples:
  %(prog)s PROJ-123
  %(prog)s PROJ-123 --author currentUser()
  %(prog)s PROJ-123 --author alice@company.com
  %(prog)s PROJ-123 --since 2025-01-01 --until 2025-01-31
  %(prog)s PROJ-123 --output json
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('issue_key', help='Issue key (e.g., PROJ-123)')
    parser.add_argument('--author', '-a',
                        help='Filter by author (email, name, or "currentUser()")')
    parser.add_argument('--since', '-s',
                        help='Only show worklogs started after this date')
    parser.add_argument('--until', '-u',
                        help='Only show worklogs started before this date')
    parser.add_argument('--profile', '-p',
                        help='JIRA profile to use')
    parser.add_argument('--output', '-o', choices=['text', 'json'], default='text',
                        help='Output format (default: text)')

    args = parser.parse_args()

    try:
        # Validate issue key
        validate_issue_key(args.issue_key)

        # Get client
        client = get_jira_client(args.profile)

        # Handle currentUser() filter
        author_filter = args.author
        if author_filter == 'currentUser()':
            current_user = client.get('/rest/api/3/myself', operation='get current user')
            author_filter = current_user.get('emailAddress') or current_user.get('accountId')

        # Convert date strings to JIRA datetime format
        since = args.since
        until = args.until
        if since:
            try:
                since = convert_to_jira_datetime_string(since)
            except ValueError:
                pass  # Use as-is if format is unrecognized

        if until:
            try:
                until = convert_to_jira_datetime_string(until)
            except ValueError:
                pass  # Use as-is if format is unrecognized

        # Get worklogs
        result = get_worklogs(client, args.issue_key,
                              author_filter=author_filter,
                              since=since,
                              until=until)

        # Output
        if args.output == 'json':
            import json
            print(json.dumps(result, indent=2))
        else:
            print(format_worklogs_text(result, args.issue_key))

        client.close()

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(1)


if __name__ == '__main__':
    main()
