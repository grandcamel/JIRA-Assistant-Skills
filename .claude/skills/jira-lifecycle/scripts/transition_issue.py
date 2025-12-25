#!/usr/bin/env python3
"""
Transition a JIRA issue to a new status.

Usage:
    python transition_issue.py PROJ-123 --name "In Progress"
    python transition_issue.py PROJ-123 --id 31
    python transition_issue.py PROJ-123 --name "Done" --resolution "Fixed"
"""

import sys
import argparse
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import print_error, JiraError, ValidationError
from validators import validate_issue_key, validate_transition_id
from formatters import print_success, format_transitions
from adf_helper import text_to_adf


def find_transition_by_name(transitions: list, name: str) -> dict:
    """
    Find a transition by name (case-insensitive, partial match).

    Args:
        transitions: List of transition objects
        name: Transition name to find

    Returns:
        Transition object

    Raises:
        ValidationError: If transition not found or ambiguous
    """
    name_lower = name.lower()

    exact_matches = [t for t in transitions if t['name'].lower() == name_lower]
    if len(exact_matches) == 1:
        return exact_matches[0]
    elif len(exact_matches) > 1:
        raise ValidationError(
            f"Multiple exact matches for transition '{name}': " +
            ', '.join(t['name'] for t in exact_matches)
        )

    partial_matches = [t for t in transitions if name_lower in t['name'].lower()]
    if len(partial_matches) == 1:
        return partial_matches[0]
    elif len(partial_matches) > 1:
        raise ValidationError(
            f"Ambiguous transition name '{name}'. Matches: " +
            ', '.join(t['name'] for t in partial_matches)
        )

    raise ValidationError(
        f"Transition '{name}' not found. Available: " +
        ', '.join(t['name'] for t in transitions)
    )


def transition_issue(issue_key: str, transition_id: str = None,
                    transition_name: str = None, resolution: str = None,
                    comment: str = None, fields: dict = None,
                    profile: str = None) -> None:
    """
    Transition an issue to a new status.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        transition_id: Transition ID
        transition_name: Transition name (alternative to ID)
        resolution: Resolution to set (for Done transitions)
        comment: Comment to add
        fields: Additional fields to set
        profile: JIRA profile to use
    """
    issue_key = validate_issue_key(issue_key)

    if not transition_id and not transition_name:
        raise ValidationError("Either --id or --name must be specified")

    client = get_jira_client(profile)

    transitions = client.get_transitions(issue_key)

    if not transitions:
        raise ValidationError(f"No transitions available for {issue_key}")

    if transition_name:
        transition = find_transition_by_name(transitions, transition_name)
        transition_id = transition['id']
    else:
        transition_id = validate_transition_id(transition_id)
        matching = [t for t in transitions if t['id'] == transition_id]
        if not matching:
            available = format_transitions(transitions)
            raise ValidationError(
                f"Transition ID '{transition_id}' not available.\n\n{available}"
            )
        transition = matching[0]

    transition_fields = fields or {}

    if resolution:
        transition_fields['resolution'] = {'name': resolution}

    if comment:
        transition_fields['comment'] = text_to_adf(comment)

    client.transition_issue(issue_key, transition_id, fields=transition_fields if transition_fields else None)
    client.close()


def main():
    parser = argparse.ArgumentParser(
        description='Transition a JIRA issue to a new status',
        epilog='Example: python transition_issue.py PROJ-123 --name "In Progress"'
    )

    parser.add_argument('issue_key',
                       help='Issue key (e.g., PROJ-123)')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--id',
                      help='Transition ID')
    group.add_argument('--name', '-n',
                      help='Transition name (e.g., "In Progress", "Done")')

    parser.add_argument('--resolution', '-r',
                       help='Resolution (for Done transitions): Fixed, Won\'t Fix, Duplicate, etc.')
    parser.add_argument('--comment', '-c',
                       help='Comment to add during transition')
    parser.add_argument('--fields',
                       help='Additional fields as JSON string')
    parser.add_argument('--profile',
                       help='JIRA profile to use (default: from config)')

    args = parser.parse_args()

    try:
        fields = json.loads(args.fields) if args.fields else None

        transition_issue(
            issue_key=args.issue_key,
            transition_id=args.id,
            transition_name=args.name,
            resolution=args.resolution,
            comment=args.comment,
            fields=fields,
            profile=args.profile
        )

        target = args.name or f"transition {args.id}"
        print_success(f"Transitioned {args.issue_key} to {target}")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
