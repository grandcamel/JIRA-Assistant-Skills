#!/usr/bin/env python3
"""
Resolve a JIRA issue.

Usage:
    python resolve_issue.py PROJ-123 --resolution Fixed
    python resolve_issue.py PROJ-123 --resolution "Won't Fix" --comment "Not a bug"
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

# Keywords that indicate a resolution/completion transition
RESOLVE_KEYWORDS = ["done", "resolve", "close", "complete"]


def resolve_issue(
    issue_key: str,
    resolution: str = "Fixed",
    comment: str | None = None,
) -> None:
    """
    Resolve an issue.

    Finds and executes the appropriate resolution transition.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        resolution: Resolution value (Fixed, Won't Fix, Duplicate, etc.)
        comment: Optional comment
    """
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client()

    transitions = client.get_transitions(issue_key)

    if not transitions:
        raise ValidationError(f"No transitions available for {issue_key}")

    transition = find_transition_by_keywords(
        transitions, RESOLVE_KEYWORDS, prefer_exact="done"
    )

    if not transition:
        available = format_transitions(transitions)
        raise ValidationError(
            f"No resolution transition found for {issue_key}.\n"
            f"Available transitions:\n{available}"
        )

    fields = {"resolution": {"name": resolution}}

    if comment:
        fields["comment"] = text_to_adf(comment)

    client.transition_issue(issue_key, transition["id"], fields=fields)
    client.close()


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Resolve a JIRA issue",
        epilog="Example: python resolve_issue.py PROJ-123 --resolution Fixed",
    )

    parser.add_argument("issue_key", help="Issue key (e.g., PROJ-123)")
    parser.add_argument(
        "--resolution",
        "-r",
        default="Fixed",
        help="Resolution (default: Fixed). Common: Fixed, Won't Fix, Duplicate, Cannot Reproduce, Won't Do",
    )
    parser.add_argument("--comment", "-c", help="Optional comment")

    args = parser.parse_args(argv)

    try:
        resolve_issue(
            issue_key=args.issue_key,
            resolution=args.resolution,
            comment=args.comment,
        )

        print_success(f"Resolved {args.issue_key} as {args.resolution}")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
