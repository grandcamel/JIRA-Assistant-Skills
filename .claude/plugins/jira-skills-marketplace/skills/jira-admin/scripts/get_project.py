#!/usr/bin/env python3
"""
Get JIRA project details.

Retrieves detailed information about a project including lead, category,
components, and versions.

Examples:
    # Get basic project info
    python get_project.py PROJ

    # Get with components and versions
    python get_project.py PROJ --show-components --show-versions

    # JSON output
    python get_project.py PROJ --output json
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import JiraError, ValidationError, print_error
from validators import validate_project_key


def get_project(
    project_key: str,
    expand: Optional[List[str]] = None,
    show_components: bool = False,
    show_versions: bool = False,
    output_format: str = "text",
    client=None
) -> Dict[str, Any]:
    """
    Get project details.

    Args:
        project_key: Project key (e.g., PROJ)
        expand: Fields to expand (description, lead, issueTypes, url, permissions)
        show_components: Include project components
        show_versions: Include project versions
        output_format: Output format (text, json)
        client: JiraClient instance (optional)

    Returns:
        Project data dictionary

    Raises:
        ValidationError: If project key is invalid
        JiraError: If API call fails
    """
    # Validate input
    project_key = validate_project_key(project_key)

    # Create client if not provided
    should_close = False
    if client is None:
        client = get_jira_client()
        should_close = True

    try:
        # Get project with expansions
        project = client.get_project(project_key, expand=expand)

        # Fetch components if requested
        if show_components:
            try:
                project['components'] = client.get_project_components(project_key)
            except JiraError:
                project['components'] = []

        # Fetch versions if requested
        if show_versions:
            try:
                project['versions'] = client.get_project_versions(project_key)
            except JiraError:
                project['versions'] = []

        return project

    finally:
        if should_close:
            client.close()


def format_output(project: Dict[str, Any], output_format: str = "text",
                  show_components: bool = False, show_versions: bool = False) -> str:
    """Format project data for output."""
    if output_format == "json":
        return json.dumps(project, indent=2)

    # Text output
    lines = [
        f"Project: {project.get('key')} - {project.get('name')}",
        "=" * 60,
        "",
        f"  ID:          {project.get('id')}",
        f"  Type:        {project.get('projectTypeKey', 'N/A')}",
        f"  Style:       {project.get('style', 'N/A')}",
    ]

    # Lead
    lead = project.get('lead')
    if lead:
        lines.append(f"  Lead:        {lead.get('displayName', 'N/A')} ({lead.get('emailAddress', 'N/A')})")
    else:
        lines.append("  Lead:        Not assigned")

    # Category
    category = project.get('projectCategory')
    if category:
        lines.append(f"  Category:    {category.get('name', 'N/A')}")

    # Description
    description = project.get('description')
    if description:
        lines.append(f"  Description: {description[:100]}{'...' if len(description) > 100 else ''}")

    # URL
    url = project.get('url')
    if url:
        lines.append(f"  URL:         {url}")

    # Assignee Type
    assignee_type = project.get('assigneeType')
    if assignee_type:
        lines.append(f"  Assignee:    {assignee_type}")

    # Avatar URLs
    avatar = project.get('avatarUrls', {}).get('48x48')
    if avatar:
        lines.append(f"  Avatar:      {avatar}")

    # Components
    components = project.get('components', [])
    if show_components and components:
        lines.append("")
        lines.append("Components:")
        for comp in components:
            desc = comp.get('description', '')[:40] if comp.get('description') else ''
            lines.append(f"  - {comp.get('name')}: {desc}")
    elif show_components:
        lines.append("")
        lines.append("Components: None")

    # Versions
    versions = project.get('versions', [])
    if show_versions and versions:
        lines.append("")
        lines.append("Versions:")
        for ver in versions:
            released = "Released" if ver.get('released') else "Unreleased"
            lines.append(f"  - {ver.get('name')} ({released})")
    elif show_versions:
        lines.append("")
        lines.append("Versions: None")

    return "\n".join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Get JIRA project details",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get basic project info
  %(prog)s PROJ

  # Get with components and versions
  %(prog)s PROJ --show-components --show-versions

  # JSON output
  %(prog)s PROJ --output json

  # Expand additional fields
  %(prog)s PROJ --expand description,lead,issueTypes
        """
    )

    # Required arguments
    parser.add_argument(
        "project_key",
        help="Project key (e.g., PROJ)"
    )

    # Optional arguments
    parser.add_argument(
        "--expand", "-e",
        help="Comma-separated fields to expand (description, lead, issueTypes, url, permissions)"
    )
    parser.add_argument(
        "--show-components", "-c",
        action="store_true",
        help="Include project components"
    )
    parser.add_argument(
        "--show-versions", "-v",
        action="store_true",
        help="Include project versions"
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

        # Parse expand list
        expand_list = None
        if args.expand:
            expand_list = [x.strip() for x in args.expand.split(',')]

        result = get_project(
            project_key=args.project_key,
            expand=expand_list,
            show_components=args.show_components,
            show_versions=args.show_versions,
            output_format=args.output,
            client=client
        )

        print(format_output(
            result,
            args.output,
            args.show_components,
            args.show_versions
        ))

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
