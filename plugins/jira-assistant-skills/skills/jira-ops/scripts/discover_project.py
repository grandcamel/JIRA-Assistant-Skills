#!/usr/bin/env python3
"""
Discover JIRA project context and save to skill directory or settings.

This script fetches project metadata, workflows, and usage patterns from JIRA
and saves them in a format that Claude can use for intelligent defaults.

Usage:
    python discover_project.py PROJ
    python discover_project.py PROJ --profile development
    python discover_project.py PROJ --personal
    python discover_project.py PROJ --sample-size 200 --days 60
    python discover_project.py PROJ --output json --no-save
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError
from jira_assistant_skills_lib import format_json, print_success, print_info, print_warning


def get_skills_root() -> Path:
    """Get the root path of the skills directory."""
    return Path(__file__).parent.parent.parent.parent


def discover_metadata(client, project_key: str) -> Dict[str, Any]:
    """
    Fetch project metadata from JIRA.

    Discovers:
    - Project info (name, type, lead)
    - Issue types with their statuses
    - Components
    - Versions
    - Priorities
    - Assignable users

    Args:
        client: JiraClient instance
        project_key: JIRA project key

    Returns:
        Dict with metadata
    """
    print_info(f"Discovering metadata for {project_key}...")

    metadata = {
        'project_key': project_key,
        'discovered_at': datetime.utcnow().isoformat() + 'Z'
    }

    # Get project info
    project = client.get_project(project_key, expand=['lead', 'description'])
    metadata['project_name'] = project.get('name', project_key)
    metadata['project_type'] = project.get('projectTypeKey', 'software')
    metadata['is_team_managed'] = project.get('simplified', False)

    if project.get('lead'):
        metadata['project_lead'] = {
            'account_id': project['lead'].get('accountId'),
            'display_name': project['lead'].get('displayName')
        }

    # Get issue types with statuses
    print_info("  Fetching issue types and statuses...")
    statuses_by_type = client.get_project_statuses(project_key)

    issue_types = []
    for item in statuses_by_type:
        issue_type = {
            'id': item.get('id'),
            'name': item.get('name'),
            'subtask': item.get('subtask', False),
            'statuses': [s.get('name') for s in item.get('statuses', [])]
        }
        issue_types.append(issue_type)

    metadata['issue_types'] = issue_types
    print_info(f"    Found {len(issue_types)} issue types")

    # Get components
    print_info("  Fetching components...")
    components = client.get_project_components(project_key)
    metadata['components'] = [
        {
            'id': c.get('id'),
            'name': c.get('name'),
            'description': c.get('description'),
            'lead': c.get('lead', {}).get('displayName') if c.get('lead') else None
        }
        for c in components
    ]
    print_info(f"    Found {len(metadata['components'])} components")

    # Get versions
    print_info("  Fetching versions...")
    versions = client.get_project_versions(project_key)
    metadata['versions'] = [
        {
            'id': v.get('id'),
            'name': v.get('name'),
            'description': v.get('description'),
            'released': v.get('released', False),
            'archived': v.get('archived', False),
            'release_date': v.get('releaseDate')
        }
        for v in versions
    ]
    print_info(f"    Found {len(metadata['versions'])} versions")

    # Get priorities (global, but useful for context)
    print_info("  Fetching priorities...")
    try:
        priorities = client.get('/rest/api/3/priority')
        metadata['priorities'] = [
            {
                'id': p.get('id'),
                'name': p.get('name')
            }
            for p in priorities
        ]
        print_info(f"    Found {len(metadata['priorities'])} priorities")
    except Exception:
        metadata['priorities'] = []

    # Get assignable users
    print_info("  Fetching assignable users...")
    try:
        users = client.find_assignable_users('', project_key, max_results=100)
        metadata['assignable_users'] = [
            {
                'account_id': u.get('accountId'),
                'display_name': u.get('displayName'),
                'email': u.get('emailAddress')
            }
            for u in users
        ]
        print_info(f"    Found {len(metadata['assignable_users'])} assignable users")
    except Exception:
        metadata['assignable_users'] = []

    return metadata


def discover_workflows(client, project_key: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Discover workflow transitions by sampling issues in each status.

    For each issue type, finds issues in each status and queries their
    available transitions to build a transition map.

    Args:
        client: JiraClient instance
        project_key: JIRA project key
        metadata: Previously discovered metadata (for issue types/statuses)

    Returns:
        Dict with workflow data
    """
    print_info("Discovering workflows...")

    workflows = {
        'project_key': project_key,
        'discovered_at': datetime.utcnow().isoformat() + 'Z',
        'by_issue_type': {}
    }

    issue_types = metadata.get('issue_types', [])

    for issue_type in issue_types:
        type_name = issue_type.get('name')
        statuses = issue_type.get('statuses', [])

        if not statuses:
            continue

        print_info(f"  Processing {type_name}...")

        type_workflow = {
            'statuses': [],
            'transitions': {}
        }

        # Get status details
        status_details = []
        for status_name in statuses:
            # Try to find an issue in this status to get status details
            jql = f'project = "{project_key}" AND issuetype = "{type_name}" AND status = "{status_name}"'
            try:
                results = client.search_issues(jql, fields=['status'], max_results=1)
                issues = results.get('issues', [])
                if issues:
                    status = issues[0].get('fields', {}).get('status', {})
                    status_details.append({
                        'id': status.get('id'),
                        'name': status.get('name'),
                        'category': status.get('statusCategory', {}).get('key', 'undefined')
                    })
                else:
                    # No issue in this status, add with minimal info
                    status_details.append({
                        'name': status_name,
                        'category': 'undefined'
                    })
            except Exception:
                status_details.append({
                    'name': status_name,
                    'category': 'undefined'
                })

        type_workflow['statuses'] = status_details

        # Discover transitions for each status
        for status_name in statuses:
            # Find an issue in this status
            jql = f'project = "{project_key}" AND issuetype = "{type_name}" AND status = "{status_name}"'
            try:
                results = client.search_issues(jql, fields=['key'], max_results=1)
                issues = results.get('issues', [])

                if issues:
                    issue_key = issues[0].get('key')
                    transitions = client.get_transitions(issue_key)

                    type_workflow['transitions'][status_name] = [
                        {
                            'id': t.get('id'),
                            'name': t.get('name'),
                            'to_status': t.get('to', {}).get('name'),
                            'to_status_id': t.get('to', {}).get('id')
                        }
                        for t in transitions
                    ]
                else:
                    type_workflow['transitions'][status_name] = []

            except Exception as e:
                print_warning(f"    Could not get transitions for {status_name}: {e}")
                type_workflow['transitions'][status_name] = []

        workflows['by_issue_type'][type_name] = type_workflow
        print_info(f"    Found {len(type_workflow['transitions'])} status transition maps")

    return workflows


