#!/usr/bin/env python3
"""
Get workflow information for a specific JIRA issue.

Shows the workflow that applies to an issue, including current status,
available transitions, and workflow scheme information.
"""

import argparse
import json
import re
import sys
from typing import Any

# Add shared lib to path
from jira_assistant_skills_lib import (
    JiraError,
    ValidationError,
    get_jira_client,
    print_error,
)


def validate_issue_key(issue_key: str) -> bool:
    """Validate issue key format (PROJECT-123)."""
    pattern = r"^[A-Z][A-Z0-9]*-[0-9]+$"
    return bool(re.match(pattern, issue_key))


def get_workflow_for_issue(
    client, issue_key: str, show_transitions: bool = False, show_scheme: bool = False
) -> dict[str, Any]:
    """
    Get workflow information for a specific issue.

    Args:
        client: JiraClient instance
        issue_key: Issue key (e.g., PROJ-123)
        show_transitions: Include available transitions
        show_scheme: Include workflow scheme details

    Returns:
        Dict with issue workflow information

    Raises:
        ValidationError: If issue key format is invalid
        NotFoundError: If issue not found
        PermissionError: If user lacks permission
    """
    # Validate issue key format
    if not validate_issue_key(issue_key):
        raise ValidationError(
            f"Invalid issue key format: {issue_key}. "
            "Issue keys must match pattern PROJECT-123 (uppercase letters, dash, numbers)."
        )

    # Get issue details
    issue = client.get_issue(issue_key)

    fields = issue.get("fields", {})
    status = fields.get("status", {})
    issue_type = fields.get("issuetype", {})
    project = fields.get("project", {})
    project_key = project.get("key", "")

    # Build result
    result = {
        "issue_key": issue_key,
        "issue_type": issue_type.get("name", "Unknown"),
        "issue_type_id": issue_type.get("id", ""),
        "project_key": project_key,
        "project_name": project.get("name", "Unknown"),
        "current_status": {
            "id": status.get("id", ""),
            "name": status.get("name", "Unknown"),
            "category": status.get("statusCategory", {}).get("name", "Unknown"),
            "category_key": status.get("statusCategory", {}).get("key", ""),
        },
    }

    # Get workflow scheme for project to determine workflow
    try:
        scheme_response = client.get_workflow_scheme_for_project(project_key)
        scheme = scheme_response.get("workflowScheme", {})
        scheme_id = scheme.get("id")

        # Get full scheme details
        if scheme_id:
            scheme_detail = client.get_workflow_scheme(scheme_id)
            issue_type_mappings = scheme_detail.get("issueTypeMappings", {})

            # Find workflow for this issue type
            workflow_name = issue_type_mappings.get(
                issue_type.get("id"), scheme_detail.get("defaultWorkflow", "jira")
            )
            result["workflow_name"] = workflow_name

            if show_scheme:
                result["workflow_scheme"] = {
                    "id": scheme_id,
                    "name": scheme_detail.get("name", "Unknown"),
                    "description": scheme_detail.get("description", ""),
                    "default_workflow": scheme_detail.get("defaultWorkflow", "jira"),
                }
    except JiraError:
        # Use default if can't get scheme
        result["workflow_name"] = "jira"

    # Get available transitions if requested
    if show_transitions:
        try:
            transitions = client.get_transitions(issue_key)
            result["available_transitions"] = [
                {
                    "id": t.get("id", ""),
                    "name": t.get("name", "Unknown"),
                    "to_status": t.get("to", {}).get("name", "Unknown"),
                    "to_status_id": t.get("to", {}).get("id", ""),
                    "is_global": t.get("isGlobal", False),
                    "has_screen": t.get("hasScreen", False),
                }
                for t in transitions
            ]
        except JiraError:
            result["available_transitions"] = []

    return result


def format_issue_workflow(result: dict[str, Any]) -> str:
    """Format issue workflow information as human-readable text."""
    lines = []

    lines.append(f"Workflow Information for {result['issue_key']}")
    lines.append("=" * 50)
    lines.append("")

    lines.append("Issue Details:")
    lines.append(f"  Issue Key:    {result['issue_key']}")
    lines.append(f"  Issue Type:   {result['issue_type']}")
    lines.append(f"  Project:      {result['project_name']} ({result['project_key']})")
    lines.append("")

    status = result.get("current_status", {})
    lines.append("Current Status:")
    lines.append(f"  Name:     {status.get('name', 'Unknown')}")
    lines.append(f"  Category: {status.get('category', 'Unknown')}")
    lines.append("")

    if "workflow_name" in result:
        lines.append(f"Workflow: {result['workflow_name']}")
        lines.append("")

    if "workflow_scheme" in result:
        scheme = result["workflow_scheme"]
        lines.append("Workflow Scheme:")
        lines.append(f"  ID:              {scheme.get('id', 'N/A')}")
        lines.append(f"  Name:            {scheme.get('name', 'Unknown')}")
        lines.append(f"  Default Workflow: {scheme.get('default_workflow', 'jira')}")
        if scheme.get("description"):
            lines.append(f"  Description:     {scheme['description']}")
        lines.append("")

    if "available_transitions" in result:
        transitions = result["available_transitions"]
        lines.append(f"Available Transitions ({len(transitions)}):")
        if transitions:
            for t in transitions:
                global_flag = " [Global]" if t.get("is_global") else ""
                lines.append(f"  - {t['name']} -> {t['to_status']}{global_flag}")
        else:
            lines.append("  No transitions available from current status")
        lines.append("")

    return "\n".join(lines)


def format_issue_workflow_json(result: dict[str, Any]) -> str:
    """Format issue workflow information as JSON."""
    return json.dumps(result, indent=2, default=str)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Get workflow information for a JIRA issue",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get basic workflow info for an issue
  python get_workflow_for_issue.py PROJ-123

  # Show available transitions
  python get_workflow_for_issue.py PROJ-123 --show-transitions

  # Show workflow scheme info
  python get_workflow_for_issue.py PROJ-123 --show-scheme

  # Show everything
  python get_workflow_for_issue.py PROJ-123 --show-transitions --show-scheme

  # JSON output
  python get_workflow_for_issue.py PROJ-123 --output json
        """,
    )

    parser.add_argument("issue_key", help="Issue key (e.g., PROJ-123)")
    parser.add_argument(
        "--show-transitions",
        "-t",
        action="store_true",
        help="Show available transitions from current status",
    )
    parser.add_argument(
        "--show-scheme", "-s", action="store_true", help="Show workflow scheme details"
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args(argv)

    try:
        client = get_jira_client()

        result = get_workflow_for_issue(
            client=client,
            issue_key=args.issue_key,
            show_transitions=args.show_transitions,
            show_scheme=args.show_scheme,
        )

        if args.output == "json":
            print(format_issue_workflow_json(result))
        else:
            print(format_issue_workflow(result))

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    finally:
        if "client" in locals():
            client.close()


if __name__ == "__main__":
    main()
