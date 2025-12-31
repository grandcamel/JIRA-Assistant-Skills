#!/usr/bin/env python3
"""
Set the project lead for a JIRA project.

The project lead is the default assignee for issues and receives certain
notifications by default.

Requires project administrator permissions.

Examples:
    # Set lead by email
    python set_project_lead.py PROJ --lead alice@example.com

    # Set lead by account ID
    python set_project_lead.py PROJ --account-id 557058:test-user-id
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Add shared lib to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import JiraError, ValidationError, print_error
from jira_assistant_skills_lib import validate_project_key


def set_project_lead(
    project_key: str,
    lead_email: Optional[str] = None,
    lead_account_id: Optional[str] = None,
    client=None
) -> Dict[str, Any]:
    """
    Set the project lead.

    Args:
        project_key: Project key
        lead_email: Lead's email address (will look up account ID)
        lead_account_id: Lead's account ID (used directly)
        client: JiraClient instance (optional)

    Returns:
        Updated project data

    Raises:
        ValidationError: If neither email nor account ID provided, or user not found
        JiraError: If API call fails
    """
    project_key = validate_project_key(project_key)

    if not lead_email and not lead_account_id:
        raise ValidationError(
            "Must specify either --lead (email) or --account-id"
        )

    should_close = False
    if client is None:
        client = get_jira_client()
        should_close = True

    try:
        account_id = lead_account_id

        # Look up account ID by email if needed
        if lead_email and not lead_account_id:
            users = client.search_users(query=lead_email)

            # Find exact email match
            found = None
            for user in users:
                if user.get('emailAddress', '').lower() == lead_email.lower():
                    found = user
                    break

            if not found:
                raise ValidationError(
                    f"User with email '{lead_email}' not found. "
                    f"Make sure the user has access to the JIRA instance."
                )

            account_id = found.get('accountId')

        # Update project with new lead
        result = client.update_project(project_key, lead=account_id)
        return result

    finally:
        if should_close:
            client.close()


def format_output(project: Dict[str, Any], output_format: str = "text") -> str:
    """Format result for output."""
    if output_format == "json":
        return json.dumps(project, indent=2)

    # Text output
    lead = project.get('lead', {})
    lines = [
        f"Project lead updated for {project.get('key', 'Unknown')}",
        "",
        f"  New Lead: {lead.get('displayName', 'N/A')}",
    ]

    if lead.get('emailAddress'):
        lines.append(f"  Email:    {lead.get('emailAddress')}")

    lines.append(f"  Account:  {lead.get('accountId', 'N/A')}")

    return "\n".join(lines)


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Set the project lead for a JIRA project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Set lead by email
  %(prog)s PROJ --lead alice@example.com

  # Set lead by account ID
  %(prog)s PROJ --account-id 557058:test-user-id
        """
    )

    # Required arguments
    parser.add_argument(
        "project_key",
        help="Project key (e.g., PROJ)"
    )

    # Lead specification (at least one required)
    lead_group = parser.add_mutually_exclusive_group(required=True)
    lead_group.add_argument(
        "--lead", "-l",
        dest="lead_email",
        help="Lead's email address"
    )
    lead_group.add_argument(
        "--account-id", "-a",
        dest="account_id",
        help="Lead's account ID"
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

        result = set_project_lead(
            project_key=args.project_key,
            lead_email=args.lead_email,
            lead_account_id=args.account_id,
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
