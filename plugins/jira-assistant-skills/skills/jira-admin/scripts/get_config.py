#!/usr/bin/env python3
"""
Get complete configuration for a JIRA project.

Shows project settings, lead, default assignee, category, and optionally
scheme information (permissions, notifications, workflows, etc.).

Examples:
    # Get basic configuration
    python get_config.py PROJ

    # Include scheme details
    python get_config.py PROJ --show-schemes

    # JSON output
    python get_config.py PROJ --output json
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Dict, Any

# Add shared lib to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import JiraError, print_error
from jira_assistant_skills_lib import validate_project_key


def get_project_config(
    project_key: str,
    show_schemes: bool = False,
    client=None
) -> Dict[str, Any]:
    """
    Get complete project configuration.

    Args:
        project_key: Project key
        show_schemes: Include scheme details in output
        client: JiraClient instance (optional)

    Returns:
        Project configuration data

    Raises:
        JiraError: If API call fails
    """
    project_key = validate_project_key(project_key)

    should_close = False
    if client is None:
        client = get_jira_client()
        should_close = True

    try:
        # Get project with expanded fields
        expand_fields = ['description', 'lead', 'projectKeys', 'url']
        if show_schemes:
            expand_fields.extend([
                'issueTypes', 'versions', 'components'
            ])

        result = client.get_project(project_key, expand=expand_fields)
        return result

    finally:
        if should_close:
            client.close()


def format_output(project: Dict[str, Any], output_format: str = "text",
                  show_schemes: bool = False) -> str:
    """Format project configuration for output."""
    if output_format == "json":
        return json.dumps(project, indent=2)

    # Text output
    lines = [
        f"Project Configuration: {project.get('key', 'Unknown')} - {project.get('name', 'Unknown')}",
        "=" * 70,
        ""
    ]

    # Basic Settings
    lines.append("Basic Settings:")

    lines.append(f"  Key:               {project.get('key', 'N/A')}")
    lines.append(f"  Name:              {project.get('name', 'N/A')}")
    lines.append(f"  ID:                {project.get('id', 'N/A')}")
    lines.append(f"  Type:              {project.get('projectTypeKey', 'N/A')}")

    style = "Team-managed (next-gen)" if project.get('simplified') else "Company-managed (classic)"
    lines.append(f"  Style:             {style}")

    lines.append(f"  Private:           {'Yes' if project.get('isPrivate') else 'No'}")

    # Lead
    lead = project.get('lead', {})
    if lead:
        lines.append(f"  Lead:              {lead.get('displayName', 'N/A')}")
        if lead.get('emailAddress'):
            lines.append(f"                     ({lead.get('emailAddress')})")

    # Default Assignee
    assignee_type = project.get('assigneeType', 'N/A')
    assignee_desc = {
        'PROJECT_LEAD': 'Project Lead',
        'UNASSIGNED': 'Unassigned',
        'COMPONENT_LEAD': 'Component Lead'
    }.get(assignee_type, assignee_type)
    lines.append(f"  Default Assignee:  {assignee_desc}")

    # Category
    category = project.get('projectCategory', {})
    if category:
        lines.append(f"  Category:          {category.get('name', 'None')}")
        if category.get('description'):
            lines.append(f"                     ({category.get('description')})")
    else:
        lines.append(f"  Category:          None")

    # URL
    if project.get('url'):
        lines.append(f"  URL:               {project.get('url')}")

    # Description
    description = project.get('description', '')
    if description:
        lines.append("")
        lines.append("Description:")
        # Truncate long descriptions
        if len(description) > 200:
            lines.append(f"  {description[:200]}...")
        else:
            lines.append(f"  {description}")

    # Avatar URLs
    avatar_urls = project.get('avatarUrls', {})
    if avatar_urls:
        lines.append("")
        lines.append("Avatar URLs:")
        for size, url in avatar_urls.items():
            lines.append(f"  {size}: {url}")

    # Show schemes if requested
    if show_schemes:
        lines.append("")
        lines.append("Schemes:")

        # Permission Scheme
        perm_scheme = project.get('permissionScheme', {})
        if perm_scheme:
            lines.append(f"  Permission Scheme:     {perm_scheme.get('name', 'N/A')} (ID: {perm_scheme.get('id', 'N/A')})")
        else:
            lines.append(f"  Permission Scheme:     Default")

        # Notification Scheme
        notif_scheme = project.get('notificationScheme', {})
        if notif_scheme:
            lines.append(f"  Notification Scheme:   {notif_scheme.get('name', 'N/A')} (ID: {notif_scheme.get('id', 'N/A')})")
        else:
            lines.append(f"  Notification Scheme:   Default")

        # Issue Type Screen Scheme
        its_scheme = project.get('issueTypeScreenScheme', {})
        if its_scheme:
            lines.append(f"  Screen Scheme:         {its_scheme.get('name', 'N/A')} (ID: {its_scheme.get('id', 'N/A')})")

        # Issue Security Scheme
        sec_scheme = project.get('issueSecurityScheme', {})
        if sec_scheme:
            lines.append(f"  Issue Security Scheme: {sec_scheme.get('name', 'N/A')} (ID: {sec_scheme.get('id', 'N/A')})")
        else:
            lines.append(f"  Issue Security Scheme: None")

    # Issue Types (if expanded)
    issue_types = project.get('issueTypes', [])
    if issue_types:
        lines.append("")
        lines.append(f"Issue Types ({len(issue_types)}):")
        for it in issue_types[:5]:  # Show first 5
            subtask = " (subtask)" if it.get('subtask') else ""
            lines.append(f"  - {it.get('name', 'N/A')}{subtask}")
        if len(issue_types) > 5:
            lines.append(f"  ... and {len(issue_types) - 5} more")

    # Components (if expanded)
    components = project.get('components', [])
    if components:
        lines.append("")
        lines.append(f"Components ({len(components)}):")
        for comp in components[:5]:  # Show first 5
            lines.append(f"  - {comp.get('name', 'N/A')}")
        if len(components) > 5:
            lines.append(f"  ... and {len(components) - 5} more")

    # Versions (if expanded)
    versions = project.get('versions', [])
    if versions:
        lines.append("")
        lines.append(f"Versions ({len(versions)}):")
        for ver in versions[:5]:  # Show first 5
            released = " (released)" if ver.get('released') else ""
            archived = " (archived)" if ver.get('archived') else ""
            lines.append(f"  - {ver.get('name', 'N/A')}{released}{archived}")
        if len(versions) > 5:
            lines.append(f"  ... and {len(versions) - 5} more")

    # Footer
    lines.append("")
    lines.append(f"Self Link: {project.get('self', 'N/A')}")

    return "\n".join(lines)


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Get complete configuration for a JIRA project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get basic configuration
  %(prog)s PROJ

  # Include scheme details
  %(prog)s PROJ --show-schemes

  # JSON output
  %(prog)s PROJ --output json
        """
    )

    # Required arguments
    parser.add_argument(
        "project_key",
        help="Project key (e.g., PROJ)"
    )

    # Optional arguments
    parser.add_argument(
        "--show-schemes", "-s",
        action="store_true",
        help="Include scheme details (permissions, notifications, etc.)"
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

        result = get_project_config(
            project_key=args.project_key,
            show_schemes=args.show_schemes,
            client=client
        )

        print(format_output(result, args.output, args.show_schemes))

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    finally:
        if 'client' in locals():
            client.close()


if __name__ == "__main__":
    main()
