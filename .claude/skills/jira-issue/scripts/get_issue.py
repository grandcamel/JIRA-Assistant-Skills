#!/usr/bin/env python3
"""
Get and display a JIRA issue.

Usage:
    python get_issue.py PROJ-123
    python get_issue.py PROJ-123 --detailed
    python get_issue.py PROJ-123 --output json
"""

import sys
import os
import argparse
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import print_error, JiraError
from validators import validate_issue_key
from formatters import format_issue, format_json


def get_issue(issue_key: str, fields: list = None, profile: str = None) -> dict:
    """
    Get a JIRA issue.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        fields: Specific fields to retrieve (default: all)
        profile: JIRA profile to use

    Returns:
        Issue data dictionary
    """
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client(profile)
    issue = client.get_issue(issue_key, fields=fields)
    client.close()

    return issue


def main():
    parser = argparse.ArgumentParser(
        description='Get and display a JIRA issue',
        epilog='Example: python get_issue.py PROJ-123 --detailed'
    )

    parser.add_argument('issue_key',
                       help='Issue key (e.g., PROJ-123)')
    parser.add_argument('--fields', '-f',
                       help='Comma-separated list of fields to retrieve')
    parser.add_argument('--detailed', '-d',
                       action='store_true',
                       help='Show detailed information including description')
    parser.add_argument('--output', '-o',
                       choices=['text', 'json'],
                       default='text',
                       help='Output format (default: text)')
    parser.add_argument('--profile',
                       help='JIRA profile to use (default: from config)')

    args = parser.parse_args()

    try:
        fields = [f.strip() for f in args.fields.split(',')] if args.fields else None

        issue = get_issue(
            issue_key=args.issue_key,
            fields=fields,
            profile=args.profile
        )

        if args.output == 'json':
            print(format_json(issue))
        else:
            print(format_issue(issue, detailed=args.detailed))

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
