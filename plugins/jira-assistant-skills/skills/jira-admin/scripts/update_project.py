#!/usr/bin/env python3
"""
Update JIRA project settings.

Modifies project properties including name, description, lead, URL,
default assignee, and category.

Examples:
    # Update project name
    python update_project.py PROJ --name "New Project Name"

    # Change project lead
    python update_project.py PROJ --lead bob@example.com

    # Update multiple fields
    python update_project.py PROJ --name "Updated" --description "New desc" --url https://example.com
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any

# Add shared lib to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import JiraError, ValidationError, print_error
from jira_assistant_skills_lib import (
    validate_project_key,
    validate_project_name,
    validate_assignee_type,
)


def update_project(
    project_key: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    lead: Optional[str] = None,
    url: Optional[str] = None,
    assignee_type: Optional[str] = None,
    category_id: Optional[int] = None,
    client=None
) -> Dict[str, Any]:
    """
    Update a JIRA project.

    Args:
        project_key: Project key to update
        name: New project name
        description: New description
        lead: New lead (account ID or email)
        url: New project URL
        assignee_type: Default assignee type (PROJECT_LEAD, UNASSIGNED, COMPONENT_LEAD)
        category_id: Category ID to assign project to
        client: JiraClient instance (optional)

    Returns:
        Updated project data

    Raises:
        ValidationError: If input validation fails
        JiraError: If API call fails
    """
    # Validate project key
    project_key = validate_project_key(project_key)

    # Validate inputs
    if name:
        name = validate_project_name(name)

    if assignee_type:
        assignee_type = validate_assignee_type(assignee_type)

    # Check if any field is being updated
    if not any([name, description, lead, url, assignee_type, category_id]):
        raise ValidationError(
            "At least one field must be specified for update. "
            "Use --name, --description, --lead, --url, --assignee-type, or --category."
        )

    # Create client if not provided
    should_close = False
    if client is None:
        client = get_jira_client()
        should_close = True

    try:
        # Resolve lead if it's an email
        lead_account_id = None
        if lead:
            if '@' in lead:
                # Search for user by email
                users = client.search_users(lead, max_results=1)
                if users:
                    lead_account_id = users[0].get('accountId')
                else:
                    raise ValidationError(f"User not found: {lead}")
            else:
                lead_account_id = lead

        # Build update kwargs
        kwargs = {}
        if name:
            kwargs['name'] = name
        if description is not None:  # Allow empty string to clear
            kwargs['description'] = description
        if lead_account_id:
            kwargs['lead'] = lead_account_id
        if url is not None:
            kwargs['url'] = url
        if assignee_type:
            kwargs['assignee_type'] = assignee_type
        if category_id is not None:
            kwargs['category_id'] = category_id

        # Update project
        result = client.update_project(project_key, **kwargs)

        return result

    finally:
        if should_close:
            client.close()


def format_output(project: Dict[str, Any], output_format: str = "text") -> str:
    """Format project data for output."""
    if output_format == "json":
        return json.dumps(project, indent=2)

    # Text output
    lines = [
        "Project updated successfully!",
        "",
        f"  Key:         {project.get('key')}",
        f"  Name:        {project.get('name', 'N/A')}",
    ]

    # Lead
    lead = project.get('lead')
    if lead:
        lines.append(f"  Lead:        {lead.get('displayName', 'N/A')}")

    # Category
    category = project.get('projectCategory')
    if category:
        lines.append(f"  Category:    {category.get('name', 'N/A')}")

    # Description
    description = project.get('description')
    if description:
        lines.append(f"  Description: {description[:50]}{'...' if len(description) > 50 else ''}")

    # URL
    url = project.get('url')
    if url:
        lines.append(f"  URL:         {url}")

    # Assignee Type
    assignee_type = project.get('assigneeType')
    if assignee_type:
        lines.append(f"  Assignee:    {assignee_type}")

    return "\n".join(lines)


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Update JIRA project settings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update project name
  %(prog)s PROJ --name "New Project Name"

  # Change project lead
  %(prog)s PROJ --lead bob@example.com

  # Update description
  %(prog)s PROJ --description "New description for the project"

  # Change default assignee type
  %(prog)s PROJ --assignee-type UNASSIGNED

  # Assign to category
  %(prog)s PROJ --category 10001

  # Update multiple fields
  %(prog)s PROJ --name "Updated" --url https://example.com
        """
    )

    # Required arguments
    parser.add_argument(
        "project_key",
        help="Project key to update (e.g., PROJ)"
    )

    # Update fields
    parser.add_argument(
        "--name", "-n",
        help="New project name"
    )
    parser.add_argument(
        "--description", "-d",
        help="New project description (use empty string to clear)"
    )
    parser.add_argument(
        "--lead", "-l",
        help="New project lead (email or account ID)"
    )
    parser.add_argument(
        "--url", "-u",
        help="New project URL"
    )
    parser.add_argument(
        "--assignee-type",
        choices=['PROJECT_LEAD', 'UNASSIGNED', 'COMPONENT_LEAD'],
        help="Default assignee type for new issues"
    )
    parser.add_argument(
        "--category",
        type=int,
        help="Category ID to assign project to"
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

    args = parser.parse_args(argv)

    try:
        client = get_jira_client(profile=args.profile)

        result = update_project(
            project_key=args.project_key,
            name=args.name,
            description=args.description,
            lead=args.lead,
            url=args.url,
            assignee_type=args.assignee_type,
            category_id=args.category,
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
