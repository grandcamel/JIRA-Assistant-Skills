#!/usr/bin/env python3
"""
Create a sub-task issue in JIRA linked to a parent issue.

Usage:
    python create_subtask.py --parent PROJ-101 --summary "Implement login API"
    python create_subtask.py --parent PROJ-101 --summary "Task" --assignee self
    python create_subtask.py --parent PROJ-101 --summary "Task" --estimate 4h
"""

import sys
import argparse
import json
from pathlib import Path

# Add shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

# Imports from shared library
from config_manager import get_jira_client
from error_handler import print_error, JiraError, ValidationError
from validators import validate_issue_key
from formatters import print_success
from adf_helper import markdown_to_adf, text_to_adf


def create_subtask(parent_key: str, summary: str, description: str = None,
                   assignee: str = None, priority: str = None,
                   labels: list = None, time_estimate: str = None,
                   custom_fields: dict = None,
                   profile: str = None, client=None) -> dict:
    """
    Create a new Sub-task issue in JIRA linked to a parent.

    Args:
        parent_key: Parent issue key (required)
        summary: Subtask summary/title (required)
        description: Subtask description (supports markdown)
        assignee: Assignee account ID or "self"
        priority: Priority name
        labels: List of labels
        time_estimate: Time estimate (e.g., "4h", "2d")
        custom_fields: Additional custom fields
        profile: JIRA profile to use
        client: JiraClient instance (for testing)

    Returns:
        Created subtask data from JIRA API

    Raises:
        ValidationError: If inputs are invalid or parent can't have subtasks
        JiraError: If API call fails
    """
    # Validate required fields
    if not parent_key:
        raise ValidationError("Parent key is required")

    if not summary:
        raise ValidationError("Summary is required")

    parent_key = validate_issue_key(parent_key)

    # Initialize client
    if not client:
        client = get_jira_client(profile)
        should_close = True
    else:
        should_close = False

    try:
        # Fetch parent issue to get project and validate
        parent = client.get_issue(parent_key)

        # Validate parent can have subtasks (subtasks can't have subtasks)
        if parent['fields']['issuetype'].get('subtask', False):
            raise ValidationError(
                f"{parent_key} is a subtask and cannot have subtasks"
            )

        # Get project from parent
        project_key = parent['fields']['project']['key']

        # Find the subtask issue type
        issue_types = client.get('/rest/api/3/issuetype')
        subtask_type = None
        for itype in issue_types:
            if itype.get('subtask', False):
                subtask_type = itype['name']
                break

        if not subtask_type:
            raise ValidationError("No subtask issue type found in JIRA instance")

        # Build fields dictionary
        fields = {
            'project': {'key': project_key},
            'parent': {'key': parent_key},
            'issuetype': {'name': subtask_type},
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
                account_id = client.get_current_user_id()
                fields['assignee'] = {'accountId': account_id}
            elif '@' in assignee:
                fields['assignee'] = {'emailAddress': assignee}
            else:
                fields['assignee'] = {'accountId': assignee}

        # Add labels
        if labels:
            fields['labels'] = labels

        # Add time estimate
        if time_estimate:
            fields['timetracking'] = {
                'originalEstimate': time_estimate
            }

        # Add any additional custom fields
        if custom_fields:
            fields.update(custom_fields)

        # Create the subtask
        result = client.create_issue(fields)
        return result

    finally:
        if should_close:
            client.close()


def main():
    parser = argparse.ArgumentParser(
        description='Create a sub-task issue in JIRA',
        epilog='Example: python create_subtask.py --parent PROJ-101 --summary "Implement login API"'
    )

    parser.add_argument('--parent', '-p', required=True,
                       help='Parent issue key (e.g., PROJ-101)')
    parser.add_argument('--summary', '-s', required=True,
                       help='Subtask summary (title)')
    parser.add_argument('--description', '-d',
                       help='Subtask description (supports markdown)')
    parser.add_argument('--priority',
                       help='Priority (Highest, High, Medium, Low, Lowest)')
    parser.add_argument('--assignee', '-a',
                       help='Assignee (account ID, email, or "self")')
    parser.add_argument('--estimate', '-e',
                       help='Time estimate (e.g., 4h, 2d, 1w)')
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

        result = create_subtask(
            parent_key=args.parent,
            summary=args.summary,
            description=args.description,
            assignee=args.assignee,
            priority=args.priority,
            labels=labels,
            time_estimate=args.estimate,
            custom_fields=custom_fields,
            profile=args.profile
        )

        subtask_key = result.get('key')

        if args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            print_success(f"Created subtask: {subtask_key}")
            print(f"Parent: {args.parent}")
            if args.estimate:
                print(f"Estimate: {args.estimate}")
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
