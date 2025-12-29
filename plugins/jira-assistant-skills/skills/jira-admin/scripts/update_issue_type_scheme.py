#!/usr/bin/env python3
"""
Update an issue type scheme in JIRA.

Updates name, description, or default issue type.
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


def update_issue_type_scheme(
    scheme_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    default_issue_type_id: Optional[str] = None,
    client=None,
    profile: Optional[str] = None
) -> bool:
    """
    Update an issue type scheme.

    Args:
        scheme_id: Scheme ID to update
        name: New name (optional)
        description: New description (optional)
        default_issue_type_id: New default issue type ID (optional)
        client: JiraClient instance (for testing)
        profile: Configuration profile name

    Returns:
        True if successful

    Raises:
        ValidationError: If no update parameters provided
        JiraError: On API failure
    """
    # Validate at least one update parameter
    if name is None and description is None and default_issue_type_id is None:
        raise ValidationError(
            "At least one of name, description, or default_issue_type_id must be specified"
        )

    if client is None:
        client = get_jira_client(profile=profile)

    try:
        client.update_issue_type_scheme(
            scheme_id=scheme_id,
            name=name,
            description=description,
            default_issue_type_id=default_issue_type_id
        )
        return True
    finally:
        if client:
            client.close()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Update an issue type scheme in JIRA',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update scheme name
  python update_issue_type_scheme.py 10001 --name "New Name"

  # Update description
  python update_issue_type_scheme.py 10001 --description "New description"

  # Update default issue type
  python update_issue_type_scheme.py 10001 --default-issue-type-id 10002

  # Update multiple fields
  python update_issue_type_scheme.py 10001 --name "Dev Scheme" --description "For development"

  # Use specific profile
  python update_issue_type_scheme.py 10001 --name "New Name" --profile production

Note:
  Requires 'Administer Jira' global permission.
  At least one field must be specified for update.
  Cannot modify the default issue type scheme name.
"""
    )

    parser.add_argument(
        'scheme_id',
        help='Issue type scheme ID to update'
    )
    parser.add_argument(
        '--name',
        help='New scheme name'
    )
    parser.add_argument(
        '--description',
        help='New scheme description'
    )
    parser.add_argument(
        '--default-issue-type-id',
        help='New default issue type ID'
    )
    parser.add_argument(
        '--profile',
        help='Configuration profile to use'
    )

    args = parser.parse_args()

    try:
        update_issue_type_scheme(
            scheme_id=args.scheme_id,
            name=args.name,
            description=args.description,
            default_issue_type_id=args.default_issue_type_id,
            profile=args.profile
        )

        print(f"Issue type scheme {args.scheme_id} updated successfully.")

    except (ValidationError, JiraError) as e:
        print_error(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
