#!/usr/bin/env python3
"""
Search automation rules with filters.

Search for automation rules by trigger type, state, and/or scope.

Usage:
    python search_automation_rules.py --trigger "jira.issue.event.trigger:created"
    python search_automation_rules.py --state enabled
    python search_automation_rules.py --scope "ari:cloud:jira:...:project/10000"
    python search_automation_rules.py --trigger issue_created --state enabled
    python search_automation_rules.py --project PROJ
    python search_automation_rules.py --output json
    python search_automation_rules.py --profile development
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_automation_client
from error_handler import print_error, JiraError, AutomationError
from formatters import format_table


def search_automation_rules(
    client=None,
    trigger: Optional[str] = None,
    state: Optional[str] = None,
    scope: Optional[str] = None,
    project: Optional[str] = None,
    limit: int = 50,
    fetch_all: bool = False,
    profile: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search automation rules with filters.

    Args:
        client: AutomationClient instance (optional, created if not provided)
        trigger: Filter by trigger type
        state: Filter by state ('enabled' or 'disabled')
        scope: Filter by scope (project ARI)
        project: Filter by project key (converted to scope)
        limit: Maximum results per page
        fetch_all: If True, fetch all pages
        profile: JIRA profile to use

    Returns:
        List of matching automation rules
    """
    if client is None:
        client = get_automation_client(profile)

    # Convert project key to scope if provided
    if project and not scope:
        # In production, we'd need to look up the project ARI
        scope = f"ari:cloud:jira:*:project/{project}" if not project.startswith('ari:') else project

    all_rules = []
    cursor = None

    while True:
        response = client.search_rules(
            trigger=trigger,
            state=state.upper() if state else None,
            scope=scope,
            limit=limit,
            cursor=cursor
        )

        rules = response.get('values', [])
        all_rules.extend(rules)

        # Check for pagination
        if not fetch_all or not response.get('hasMore', False):
            break

        # Get next cursor
        links = response.get('links', {})
        next_link = links.get('next', '')
        if '?cursor=' in next_link:
            cursor = next_link.split('?cursor=')[-1]
        else:
            break

    return all_rules


def format_rule_summary(rule: Dict[str, Any]) -> Dict[str, str]:
    """Format a rule for display."""
    scope_resources = rule.get('ruleScope', {}).get('resources', [])
    scope = 'Global' if not scope_resources else 'Project'

    trigger = rule.get('trigger', {})
    trigger_type = trigger.get('type', 'Unknown')
    # Simplify trigger type for display
    if ':' in trigger_type:
        trigger_display = trigger_type.split(':')[-1]
    else:
        trigger_display = trigger_type

    return {
        'Name': rule.get('name', 'Unnamed'),
        'State': rule.get('state', 'UNKNOWN'),
        'Scope': scope,
        'Trigger': trigger_display,
        'Updated': rule.get('updated', '')[:10] if rule.get('updated') else 'N/A'
    }


# Common trigger type shortcuts
TRIGGER_SHORTCUTS = {
    'issue_created': 'jira.issue.event.trigger:created',
    'created': 'jira.issue.event.trigger:created',
    'issue_updated': 'jira.issue.event.trigger:updated',
    'updated': 'jira.issue.event.trigger:updated',
    'issue_transitioned': 'jira.issue.event.trigger:transitioned',
    'transitioned': 'jira.issue.event.trigger:transitioned',
    'comment_added': 'jira.issue.event.trigger:comment_added',
    'comment': 'jira.issue.event.trigger:comment_added',
    'field_changed': 'jira.issue.field.changed',
    'priority_changed': 'jira.issue.field.changed:priority',
    'assignee_changed': 'jira.issue.field.changed:assignee',
    'status_changed': 'jira.issue.field.changed:status',
    'scheduled': 'jira.scheduled.trigger',
    'manual': 'jira.manual.trigger'
}


