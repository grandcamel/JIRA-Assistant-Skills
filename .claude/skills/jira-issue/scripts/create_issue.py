#!/usr/bin/env python3
"""
Create a new JIRA issue.

Usage:
    python create_issue.py --project PROJ --type Bug --summary "Issue summary"
    python create_issue.py --project PROJ --type Task --summary "Task" --description "Details" --priority High
    python create_issue.py --template bug --project PROJ --summary "Bug title"
    python create_issue.py --project PROJ --type Story --summary "Story" --epic PROJ-100 --story-points 5
"""

import sys
import os
import argparse
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import print_error, JiraError
from validators import validate_project_key, validate_issue_key
from formatters import format_issue, print_success
from adf_helper import markdown_to_adf, text_to_adf

EPIC_LINK_FIELD = 'customfield_10014'
STORY_POINTS_FIELD = 'customfield_10016'


def load_template(template_name: str) -> dict:
    """Load issue template from assets/templates directory."""
    template_dir = Path(__file__).parent.parent / 'assets' / 'templates'
    template_file = template_dir / f'{template_name}_template.json'

    if not template_file.exists():
        raise FileNotFoundError(f"Template not found: {template_name}")

    with open(template_file, 'r') as f:
        return json.load(f)


def create_issue(project: str, issue_type: str, summary: str,
                description: str = None, priority: str = None,
                assignee: str = None, labels: list = None,
                components: list = None, template: str = None,
                custom_fields: dict = None, profile: str = None,
                epic: str = None, sprint: int = None,
                story_points: float = None) -> dict:
    """
    Create a new JIRA issue.

    Args:
        project: Project key
        issue_type: Issue type (Bug, Task, Story, etc.)
        summary: Issue summary
        description: Issue description (markdown supported)
        priority: Priority name
        assignee: Assignee account ID or email
        labels: List of labels
        components: List of component names
        template: Template name to use as base
        custom_fields: Additional custom fields
        profile: JIRA profile to use
        epic: Epic key to link this issue to
        sprint: Sprint ID to add this issue to
        story_points: Story point estimate

    Returns:
        Created issue data
    """
    project = validate_project_key(project)

    fields = {}

    if template:
        template_data = load_template(template)
        fields = template_data.get('fields', {})

    fields['project'] = {'key': project}
    fields['issuetype'] = {'name': issue_type}
    fields['summary'] = summary

    if description:
        if description.strip().startswith('{'):
            fields['description'] = json.loads(description)
        elif '\n' in description or any(md in description for md in ['**', '*', '#', '`', '[']):
            fields['description'] = markdown_to_adf(description)
        else:
            fields['description'] = text_to_adf(description)

    if priority:
        fields['priority'] = {'name': priority}

    if assignee:
        if assignee.lower() == 'self':
            # Will resolve to current user's account ID
            client = get_jira_client(profile)
            account_id = client.get_current_user_id()
            fields['assignee'] = {'accountId': account_id}
            client.close()
        elif '@' in assignee:
            fields['assignee'] = {'emailAddress': assignee}
        else:
            fields['assignee'] = {'accountId': assignee}

    if labels:
        fields['labels'] = labels

    if components:
        fields['components'] = [{'name': comp} for comp in components]

    if custom_fields:
        fields.update(custom_fields)

    # Agile fields
    if epic:
        epic = validate_issue_key(epic)
        fields[EPIC_LINK_FIELD] = epic

    if story_points is not None:
        fields[STORY_POINTS_FIELD] = story_points

    client = get_jira_client(profile)
    result = client.create_issue(fields)

    # Add to sprint after creation (sprint assignment requires issue to exist)
    if sprint:
        issue_key = result.get('key')
        client.move_issues_to_sprint(sprint, [issue_key])

    client.close()

    return result


def main():
    parser = argparse.ArgumentParser(
        description='Create a new JIRA issue',
        epilog='Example: python create_issue.py --project PROJ --type Bug --summary "Login fails"'
    )

    parser.add_argument('--project', '-p', required=True,
                       help='Project key (e.g., PROJ, DEV)')
    parser.add_argument('--type', '-t', required=True,
                       help='Issue type (Bug, Task, Story, etc.)')
    parser.add_argument('--summary', '-s', required=True,
                       help='Issue summary (title)')
    parser.add_argument('--description', '-d',
                       help='Issue description (supports markdown)')
    parser.add_argument('--priority',
                       help='Priority (Highest, High, Medium, Low, Lowest)')
    parser.add_argument('--assignee', '-a',
                       help='Assignee (account ID, email, or "self")')
    parser.add_argument('--labels', '-l',
                       help='Comma-separated labels')
    parser.add_argument('--components', '-c',
                       help='Comma-separated component names')
    parser.add_argument('--template',
                       choices=['bug', 'task', 'story'],
                       help='Use a predefined template')
    parser.add_argument('--custom-fields',
                       help='Custom fields as JSON string')
    parser.add_argument('--epic', '-e',
                       help='Epic key to link this issue to (e.g., PROJ-100)')
    parser.add_argument('--sprint',
                       type=int,
                       help='Sprint ID to add this issue to')
    parser.add_argument('--story-points', '--points',
                       type=float,
                       help='Story point estimate')
    parser.add_argument('--profile',
                       help='JIRA profile to use (default: from config)')
    parser.add_argument('--output', '-o',
                       choices=['text', 'json'],
                       default='text',
                       help='Output format (default: text)')

    args = parser.parse_args()

    try:
        labels = [l.strip() for l in args.labels.split(',')] if args.labels else None
        components = [c.strip() for c in args.components.split(',')] if args.components else None
        custom_fields = json.loads(args.custom_fields) if args.custom_fields else None

        result = create_issue(
            project=args.project,
            issue_type=args.type,
            summary=args.summary,
            description=args.description,
            priority=args.priority,
            assignee=args.assignee,
            labels=labels,
            components=components,
            template=args.template,
            custom_fields=custom_fields,
            profile=args.profile,
            epic=args.epic,
            sprint=args.sprint,
            story_points=args.story_points
        )

        issue_key = result.get('key')

        if args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            print_success(f"Created issue: {issue_key}")
            print(f"URL: {result.get('self', '').replace('/rest/api/3/issue/', '/browse/')}")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