def discover_patterns(client, project_key: str, sample_size: int = 100,
                      sample_period_days: int = 30) -> Dict[str, Any]:
    """
    Analyze recent issues to discover usage patterns.

    Samples recent issues and analyzes:
    - Assignee distribution per issue type
    - Label frequency
    - Component usage
    - Priority distribution
    - Story points patterns

    Args:
        client: JiraClient instance
        project_key: JIRA project key
        sample_size: Maximum number of issues to sample
        sample_period_days: How many days back to sample

    Returns:
        Dict with pattern data
    """
    print_info(f"Discovering patterns (last {sample_period_days} days, up to {sample_size} issues)...")

    patterns = {
        'project_key': project_key,
        'sample_size': 0,
        'sample_period_days': sample_period_days,
        'discovered_at': datetime.utcnow().isoformat() + 'Z',
        'by_issue_type': {},
        'common_labels': [],
        'top_assignees': []
    }

    # Build JQL for recent issues
    since_date = (datetime.utcnow() - timedelta(days=sample_period_days)).strftime('%Y-%m-%d')
    jql = f'project = "{project_key}" AND created >= "{since_date}" ORDER BY created DESC'

    # Fields to fetch
    fields = [
        'issuetype', 'assignee', 'reporter', 'priority',
        'labels', 'components', 'status',
        'customfield_10016'  # Story points (common ID)
    ]

    try:
        results = client.search_issues(jql, fields=fields, max_results=sample_size)
        issues = results.get('issues', [])
        patterns['sample_size'] = len(issues)
        print_info(f"  Sampled {len(issues)} issues")
    except Exception as e:
        print_warning(f"  Could not sample issues: {e}")
        return patterns

    if not issues:
        return patterns

    # Aggregate by issue type
    by_type: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        'issue_count': 0,
        'assignees': defaultdict(lambda: {'count': 0, 'display_name': ''}),
        'labels': defaultdict(int),
        'components': defaultdict(int),
        'priorities': defaultdict(int),
        'story_points': []
    })

    # Overall aggregations
    all_labels: Dict[str, int] = defaultdict(int)
    all_assignees: Dict[str, Dict[str, Any]] = defaultdict(lambda: {'count': 0, 'display_name': ''})

    for issue in issues:
        fields_data = issue.get('fields', {})
        issue_type = fields_data.get('issuetype', {}).get('name', 'Unknown')

        type_data = by_type[issue_type]
        type_data['issue_count'] += 1

        # Assignee
        assignee = fields_data.get('assignee')
        if assignee:
            account_id = assignee.get('accountId', 'unknown')
            display_name = assignee.get('displayName', 'Unknown')
            type_data['assignees'][account_id]['count'] += 1
            type_data['assignees'][account_id]['display_name'] = display_name
            all_assignees[account_id]['count'] += 1
            all_assignees[account_id]['display_name'] = display_name

        # Labels
        labels = fields_data.get('labels', [])
        for label in labels:
            type_data['labels'][label] += 1
            all_labels[label] += 1

        # Components
        components = fields_data.get('components', [])
        for comp in components:
            comp_name = comp.get('name', 'Unknown')
            type_data['components'][comp_name] += 1

        # Priority
        priority = fields_data.get('priority')
        if priority:
            priority_name = priority.get('name', 'Unknown')
            type_data['priorities'][priority_name] += 1

        # Story points
        story_points = fields_data.get('customfield_10016')
        if story_points is not None:
            type_data['story_points'].append(story_points)

    # Convert to final format with percentages
    for type_name, type_data in by_type.items():
        issue_count = type_data['issue_count']

        # Convert assignees
        assignees = {}
        for account_id, data in type_data['assignees'].items():
            assignees[account_id] = {
                'display_name': data['display_name'],
                'count': data['count'],
                'percentage': round(data['count'] / issue_count * 100, 1)
            }

        # Convert priorities
        priorities = {}
        for priority_name, count in type_data['priorities'].items():
            priorities[priority_name] = {
                'count': count,
                'percentage': round(count / issue_count * 100, 1)
            }

        # Story points stats
        story_points_list = type_data['story_points']
        story_points_info = {}
        if story_points_list:
            story_points_info = {
                'avg': round(sum(story_points_list) / len(story_points_list), 1),
                'distribution': dict(defaultdict(int))
            }
            for sp in story_points_list:
                story_points_info['distribution'][str(int(sp))] = \
                    story_points_info['distribution'].get(str(int(sp)), 0) + 1

        patterns['by_issue_type'][type_name] = {
            'issue_count': issue_count,
            'assignees': assignees,
            'labels': dict(type_data['labels']),
            'components': dict(type_data['components']),
            'priorities': priorities,
            'story_points': story_points_info
        }

    # Common labels (sorted by frequency)
    sorted_labels = sorted(all_labels.items(), key=lambda x: x[1], reverse=True)
    patterns['common_labels'] = [label for label, _ in sorted_labels[:20]]

    # Top assignees (sorted by total assignments)
    sorted_assignees = sorted(
        all_assignees.items(),
        key=lambda x: x[1]['count'],
        reverse=True
    )
    patterns['top_assignees'] = [
        {
            'account_id': account_id,
            'display_name': data['display_name'],
            'total_assignments': data['count']
        }
        for account_id, data in sorted_assignees[:20]
    ]

    print_info(f"  Found {len(patterns['by_issue_type'])} issue types with patterns")
    print_info(f"  Top assignees: {', '.join([a['display_name'] for a in patterns['top_assignees'][:3]])}")
    print_info(f"  Common labels: {', '.join(patterns['common_labels'][:5])}")

    return patterns


