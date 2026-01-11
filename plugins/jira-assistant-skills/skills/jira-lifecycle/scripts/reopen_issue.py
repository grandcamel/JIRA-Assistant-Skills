#!/usr/bin/env python3
"""
Reopen a closed or resolved JIRA issue.

Usage:
    python reopen_issue.py PROJ-123
    python reopen_issue.py PROJ-123 --comment "Regression found"
"""

import argparse
import sys

from jira_assistant_skills_lib import (
    JiraError,
    ValidationError,
    find_transition_by_keywords,
    format_transitions,
    get_jira_client,
    print_error,
    print_success,
    text_to_adf,
    validate_issue_key,
)

# Keywords that indicate a reopen/backlog transition
REOPEN_KEYWORDS = ["reopen", "to do", "todo", "open", "backlog"]


def reopen_issue(
    issue_key: str, comment: str | None = None
) -> None:
    """
    Reopen a closed or resolved issue.

    Finds and executes the appropriate reopen transition.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        comment: Optional comment explaining why issue was reopened
    """
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client()

    transitions = client.get_transitions(issue_key)

    if not transitions:
        raise ValidationError(f"No transitions available for {issue_key}")

    # Try to find reopen transition, preferring 'reopen' exact match, then 'to do'
    transition = find_transition_by_keywords(
        transitions, REOPEN_KEYWORDS, prefer_exact="reopen"
    )

    # If no exact 'reopen', try 'to do' as secondary preference
    if transition and "reopen" not in transition["name"].lower():
        todo_trans = find_transition_by_keywords(
            transitions, ["to do", "todo"], prefer_exact="to do"
        )
        if todo_trans:
            transition = todo_trans

    if not transition:
        available = format_transitions(transitions)
        raise ValidationError(
            f"No reopen transition found for {issue_key}.\n"
            f"Available transitions:\n{available}"
        )

    fields = None
    if comment:
        fields = {"comment": text_to_adf(comment)}

    client.transition_issue(issue_key, transition["id"], fields=fields)
    client.close()


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Reopen a closed or resolved JIRA issue",
        epilog='Example: python reopen_issue.py PROJ-123 --comment "Regression found"',
    )

    parser.add_argument("issue_key", help="Issue key (e.g., PROJ-123)")
    parser.add_argument(
        "--comment", "-c", help="Comment explaining why issue was reopened"
    )

    args = parser.parse_args(argv)

    try:
        reopen_issue(
            issue_key=args.issue_key, comment=args.comment
        )

        print_success(f"Reopened {args.issue_key}")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
