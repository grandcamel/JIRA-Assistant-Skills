#!/usr/bin/env python3
"""
Clone a JIRA issue with optional link handling.

Usage:
    python clone_issue.py PROJ-123
    python clone_issue.py PROJ-123 --include-subtasks
    python clone_issue.py PROJ-123 --include-links
    python clone_issue.py PROJ-123 --to-project OTHER
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import print_error, JiraError
from validators import validate_issue_key

# Fields that can be cloned to new issue
CLONEABLE_FIELDS = [
    'summary', 'description', 'priority', 'labels', 'components',
    'assignee', 'reporter', 'environment', 'fixVersions', 'versions'
]


def extract_cloneable_fields(issue: Dict[str, Any], to_project: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract fields from an issue that can be cloned.

    Args:
        issue: Original issue data
        to_project: Target project key (if different from original)

    Returns:
        Dict of fields for new issue
    """
    original_fields = issue.get('fields', {})
    new_fields = {}

    # Project - either original or target
    if to_project:
        new_fields['project'] = {'key': to_project}
    else:
        project = original_fields.get('project', {})
        new_fields['project'] = {'key': project.get('key')}

    # Issue type
    issuetype = original_fields.get('issuetype', {})
    new_fields['issuetype'] = {'name': issuetype.get('name', 'Task')}

    # Summary - prefix with clone indicator
    original_summary = original_fields.get('summary', 'Untitled')
    new_fields['summary'] = f"[Clone of {issue['key']}] {original_summary}"

    # Clone other fields if they exist and have values
    for field_name in CLONEABLE_FIELDS:
        if field_name == 'summary':
            continue  # Already handled

        value = original_fields.get(field_name)
        if value is not None:
            # Handle special field formats
            if field_name in ['priority']:
                if isinstance(value, dict) and 'name' in value:
                    new_fields[field_name] = {'name': value['name']}
            elif field_name in ['labels']:
                new_fields[field_name] = value if isinstance(value, list) else []
            elif field_name in ['components', 'fixVersions', 'versions']:
                # Only copy if staying in same project
                if not to_project:
                    new_fields[field_name] = value
            elif field_name in ['assignee', 'reporter']:
                if isinstance(value, dict) and 'accountId' in value:
                    new_fields[field_name] = {'accountId': value['accountId']}
            else:
                new_fields[field_name] = value

    return new_fields


def clone_issue(issue_key: str, to_project: Optional[str] = None,
                summary: Optional[str] = None, include_subtasks: bool = False,
                include_links: bool = False, create_clone_link: bool = True,
                profile: str = None) -> Dict[str, Any]:
    """
    Clone a JIRA issue.

    Args:
        issue_key: Issue key to clone
        to_project: Target project (default: same project)
        summary: Custom summary for clone (default: "[Clone of X] original summary")
        include_subtasks: Clone subtasks as well
        include_links: Copy links from original
        create_clone_link: Create 'clones' link to original
        profile: JIRA profile

    Returns:
        Dict with clone result
    """
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client(profile)

    try:
        # Get original issue
        original = client.get_issue(issue_key)

        # Extract cloneable fields
        new_fields = extract_cloneable_fields(original, to_project)

        # Override summary if specified
        if summary:
            new_fields['summary'] = summary

        # Create clone
        created = client.create_issue(new_fields)
        clone_key = created['key']

        result = {
            'original_key': issue_key,
            'clone_key': clone_key,
            'project': new_fields['project']['key'],
            'links_copied': 0,
            'subtasks_cloned': 0
        }

        # Create clone link
        if create_clone_link:
            try:
                client.create_link('Cloners', clone_key, issue_key)
                result['clone_link_created'] = True
            except JiraError:
                result['clone_link_created'] = False

        # Copy links from original
        if include_links:
            original_links = original.get('fields', {}).get('issuelinks', [])
            links_copied = 0

            for link in original_links:
                link_type = link['type']['name']
                try:
                    if 'outwardIssue' in link:
                        # Original has outward link, clone should too
                        target_key = link['outwardIssue']['key']
                        client.create_link(link_type, clone_key, target_key)
                        links_copied += 1
                    elif 'inwardIssue' in link:
                        # Original has inward link, clone should too
                        source_key = link['inwardIssue']['key']
                        client.create_link(link_type, source_key, clone_key)
                        links_copied += 1
                except JiraError:
                    # Skip links that fail (may be cross-project restrictions)
                    pass

            result['links_copied'] = links_copied

        # Clone subtasks
        if include_subtasks:
            subtasks = original.get('fields', {}).get('subtasks', [])
            subtasks_cloned = 0

            for subtask in subtasks:
                try:
                    subtask_full = client.get_issue(subtask['key'])
                    subtask_fields = extract_cloneable_fields(subtask_full, to_project)

                    # Set parent to clone
                    subtask_fields['parent'] = {'key': clone_key}

                    # Prefix subtask summary
                    original_summary = subtask_full.get('fields', {}).get('summary', '')
                    subtask_fields['summary'] = f"[Clone] {original_summary}"

                    # Create subtask clone
                    client.create_issue(subtask_fields)
                    subtasks_cloned += 1
                except JiraError:
                    # Skip subtasks that fail
                    pass

            result['subtasks_cloned'] = subtasks_cloned

        return result

    finally:
        client.close()


def format_clone_result(result: Dict[str, Any], output_format: str = 'text') -> str:
    """
    Format clone result for output.

    Args:
        result: Clone result dict
        output_format: 'text' or 'json'

    Returns:
        Formatted string
    """
    if output_format == 'json':
        return json.dumps(result, indent=2)

    lines = []
    lines.append(f"Cloned {result['original_key']} -> {result['clone_key']}")
    lines.append(f"  Project: {result.get('project', 'N/A')}")

    if result.get('clone_link_created'):
        lines.append(f"  Clone link: Created")

    if result.get('links_copied', 0) > 0:
        lines.append(f"  Links copied: {result['links_copied']}")

    if result.get('subtasks_cloned', 0) > 0:
        lines.append(f"  Subtasks cloned: {result['subtasks_cloned']}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Clone a JIRA issue',
        epilog='Example: python clone_issue.py PROJ-123 --include-links'
    )

    parser.add_argument('issue_key',
                       help='Issue key to clone (e.g., PROJ-123)')

    parser.add_argument('--summary', '-s',
                       help='Custom summary for clone')
    parser.add_argument('--to-project', '-p',
                       help='Clone to different project')
    parser.add_argument('--include-subtasks',
                       action='store_true',
                       help='Clone subtasks as well')
    parser.add_argument('--include-links',
                       action='store_true',
                       help='Copy links from original issue')
    parser.add_argument('--no-link',
                       action='store_true',
                       help='Do not create "clones" link to original')
    parser.add_argument('--output', '-o',
                       choices=['text', 'json'],
                       default='text',
                       help='Output format (default: text)')
    parser.add_argument('--profile',
                       help='JIRA profile to use (default: from config)')

    args = parser.parse_args()

    try:
        result = clone_issue(
            issue_key=args.issue_key,
            to_project=args.to_project,
            summary=args.summary,
            include_subtasks=args.include_subtasks,
            include_links=args.include_links,
            create_clone_link=not args.no_link,
            profile=args.profile
        )

        output = format_clone_result(result, output_format=args.output)
        print(output)

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