def generate_skill_md(project_key: str, metadata: Dict[str, Any],
                      workflows: Dict[str, Any], patterns: Dict[str, Any]) -> str:
    """
    Generate SKILL.md content for a project skill.

    Args:
        project_key: JIRA project key
        metadata: Discovered metadata
        workflows: Discovered workflows
        patterns: Discovered patterns

    Returns:
        SKILL.md content as string
    """
    project_name = metadata.get('project_name', project_key)
    discovered_at = metadata.get('discovered_at', datetime.utcnow().isoformat() + 'Z')

    # Build issue types list
    issue_types = [t.get('name') for t in metadata.get('issue_types', [])]
    components = [c.get('name') for c in metadata.get('components', [])]
    active_versions = [v.get('name') for v in metadata.get('versions', [])
                       if not v.get('archived') and not v.get('released')][:5]

    # Top assignees
    top_assignees = [a.get('display_name') for a in patterns.get('top_assignees', [])[:5]]
    common_labels = patterns.get('common_labels', [])[:10]

    content = f'''---
name: "JIRA Project Context: {project_key}"
description: "Project-specific context for {project_key} including workflows, defaults, and usage patterns. Auto-discovered from JIRA API."
auto_generated: true
---

# jira-project-{project_key}

Project context for **{project_name}** ({project_key}), providing intelligent defaults and workflow understanding.

## When to use this skill

This skill is automatically loaded when working with issues in the {project_key} project. It provides:
- Default values for issue creation
- Valid workflow transitions
- Usage pattern insights

## Project Overview

- **Project Key**: {project_key}
- **Project Name**: {project_name}
- **Type**: {metadata.get('project_type', 'software')}

### Issue Types
{', '.join(issue_types) if issue_types else 'None discovered'}

### Components
{', '.join(components) if components else 'None configured'}

### Active Versions
{', '.join(active_versions) if active_versions else 'None active'}

## Usage Patterns (Last {patterns.get('sample_period_days', 30)} Days)

**Sample Size**: {patterns.get('sample_size', 0)} issues

### Top Assignees
{chr(10).join(['- ' + name for name in top_assignees]) if top_assignees else 'No assignment data'}

### Common Labels
{', '.join(common_labels) if common_labels else 'No labels used'}

## Context Files

- `context/metadata.json` - Issue types, components, versions, priorities
- `context/workflows.json` - Status transitions by issue type
- `context/patterns.json` - Usage patterns from recent issues
- `defaults.json` - Team-configured default values (edit to customize)

## Refresh Context

To refresh this context from JIRA:

```bash
python .claude/skills/jira-ops/scripts/discover_project.py {project_key}
```

## Last Updated

- **Discovered**: {discovered_at}
- **Sample Period**: {patterns.get('sample_period_days', 30)} days
- **Sample Size**: {patterns.get('sample_size', 0)} issues
'''

    return content


