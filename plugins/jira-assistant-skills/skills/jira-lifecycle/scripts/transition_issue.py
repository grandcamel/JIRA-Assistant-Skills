#!/usr/bin/env python3
"""
Transition a JIRA issue to a new status.

If project context has been discovered (via discover_project.py), error messages
and dry-run output will include expected workflow transitions from the context.

Usage:
    python transition_issue.py PROJ-123 --name "In Progress"
    python transition_issue.py PROJ-123 --id 31
    python transition_issue.py PROJ-123 --name "Done" --resolution "Fixed"
    python transition_issue.py PROJ-123 --name "In Progress" --sprint 42
    python transition_issue.py PROJ-123 --name "Done" --dry-run  # Preview with context hints
"""

import argparse
import json
import sys

from jira_assistant_skills_lib import (
    JiraError,
    ValidationError,
    find_transition_by_name,
    format_transitions,
    get_jira_client,
    get_project_context,
    get_valid_transitions,
    has_project_context,
    print_error,
    print_info,
    print_success,
    text_to_adf,
    validate_issue_key,
    validate_transition_id,
)


def get_context_workflow_hint(
    project_key: str,
    issue_type: str,
    current_status: str,
) -> str:
    """
    Get workflow hint from project context if available.

    Args:
        project_key: Project key
        issue_type: Issue type name
        current_status: Current status name

    Returns:
        String with expected transitions from context, or empty string if no context
    """
    if not has_project_context(project_key):
        return ""

    context = get_project_context(project_key)
    if not context.has_context():
        return ""

    valid_transitions = get_valid_transitions(context, issue_type, current_status)
    if not valid_transitions:
        return ""

    # Format context workflow info
    lines = ["\nExpected transitions from project context:"]
    for t in valid_transitions:
        lines.append(f"  - {t.get('name')} → {t.get('to_status')}")

    return "\n".join(lines)


def transition_issue(
    issue_key: str,
    transition_id: str | None = None,
    transition_name: str | None = None,
    resolution: str | None = None,
    comment: str | None = None,
    fields: dict | None = None,
    sprint_id: int | None = None,
    dry_run: bool = False,
) -> dict:
    """
    Transition an issue to a new status.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        transition_id: Transition ID
        transition_name: Transition name (alternative to ID)
        resolution: Resolution to set (for Done transitions)
        comment: Comment to add
        fields: Additional fields to set
        sprint_id: Sprint ID to move issue to after transition
        dry_run: If True, preview changes without making them

    Returns:
        Dictionary with transition details
    """
    issue_key = validate_issue_key(issue_key)

    if not transition_id and not transition_name:
        raise ValidationError("Either --id or --name must be specified")

    client = get_jira_client()

    # Get issue details first for context hints
    issue = client.get_issue(issue_key, fields=["status", "issuetype", "project"])
    current_status = issue.get("fields", {}).get("status", {}).get("name", "Unknown")
    issue_type = issue.get("fields", {}).get("issuetype", {}).get("name", "Unknown")
    project_key = (
        issue.get("fields", {}).get("project", {}).get("key", issue_key.split("-")[0])
    )

    transitions = client.get_transitions(issue_key)

    if not transitions:
        context_hint = get_context_workflow_hint(
            project_key, issue_type, current_status
        )
        raise ValidationError(
            f"No transitions available for {issue_key} (status: {current_status}){context_hint}"
        )

    if transition_name:
        transition = find_transition_by_name(transitions, transition_name)
        transition_id = transition["id"]
    else:
        transition_id = validate_transition_id(transition_id)
        matching = [t for t in transitions if t["id"] == transition_id]
        if not matching:
            available = format_transitions(transitions)
            context_hint = get_context_workflow_hint(
                project_key, issue_type, current_status
            )
            raise ValidationError(
                f"Transition ID '{transition_id}' not available.\n\n{available}{context_hint}"
            )
        transition = matching[0]

    transition_fields = fields or {}

    if resolution:
        transition_fields["resolution"] = {"name": resolution}

    if comment:
        transition_fields["comment"] = text_to_adf(comment)

    target_status = transition.get("to", {}).get(
        "name", transition.get("name", "Unknown")
    )

    result = {
        "issue_key": issue_key,
        "transition": transition.get("name"),
        "transition_id": transition_id,
        "current_status": current_status,
        "target_status": target_status,
        "resolution": resolution,
        "comment": comment is not None,
        "sprint_id": sprint_id,
        "dry_run": dry_run,
    }

    if dry_run:
        print_info(f"[DRY RUN] Would transition {issue_key}:")
        print(f"  Current status: {current_status}")
        print(f"  Target status: {target_status}")
        print(f"  Transition: {transition.get('name')}")
        if resolution:
            print(f"  Resolution: {resolution}")
        if comment:
            print("  Comment: (would add comment)")
        if sprint_id:
            print(f"  Sprint: Would move to sprint {sprint_id}")

        # Show context workflow hint if available
        context_hint = get_context_workflow_hint(
            project_key, issue_type, target_status
        )
        if context_hint:
            print(
                f"\n  After transition, expected options:{context_hint.replace(chr(10), chr(10) + '  ')}"
            )

        client.close()
        return result

    client.transition_issue(
        issue_key,
        transition_id,
        fields=transition_fields if transition_fields else None,
    )

    # Move to sprint if specified
    if sprint_id:
        client.move_issues_to_sprint(sprint_id, [issue_key])

    client.close()
    return result


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Transition a JIRA issue to a new status",
        epilog='Example: python transition_issue.py PROJ-123 --name "In Progress"',
    )

    parser.add_argument("issue_key", help="Issue key (e.g., PROJ-123)")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--id", help="Transition ID")
    group.add_argument(
        "--name", "-n", help='Transition name (e.g., "In Progress", "Done")'
    )

    parser.add_argument(
        "--resolution",
        "-r",
        help="Resolution (for Done transitions): Fixed, Won't Fix, Duplicate, etc.",
    )
    parser.add_argument("--comment", "-c", help="Comment to add during transition")
    parser.add_argument(
        "--sprint", "-s", type=int, help="Sprint ID to move issue to after transition"
    )
    parser.add_argument("--fields", help="Additional fields as JSON string")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without making them"
    )

    args = parser.parse_args(argv)

    try:
        fields = json.loads(args.fields) if args.fields else None

        transition_issue(
            issue_key=args.issue_key,
            transition_id=args.id,
            transition_name=args.name,
            resolution=args.resolution,
            comment=args.comment,
            fields=fields,
            sprint_id=args.sprint,
            dry_run=args.dry_run,
        )

        if args.dry_run:
            # Dry-run output handled in function
            pass
        else:
            target = args.name or f"transition {args.id}"
            msg = f"Transitioned {args.issue_key} to {target}"
            if args.sprint:
                msg += f" and moved to sprint {args.sprint}"
            print_success(msg)

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
