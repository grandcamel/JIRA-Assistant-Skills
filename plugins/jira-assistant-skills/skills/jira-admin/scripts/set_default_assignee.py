#!/usr/bin/env python3
"""
Set the default assignee type for a JIRA project.

The default assignee determines who issues are automatically assigned to
when created without a specific assignee.

Requires project administrator permissions.

Examples:
    # Set to project lead
    python set_default_assignee.py PROJ --type PROJECT_LEAD

    # Set to unassigned
    python set_default_assignee.py PROJ --type UNASSIGNED

    # Set to component lead
    python set_default_assignee.py PROJ --type COMPONENT_LEAD
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Dict, Any

# Add shared lib to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import JiraError, ValidationError, print_error
from jira_assistant_skills_lib import validate_project_key, validate_assignee_type


def set_default_assignee(
    project_key: str,
    assignee_type: str,
    client=None
) -> Dict[str, Any]:
    """
    Set the default assignee type for a project.

    Args:
        project_key: Project key
        assignee_type: Assignee type (PROJECT_LEAD, UNASSIGNED, COMPONENT_LEAD)
        client: JiraClient instance (optional)

    Returns:
        Updated project data

    Raises:
        ValidationError: If assignee type is invalid
        JiraError: If API call fails
    """
    project_key = validate_project_key(project_key)
    assignee_type = validate_assignee_type(assignee_type)

    should_close = False
    if client is None:
        client = get_jira_client()
        should_close = True

    try:
        result = client.update_project(project_key, assignee_type=assignee_type)
        return result

    finally:
        if should_close:
            client.close()


def format_output(project: Dict[str, Any], output_format: str = "text") -> str:
    """Format result for output."""
    if output_format == "json":
        return json.dumps(project, indent=2)

    # Text output
    assignee_type = project.get('assigneeType', 'Unknown')

    type_descriptions = {
        'PROJECT_LEAD': 'Project Lead - Issues will be assigned to the project lead',
        'UNASSIGNED': 'Unassigned - Issues will have no default assignee',
        'COMPONENT_LEAD': 'Component Lead - Issues will be assigned based on component'
    }

    description = type_descriptions.get(assignee_type, assignee_type)

    lines = [
        f"Default assignee updated for project {project.get('key', 'Unknown')}",
        "",
        f"  Type: {assignee_type}",
        f"  Meaning: {description}"
    ]

    return "\n".join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Set the default assignee type for a JIRA project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Assignee Types:
  PROJECT_LEAD   - Issues will be assigned to the project lead
  UNASSIGNED     - Issues will have no default assignee
  COMPONENT_LEAD - Issues will be assigned based on component

Examples:
  # Set to project lead
  %(prog)s PROJ --type PROJECT_LEAD

  # Set to unassigned
  %(prog)s PROJ --type UNASSIGNED

  # Set to component lead
  %(prog)s PROJ --type COMPONENT_LEAD
        """
    )

    # Required arguments
    parser.add_argument(
        "project_key",
        help="Project key (e.g., PROJ)"
    )
    parser.add_argument(
        "--type", "-t",
        required=True,
        dest="assignee_type",
        choices=['PROJECT_LEAD', 'UNASSIGNED', 'COMPONENT_LEAD'],
        help="Default assignee type"
    )

    # Output options
    parser.add_argument(
        "--output", "-o",
        choices=['text', 'json'],
        default='text',
        help="Output format (default: text)"
    )
    parser.add_argument(
        "--profile",
        help="Configuration profile to use"
    )

    args = parser.parse_args()

    try:
        client = get_jira_client(profile=args.profile)

        result = set_default_assignee(
            project_key=args.project_key,
            assignee_type=args.assignee_type,
            client=client
        )

        print(format_output(result, args.output))

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except ValidationError as e:
        print_error(e)
        sys.exit(1)
    finally:
        if 'client' in locals():
            client.close()


if __name__ == "__main__":
    main()