def generate_defaults(project_key: str, metadata: Dict[str, Any],
                      patterns: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate default values based on discovered patterns.

    Creates sensible defaults based on the most common values observed.

    Args:
        project_key: JIRA project key
        metadata: Discovered metadata
        patterns: Discovered patterns

    Returns:
        Defaults dict
    """
    defaults = {
        'project_key': project_key,
        'description': f'Auto-generated defaults for {project_key} based on usage patterns',
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'by_issue_type': {},
        'global': {}
    }

    # Get most common priority overall
    priority_counts: Dict[str, int] = defaultdict(int)
    for type_patterns in patterns.get('by_issue_type', {}).values():
        for priority_name, data in type_patterns.get('priorities', {}).items():
            priority_counts[priority_name] += data.get('count', 0)

    if priority_counts:
        most_common_priority = max(priority_counts.items(), key=lambda x: x[1])[0]
        defaults['global']['priority'] = most_common_priority

    # Per-issue-type defaults
    for type_name, type_patterns in patterns.get('by_issue_type', {}).items():
        type_defaults = {}

        # Most common priority for this type
        priorities = type_patterns.get('priorities', {})
        if priorities:
            top_priority = max(priorities.items(), key=lambda x: x[1].get('count', 0))[0]
            type_defaults['priority'] = top_priority

        # Most common assignee (if > 30% of issues)
        assignees = type_patterns.get('assignees', {})
        if assignees:
            top_assignee = max(assignees.items(), key=lambda x: x[1].get('count', 0))
            if top_assignee[1].get('percentage', 0) >= 30:
                type_defaults['assignee_hint'] = {
                    'account_id': top_assignee[0],
                    'display_name': top_assignee[1].get('display_name')
                }

        # Common labels (if used in > 20% of issues)
        labels = type_patterns.get('labels', {})
        issue_count = type_patterns.get('issue_count', 1)
        common_labels = [
            label for label, count in labels.items()
            if count / issue_count >= 0.2
        ]
        if common_labels:
            type_defaults['suggested_labels'] = common_labels[:3]

        # Average story points
        story_points = type_patterns.get('story_points', {})
        if story_points.get('avg'):
            type_defaults['typical_story_points'] = story_points['avg']

        if type_defaults:
            defaults['by_issue_type'][type_name] = type_defaults

    return defaults


def save_to_skill_directory(project_key: str, metadata: Dict[str, Any],
                            workflows: Dict[str, Any], patterns: Dict[str, Any],
                            defaults: Dict[str, Any]) -> Path:
    """
    Save discovered context to a skill directory.

    Creates:
    .claude/skills/jira-project-{PROJECT_KEY}/
    ├── SKILL.md
    ├── context/
    │   ├── metadata.json
    │   ├── workflows.json
    │   └── patterns.json
    └── defaults.json

    Args:
        project_key: JIRA project key
        metadata: Discovered metadata
        workflows: Discovered workflows
        patterns: Discovered patterns
        defaults: Generated defaults

    Returns:
        Path to skill directory
    """
    skill_path = get_skills_root() / 'skills' / f'jira-project-{project_key}'

    # Create directories
    skill_path.mkdir(parents=True, exist_ok=True)
    context_dir = skill_path / 'context'
    context_dir.mkdir(exist_ok=True)

    # Write SKILL.md
    skill_md = generate_skill_md(project_key, metadata, workflows, patterns)
    (skill_path / 'SKILL.md').write_text(skill_md, encoding='utf-8')

    # Write context files
    (context_dir / 'metadata.json').write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding='utf-8'
    )
    (context_dir / 'workflows.json').write_text(
        json.dumps(workflows, indent=2, ensure_ascii=False), encoding='utf-8'
    )
    (context_dir / 'patterns.json').write_text(
        json.dumps(patterns, indent=2, ensure_ascii=False), encoding='utf-8'
    )

    # Write defaults
    (skill_path / 'defaults.json').write_text(
        json.dumps(defaults, indent=2, ensure_ascii=False), encoding='utf-8'
    )

    return skill_path


def save_to_settings_local(project_key: str, defaults: Dict[str, Any],
                           profile: str = 'production') -> Path:
    """
    Save defaults to settings.local.json for personal use.

    Args:
        project_key: JIRA project key
        defaults: Defaults to save
        profile: JIRA profile name

    Returns:
        Path to settings.local.json
    """
    settings_path = get_skills_root().parent / 'settings.local.json'

    # Load existing settings or create new
    if settings_path.exists():
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
    else:
        settings = {}

    # Ensure structure exists
    if 'jira' not in settings:
        settings['jira'] = {}
    if 'profiles' not in settings['jira']:
        settings['jira']['profiles'] = {}
    if profile not in settings['jira']['profiles']:
        settings['jira']['profiles'][profile] = {}
    if 'projects' not in settings['jira']['profiles'][profile]:
        settings['jira']['profiles'][profile]['projects'] = {}

    # Add project defaults
    settings['jira']['profiles'][profile]['projects'][project_key] = {
        'defaults': defaults.get('by_issue_type', {}),
        'global_defaults': defaults.get('global', {})
    }

    # Write settings
    with open(settings_path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

    return settings_path


def discover_project(project_key: str, profile: str = None,
                     sample_size: int = 100, sample_period_days: int = 30,
                     save_skill: bool = True, save_personal: bool = False) -> Dict[str, Any]:
    """
    Main discovery function.

    Args:
        project_key: JIRA project key
        profile: JIRA profile to use
        sample_size: Number of issues to sample for patterns
        sample_period_days: How many days back to sample
        save_skill: If True, save to skill directory
        save_personal: If True, save to settings.local.json

    Returns:
        Dict with all discovered context
    """
    client = get_jira_client(profile)

    try:
        # Discover metadata
        metadata = discover_metadata(client, project_key)

        # Discover workflows
        workflows = discover_workflows(client, project_key, metadata)

        # Discover patterns
        patterns = discover_patterns(client, project_key, sample_size, sample_period_days)

        # Generate defaults
        defaults = generate_defaults(project_key, metadata, patterns)

        context = {
            'metadata': metadata,
            'workflows': workflows,
            'patterns': patterns,
            'defaults': defaults
        }

        # Save outputs
        if save_skill:
            skill_path = save_to_skill_directory(
                project_key, metadata, workflows, patterns, defaults
            )
            print_success(f"Saved skill directory: {skill_path}")

        if save_personal:
            settings_path = save_to_settings_local(
                project_key, defaults, profile or 'production'
            )
            print_success(f"Saved to settings: {settings_path}")

        return context

    finally:
        client.close()


def main():
    parser = argparse.ArgumentParser(
        description='Discover JIRA project context and save to skill directory',
        epilog='''
Examples:
  %(prog)s PROJ                           # Discover and save to skill directory
  %(prog)s PROJ --profile development     # Use specific profile
  %(prog)s PROJ --personal                # Save to settings.local.json only
  %(prog)s PROJ --sample-size 200         # Sample more issues for patterns
  %(prog)s PROJ --output json --no-save   # Output JSON without saving
        '''
    )

    parser.add_argument('project_key',
                        help='JIRA project key (e.g., PROJ)')
    parser.add_argument('--profile',
                        help='JIRA profile to use (default: from config)')
    parser.add_argument('--sample-size', '-s',
                        type=int,
                        default=100,
                        help='Number of issues to sample for patterns (default: 100)')
    parser.add_argument('--days', '-d',
                        type=int,
                        default=30,
                        help='Sample period in days (default: 30)')
    parser.add_argument('--personal', '-p',
                        action='store_true',
                        help='Save to settings.local.json instead of skill directory')
    parser.add_argument('--both',
                        action='store_true',
                        help='Save to both skill directory and settings.local.json')
    parser.add_argument('--no-save',
                        action='store_true',
                        help='Do not save output (useful with --output json)')
    parser.add_argument('--output', '-o',
                        choices=['text', 'json'],
                        default='text',
                        help='Output format (default: text)')

    args = parser.parse_args()

    # Normalize project key to uppercase
    project_key = args.project_key.upper()

    # Determine save options
    save_skill = not args.personal and not args.no_save
    save_personal = args.personal or args.both

    if args.both:
        save_skill = True
        save_personal = True

    try:
        context = discover_project(
            project_key=project_key,
            profile=args.profile,
            sample_size=args.sample_size,
            sample_period_days=args.days,
            save_skill=save_skill,
            save_personal=save_personal
        )

        if args.output == 'json':
            print(format_json(context))
        elif not args.no_save:
            print()
            print_success(f"Discovery complete for {project_key}!")
            print()
            print("Next steps:")
            print(f"  1. Review defaults.json in .claude/skills/jira-project-{project_key}/")
            print("  2. Customize defaults as needed")
            print("  3. Commit the skill directory to share with your team")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
