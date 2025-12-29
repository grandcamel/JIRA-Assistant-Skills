#!/usr/bin/env python3
"""
Create a new issue type scheme in JIRA.

Creates a scheme with specified issue types.
Requires 'Administer Jira' global permission.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add shared lib to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import JiraError, ValidationError, print_error


def create_issue_type_scheme(
    name: str,
    issue_type_ids: List[str],
    description: Optional[str] = None,
    default_issue_type_id: Optional[str] = None,
    client=None,
    profile: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new issue type scheme.

    Args:
        name: Scheme name
        issue_type_ids: List of issue type IDs to include
        description: Scheme description
        default_issue_type_id: Default issue type ID
        client: JiraClient instance (for testing)
        profile: Configuration profile name

    Returns:
        Created scheme response with issueTypeSchemeId

    Raises:
        ValidationError: If validation fails
        JiraError: On API failure
    """
    # Validate inputs
    if not name or not name.strip():
        raise ValidationError("Scheme name cannot be empty")

    if not issue_type_ids:
        raise ValidationError("At least one issue type ID is required")

    name = name.strip()

    if client is None:
        client = get_jira_client(profile=profile)

    try:
        result = client.create_issue_type_scheme(
            name=name,
            issue_type_ids=issue_type_ids,
            description=description,
            default_issue_type_id=default_issue_type_id
        )
        return result
    finally:
        if client:
            client.close()


def format_created_scheme(result: Dict[str, Any], output_format: str = 'detail') -> str:
    """Format created scheme for display."""
    if output_format == 'json':
        return json.dumps(result, indent=2)

    lines = []
    lines.append("Issue type scheme created successfully!")
    lines.append("=" * 40)
    lines.append(f"Scheme ID: {result.get('issueTypeSchemeId', 'Unknown')}")

    return '\n'.join(lines)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Create a new issue type scheme in JIRA',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create scheme with issue types
  python create_issue_type_scheme.py --name "Software Scheme" --issue-type-ids 10001 10002 10003

  # Create with description
  python create_issue_type_scheme.py --name "Bug Tracking" --issue-type-ids 10003 10004 \\
      --description "Scheme for bug tracking projects"

  # Create with default issue type
  python create_issue_type_scheme.py --name "Dev Scheme" --issue-type-ids 10001 10002 \\
      --default-issue-type-id 10001

  # Output as JSON
  python create_issue_type_scheme.py --name "Test" --issue-type-ids 10001 --format json

  # Use specific profile
  python create_issue_type_scheme.py --name "Test" --issue-type-ids 10001 --profile production

Note:
  Requires 'Administer Jira' global permission.
  At least one issue type ID is required.
  The default issue type must be included in the issue type list.
"""
    )

    parser.add_argument(
        '--name',
        required=True,
        help='Scheme name'
    )
    parser.add_argument(
        '--issue-type-ids',
        nargs='+',
        required=True,
        help='Issue type IDs to include in the scheme'
    )
    parser.add_argument(
        '--description',
        help='Scheme description'
    )
    parser.add_argument(
        '--default-issue-type-id',
        help='Default issue type ID'
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

    args = parser.parse_args()

    try:
        result = create_issue_type_scheme(
            name=args.name,
            issue_type_ids=args.issue_type_ids,
            description=args.description,
            default_issue_type_id=args.default_issue_type_id,
            profile=args.profile
        )

        output = format_created_scheme(result, args.format)
        print(output)

    except (ValidationError, JiraError) as e:
        print_error(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
