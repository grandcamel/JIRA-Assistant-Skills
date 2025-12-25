#!/usr/bin/env python3
"""
Resolve a JIRA issue.

Usage:
    python resolve_issue.py PROJ-123 --resolution Fixed
    python resolve_issue.py PROJ-123 --resolution "Won't Fix" --comment "Not a bug"
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


def resolve_issue(issue_key: str, resolution: str = "Fixed",
                 comment: str = None, profile: str = None) -> None:
    """
    Resolve an issue.

    Finds and executes the appropriate resolution transition.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        resolution: Resolution value (Fixed, Won't Fix, Duplicate, etc.)
        comment: Optional comment
        profile: JIRA profile to use
    """
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client(profile)

    transitions = client.get_transitions(issue_key)

    if not transitions:
        raise ValidationError(f"No transitions available for {issue_key}")

    resolve_transitions = [
        t for t in transitions
        if any(keyword in t['name'].lower() for keyword in ['done', 'resolve', 'close', 'complete'])
    ]

    if not resolve_transitions:
        available = format_transitions(transitions)
        raise ValidationError(
            f"No resolution transition found for {issue_key}.\n"
            f"Available transitions:\n{available}"
        )

    if len(resolve_transitions) > 1:
        done_trans = [t for t in resolve_transitions if t['name'].lower() == 'done']
        if done_trans:
            transition = done_trans[0]
        else:
            transition = resolve_transitions[0]
    else:
        transition = resolve_transitions[0]

    fields = {
        'resolution': {'name': resolution}
    }

    if comment:
        fields['comment'] = text_to_adf(comment)

    client.transition_issue(issue_key, transition['id'], fields=fields)
    client.close()


def main():
    parser = argparse.ArgumentParser(
        description='Resolve a JIRA issue',
        epilog='Example: python resolve_issue.py PROJ-123 --resolution Fixed'
    )

    parser.add_argument('issue_key',
                       help='Issue key (e.g., PROJ-123)')
    parser.add_argument('--resolution', '-r',
                       default='Fixed',
                       help='Resolution (default: Fixed). Common: Fixed, Won\'t Fix, Duplicate, Cannot Reproduce, Won\'t Do')
    parser.add_argument('--comment', '-c',
                       help='Optional comment')
    parser.add_argument('--profile',
                       help='JIRA profile to use (default: from config)')

    args = parser.parse_args()

    try:
        resolve_issue(
            issue_key=args.issue_key,
            resolution=args.resolution,
            comment=args.comment,
            profile=args.profile
        )

        print_success(f"Resolved {args.issue_key} as {args.resolution}")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
