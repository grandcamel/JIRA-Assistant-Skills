#!/usr/bin/env python3
"""
Create a new Epic issue in JIRA.

Usage:
    python create_epic.py --project PROJ --summary "Epic summary"
    python create_epic.py --project PROJ --summary "Epic" --epic-name "MVP" --color blue
    python create_epic.py --project PROJ --summary "Epic" --description "Details" --assignee self
"""

import sys
import argparse
import json
from pathlib import Path

# Add shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'shared' / 'scripts' / 'lib'))

# Imports from shared library
from config_manager import get_jira_client
from error_handler import print_error, JiraError, ValidationError
from validators import validate_project_key
from formatters import print_success
from adf_helper import markdown_to_adf, text_to_adf

# Valid epic colors in JIRA
VALID_EPIC_COLORS = [
    'blue', 'cyan', 'green', 'yellow', 'orange', 'red',
    'magenta', 'purple', 'lime', 'pink', 'teal'
]


def create_epic(project: str, summary: str, description: str = None,
                epic_name: str = None, color: str = None,
                priority: str = None, assignee: str = None,
                labels: list = None, custom_fields: dict = None,
                profile: str = None, client=None) -> dict:
    """
    Create a new Epic issue in JIRA.

    Args:
        project: Project key (required)
        summary: Epic summary/title (required)
        description: Epic description (supports markdown)
        epic_name: Epic Name field value
        color: Epic color (blue, green, red, etc.)
        priority: Priority name
        assignee: Assignee account ID or "self"
        labels: List of labels
        custom_fields: Additional custom fields
        profile: JIRA profile to use

    Returns:
        Created epic data from JIRA API

    Raises:
        ValidationError: If inputs are invalid
        JiraError: If API call fails
    """
    # Validate required fields
    if not project:
        raise ValidationError("Project key is required")

    if not summary:
        raise ValidationError("Summary is required")

    project = validate_project_key(project)

    # Validate epic color if provided
    if color and color.lower() not in VALID_EPIC_COLORS:
        raise ValidationError(
            f"Invalid epic color: {color}. Valid colors: {', '.join(VALID_EPIC_COLORS)}"
        )

    # Build fields dictionary
    fields = {
        'project': {'key': project},
        'issuetype': {'name': 'Epic'},
        'summary': summary
    }

    # Add description with ADF conversion
    if description:
        if description.strip().startswith('{'):
            # Already ADF JSON
            fields['description'] = json.loads(description)
        elif '\n' in description or any(md in description for md in ['**', '*', '#', '`', '[']):
            # Markdown format
            fields['description'] = markdown_to_adf(description)
        else:
            # Plain text
            fields['description'] = text_to_adf(description)

    # Add priority
    if priority:
        fields['priority'] = {'name': priority}

    # Add assignee
    if assignee:
        if assignee.lower() == 'self':
            temp_client = client or get_jira_client(profile)
            account_id = temp_client.get_current_user_id()
            fields['assignee'] = {'accountId': account_id}
            if not client:
                temp_client.close()
        elif '@' in assignee:
            fields['assignee'] = {'emailAddress': assignee}
        else:
            fields['assignee'] = {'accountId': assignee}

    # Add labels
    if labels:
        fields['labels'] = labels

    # Add epic-specific custom fields
    # Note: customfield IDs may vary per JIRA instance
    if epic_name:
        fields['customfield_10011'] = epic_name  # Epic Name

    if color:
        fields['customfield_10012'] = color.lower()  # Epic Color

    # Add any additional custom fields
    if custom_fields:
        fields.update(custom_fields)

    # Create the epic
    if not client:
        client = get_jira_client(profile)
        should_close = True
    else:
        should_close = False

    try:
        result = client.create_issue(fields)
        return result
    finally:
        if should_close:
            client.close()


def main():
    parser = argparse.ArgumentParser(
        description='Create a new Epic issue in JIRA',
        epilog='Example: python create_epic.py --project PROJ --summary "Mobile App MVP" --epic-name "MVP"'
    )

    parser.add_argument('--project', '-p', required=True,
                       help='Project key (e.g., PROJ, DEV)')
    parser.add_argument('--summary', '-s', required=True,
                       help='Epic summary (title)')
    parser.add_argument('--description', '-d',
                       help='Epic description (supports markdown)')
    parser.add_argument('--epic-name', '-n',
                       help='Epic Name field value')
    parser.add_argument('--color', '-c',
                       choices=VALID_EPIC_COLORS,
                       help=f'Epic color ({", ".join(VALID_EPIC_COLORS[:5])}...)')
    parser.add_argument('--priority',
                       help='Priority (Highest, High, Medium, Low, Lowest)')
    parser.add_argument('--assignee', '-a',
                       help='Assignee (account ID, email, or "self")')
    parser.add_argument('--labels', '-l',
                       help='Comma-separated labels')
    parser.add_argument('--custom-fields',
                       help='Custom fields as JSON string')
    parser.add_argument('--profile',
                       help='JIRA profile to use (default: from config)')
    parser.add_argument('--output', '-o',
                       choices=['text', 'json'],
                       default='text',
                       help='Output format (default: text)')

    args = parser.parse_args()

    try:
        labels = [l.strip() for l in args.labels.split(',')] if args.labels else None
        custom_fields = json.loads(args.custom_fields) if args.custom_fields else None

        result = create_epic(
            project=args.project,
            summary=args.summary,
            description=args.description,
            epic_name=args.epic_name,
            color=args.color,
            priority=args.priority,
            assignee=args.assignee,
            labels=labels,
            custom_fields=custom_fields,
            profile=args.profile
        )

        epic_key = result.get('key')

        if args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            print_success(f"Created epic: {epic_key}")
            if args.epic_name:
                print(f"Epic Name: {args.epic_name}")
            print(f"URL: {result.get('self', '').replace('/rest/api/3/issue/', '/browse/')}")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except ValidationError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
