#!/usr/bin/env python3
"""
Create a new issue type in JIRA.

Creates a global or project-scoped issue type.
Requires 'Administer Jira' global permission.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add shared lib to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import JiraError, ValidationError, print_error


def validate_issue_type_name(name: str) -> str:
    """Validate issue type name."""
    if not name or not name.strip():
        raise ValidationError("Issue type name cannot be empty")

    name = name.strip()
    if len(name) > 60:
        raise ValidationError(f"Issue type name must be 60 characters or less (got {len(name)})")

    return name


def validate_issue_type_type(issue_type: str) -> str:
    """Validate issue type type."""
    valid_types = ['standard', 'subtask']
    if issue_type not in valid_types:
        raise ValidationError(
            f"Invalid issue type: '{issue_type}'. Must be one of: {', '.join(valid_types)}"
        )
    return issue_type


def create_issue_type(
    name: str,
    description: Optional[str] = None,
    issue_type: str = 'standard',
    hierarchy_level: Optional[int] = None,
    client=None,
    profile: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new issue type.

    Args:
        name: Issue type name (max 60 characters)
        description: Issue type description
        issue_type: 'standard' or 'subtask'
        hierarchy_level: Hierarchy level (-1 for subtask, 0 for standard, 1+ for higher)
        client: JiraClient instance (for testing)
        profile: Configuration profile name

    Returns:
        Created issue type details

    Raises:
        ValidationError: If input validation fails
        PermissionError: If lacking admin permission
        JiraError: On API failure
    """
    # Validate inputs
    name = validate_issue_type_name(name)
    issue_type = validate_issue_type_type(issue_type)

    if client is None:
        client = get_jira_client(profile=profile)

    try:
        result = client.create_issue_type(
            name=name,
            description=description,
            issue_type=issue_type,
            hierarchy_level=hierarchy_level
        )
        return result
    finally:
        if client:
            client.close()


def format_created_issue_type(issue_type: Dict[str, Any], output_format: str = 'detail') -> str:
    """Format created issue type for display."""
    if output_format == 'json':
        return json.dumps(issue_type, indent=2)

    lines = []
    lines.append("Issue type created successfully!")
    lines.append("=" * 40)
    lines.append(f"ID:          {issue_type.get('id', '')}")
    lines.append(f"Name:        {issue_type.get('name', '')}")
    lines.append(f"Description: {issue_type.get('description', '') or 'None'}")
    lines.append(f"Subtask:     {'Yes' if issue_type.get('subtask') else 'No'}")
    lines.append(f"Hierarchy:   {issue_type.get('hierarchyLevel', 0)}")

    return '\n'.join(lines)


def main(argv: list[str] | None = None):
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Create a new issue type in JIRA',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create standard issue type
  python create_issue_type.py --name "Incident" --description "An unplanned interruption"

  # Create subtask type
  python create_issue_type.py --name "Sub-bug" --type subtask

  # Create with specific hierarchy level
  python create_issue_type.py --name "Initiative" --hierarchy 2

  # Output as JSON
  python create_issue_type.py --name "Change Request" --format json

  # Use specific profile
  python create_issue_type.py --name "Incident" --profile production

Note:
  Requires 'Administer Jira' global permission.
  Issue type name must be unique and <= 60 characters.
"""
    )

    parser.add_argument(
        '--name',
        required=True,
        help='Issue type name (max 60 characters)'
    )
    parser.add_argument(
        '--description',
        help='Issue type description'
    )
    parser.add_argument(
        '--type',
        choices=['standard', 'subtask'],
        default='standard',
        dest='issue_type',
        help='Issue type kind (default: standard)'
    )
    parser.add_argument(
        '--hierarchy',
        type=int,
        metavar='LEVEL',
        help='Hierarchy level (-1=subtask, 0=standard, 1=epic, 2+=higher)'
    )
    parser.add_argument(
        '--format',
        choices=['detail', 'json'],
        default='detail',
        help='Output format (default: detail)'
    )
    parser.add_argument(
        '--profile',
        help='Configuration profile to use'
    )

    args = parser.parse_args(argv)

    try:
        issue_type = create_issue_type(
            name=args.name,
            description=args.description,
            issue_type=args.issue_type,
            hierarchy_level=args.hierarchy,
            profile=args.profile
        )

        output = format_created_issue_type(issue_type, args.format)
        print(output)

    except (ValidationError, JiraError) as e:
        print_error(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
