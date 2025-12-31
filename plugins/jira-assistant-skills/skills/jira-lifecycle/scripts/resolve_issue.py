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


from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError, ValidationError
from jira_assistant_skills_lib import validate_issue_key
from jira_assistant_skills_lib import print_success, format_transitions
from jira_assistant_skills_lib import text_to_adf
from jira_assistant_skills_lib import find_transition_by_keywords


# Keywords that indicate a resolution/completion transition
RESOLVE_KEYWORDS = ['done', 'resolve', 'close', 'complete']


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

    transition = find_transition_by_keywords(
        transitions,
        RESOLVE_KEYWORDS,
        prefer_exact='done'
    )

    if not transition:
        available = format_transitions(transitions)
        raise ValidationError(
            f"No resolution transition found for {issue_key}.\n"
            f"Available transitions:\n{available}"
        )

    fields = {
        'resolution': {'name': resolution}
    }

    if comment:
        fields['comment'] = text_to_adf(comment)

    client.transition_issue(issue_key, transition['id'], fields=fields)
    client.close()


def main(argv: list[str] | None = None):
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

    args = parser.parse_args(argv)

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
