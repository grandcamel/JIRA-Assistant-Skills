#!/usr/bin/env python3
"""
Reopen a closed or resolved JIRA issue.

Usage:
    python reopen_issue.py PROJ-123
    python reopen_issue.py PROJ-123 --comment "Regression found"
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import print_error, JiraError, ValidationError
from validators import validate_issue_key
from formatters import print_success, format_transitions
from adf_helper import text_to_adf


def reopen_issue(issue_key: str, comment: str = None, profile: str = None) -> None:
    """
    Reopen a closed or resolved issue.

    Finds and executes the appropriate reopen transition.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        comment: Optional comment explaining why issue was reopened
        profile: JIRA profile to use
    """
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client(profile)

    transitions = client.get_transitions(issue_key)

    if not transitions:
        raise ValidationError(f"No transitions available for {issue_key}")

    reopen_transitions = [
        t for t in transitions
        if any(keyword in t['name'].lower() for keyword in ['reopen', 'to do', 'todo', 'open', 'backlog'])
    ]

    if not reopen_transitions:
        available = format_transitions(transitions)
        raise ValidationError(
            f"No reopen transition found for {issue_key}.\n"
            f"Available transitions:\n{available}"
        )

    reopen_exact = [t for t in reopen_transitions if 'reopen' in t['name'].lower()]
    if reopen_exact:
        transition = reopen_exact[0]
    elif len(reopen_transitions) == 1:
        transition = reopen_transitions[0]
    else:
        todo_trans = [t for t in reopen_transitions if 'to do' in t['name'].lower() or 'todo' in t['name'].lower()]
        if todo_trans:
            transition = todo_trans[0]
        else:
            transition = reopen_transitions[0]

    fields = None
    if comment:
        fields = {'comment': text_to_adf(comment)}

    client.transition_issue(issue_key, transition['id'], fields=fields)
    client.close()


def main():
    parser = argparse.ArgumentParser(
        description='Reopen a closed or resolved JIRA issue',
        epilog='Example: python reopen_issue.py PROJ-123 --comment "Regression found"'
    )

    parser.add_argument('issue_key',
                       help='Issue key (e.g., PROJ-123)')
    parser.add_argument('--comment', '-c',
                       help='Comment explaining why issue was reopened')
    parser.add_argument('--profile',
                       help='JIRA profile to use (default: from config)')

    args = parser.parse_args()

    try:
        reopen_issue(
            issue_key=args.issue_key,
            comment=args.comment,
            profile=args.profile
        )

        print_success(f"Reopened {args.issue_key}")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