def expand_trigger(trigger: str) -> str:
    """Expand trigger shortcut to full type."""
    return TRIGGER_SHORTCUTS.get(trigger.lower(), trigger)


def main():
    parser = argparse.ArgumentParser(
        description='Search automation rules with filters',
        epilog='''
Examples:
    # Search by trigger type
    python search_automation_rules.py --trigger "jira.issue.event.trigger:created"
    python search_automation_rules.py --trigger issue_created  # shortcut

    # Search by state
    python search_automation_rules.py --state enabled
    python search_automation_rules.py --state disabled

    # Search by scope
    python search_automation_rules.py --scope "ari:cloud:jira:...:project/10000"
    python search_automation_rules.py --project PROJ

    # Combined search
    python search_automation_rules.py --trigger issue_created --state enabled
    python search_automation_rules.py --trigger transitioned --project PROJ

    # Output as JSON
    python search_automation_rules.py --trigger issue_created --output json

    # Use specific profile
    python search_automation_rules.py --profile development

Trigger shortcuts:
    issue_created, created     -> jira.issue.event.trigger:created
    issue_updated, updated     -> jira.issue.event.trigger:updated
    issue_transitioned, transitioned -> jira.issue.event.trigger:transitioned
    comment_added, comment     -> jira.issue.event.trigger:comment_added
    field_changed              -> jira.issue.field.changed
    priority_changed           -> jira.issue.field.changed:priority
    assignee_changed           -> jira.issue.field.changed:assignee
    status_changed             -> jira.issue.field.changed:status
    scheduled                  -> jira.scheduled.trigger
    manual                     -> jira.manual.trigger
        '''
    )

    parser.add_argument('--trigger', '-t', help='Filter by trigger type (or shortcut)')
    parser.add_argument('--state', '-s', choices=['enabled', 'disabled'],
                        help='Filter by state')
    parser.add_argument('--scope', help='Filter by scope (project ARI)')
    parser.add_argument('--project', '-p', help='Filter by project key')
    parser.add_argument('--limit', '-l', type=int, default=50,
                        help='Maximum results (default: 50)')
    parser.add_argument('--all', '-a', action='store_true', dest='fetch_all',
                        help='Fetch all pages of results')
    parser.add_argument('--output', '-o', choices=['table', 'json', 'csv'],
                        default='table', help='Output format (default: table)')
    parser.add_argument('--profile', help='JIRA profile to use')

    args = parser.parse_args()

    # At least one filter should be provided
    if not any([args.trigger, args.state, args.scope, args.project]):
        parser.error("At least one filter (--trigger, --state, --scope, --project) must be provided")

    try:
        # Expand trigger shortcut if provided
        trigger = expand_trigger(args.trigger) if args.trigger else None

        rules = search_automation_rules(
            trigger=trigger,
            state=args.state,
            scope=args.scope,
            project=args.project,
            limit=args.limit,
            fetch_all=args.fetch_all,
            profile=args.profile
        )

        if not rules:
            print("No automation rules found matching the criteria.")
            return

        if args.output == 'json':
            print(json.dumps(rules, indent=2))
        elif args.output == 'csv':
            # CSV output
            headers = ['Name', 'State', 'Scope', 'Trigger', 'Updated']
            print(','.join(headers))
            for rule in rules:
                formatted = format_rule_summary(rule)
                row = [f'"{formatted[h]}"' for h in headers]
                print(','.join(row))
        else:
            # Table output
            filters = []
            if args.trigger:
                filters.append(f"trigger={args.trigger}")
            if args.state:
                filters.append(f"state={args.state}")
            if args.project:
                filters.append(f"project={args.project}")
            if args.scope:
                filters.append(f"scope={args.scope[:30]}...")

            print(f"\nSearch Results ({len(rules)} found)")
            print(f"Filters: {', '.join(filters)}")
            print("=" * 80)

            rows = [format_rule_summary(rule) for rule in rules]
            if rows:
                table = format_table(rows)
                print(table)

    except (JiraError, AutomationError) as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
