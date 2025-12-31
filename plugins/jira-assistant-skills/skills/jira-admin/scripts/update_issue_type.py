#!/usr/bin/env python3
"""
Update an issue type in JIRA.

Updates name, description, or avatar of an existing issue type.
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


def update_issue_type(
    issue_type_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    avatar_id: Optional[int] = None,
    client=None,
    profile: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update an issue type.

    Args:
        issue_type_id: Issue type ID to update
        name: New name (optional)
        description: New description (optional)
        avatar_id: New avatar ID (optional)
        client: JiraClient instance (for testing)
        profile: Configuration profile name

    Returns:
        Updated issue type details

    Raises:
        ValidationError: If no fields to update or validation fails
        NotFoundError: If issue type not found
        PermissionError: If lacking admin permission
        JiraError: On API failure
    """
    # Validate at least one field is being updated
    if name is None and description is None and avatar_id is None:
        raise ValidationError("At least one field (name, description, or avatar_id) must be specified")

    # Validate name if provided
    if name is not None:
        name = validate_issue_type_name(name)

    if client is None:
        client = get_jira_client(profile=profile)

    try:
        result = client.update_issue_type(
            issue_type_id=issue_type_id,
            name=name,
            description=description,
            avatar_id=avatar_id
        )
        return result
    finally:
        if client:
            client.close()


def format_updated_issue_type(issue_type: Dict[str, Any], output_format: str = 'detail') -> str:
    """Format updated issue type for display."""
    if output_format == 'json':
        return json.dumps(issue_type, indent=2)

    lines = []
    lines.append("Issue type updated successfully!")
    lines.append("=" * 40)
    lines.append(f"ID:          {issue_type.get('id', '')}")
    lines.append(f"Name:        {issue_type.get('name', '')}")
    lines.append(f"Description: {issue_type.get('description', '') or 'None'}")
    lines.append(f"Subtask:     {'Yes' if issue_type.get('subtask') else 'No'}")
    lines.append(f"Hierarchy:   {issue_type.get('hierarchyLevel', 0)}")

    if issue_type.get('avatarId'):
        lines.append(f"Avatar ID:   {issue_type.get('avatarId')}")

    return '\n'.join(lines)


def main(argv: list[str] | None = None):
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Update an issue type in JIRA',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update issue type name
  python update_issue_type.py 10001 --name "User Story"

  # Update description
  python update_issue_type.py 10001 --description "A user-facing feature"

  # Update avatar
  python update_issue_type.py 10001 --avatar-id 10400

  # Update multiple fields
  python update_issue_type.py 10001 --name "Feature Request" --description "A request for new functionality"

  # Output as JSON
  python update_issue_type.py 10001 --name "Bug" --format json

  # Use specific profile
  python update_issue_type.py 10001 --name "Bug" --profile production

Note:
  Requires 'Administer Jira' global permission.
  At least one field must be specified.
"""
    )

    parser.add_argument(
        'issue_type_id',
        help='Issue type ID to update'
    )
    parser.add_argument(
        '--name',
        help='New name (max 60 characters)'
    )
    parser.add_argument(
        '--description',
        help='New description'
    )
    parser.add_argument(
        '--avatar-id',
        type=int,
        help='New avatar ID'
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
        issue_type = update_issue_type(
            issue_type_id=args.issue_type_id,
            name=args.name,
            description=args.description,
            avatar_id=args.avatar_id,
            profile=args.profile
        )

        output = format_updated_issue_type(issue_type, args.format)
        print(output)

    except (ValidationError, JiraError) as e:
        print_error(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
