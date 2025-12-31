#!/usr/bin/env python3
"""
Get available transitions for a JIRA issue.

Usage:
    python get_transitions.py PROJ-123
    python get_transitions.py PROJ-123 --output json
"""

import sys
import argparse
import json
from pathlib import Path


from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError
from jira_assistant_skills_lib import validate_issue_key
from jira_assistant_skills_lib import format_transitions, format_json


def get_transitions(issue_key: str, profile: str = None) -> list:
    """
    Get available transitions for an issue.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        profile: JIRA profile to use

    Returns:
        List of available transitions
    """
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client(profile)
    transitions = client.get_transitions(issue_key)
    client.close()

    return transitions


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description='Get available transitions for a JIRA issue',
        epilog='Example: python get_transitions.py PROJ-123'
    )

    parser.add_argument('issue_key',
                       help='Issue key (e.g., PROJ-123)')
    parser.add_argument('--output', '-o',
                       choices=['text', 'json'],
                       default='text',
                       help='Output format (default: text)')
    parser.add_argument('--profile',
                       help='JIRA profile to use (default: from config)')

    args = parser.parse_args(argv)

    try:
        transitions = get_transitions(
            issue_key=args.issue_key,
            profile=args.profile
        )

        if not transitions:
            print(f"No transitions available for {args.issue_key}")
            return

        if args.output == 'json':
            print(format_json(transitions))
        else:
            print(f"\nAvailable transitions for {args.issue_key}:\n")
            print(format_transitions(transitions))

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
