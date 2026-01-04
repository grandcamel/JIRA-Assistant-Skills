#!/usr/bin/env python3
"""
Create a new JIRA issue.

If project context has been discovered (via discover_project.py), default values
for priority, assignee, labels, components, and story_points will be applied
automatically for unspecified fields. Use --no-defaults to skip this behavior.

Usage:
    python create_issue.py --project PROJ --type Bug --summary "Issue summary"
    python create_issue.py --project PROJ --type Task --summary "Task" --description "Details" --priority High
    python create_issue.py --template bug --project PROJ --summary "Bug title"
    python create_issue.py --project PROJ --type Story --summary "Story" --epic PROJ-100 --story-points 5
    python create_issue.py --project PROJ --type Task --summary "Task" --blocks PROJ-123
    python create_issue.py --project PROJ --type Task --summary "Task" --relates-to PROJ-456
    python create_issue.py --project PROJ --type Task --summary "Task" --estimate "2d"
    python create_issue.py --project PROJ --type Bug --summary "Bug" --no-defaults
"""

import sys
import os
import argparse
import json
from pathlib import Path


from jira_assistant_skills_lib import get_jira_client, get_agile_fields, get_project_defaults, has_project_context
from jira_assistant_skills_lib import print_error, JiraError, PermissionError, NotFoundError
from jira_assistant_skills_lib import validate_project_key, validate_issue_key
from jira_assistant_skills_lib import format_issue, print_success
from jira_assistant_skills_lib import markdown_to_adf, text_to_adf


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
                story_points: float = None,
                blocks: list = None, relates_to: list = None,
                estimate: str = None, no_defaults: bool = False) -> dict:
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
        blocks: List of issue keys this issue blocks
        relates_to: List of issue keys this issue relates to
        estimate: Original time estimate (e.g., '2d', '4h')
        no_defaults: If True, skip applying project context defaults

    Returns:
        Created issue data
    """
    project = validate_project_key(project)

    # Apply project context defaults for unspecified fields
    defaults_applied = []
    if not no_defaults and has_project_context(project, profile):
        defaults = get_project_defaults(project, issue_type, profile)
        if defaults:
            if priority is None and 'priority' in defaults:
                priority = defaults['priority']
                defaults_applied.append('priority')
            if assignee is None and 'assignee' in defaults:
                assignee = defaults['assignee']
                defaults_applied.append('assignee')
            if labels is None and 'labels' in defaults:
                labels = defaults['labels']
                defaults_applied.append('labels')
            if components is None and 'components' in defaults:
                components = defaults['components']
                defaults_applied.append('components')
            if story_points is None and 'story_points' in defaults:
                story_points = defaults['story_points']
                defaults_applied.append('story_points')

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

    # Agile fields - get field IDs from configuration
    if epic or story_points is not None:
        agile_fields = get_agile_fields(profile)

        if epic:
            epic = validate_issue_key(epic)
            fields[agile_fields['epic_link']] = epic

        if story_points is not None:
            fields[agile_fields['story_points']] = story_points

    # Time tracking
    if estimate:
        fields['timetracking'] = {'originalEstimate': estimate}

    client = get_jira_client(profile)
    result = client.create_issue(fields)

    # Add to sprint after creation (sprint assignment requires issue to exist)
    issue_key = result.get('key')
    if sprint:
        client.move_issues_to_sprint(sprint, [issue_key])

    # Create issue links after creation
    links_created = []
    links_failed = []
    if blocks:
        for target_key in blocks:
            target_key = validate_issue_key(target_key)
            try:
                client.create_link('Blocks', issue_key, target_key)
                links_created.append(f"blocks {target_key}")
            except (PermissionError, NotFoundError) as e:
                links_failed.append(f"blocks {target_key}: {str(e)}")

    if relates_to:
        for target_key in relates_to:
            target_key = validate_issue_key(target_key)
            try:
                client.create_link('Relates', issue_key, target_key)
                links_created.append(f"relates to {target_key}")
            except (PermissionError, NotFoundError) as e:
                links_failed.append(f"relates to {target_key}: {str(e)}")

    if links_created:
        result['links_created'] = links_created
    if links_failed:
        result['links_failed'] = links_failed
    if defaults_applied:
        result['defaults_applied'] = defaults_applied

    client.close()

    return result


def main(argv: list[str] | None = None):
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
    parser.add_argument('--blocks',
                       help='Comma-separated issue keys this issue blocks')
    parser.add_argument('--relates-to',
                       help='Comma-separated issue keys this issue relates to')
    parser.add_argument('--estimate',
                       help='Original time estimate (e.g., 2d, 4h, 1w)')
    parser.add_argument('--profile',
                       help='JIRA profile to use (default: from config)')
    parser.add_argument('--no-defaults',
                       action='store_true',
                       help='Disable project context defaults')
    parser.add_argument('--output', '-o',
                       choices=['text', 'json'],
                       default='text',
                       help='Output format (default: text)')

    args = parser.parse_args(argv)

    try:
        labels = [l.strip() for l in args.labels.split(',')] if args.labels else None
        components = [c.strip() for c in args.components.split(',')] if args.components else None
        custom_fields = json.loads(args.custom_fields) if args.custom_fields else None
        blocks = [k.strip() for k in args.blocks.split(',')] if args.blocks else None
        relates_to = [k.strip() for k in args.relates_to.split(',')] if args.relates_to else None

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
            story_points=args.story_points,
            blocks=blocks,
            relates_to=relates_to,
            estimate=args.estimate,
            no_defaults=args.no_defaults
        )

        issue_key = result.get('key')

        if args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            print_success(f"Created issue: {issue_key}")
            print(f"URL: {result.get('self', '').replace('/rest/api/3/issue/', '/browse/')}")
            defaults_applied = result.get('defaults_applied', [])
            if defaults_applied:
                print(f"Defaults applied: {', '.join(defaults_applied)}")
            links_created = result.get('links_created', [])
            if links_created:
                print(f"Links: {', '.join(links_created)}")
            links_failed = result.get('links_failed', [])
            if links_failed:
                print(f"Links failed: {', '.join(links_failed)}")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
