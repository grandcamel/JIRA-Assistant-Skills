#!/usr/bin/env python3
"""
Create a new JIRA project.

Creates a project with the specified key, name, type, and optional settings.
Requires JIRA administrator permissions.

Examples:
    # Create a Scrum software project
    python create_project.py --key MOBILE --name "Mobile App" --type software --template scrum

    # Create with specific lead
    python create_project.py --key WEBAPP --name "Web App" --type software --lead alice@example.com

    # Create business project with description
    python create_project.py --key MKTG --name "Marketing" --type business \\
        --description "Marketing campaigns and initiatives"
"""

import argparse
import json
import sys
from typing import Any

# Add shared lib to path
from jira_assistant_skills_lib import (
    JiraError,
    ValidationError,
    get_jira_client,
    print_error,
    validate_project_key,
    validate_project_name,
    validate_project_template,
    validate_project_type,
)


def create_project(
    key: str,
    name: str,
    project_type: str,
    template: str | None = None,
    lead: str | None = None,
    description: str | None = None,
    category_id: int | None = None,
    client=None,
) -> dict[str, Any]:
    """
    Create a new JIRA project.

    Args:
        key: Project key (2-10 uppercase letters/numbers, starting with letter)
        name: Project name
        project_type: Project type (software, business, service_desk)
        template: Template shortcut (scrum, kanban, basic) or full template key
        lead: Account ID or email of project lead (defaults to current user)
        description: Project description
        category_id: Category ID to assign project to
        client: JiraClient instance (optional, will create if not provided)

    Returns:
        Created project data

    Raises:
        ValidationError: If input validation fails
        JiraError: If API call fails
    """
    # Validate inputs
    key = validate_project_key(key)
    name = validate_project_name(name)
    project_type = validate_project_type(project_type)

    # Expand template shortcut if provided
    template_key = None
    if template:
        template_key = validate_project_template(template)
    else:
        # Default templates by project type
        default_templates = {
            "software": "com.pyxis.greenhopper.jira:gh-simplified-agility-scrum",
            "business": "com.atlassian.jira-core-project-templates:jira-core-project-management",
            "service_desk": "com.atlassian.servicedesk:simplified-it-service-desk",
        }
        template_key = default_templates.get(project_type)

    # Create client if not provided
    should_close = False
    if client is None:
        client = get_jira_client()
        should_close = True

    try:
        # Resolve lead if it's an email
        lead_account_id = None
        if lead:
            # Check if it's an email (contains @)
            if "@" in lead:
                # Search for user by email
                users = client.search_users(lead, max_results=1)
                if users:
                    lead_account_id = users[0].get("accountId")
                else:
                    raise ValidationError(f"User not found: {lead}")
            else:
                # Assume it's an account ID
                lead_account_id = lead

        # Create project
        result = client.create_project(
            key=key,
            name=name,
            project_type_key=project_type,
            template_key=template_key,
            lead_account_id=lead_account_id,
            description=description,
        )

        # Assign to category if specified
        if category_id:
            try:
                client.update_project(key, category_id=category_id)
            except JiraError as e:
                print(f"Warning: Could not assign category: {e}", file=sys.stderr)

        return result

    finally:
        if should_close:
            client.close()


def format_output(project: dict[str, Any], output_format: str = "text") -> str:
    """Format project data for output."""
    if output_format == "json":
        return json.dumps(project, indent=2)

    # Text output
    lines = [
        "Project created successfully!",
        "",
        f"  Key:  {project.get('key')}",
        f"  ID:   {project.get('id')}",
        f"  Name: {project.get('name', 'N/A')}",
        f"  Type: {project.get('projectTypeKey', 'N/A')}",
        f"  URL:  {project.get('self', 'N/A')}",
    ]

    return "\n".join(lines)


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create a new JIRA project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a Scrum software project
  %(prog)s --key MOBILE --name "Mobile App" --type software --template scrum

  # Create with specific lead
  %(prog)s --key WEBAPP --name "Web App" --type software --lead alice@example.com

  # Create business project with description
  %(prog)s --key MKTG --name "Marketing" --type business \\
      --description "Marketing campaigns"

Template shortcuts:
  scrum             Scrum board (Jira Software)
  kanban            Kanban board (Jira Software)
  basic             Basic software project
  project-management Business project management
  it-service-desk   IT service desk (JSM)
        """,
    )

    # Required arguments
    parser.add_argument(
        "--key",
        "-k",
        required=True,
        help="Project key (2-10 uppercase letters/numbers, must start with letter)",
    )
    parser.add_argument("--name", "-n", required=True, help="Project name")
    parser.add_argument(
        "--type",
        "-t",
        required=True,
        choices=["software", "business", "service_desk"],
        help="Project type",
    )

    # Optional arguments
    parser.add_argument(
        "--template",
        help="Template shortcut (scrum, kanban, basic) or full template key",
    )
    parser.add_argument(
        "--lead",
        "-l",
        help="Project lead (email or account ID, defaults to current user)",
    )
    parser.add_argument("--description", "-d", help="Project description")
    parser.add_argument("--category", type=int, help="Category ID to assign project to")

    # Output options
    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument("--profile", help="Configuration profile to use")

    args = parser.parse_args(argv)

    try:
        client = get_jira_client(profile=args.profile)

        result = create_project(
            key=args.key,
            name=args.name,
            project_type=args.type,
            template=args.template,
            lead=args.lead,
            description=args.description,
            category_id=args.category,
            client=client,
        )

        print(format_output(result, args.output))

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except ValidationError as e:
        print_error(e)
        sys.exit(1)
    finally:
        if "client" in locals():
            client.close()


if __name__ == "__main__":
    main()
